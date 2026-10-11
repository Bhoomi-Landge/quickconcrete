import os
import unittest
from datetime import date, timedelta

from models import Order, Plant, Supplier, User, db
from services.seed_service import DEMO_SUPPLIER_EMAIL

from test_authorization import register_supplier
from test_helpers import (
    base_order_json,
    demo_plant_id,
    full_requirements_payload,
    login,
    make_app,
    register_contractor,
)


class OrderModificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.db_path = make_app()
        cls.client = cls.app.test_client()
        cls.plant_id = demo_plant_id(cls.app)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.db_path)

    def setUp(self):
        self.client.post("/api/auth/logout")

    def _place_placed_order(self, tag="mod"):
        email, _ = register_contractor(self.client, tag)
        r = self.client.post(
            "/api/sites",
            json={"site_name": "S", "address": "A", "city": "Mumbai", "pincode": "400001"},
        )
        site_id = r.json["site"]["id"]
        r = self.client.post(
            "/api/orders",
            json=base_order_json(site_id, self.plant_id, **full_requirements_payload()),
        )
        self.assertEqual(r.status_code, 201, r.json)
        return email, r.json["order"]["id"], site_id

    def test_contractor_edits_own_placed_order(self):
        email, order_id, site_id = self._place_placed_order("edit1")
        tomorrow = (date.today() + timedelta(days=2)).isoformat()
        r = self.client.patch(
            f"/api/orders/{order_id}",
            json={"quantity_m3": 4, "delivery_date": tomorrow, "delivery_time": "14:00"},
        )
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(r.json["order"]["quantity_m3"], 4)
        self.assertIsNotNone(r.json["order"]["contractor_modified_at"])

    def test_other_contractor_cannot_edit(self):
        _, order_id, _ = self._place_placed_order("edit2")
        self.client.post("/api/auth/logout")
        register_contractor(self.client, "edit2b")
        r = self.client.patch(f"/api/orders/{order_id}", json={"quantity_m3": 1})
        self.assertEqual(r.status_code, 404)

    def test_supplier_cannot_use_contractor_patch(self):
        _, order_id, _ = self._place_placed_order("edit3")
        self.client.post("/api/auth/logout")
        login(self.client, DEMO_SUPPLIER_EMAIL, "demo123")
        r = self.client.patch(f"/api/orders/{order_id}", json={"quantity_m3": 1})
        self.assertEqual(r.status_code, 403)

    def test_cannot_edit_accepted_order(self):
        email, order_id, _ = self._place_placed_order("edit4")
        self.client.post("/api/auth/logout")
        login(self.client, DEMO_SUPPLIER_EMAIL, "demo123")
        self.client.post(f"/api/supplier/orders/{order_id}/accept")
        self.client.post("/api/auth/logout")
        login(self.client, email, "secret1")
        r = self.client.patch(f"/api/orders/{order_id}", json={"quantity_m3": 1})
        self.assertEqual(r.status_code, 409)

    def test_delivery_time_today_in_past_rejected(self):
        _, order_id, _ = self._place_placed_order("edit5b")
        r = self.client.patch(
            f"/api/orders/{order_id}",
            json={"delivery_date": date.today().isoformat(), "delivery_time": "00:01"},
        )
        self.assertEqual(r.status_code, 400)

    def test_invalid_quantity_and_delivery_date(self):
        _, order_id, _ = self._place_placed_order("edit5")
        r = self.client.patch(f"/api/orders/{order_id}", json={"quantity_m3": -1})
        self.assertEqual(r.status_code, 400)
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        r = self.client.patch(
            f"/api/orders/{order_id}",
            json={"delivery_date": yesterday, "delivery_time": "10:00"},
        )
        self.assertEqual(r.status_code, 400)

    def test_cannot_use_other_contractors_site(self):
        email_a, order_id, _ = self._place_placed_order("edit6a")
        self.client.post("/api/auth/logout")
        register_contractor(self.client, "edit6b")
        r = self.client.post(
            "/api/sites",
            json={"site_name": "B", "address": "B", "city": "Mumbai", "pincode": "400002"},
        )
        other_site = r.json["site"]["id"]
        self.client.post("/api/auth/logout")
        login(self.client, email_a, "secret1")
        r = self.client.patch(f"/api/orders/{order_id}", json={"site_id": other_site})
        self.assertEqual(r.status_code, 404)

    def test_invalid_plant_grade_combination(self):
        email, order_id, _ = self._place_placed_order("edit7")
        self.client.post("/api/auth/logout")
        register_supplier(self.client, "badg", "Bad Grade Co")
        with self.app.app_context():
            user = User.query.filter_by(email="badg_supplier@test.local").first()
            supplier = Supplier.query.filter_by(user_id=user.id).first()
            plant_b = Plant.query.filter_by(supplier_id=supplier.id).first()
            bad_plant = plant_b.id
        self.client.post("/api/auth/logout")
        login(self.client, email, "secret1")
        r = self.client.patch(
            f"/api/orders/{order_id}",
            json={"plant_id": bad_plant, "concrete_grade": "M99"},
        )
        self.assertEqual(r.status_code, 404)

    def test_update_requirements(self):
        _, order_id, _ = self._place_placed_order("edit8")
        r = self.client.patch(
            f"/api/orders/{order_id}",
            json={
                "pump_required": False,
                "placement_method": "CHUTE",
                "workability_test_type": "SLUMP_FLOW",
                "target_slump_mm": 650,
                "minimum_slump_mm": None,
                "maximum_slump_mm": None,
                "special_concrete_type": "SCC",
            },
        )
        self.assertEqual(r.status_code, 200, r.json)
        self.assertFalse(r.json["order"]["pump_required"])
        self.assertEqual(r.json["order"]["special_concrete_type"], "SCC")

    def test_partial_update_preserves_omitted_fields(self):
        _, order_id, _ = self._place_placed_order("edit9")
        with self.app.app_context():
            before = Order.query.get(order_id)
            prev_grade = before.concrete_grade
            prev_pump = before.pump_required
        r = self.client.patch(f"/api/orders/{order_id}", json={"quantity_m3": 3})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["order"]["concrete_grade"], prev_grade)
        self.assertEqual(r.json["order"]["pump_required"], prev_pump)

    def test_invalid_partial_requirement_patch(self):
        _, order_id, _ = self._place_placed_order("edit10")
        r = self.client.patch(
            f"/api/orders/{order_id}",
            json={"pump_required": False, "pump_type": "BOOM"},
        )
        self.assertEqual(r.status_code, 400)

    def test_supplier_sees_latest_requirements(self):
        _, order_id, _ = self._place_placed_order("edit11")
        r = self.client.patch(
            f"/api/orders/{order_id}",
            json={
                "pump_required": False,
                "placement_method": "DIRECT_DISCHARGE",
                "workability_test_type": "SLUMP",
                "target_slump_mm": 80,
                "minimum_slump_mm": None,
                "maximum_slump_mm": None,
                "special_concrete_type": "NORMAL",
            },
        )
        self.assertEqual(r.status_code, 200, r.json)
        self.client.post("/api/auth/logout")
        login(self.client, DEMO_SUPPLIER_EMAIL, "demo123")
        r = self.client.get(f"/api/supplier/orders/{order_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["order"]["placement_method"], "DIRECT_DISCHARGE")
        self.assertEqual(r.json["order"]["target_slump_mm"], 80)

    def test_legacy_null_requirements_still_readable(self):
        _, order_id, _ = self._place_placed_order("edit12")
        with self.app.app_context():
            order = Order.query.get(order_id)
            order.pump_required = None
            order.placement_method = None
            db.session.commit()
        r = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json["order"]["pump_required"])


if __name__ == "__main__":
    unittest.main()
