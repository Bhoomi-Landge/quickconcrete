from models import CONCRETE_GRADES, ConcreteProduct, Plant, Supplier, User, db
from services.auth_service import hash_password

DEMO_SUPPLIER_EMAIL = "demo-supplier@quickconcrete.local"

DEMO_GRADE_PRICES = {
    "M20": 4500.0,
    "M25": 4800.0,
    "M30": 5100.0,
    "M35": 5400.0,
    "M40": 5700.0,
}


def seed_demo_supplier_catalog():
    """Seed demo supplier with plant-scoped products (non-destructive)."""
    if Plant.query.count() > 0 and ConcreteProduct.query.filter(ConcreteProduct.plant_id.isnot(None)).count() > 0:
        return

    user = User.query.filter_by(email=DEMO_SUPPLIER_EMAIL).first()
    if not user:
        user = User(
            name="Demo RMC Supplier",
            email=DEMO_SUPPLIER_EMAIL,
            password_hash=hash_password("demo123"),
            role="SUPPLIER",
            phone="+91 90000 00001",
        )
        db.session.add(user)
        db.session.flush()

    supplier = Supplier.query.filter_by(user_id=user.id).first()
    if not supplier:
        supplier = Supplier(
            user_id=user.id,
            company_name="Demo RMC Pvt Ltd",
            address="Plot 45, Industrial Estate",
            city="Mumbai",
            phone="+91 90000 00001",
            is_active=True,
        )
        db.session.add(supplier)
        db.session.flush()

    plant = Plant.query.filter_by(supplier_id=supplier.id).first()
    if not plant:
        plant = Plant(
            supplier_id=supplier.id,
            plant_name=f"{supplier.company_name} — Plant 1 (Andheri)",
            address="Plot 45, Industrial Estate",
            city="Mumbai",
            pincode="400053",
            is_active=True,
        )
        db.session.add(plant)
        db.session.flush()

    existing_grades = {
        p.grade
        for p in ConcreteProduct.query.filter_by(plant_id=plant.id).all()
    }
    for grade in CONCRETE_GRADES:
        if grade in existing_grades:
            continue
        db.session.add(
            ConcreteProduct(
                plant_id=plant.id,
                supplier_id=supplier.id,
                grade=grade,
                price_per_m3=DEMO_GRADE_PRICES.get(grade, 5000.0),
                available_quantity=10000.0,
                is_available=True,
            )
        )

    db.session.commit()
