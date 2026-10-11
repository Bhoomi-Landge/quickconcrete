import os
import unittest

from services.seed_service import DEMO_SUPPLIER_EMAIL
from test_helpers import (
    base_order_json,
    demo_plant_id,
    full_requirements_payload,
    login,
    make_app,
    register_contractor,
)
class OrderRequirementsTests(unittest.TestCase):
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

    def _create_site(self):
        register_contractor(self.client, f"req{id(self)}")
        r = self.client.post(
            "/api/sites",
            json={
                "site_name": "Site",
                "address": "A",
                "city": "Mumbai",
                "pincode": "400001",
            },
        )
        self.assertEqual(r.status_code, 201, r.json)
        return r.json["site"]["id"]

    def test_valid_order_with_all_new_fields(self):
        site_id = self._create_site()
        payload = base_order_json(site_id, self.plant_id, **full_requirements_payload())
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 201, r.json)
        order = r.json["order"]
        self.assertTrue(order["pump_required"])
        self.assertEqual(order["pump_type"], "BOOM")
        self.assertEqual(order["placement_method"], "PUMP")
        self.assertEqual(order["workability_test_type"], "SLUMP")
        self.assertEqual(order["target_slump_mm"], 100)
        self.assertEqual(order["special_concrete_type"], "NORMAL")

    def test_legacy_client_without_new_fields(self):
        site_id = self._create_site()
        payload = base_order_json(site_id, self.plant_id)
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 201, r.json)
        order = r.json["order"]
        self.assertIsNone(order["pump_required"])
        self.assertIsNone(order["placement_method"])

    def test_invalid_pump_required_string(self):
        site_id = self._create_site()
        payload = base_order_json(
            site_id,
            self.plant_id,
            pump_required="maybe",
            placement_method="CHUTE",
            workability_test_type="SLUMP",
            target_slump_mm=100,
            special_concrete_type="NORMAL",
        )
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 400)
        self.assertIn("true or false", r.json["error"])

    def test_pump_required_false_string_not_truthy(self):
        site_id = self._create_site()
        payload = base_order_json(
            site_id,
            self.plant_id,
            pump_required="false",
            placement_method="CHUTE",
            workability_test_type="SLUMP",
            target_slump_mm=100,
            special_concrete_type="NORMAL",
        )
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 201, r.json)
        self.assertFalse(r.json["order"]["pump_required"])

    def test_invalid_placement_method(self):
        site_id = self._create_site()
        payload = base_order_json(
            site_id,
            self.plant_id,
            pump_required=False,
            placement_method="HELICOPTER",
            workability_test_type="SLUMP",
            target_slump_mm=100,
            special_concrete_type="NORMAL",
        )
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 400)

    def test_invalid_workability_test_type(self):
        site_id = self._create_site()
        payload = base_order_json(
            site_id,
            self.plant_id,
            pump_required=False,
            placement_method="CHUTE",
            workability_test_type="FLOW",
            target_slump_mm=100,
            special_concrete_type="NORMAL",
        )
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 400)

    def test_negative_and_out_of_range_measurements(self):
        site_id = self._create_site()
        base = {
            "pump_required": False,
            "placement_method": "CHUTE",
            "workability_test_type": "SLUMP",
            "special_concrete_type": "NORMAL",
        }
        for target in [0, -5, 10001]:
            r = self.client.post(
                "/api/orders",
                json=base_order_json(site_id, self.plant_id, **base, target_slump_mm=target),
            )
            self.assertEqual(r.status_code, 400, target)

    def test_invalid_range_and_target_outside_range(self):
        site_id = self._create_site()
        base = {
            "pump_required": False,
            "placement_method": "CHUTE",
            "workability_test_type": "SLUMP",
            "special_concrete_type": "NORMAL",
        }
        r = self.client.post(
            "/api/orders",
            json=base_order_json(
                site_id,
                self.plant_id,
                **base,
                target_slump_mm=100,
                minimum_slump_mm=110,
                maximum_slump_mm=120,
            ),
        )
        self.assertEqual(r.status_code, 400)

        r = self.client.post(
            "/api/orders",
            json=base_order_json(
                site_id,
                self.plant_id,
                **base,
                target_slump_mm=50,
                minimum_slump_mm=60,
                maximum_slump_mm=80,
            ),
        )
        self.assertEqual(r.status_code, 400)

    def test_invalid_special_concrete_type(self):
        site_id = self._create_site()
        payload = base_order_json(
            site_id,
            self.plant_id,
            pump_required=False,
            placement_method="CHUTE",
            workability_test_type="SLUMP",
            target_slump_mm=100,
            special_concrete_type="MAGIC",
        )
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 400)

    def test_pump_details_rejected_without_pump(self):
        site_id = self._create_site()
        payload = base_order_json(
            site_id,
            self.plant_id,
            pump_required=False,
            pump_type="BOOM",
            placement_method="CHUTE",
            workability_test_type="SLUMP",
            target_slump_mm=100,
            special_concrete_type="NORMAL",
        )
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 400)

    def test_placement_pump_conflict(self):
        site_id = self._create_site()
        payload = base_order_json(
            site_id,
            self.plant_id,
            pump_required=False,
            placement_method="PUMP",
            workability_test_type="SLUMP",
            target_slump_mm=100,
            special_concrete_type="NORMAL",
        )
        r = self.client.post("/api/orders", json=payload)
        self.assertEqual(r.status_code, 400)
        self.assertIn("Without pump", r.json["error"])

    def test_fields_in_contractor_and_supplier_responses(self):
        site_id = self._create_site()
        payload = base_order_json(site_id, self.plant_id, **full_requirements_payload())
        r = self.client.post("/api/orders", json=payload)
        order_id = r.json["order"]["id"]

        r = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["order"]["pump_type"], "BOOM")

        self.client.post("/api/auth/logout")
        login(self.client, DEMO_SUPPLIER_EMAIL, "demo123")
        r = self.client.get(f"/api/supplier/orders/{order_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["order"]["workability_test_type"], "SLUMP")

    def test_null_requirements_readable_after_fetch(self):
        site_id = self._create_site()
        r = self.client.post("/api/orders", json=base_order_json(site_id, self.plant_id))
        order_id = r.json["order"]["id"]
        r = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json["order"]["pump_required"])
        self.assertIsNone(r.json["order"]["target_slump_mm"])

    def test_contractor_order_isolation_with_requirements(self):
        email_a, _ = register_contractor(self.client, "isoA")
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
        order_id = r.json["order"]["id"]
        self.client.post("/api/auth/logout")

        register_contractor(self.client, "isoB")
        r = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(r.status_code, 404)

        login(self.client, email_a, "secret1")
        r = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
