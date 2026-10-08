from datetime import date

from models import ConcreteProduct, Order, Plant, Supplier, db
from services.site_service import get_site_for_contractor


class OrderError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _parse_quantity(value):
    try:
        qty = float(value)
    except (TypeError, ValueError):
        raise OrderError("Quantity must be a number.")
    if qty <= 0:
        raise OrderError("Quantity must be greater than zero.")
    if qty > 500:
        raise OrderError("Quantity cannot exceed 500 m³ for this MVP.")
    return round(qty, 2)


def _parse_grade(grade):
    grade = (grade or "").strip().upper()
    if not grade or len(grade) > 30:
        raise OrderError("Concrete grade is required.")
    return grade


def _parse_plant_id(value):
    try:
        plant_id = int(value)
    except (TypeError, ValueError):
        raise OrderError("RMC plant selection is required.")
    if plant_id <= 0:
        raise OrderError("Invalid plant selection.")
    return plant_id


def _parse_delivery_date(value):
    if not value:
        raise OrderError("Delivery date is required.")
    try:
        if isinstance(value, date):
            delivery = value
        else:
            delivery = date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        raise OrderError("Delivery date must be YYYY-MM-DD.")
    if delivery < date.today():
        raise OrderError("Delivery date cannot be in the past.")
    return delivery


def _parse_delivery_time(value):
    delivery_time = (value or "").strip()
    if not delivery_time:
        raise OrderError("Delivery time is required.")
    if len(delivery_time) > 20:
        raise OrderError("Delivery time is too long.")
    return delivery_time


def get_product_for_plant_and_grade(plant_id, grade):
    grade = _parse_grade(grade)
    product = (
        ConcreteProduct.query.join(Plant)
        .join(Supplier)
        .filter(
            ConcreteProduct.plant_id == plant_id,
            ConcreteProduct.grade == grade,
            ConcreteProduct.is_available.is_(True),
            Plant.is_active.is_(True),
            Supplier.is_active.is_(True),
        )
        .first()
    )
    if not product:
        raise OrderError("Selected grade is not available at this plant.", 404)
    if product.available_quantity <= 0:
        raise OrderError("Selected grade is temporarily unavailable at this plant.", 409)
    return product


def get_catalog():
    """Legacy endpoint — returns flat list of all available plant products."""
    products = (
        ConcreteProduct.query.join(Plant)
        .join(Supplier)
        .filter(
            ConcreteProduct.is_available.is_(True),
            Plant.is_active.is_(True),
            Supplier.is_active.is_(True),
        )
        .order_by(Supplier.company_name, Plant.plant_name, ConcreteProduct.grade)
        .all()
    )
    catalog = []
    for product in products:
        plant = product.plant
        supplier = plant.supplier if plant else None
        catalog.append(
            {
                "grade": product.grade,
                "price_per_m3": product.price_per_m3,
                "supplier_id": supplier.id if supplier else None,
                "supplier_name": supplier.company_name if supplier else None,
                "plant_id": product.plant_id,
                "plant_name": plant.plant_name if plant else None,
                "plant_city": plant.city if plant else None,
            }
        )
    return catalog


def estimate_order(contractor_id, data):
    site_id = data.get("site_id")
    if not site_id:
        raise OrderError("Construction site is required.")
    get_site_for_contractor(contractor_id, site_id)

    plant_id = _parse_plant_id(data.get("plant_id"))
    grade = _parse_grade(data.get("concrete_grade") or data.get("grade"))
    quantity_m3 = _parse_quantity(data.get("quantity_m3"))

    product = get_product_for_plant_and_grade(plant_id, grade)
    plant = product.plant
    supplier = plant.supplier
    price_per_m3 = product.price_per_m3
    total_amount = round(quantity_m3 * price_per_m3, 2)

    return {
        "concrete_grade": grade,
        "quantity_m3": quantity_m3,
        "price_per_m3": price_per_m3,
        "total_amount": total_amount,
        "supplier_id": supplier.id,
        "supplier_name": supplier.company_name,
        "plant_id": plant.id,
        "plant_name": plant.plant_name,
        "plant_address": plant.address,
        "plant_city": plant.city,
        "plant_pincode": plant.pincode,
    }


def create_order(contractor_id, data):
    site_id = data.get("site_id")
    if not site_id:
        raise OrderError("Construction site is required.")
    site = get_site_for_contractor(contractor_id, site_id)

    plant_id = _parse_plant_id(data.get("plant_id"))
    grade = _parse_grade(data.get("concrete_grade") or data.get("grade"))
    quantity_m3 = _parse_quantity(data.get("quantity_m3"))
    delivery_date = _parse_delivery_date(data.get("delivery_date"))
    delivery_time = _parse_delivery_time(data.get("delivery_time"))
    instructions = (data.get("special_instructions") or "").strip() or None

    product = get_product_for_plant_and_grade(plant_id, grade)
    if quantity_m3 < product.minimum_order_m3:
        raise OrderError(
            f"Minimum order for {grade} is {product.minimum_order_m3} m³ at this plant.",
        )
    if quantity_m3 > product.available_quantity:
        raise OrderError(
            f"Requested quantity exceeds available stock ({product.available_quantity} m³).",
            409,
        )

    price_per_m3 = product.price_per_m3
    total_amount = round(quantity_m3 * price_per_m3, 2)

    order = Order(
        contractor_id=contractor_id,
        supplier_id=product.resolved_supplier_id,
        plant_id=product.plant_id,
        product_id=product.id,
        site_id=site.id,
        concrete_grade=grade,
        quantity_m3=quantity_m3,
        price_per_m3=price_per_m3,
        total_amount=total_amount,
        delivery_date=delivery_date,
        delivery_time=delivery_time,
        special_instructions=instructions,
        status="PLACED",
    )
    db.session.add(order)
    db.session.commit()
    return order


def list_orders_for_contractor(contractor_id):
    return (
        Order.query.filter_by(contractor_id=contractor_id)
        .order_by(Order.created_at.desc())
        .all()
    )


def get_order_for_contractor(contractor_id, order_id):
    order = Order.query.filter_by(id=order_id, contractor_id=contractor_id).first()
    if not order:
        raise OrderError("Order not found.", 404)
    return order


def order_to_dict(order, for_supplier=False):
    site = order.site
    supplier = order.supplier
    data = {
        "id": order.id,
        "order_number": f"QC{order.id:04d}",
        "contractor_id": order.contractor_id,
        "supplier_id": order.supplier_id,
        "plant_id": order.plant_id,
        "plant_name": order.plant.plant_name if order.plant else None,
        "product_id": order.product_id,
        "supplier_name": supplier.company_name if supplier else None,
        "site_id": order.site_id,
        "site_name": site.site_name if site else None,
        "site_city": site.city if site else None,
        "site_address": site.address if site else None,
        "site_pincode": site.pincode if site else None,
        "concrete_grade": order.concrete_grade,
        "quantity_m3": order.quantity_m3,
        "price_per_m3": order.price_per_m3,
        "total_amount": order.total_amount,
        "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
        "delivery_time": order.delivery_time,
        "special_instructions": order.special_instructions,
        "status": order.status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }
    if for_supplier and order.contractor:
        data["contractor_name"] = order.contractor.name
        data["contractor_phone"] = order.contractor.phone
    return data
