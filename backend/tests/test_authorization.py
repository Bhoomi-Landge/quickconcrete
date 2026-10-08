import os
import tempfile
import unittest
from datetime import date, timedelta

from models import ConcreteProduct, Order, Plant, Site, Supplier, Truck, User, db
from services.auth_service import hash_password


def make_app():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"
    from app import create_app

    app = create_app()
    return app, path


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def register_contractor(client, tag):
    email = f"{tag}_contractor@test.local"
    r = client.post(
        "/api/auth/register",
        json={"name": f"C {tag}", "email": email, "password": "secret1", "role": "CONTRACTOR"},
    )
    assert r.status_code == 201, r.json
    return email, r.json["user"]["id"]


def register_supplier(client, tag, company):
    email = f"{tag}_supplier@test.local"
    r = client.post(
        "/api/auth/register",
        json={"name": f"S {tag}", "email": email, "password": "secret1", "role": "SUPPLIER"},
    )
    assert r.status_code == 201, r.json
    with client.application.app_context():
        user = User.query.filter_by(email=email).first()
        supplier = Supplier.query.filter_by(user_id=user.id).first()
        plant = Plant.query.filter_by(supplier_id=supplier.id).first()
        product = ConcreteProduct(
            plant_id=plant.id,
            supplier_id=supplier.id,
            grade="M25",
            price_per_m3=5000,
            available_quantity=100,
            is_available=True,
        )
        truck = Truck(
            plant_id=plant.id,
            supplier_id=supplier.id,
            truck_number=f"MH-{tag.upper()}",
            driver_name="Driver",
            driver_phone="9999999999",
            capacity_m3=6,
            is_available=True,
        )
        db.session.add(product)
        db.session.add(truck)
        db.session.commit()
        return email, supplier.id, plant.id, product.id, truck.id


class AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.db_path = make_app()
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            admin = User(
                name="Admin",
                email="auth_admin@test.local",
                password_hash=hash_password("admin123"),
                role="ADMIN",
            )
            db.session.add(admin)
            db.session.commit()

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.db_path)

    def setUp(self):
        self.client.post("/api/auth/logout")

    def test_contractor_site_isolation(self):
        email_a, _ = register_contractor(self.client, "a")
        r = self.client.post(
            "/api/sites",
            json={
                "site_name": "A Site",
                "address": "A",
                "city": "Mumbai",
                "pincode": "400001",
            },
        )
        site_a = r.json["site"]["id"]
        self.client.post("/api/auth/logout")

        register_contractor(self.client, "b")
        r = self.client.get(f"/api/sites/{site_a}")
        self.assertEqual(r.status_code, 404)

        login(self.client, email_a, "secret1")
        r = self.client.get(f"/api/sites/{site_a}")
        self.assertEqual(r.status_code, 200)

    def test_contractor_order_isolation(self):
        email_a, _ = register_contractor(self.client, "oa")
        r = self.client.post(
            "/api/sites",
            json={"site_name": "S", "address": "A", "city": "Mumbai", "pincode": "400001"},
        )
        site_id = r.json["site"]["id"]
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        r = self.client.post(
            "/api/orders",
            json={
                "site_id": site_id,
                "concrete_grade": "M25",
                "quantity_m3": 2,
                "delivery_date": tomorrow,
                "delivery_time": "10:00",
            },
        )
        self.assertEqual(r.status_code, 201, r.json)
        order_id = r.json["order"]["id"]
        self.client.post("/api/auth/logout")

        register_contractor(self.client, "ob")
        r = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(r.status_code, 404)

        login(self.client, email_a, "secret1")
        r = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(r.status_code, 200)

    def test_supplier_plant_product_truck_isolation(self):
        register_supplier(self.client, "sa", "A Co")
        with self.app.app_context():
            user_a = User.query.filter_by(email="sa_supplier@test.local").first()
            sup_a = Supplier.query.filter_by(user_id=user_a.id).first()
            plant_a = Plant.query.filter_by(supplier_id=sup_a.id).first()
            product_a = ConcreteProduct.query.filter_by(plant_id=plant_a.id).first()
            truck_a = Truck.query.filter_by(plant_id=plant_a.id).first()
            plant_a_id = plant_a.id
            product_a_id = product_a.id
            truck_a_id = truck_a.id

        self.client.post("/api/auth/logout")
        register_supplier(self.client, "sb", "B Co")
        with self.app.app_context():
            user_b = User.query.filter_by(email="sb_supplier@test.local").first()
            sup_b = Supplier.query.filter_by(user_id=user_b.id).first()
            plant_b = Plant.query.filter_by(supplier_id=sup_b.id).first()
            plant_b_id = plant_b.id
            product_b_id = ConcreteProduct.query.filter_by(plant_id=plant_b.id).first().id
            truck_b_id = Truck.query.filter_by(plant_id=plant_b.id).first().id

        self.client.post("/api/auth/logout")
        login(self.client, "sa_supplier@test.local", "secret1")
        r = self.client.get(f"/api/supplier/plants/{plant_a_id}")
        self.assertEqual(r.status_code, 200)
        r = self.client.get(f"/api/supplier/plants/{plant_b_id}")
        self.assertEqual(r.status_code, 404)

        r = self.client.get(f"/api/supplier/products/{product_a_id}")
        self.assertEqual(r.status_code, 200)
        r = self.client.get(f"/api/supplier/products/{product_b_id}")
        self.assertEqual(r.status_code, 404)

        r = self.client.get(f"/api/supplier/trucks/{truck_a_id}")
        self.assertEqual(r.status_code, 200)
        r = self.client.get(f"/api/supplier/trucks/{truck_b_id}")
        self.assertEqual(r.status_code, 404)

    def test_supplier_order_isolation(self):
        email_c, _ = register_contractor(self.client, "soc")
        r = self.client.post(
            "/api/sites",
            json={"site_name": "S", "address": "A", "city": "Mumbai", "pincode": "400001"},
        )
        site_id = r.json["site"]["id"]
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        self.client.post(
            "/api/orders",
            json={
                "site_id": site_id,
                "concrete_grade": "M25",
                "quantity_m3": 1,
                "delivery_date": tomorrow,
                "delivery_time": "10:00",
            },
        )
        with self.app.app_context():
            order = Order.query.order_by(Order.id.desc()).first()
            order_id = order.id
            supplier_a_id = order.supplier_id
        self.client.post("/api/auth/logout")

        register_supplier(self.client, "other", "Other Co")
        login(self.client, "other_supplier@test.local", "secret1")
        r = self.client.get(f"/api/supplier/orders/{order_id}")
        self.assertEqual(r.status_code, 404)

    def test_supplier_cannot_modify_other_product(self):
        register_supplier(self.client, "pa", "P A")
        self.client.post("/api/auth/logout")
        register_supplier(self.client, "pb", "P B")
        with self.app.app_context():
            user_b = User.query.filter_by(email="pb_supplier@test.local").first()
            sup_b = Supplier.query.filter_by(user_id=user_b.id).first()
            product_b_id = ConcreteProduct.query.filter_by(plant_id=Plant.query.filter_by(supplier_id=sup_b.id).first().id).first().id

        self.client.post("/api/auth/logout")
        login(self.client, "pa_supplier@test.local", "secret1")
        r = self.client.patch(f"/api/supplier/products/{product_b_id}", json={"is_available": False})
        self.assertEqual(r.status_code, 404)

    def test_role_api_boundaries(self):
        register_contractor(self.client, "rolec")
        r = self.client.get("/api/supplier/summary")
        self.assertEqual(r.status_code, 403)
        self.client.post("/api/auth/logout")

        register_supplier(self.client, "roles", "Role S")
        login(self.client, "roles_supplier@test.local", "secret1")
        r = self.client.get("/api/sites")
        self.assertEqual(r.status_code, 403)
        r = self.client.get("/api/orders")
        self.assertEqual(r.status_code, 403)

    def test_admin_overview_access(self):
        register_contractor(self.client, "adm1")
        self.client.post("/api/auth/logout")
        r = login(self.client, "auth_admin@test.local", "admin123")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/api/admin/overview")
        self.assertEqual(r.status_code, 200)
        self.assertIn("overview", r.json)

        register_contractor(self.client, "adm2")
        r = self.client.get("/api/admin/overview")
        self.assertEqual(r.status_code, 403)


if __name__ == "__main__":
    unittest.main()
