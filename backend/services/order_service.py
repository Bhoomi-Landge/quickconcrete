import json
from datetime import date, datetime

from models import ConcreteProduct, Order, Plant, Supplier, db
from services.order_requirements import (
    RequirementError,
    parse_order_requirements,
    parse_order_requirements_patch,
    requirements_to_dict,
)
from services.site_service import SiteError, get_site_for_contractor

EDITABLE_ORDER_STATUSES = ("PLACED",)

_FORBIDDEN_UPDATE_KEYS = frozenset(
    {
        "id",
        "contractor_id",
        "supplier_id",
        "status",
        "price_per_m3",
        "total_amount",
        "product_id",
        "created_at",
        "contractor_modified_at",
        "contractor_modified_fields",
    }
)


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
    parts = delivery_time.replace(".", ":").split(":")
    if len(parts) < 2:
        raise OrderError("Delivery time must be HH:MM (24-hour).")
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        raise OrderError("Delivery time must be HH:MM (24-hour).")
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise OrderError("Delivery time must be a valid clock time.")
    return f"{hour:02d}:{minute:02d}"


def _validate_delivery_datetime(delivery_date, delivery_time):
    if delivery_date < date.today():
        raise OrderError("Delivery date cannot be in the past.")
    if delivery_date == date.today():
        hour, minute = map(int, delivery_time.split(":"))
        now = datetime.now()
        if hour * 60 + minute <= now.hour * 60 + now.minute:
            raise OrderError(
                "Delivery time must be in the future when delivery is scheduled for today."
            )


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
    from services.quotation_service import estimate_with_quotation

    return estimate_with_quotation(contractor_id, data)


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
    _validate_delivery_datetime(delivery_date, delivery_time)
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

    try:
        requirement_fields = parse_order_requirements(data)
    except RequirementError as exc:
        raise OrderError(exc.message, exc.status_code)

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
        **requirement_fields,
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


def _resolve_product_for_order(plant_id, grade, quantity_m3):
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
    return product


def update_order_for_contractor(contractor_id, order_id, data):
    if not data:
        raise OrderError("No updates provided.")

    for key in data:
        if key in _FORBIDDEN_UPDATE_KEYS:
            raise OrderError(f"Field '{key}' cannot be updated.", 400)

    order = get_order_for_contractor(contractor_id, order_id)
    if order.status not in EDITABLE_ORDER_STATUSES:
        raise OrderError("Only PLACED orders can be edited.", 409)

    changed_fields = []

    if "site_id" in data:
        try:
            site = get_site_for_contractor(contractor_id, data["site_id"])
        except SiteError as exc:
            raise OrderError(exc.message, exc.status_code)
        if order.site_id != site.id:
            order.site_id = site.id
            changed_fields.append("site_id")

    plant_id = order.plant_id
    grade = order.concrete_grade
    if "plant_id" in data:
        plant_id = _parse_plant_id(data["plant_id"])
    if "concrete_grade" in data or "grade" in data:
        grade = _parse_grade(data.get("concrete_grade") or data.get("grade"))

    quantity_m3 = order.quantity_m3
    if "quantity_m3" in data:
        quantity_m3 = _parse_quantity(data["quantity_m3"])

    repricing = False
    if (
        "plant_id" in data
        or "concrete_grade" in data
        or "grade" in data
        or "quantity_m3" in data
    ):
        product = _resolve_product_for_order(plant_id, grade, quantity_m3)
        if order.plant_id != product.plant_id:
            changed_fields.append("plant_id")
        if order.concrete_grade != grade:
            changed_fields.append("concrete_grade")
        if order.quantity_m3 != quantity_m3:
            changed_fields.append("quantity_m3")
        order.plant_id = product.plant_id
        order.product_id = product.id
        order.supplier_id = product.resolved_supplier_id
        order.concrete_grade = grade
        order.quantity_m3 = quantity_m3
        order.price_per_m3 = product.price_per_m3
        order.total_amount = round(quantity_m3 * product.price_per_m3, 2)

    delivery_date = order.delivery_date
    delivery_time = order.delivery_time
    if "delivery_date" in data:
        delivery_date = _parse_delivery_date(data["delivery_date"])
        changed_fields.append("delivery_date")
    if "delivery_time" in data:
        delivery_time = _parse_delivery_time(data["delivery_time"])
        changed_fields.append("delivery_time")
    if "delivery_date" in data or "delivery_time" in data:
        _validate_delivery_datetime(delivery_date, delivery_time)
        order.delivery_date = delivery_date
        order.delivery_time = delivery_time

    if "special_instructions" in data:
        instructions = (data.get("special_instructions") or "").strip() or None
        order.special_instructions = instructions
        changed_fields.append("special_instructions")

    try:
        requirement_fields = parse_order_requirements_patch(order, data)
    except RequirementError as exc:
        raise OrderError(exc.message, exc.status_code)

    if requirement_fields is not None:
        for key, value in requirement_fields.items():
            setattr(order, key, value)
        changed_fields.append("concrete_requirements")

    if not changed_fields and requirement_fields is None:
        raise OrderError("No changes to save.")

    order.contractor_modified_at = datetime.utcnow()
    order.contractor_modified_fields = json.dumps(sorted(set(changed_fields)))
    db.session.commit()
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
        "contractor_modified_at": (
            order.contractor_modified_at.isoformat() if order.contractor_modified_at else None
        ),
        "contractor_modified_fields": order.contractor_modified_fields,
        "editable": order.status in EDITABLE_ORDER_STATUSES,
        **requirements_to_dict(order),
    }
    if for_supplier and order.contractor:
        data["contractor_name"] = order.contractor.name
        data["contractor_phone"] = order.contractor.phone
    return data
