"""SQLite-safe schema upgrades for plant-based multi-tenant architecture."""

from sqlalchemy import inspect, text

from models import (
    CONCRETE_GRADES,
    ConcreteProduct,
    Order,
    Plant,
    Supplier,
    Truck,
    db,
)


def _table_exists(engine, table_name):
    return table_name in inspect(engine).get_table_names()


def _column_exists(engine, table_name, column_name):
    if not _table_exists(engine, table_name):
        return False
    columns = [col["name"] for col in inspect(engine).get_columns(table_name)]
    return column_name in columns


def _add_column_if_missing(engine, table_name, column_name, column_type):
    if not _column_exists(engine, table_name, column_name):
        dialect = engine.dialect.name
        if dialect == "postgresql" and column_type.upper() == "FLOAT":
            column_type = "DOUBLE PRECISION"
        db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
        db.session.commit()


def _default_plant_for_supplier(supplier, suffix="Plant 1"):
    return Plant(
        supplier_id=supplier.id,
        plant_name=f"{supplier.company_name} — {suffix}",
        address=supplier.address,
        city=supplier.city,
        pincode="400001",
        is_active=True,
    )


def migrate_to_plant_architecture():
    """
    Non-destructive migration:
    - Creates plants table and new FK columns on existing tables
    - Backfills one default plant per supplier when needed
    - Preserves existing rows and data
    """
    engine = db.engine
    db.create_all()

    migrate_plant_management_fields()

    _add_column_if_missing(engine, "concrete_products", "plant_id", "INTEGER")
    _add_column_if_missing(engine, "trucks", "plant_id", "INTEGER")
    _add_column_if_missing(engine, "orders", "plant_id", "INTEGER")
    _add_column_if_missing(engine, "orders", "product_id", "INTEGER")

    suppliers = Supplier.query.all()
    for supplier in suppliers:
        plants = Plant.query.filter_by(supplier_id=supplier.id).all()
        if not plants:
            plant = _default_plant_for_supplier(supplier)
            db.session.add(plant)
            db.session.flush()
            plants = [plant]

        default_plant = plants[0]

        if _column_exists(engine, "concrete_products", "supplier_id"):
            rows = db.session.execute(
                text(
                    "SELECT id, supplier_id FROM concrete_products "
                    "WHERE plant_id IS NULL AND supplier_id = :sid"
                ),
                {"sid": supplier.id},
            ).fetchall()
            for row in rows:
                db.session.execute(
                    text("UPDATE concrete_products SET plant_id = :pid WHERE id = :id"),
                    {"pid": default_plant.id, "id": row.id},
                )

        if _column_exists(engine, "trucks", "supplier_id"):
            rows = db.session.execute(
                text(
                    "SELECT id FROM trucks WHERE plant_id IS NULL AND supplier_id = :sid"
                ),
                {"sid": supplier.id},
            ).fetchall()
            for row in rows:
                db.session.execute(
                    text("UPDATE trucks SET plant_id = :pid WHERE id = :id"),
                    {"pid": default_plant.id, "id": row.id},
                )

    db.session.commit()

    if _column_exists(engine, "concrete_products", "supplier_id"):
        db.session.execute(
            text(
                "UPDATE concrete_products "
                "SET supplier_id = (SELECT supplier_id FROM plants WHERE plants.id = concrete_products.plant_id) "
                "WHERE plant_id IS NOT NULL AND (supplier_id IS NULL OR supplier_id = 0)"
            )
        )
        db.session.commit()

    if _column_exists(engine, "trucks", "supplier_id"):
        db.session.execute(
            text(
                "UPDATE trucks "
                "SET supplier_id = (SELECT supplier_id FROM plants WHERE plants.id = trucks.plant_id) "
                "WHERE plant_id IS NOT NULL AND (supplier_id IS NULL OR supplier_id = 0)"
            )
        )
        db.session.commit()

    orders_missing = Order.query.filter(Order.plant_id.is_(None)).all()
    for order in orders_missing:
        plant = Plant.query.filter_by(supplier_id=order.supplier_id).first()
        if plant:
            order.plant_id = plant.id
            product = ConcreteProduct.query.filter_by(
                plant_id=plant.id, grade=order.concrete_grade
            ).first()
            if product:
                order.product_id = product.id
    db.session.commit()


def seed_second_demo_plant_if_applicable():
    """Optional demo data: second plant for demo supplier (does not delete existing data)."""
    from services.seed_service import DEMO_SUPPLIER_EMAIL

    user = db.session.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": DEMO_SUPPLIER_EMAIL},
    ).fetchone()
    if not user:
        return

    supplier = Supplier.query.filter_by(user_id=user.id).first()
    if not supplier:
        return

    if Plant.query.filter_by(supplier_id=supplier.id).count() >= 2:
        return

    plant2 = Plant(
        supplier_id=supplier.id,
        plant_name=f"{supplier.company_name} — Plant 2 (Navi Mumbai)",
        address="MIDC Turbhe",
        city="Navi Mumbai",
        pincode="400705",
        is_active=True,
    )
    db.session.add(plant2)
    db.session.flush()

    for grade in CONCRETE_GRADES:
        base = ConcreteProduct.query.join(Plant).filter(
            Plant.supplier_id == supplier.id,
            ConcreteProduct.grade == grade,
            Plant.id != plant2.id,
        ).first()
        price = (base.price_per_m3 - 100) if base else 5000.0
        db.session.add(
            ConcreteProduct(
                plant_id=plant2.id,
                supplier_id=supplier.id,
                grade=grade,
                price_per_m3=price,
                available_quantity=8000.0,
                is_available=True,
            )
        )
    db.session.commit()


def migrate_plant_management_fields():
    engine = db.engine
    _add_column_if_missing(engine, "plants", "contact_phone", "VARCHAR(20)")
    _add_column_if_missing(engine, "plants", "operating_hours", "VARCHAR(120)")
    _add_column_if_missing(engine, "concrete_products", "minimum_order_m3", "FLOAT")
    if _column_exists(engine, "concrete_products", "minimum_order_m3"):
        db.session.execute(
            text(
                "UPDATE concrete_products SET minimum_order_m3 = 1.0 "
                "WHERE minimum_order_m3 IS NULL"
            )
        )
        db.session.commit()
    migrate_order_concrete_requirements()


def migrate_order_concrete_requirements():
    """Additive columns for structured contractor order requirements."""
    engine = db.engine
    _add_column_if_missing(engine, "orders", "pump_required", "BOOLEAN")
    _add_column_if_missing(engine, "orders", "pump_type", "VARCHAR(20)")
    _add_column_if_missing(engine, "orders", "pump_boom_reach_m", "FLOAT")
    _add_column_if_missing(engine, "orders", "pump_pipeline_length_m", "FLOAT")
    _add_column_if_missing(engine, "orders", "pump_instructions", "TEXT")
    _add_column_if_missing(engine, "orders", "placement_method", "VARCHAR(30)")
    _add_column_if_missing(engine, "orders", "placement_method_other", "TEXT")
    _add_column_if_missing(engine, "orders", "workability_test_type", "VARCHAR(20)")
    _add_column_if_missing(engine, "orders", "target_slump_mm", "INTEGER")
    _add_column_if_missing(engine, "orders", "minimum_slump_mm", "INTEGER")
    _add_column_if_missing(engine, "orders", "maximum_slump_mm", "INTEGER")
    _add_column_if_missing(engine, "orders", "special_concrete_type", "VARCHAR(30)")
    _add_column_if_missing(engine, "orders", "special_concrete_notes", "TEXT")
    _add_column_if_missing(engine, "orders", "requested_concrete_temp_c", "FLOAT")
    _add_column_if_missing(engine, "orders", "contractor_modified_at", "DATETIME")
    _add_column_if_missing(engine, "orders", "contractor_modified_fields", "TEXT")
    migrate_plant_pricing_fields()


def migrate_plant_pricing_fields():
    """Optional plant-level pump, transport, tax and lead-time fields for quotations."""
    engine = db.engine
    _add_column_if_missing(engine, "plants", "pump_charge_inr", "FLOAT")
    _add_column_if_missing(engine, "plants", "transport_charge_per_m3", "FLOAT")
    _add_column_if_missing(engine, "plants", "other_charge_inr", "FLOAT")
    _add_column_if_missing(engine, "plants", "other_charge_label", "VARCHAR(120)")
    _add_column_if_missing(engine, "plants", "gst_rate_percent", "FLOAT")
    _add_column_if_missing(engine, "plants", "estimated_lead_time_hours", "INTEGER")
    _add_column_if_missing(engine, "plants", "quotation_valid_days", "INTEGER")
