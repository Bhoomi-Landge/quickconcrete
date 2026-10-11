import os
import unittest

from models import Plant, db
from test_helpers import base_order_json, demo_plant_id, login, make_app, register_contractor
from test_authorization import register_supplier


class QuotationTests(unittest.TestCase):
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

    def _set_plant_charges(self, plant_id, **kwargs):
        with self.app.app_context():
            plant = Plant.query.get(plant_id)
            for key, val in kwargs.items():
                setattr(plant, key, val)
            db.session.commit()

    def test_concrete_subtotal_only_when_no_extra_charges(self):
        register_contractor(self.client, "q1")
        r = self.client.post(
            "/api/orders/estimate",
            json={
                "site_id": self._site_id(),
                "plant_id": self.plant_id,
                "concrete_grade": "M25",
                "quantity_m3": 2,
                "pump_required": False,
            },
        )
        self.assertEqual(r.status_code, 200, r.json)
        est = r.json["estimate"]
        self.assertEqual(est["total_amount"], est["quotation"]["concrete_subtotal_inr"])
        self.assertTrue(est["quotation"]["has_unknown_charges"])

    def _site_id(self):
        r = self.client.post(
            "/api/sites",
            json={"site_name": "S", "address": "A", "city": "Mumbai", "pincode": "400001"},
        )
        return r.json["site"]["id"]

    def test_pump_charge_when_applicable_and_published(self):
        self._set_plant_charges(self.plant_id, pump_charge_inr=5000.0)
        register_contractor(self.client, "q2")
        r = self.client.post(
            "/api/orders/estimate",
            json={
                "site_id": self._site_id(),
                "plant_id": self.plant_id,
                "concrete_grade": "M25",
                "quantity_m3": 2,
                "pump_required": True,
            },
        )
        self.assertEqual(r.status_code, 200, r.json)
        q = r.json["estimate"]["quotation"]
        pump_lines = [l for l in q["lines"] if l["code"] == "PUMP"]
        self.assertEqual(pump_lines[0]["amount_inr"], 5000.0)
        self.assertGreater(q["estimated_total_inr"], q["concrete_subtotal_inr"])

    def test_pump_unknown_when_required_but_not_published(self):
        self._set_plant_charges(self.plant_id, pump_charge_inr=None)
        register_contractor(self.client, "q3")
        r = self.client.post(
            "/api/orders/estimate",
            json={
                "site_id": self._site_id(),
                "plant_id": self.plant_id,
                "concrete_grade": "M25",
                "quantity_m3": 2,
                "pump_required": True,
            },
        )
        q = r.json["estimate"]["quotation"]
        self.assertIn("PUMP", q["unknown_charge_codes"])
        pump_line = next(l for l in q["lines"] if l["code"] == "PUMP")
        self.assertEqual(pump_line["status"], "unknown")

    def test_transport_included_when_supplied(self):
        self._set_plant_charges(self.plant_id, transport_charge_per_m3=100.0)
        register_contractor(self.client, "q4")
        r = self.client.post(
            "/api/orders/estimate",
            json={
                "site_id": self._site_id(),
                "plant_id": self.plant_id,
                "concrete_grade": "M25",
                "quantity_m3": 2,
                "pump_required": False,
            },
        )
        q = r.json["estimate"]["quotation"]
        transport = next(l for l in q["lines"] if l["code"] == "TRANSPORT")
        self.assertEqual(transport["amount_inr"], 200.0)

    def test_gst_calculation(self):
        self._set_plant_charges(self.plant_id, gst_rate_percent=18.0, transport_charge_per_m3=0.0)
        register_contractor(self.client, "q5")
        r = self.client.post(
            "/api/orders/estimate",
            json={
                "site_id": self._site_id(),
                "plant_id": self.plant_id,
                "concrete_grade": "M25",
                "quantity_m3": 2,
                "pump_required": False,
            },
        )
        q = r.json["estimate"]["quotation"]
        self.assertEqual(q["tax"]["gst_amount_inr"], round(q["subtotal_known_inr"] * 0.18, 2))

    def test_negative_plant_charge_rejected(self):
        register_supplier(self.client, "qsup", "Q Sup")
        with self.app.app_context():
            from models import User, Supplier

            user = User.query.filter_by(email="qsup_supplier@test.local").first()
            plant = Plant.query.filter_by(supplier_id=Supplier.query.filter_by(user_id=user.id).first().id).first()
            plant_id = plant.id
        with self.app.app_context():
            plant = Plant.query.get(plant_id)
            payload = {
                "plant_name": plant.plant_name,
                "address": plant.address,
                "city": plant.city,
                "pincode": plant.pincode,
                "pump_charge_inr": -10,
            }
        r = self.client.put(f"/api/supplier/plants/{plant_id}", json=payload)
        self.assertEqual(r.status_code, 400)

    def test_supplier_cannot_read_other_plant_pricing_via_compare(self):
        register_supplier(self.client, "qa", "A")
        self.client.post("/api/auth/logout")
        register_supplier(self.client, "qb", "B")
        login(self.client, "qb_supplier@test.local", "secret1")
        r = self.client.get("/api/supplier/plants/99999")
        self.assertEqual(r.status_code, 404)

    def test_compare_returns_multiple_offers(self):
        register_contractor(self.client, "q6")
        r = self.client.post(
            "/api/orders/compare",
            json={"concrete_grade": "M25", "quantity_m3": 2, "pump_required": False},
        )
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json["offers"]), 1)

    def test_create_order_still_uses_concrete_subtotal(self):
        register_contractor(self.client, "q7")
        site_id = self._site_id()
        self._set_plant_charges(self.plant_id, pump_charge_inr=9000.0, gst_rate_percent=18.0)
        r = self.client.post(
            "/api/orders",
            json=base_order_json(site_id, self.plant_id, pump_required=True, placement_method="PUMP",
                                  workability_test_type="SLUMP", target_slump_mm=100,
                                  special_concrete_type="NORMAL"),
        )
        self.assertEqual(r.status_code, 201, r.json)
        order = r.json["order"]
        self.assertEqual(order["total_amount"], round(order["quantity_m3"] * order["price_per_m3"], 2))


if __name__ == "__main__":
    unittest.main()
