import os
import tempfile
from datetime import date, timedelta

from models import Plant, Supplier, User
from services.seed_service import DEMO_SUPPLIER_EMAIL


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


def demo_plant_id(app):
    with app.app_context():
        user = User.query.filter_by(email=DEMO_SUPPLIER_EMAIL).first()
        supplier = Supplier.query.filter_by(user_id=user.id).first()
        plant = Plant.query.filter_by(supplier_id=supplier.id).first()
        return plant.id


def base_order_json(site_id, plant_id, **extra):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "site_id": site_id,
        "plant_id": plant_id,
        "concrete_grade": "M25",
        "quantity_m3": 2,
        "delivery_date": tomorrow,
        "delivery_time": "10:00",
    }
    payload.update(extra)
    return payload


def full_requirements_payload():
    return {
        "pump_required": True,
        "pump_type": "BOOM",
        "pump_boom_reach_m": 32,
        "placement_method": "PUMP",
        "workability_test_type": "SLUMP",
        "target_slump_mm": 100,
        "minimum_slump_mm": 90,
        "maximum_slump_mm": 110,
        "special_concrete_type": "NORMAL",
    }
