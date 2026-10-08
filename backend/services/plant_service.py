from models import ConcreteProduct, Order, Plant, Truck, db
from services.access_control import AccessError, deny_cross_tenant


class PlantError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _clean_plant_payload(data):
    return {
        "plant_name": (data.get("plant_name") or "").strip(),
        "address": (data.get("address") or "").strip(),
        "city": (data.get("city") or "").strip(),
        "pincode": (data.get("pincode") or "").strip(),
        "contact_phone": (data.get("contact_phone") or "").strip() or None,
        "operating_hours": (data.get("operating_hours") or "").strip() or None,
    }


def validate_plant_fields(payload):
    if not payload["plant_name"]:
        raise PlantError("Plant name is required.")
    if not payload["address"]:
        raise PlantError("Address is required.")
    if not payload["city"]:
        raise PlantError("City is required.")
    pincode = payload["pincode"]
    if not pincode or not pincode.isdigit() or len(pincode) != 6:
        raise PlantError("Pincode must be a 6-digit number.")
    return payload


def list_plants_for_supplier(supplier_id):
    return (
        Plant.query.filter_by(supplier_id=supplier_id)
        .order_by(Plant.created_at.asc())
        .all()
    )


def get_plant_for_supplier(supplier_id, plant_id):
    plant = Plant.query.filter_by(id=plant_id, supplier_id=supplier_id).first()
    if not plant:
        deny_cross_tenant()
    return plant


def create_plant_for_supplier(supplier_id, data):
    payload = validate_plant_fields(_clean_plant_payload(data))
    plant = Plant(supplier_id=supplier_id, is_active=True, **payload)
    db.session.add(plant)
    db.session.commit()
    return plant


def update_plant_for_supplier(supplier_id, plant_id, data):
    plant = get_plant_for_supplier(supplier_id, plant_id)
    payload = validate_plant_fields(_clean_plant_payload(data))
    plant.plant_name = payload["plant_name"]
    plant.address = payload["address"]
    plant.city = payload["city"]
    plant.pincode = payload["pincode"]
    plant.contact_phone = payload["contact_phone"]
    plant.operating_hours = payload["operating_hours"]
    if "is_active" in data:
        plant.is_active = bool(data["is_active"])
    db.session.commit()
    return plant


def list_products_for_plant(supplier_id, plant_id):
    plant = get_plant_for_supplier(supplier_id, plant_id)
    return (
        ConcreteProduct.query.filter_by(plant_id=plant.id)
        .order_by(ConcreteProduct.grade.asc())
        .all()
    )


def get_product_for_supplier(supplier_id, product_id):
    product = (
        ConcreteProduct.query.join(Plant)
        .filter(ConcreteProduct.id == product_id, Plant.supplier_id == supplier_id)
        .first()
    )
    if not product:
        deny_cross_tenant()
    return product


def get_truck_for_supplier(supplier_id, truck_id):
    truck = (
        Truck.query.join(Plant)
        .filter(Truck.id == truck_id, Plant.supplier_id == supplier_id)
        .first()
    )
    if not truck:
        deny_cross_tenant()
    return truck


def _validate_grade(grade):
    grade = (grade or "").strip().upper()
    if not grade or len(grade) > 30:
        raise PlantError("Grade is required (max 30 characters).")
    return grade


def create_product_for_plant(supplier_id, plant_id, data):
    plant = get_plant_for_supplier(supplier_id, plant_id)
    grade = _validate_grade(data.get("grade"))

    existing = ConcreteProduct.query.filter_by(plant_id=plant.id, grade=grade).first()
    if existing:
        raise PlantError(f"Grade {grade} already exists for this plant.", 409)

    try:
        price = float(data.get("price_per_m3"))
        available_quantity = float(data.get("available_quantity", 0))
        minimum_order_m3 = float(data.get("minimum_order_m3", 1))
    except (TypeError, ValueError):
        raise PlantError("Price and quantities must be numbers.")

    if price <= 0:
        raise PlantError("Price must be greater than zero.")
    if available_quantity < 0:
        raise PlantError("Available quantity cannot be negative.")
    if minimum_order_m3 <= 0:
        raise PlantError("Minimum order quantity must be greater than zero.")

    product = ConcreteProduct(
        plant_id=plant.id,
        supplier_id=supplier_id,
        grade=grade,
        price_per_m3=round(price, 2),
        available_quantity=round(available_quantity, 2),
        minimum_order_m3=round(minimum_order_m3, 2),
        is_available=bool(data.get("is_available", True)),
    )
    db.session.add(product)
    db.session.commit()
    return product


def bulk_import_products_for_plant(supplier_id, plant_id, rows, default_available_qty=10000.0):
    plant = get_plant_for_supplier(supplier_id, plant_id)
    created = []
    updated = []
    for row in rows:
        grade = _validate_grade(row.get("grade"))
        try:
            price = float(row.get("price_per_m3"))
        except (TypeError, ValueError):
            raise PlantError(f"Invalid price for grade {grade}.")
        if price <= 0:
            raise PlantError(f"Price must be positive for grade {grade}.")

        existing = ConcreteProduct.query.filter_by(plant_id=plant.id, grade=grade).first()
        if existing:
            existing.price_per_m3 = round(price, 2)
            existing.is_available = True
            if existing.available_quantity <= 0:
                existing.available_quantity = default_available_qty
            updated.append(existing)
        else:
            product = ConcreteProduct(
                plant_id=plant.id,
                supplier_id=supplier_id,
                grade=grade,
                price_per_m3=round(price, 2),
                available_quantity=default_available_qty,
                minimum_order_m3=float(row.get("minimum_order_m3") or 1),
                is_available=True,
            )
            db.session.add(product)
            created.append(product)
    db.session.commit()
    return {
        "created": len(created),
        "updated": len(updated),
        "products": [
            product_to_dict(p)
            for p in ConcreteProduct.query.filter_by(plant_id=plant.id).order_by(ConcreteProduct.grade).all()
        ],
    }


def update_product_for_supplier(supplier_id, product_id, data):
    product = get_product_for_supplier(supplier_id, product_id)

    if "price_per_m3" in data:
        try:
            price = float(data["price_per_m3"])
        except (TypeError, ValueError):
            raise PlantError("Price must be a number.")
        if price <= 0:
            raise PlantError("Price must be greater than zero.")
        product.price_per_m3 = round(price, 2)

    if "available_quantity" in data:
        try:
            qty = float(data["available_quantity"])
        except (TypeError, ValueError):
            raise PlantError("Available quantity must be a number.")
        if qty < 0:
            raise PlantError("Available quantity cannot be negative.")
        product.available_quantity = round(qty, 2)

    if "minimum_order_m3" in data:
        try:
            min_qty = float(data["minimum_order_m3"])
        except (TypeError, ValueError):
            raise PlantError("Minimum order quantity must be a number.")
        if min_qty <= 0:
            raise PlantError("Minimum order quantity must be greater than zero.")
        product.minimum_order_m3 = round(min_qty, 2)

    if "is_available" in data:
        product.is_available = bool(data["is_available"])

    db.session.commit()
    return product


def delete_product_for_supplier(supplier_id, product_id):
    product = get_product_for_supplier(supplier_id, product_id)
    if Order.query.filter_by(product_id=product.id).first():
        raise PlantError("This grade is linked to orders and cannot be deleted.", 409)
    db.session.delete(product)
    db.session.commit()


def delete_plant_for_supplier(supplier_id, plant_id):
    plant = get_plant_for_supplier(supplier_id, plant_id)
    if Order.query.filter_by(plant_id=plant.id).first():
        raise PlantError("This plant has orders and cannot be deleted.", 409)
    ConcreteProduct.query.filter_by(plant_id=plant.id).delete()
    Truck.query.filter_by(plant_id=plant.id).delete()
    db.session.delete(plant)
    db.session.commit()


def _grades_summary_text(available_products):
    if not available_products:
        return "None active"
    if len(available_products) > 5:
        return f"{len(available_products)} active grades"
    return ", ".join(p.grade for p in available_products)


def plant_summary(plant):
    products = ConcreteProduct.query.filter_by(plant_id=plant.id).all()
    available = [p for p in products if p.is_available]
    return {
        "product_count": len(products),
        "available_product_count": len(available),
        "grades_summary": _grades_summary_text(available),
    }


def plant_to_dict(plant, include_summary=False):
    data = {
        "id": plant.id,
        "supplier_id": plant.supplier_id,
        "plant_name": plant.plant_name,
        "address": plant.address,
        "city": plant.city,
        "pincode": plant.pincode,
        "contact_phone": plant.contact_phone,
        "operating_hours": plant.operating_hours,
        "is_active": plant.is_active,
        "created_at": plant.created_at.isoformat() if plant.created_at else None,
    }
    if include_summary:
        data.update(plant_summary(plant))
    return data


def product_to_dict(product):
    plant = product.plant
    return {
        "id": product.id,
        "plant_id": product.plant_id,
        "supplier_id": plant.supplier_id if plant else product.supplier_id,
        "grade": product.grade,
        "price_per_m3": product.price_per_m3,
        "available_quantity": product.available_quantity,
        "minimum_order_m3": product.minimum_order_m3,
        "is_available": product.is_available,
    }


def truck_to_dict(truck):
    plant = truck.plant
    return {
        "id": truck.id,
        "plant_id": truck.plant_id,
        "supplier_id": plant.supplier_id if plant else None,
        "truck_number": truck.truck_number,
        "driver_name": truck.driver_name,
        "driver_phone": truck.driver_phone,
        "capacity_m3": truck.capacity_m3,
        "is_available": truck.is_available,
    }
