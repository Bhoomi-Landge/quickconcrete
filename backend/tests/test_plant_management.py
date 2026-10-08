import os
import tempfile
import unittest

from models import Plant, User, db
from services.auth_service import hash_password


def make_app():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"
    from app import create_app

    return create_app(), path


def register_supplier(client, tag):
    email = f"{tag}_plants@test.local"
    r = client.post(
        "/api/auth/register",
        json={"name": f"S {tag}", "email": email, "password": "secret1", "role": "SUPPLIER"},
    )
    assert r.status_code == 201
    return email


class PlantManagementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.db_path = make_app()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.db_path)

    def test_supplier_plant_and_product_crud(self):
        email_a = register_supplier(self.client, "pla")
        r = self.client.post(
            "/api/supplier/plants",
            json={
                "plant_name": "Plant Alpha",
                "address": "Road 1",
                "city": "Mumbai",
                "pincode": "400001",
                "contact_phone": "9999999999",
                "operating_hours": "6am-6pm",
            },
        )
        self.assertEqual(r.status_code, 201)
        plant_id = r.json["plant"]["id"]

        r = self.client.get("/api/supplier/plants")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(p["id"] == plant_id for p in r.json["plants"]))

        r = self.client.post(
            f"/api/supplier/plants/{plant_id}/products",
            json={
                "grade": "M30",
                "price_per_m3": 5200,
                "available_quantity": 100,
                "minimum_order_m3": 2,
            },
        )
        self.assertEqual(r.status_code, 201)
        product_id = r.json["product"]["id"]

        r = self.client.get(f"/api/supplier/plants/{plant_id}/products")
        self.assertEqual(len(r.json["products"]), 1)

        r = self.client.patch(
            f"/api/supplier/products/{product_id}",
            json={"price_per_m3": 5300, "is_available": True},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["product"]["price_per_m3"], 5300)

        self.client.post("/api/auth/logout")
        register_supplier(self.client, "plb")
        r = self.client.get(f"/api/supplier/plants/{plant_id}")
        self.assertEqual(r.status_code, 404)
        r = self.client.get(f"/api/supplier/products/{product_id}")
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
