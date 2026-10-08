from models import ORDER_STATUSES, Order, Plant, Supplier, db

ACTIVE_STATUSES = ("ACCEPTED", "PREPARING", "DISPATCHED", "OUT_FOR_DELIVERY")
COMPLETED_STATUSES = ("DELIVERED",)
INCOMING_STATUSES = ("PLACED",)

STATUS_TRANSITIONS = {
    "PLACED": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"PREPARING"},
    "PREPARING": {"DISPATCHED"},
    "DISPATCHED": {"OUT_FOR_DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}


class SupplierOrderError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_supplier_profile(user):
    supplier = Supplier.query.filter_by(user_id=user.id).first()
    if supplier:
        return supplier

    supplier = Supplier(
        user_id=user.id,
        company_name=f"{user.name} RMC",
        address="Address pending",
        city="Mumbai",
        phone=user.phone or "0000000000",
        is_active=True,
    )
    db.session.add(supplier)
    db.session.flush()

    plant = Plant(
        supplier_id=supplier.id,
        plant_name=f"{supplier.company_name} — Plant 1",
        address=supplier.address,
        city=supplier.city,
        pincode="400001",
        is_active=True,
    )
    db.session.add(plant)
    db.session.commit()
    return supplier


def get_order_for_supplier(supplier_id, order_id):
    order = Order.query.filter_by(id=order_id, supplier_id=supplier_id).first()
    if not order:
        raise SupplierOrderError("Order not found.", 404)
    return order


def list_supplier_orders(supplier_id, view=None):
    query = Order.query.filter_by(supplier_id=supplier_id)

    view = (view or "all").lower()
    if view == "incoming":
        query = query.filter(Order.status.in_(INCOMING_STATUSES))
    elif view == "active":
        query = query.filter(Order.status.in_(ACTIVE_STATUSES))
    elif view == "completed":
        query = query.filter(Order.status.in_(COMPLETED_STATUSES + ("CANCELLED",)))
    elif view != "all":
        raise SupplierOrderError("Invalid view filter.")

    return query.order_by(Order.created_at.desc()).all()


def _set_status(order, new_status):
    new_status = (new_status or "").strip().upper()
    if new_status not in ORDER_STATUSES:
        raise SupplierOrderError("Invalid status.")

    allowed = STATUS_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise SupplierOrderError(
            f"Cannot change status from {order.status} to {new_status}."
        )

    order.status = new_status
    db.session.commit()
    return order


def accept_order(supplier_id, order_id):
    order = get_order_for_supplier(supplier_id, order_id)
    if order.status != "PLACED":
        raise SupplierOrderError("Only PLACED orders can be accepted.")
    return _set_status(order, "ACCEPTED")


def reject_order(supplier_id, order_id):
    order = get_order_for_supplier(supplier_id, order_id)
    if order.status != "PLACED":
        raise SupplierOrderError("Only PLACED orders can be rejected.")
    return _set_status(order, "CANCELLED")


def update_order_status(supplier_id, order_id, new_status):
    order = get_order_for_supplier(supplier_id, order_id)
    if order.status == "PLACED":
        raise SupplierOrderError("Accept or reject the order first.")
    if order.status in ("DELIVERED", "CANCELLED"):
        raise SupplierOrderError("This order can no longer be updated.")
    return _set_status(order, new_status)


def get_revenue_summary(supplier_id):
    orders = Order.query.filter_by(supplier_id=supplier_id).all()

    incoming = sum(1 for o in orders if o.status in INCOMING_STATUSES)
    active = sum(1 for o in orders if o.status in ACTIVE_STATUSES)
    completed = sum(1 for o in orders if o.status == "DELIVERED")
    cancelled = sum(1 for o in orders if o.status == "CANCELLED")

    total_revenue = round(
        sum(o.total_amount for o in orders if o.status == "DELIVERED"),
        2,
    )
    pending_value = round(
        sum(o.total_amount for o in orders if o.status in ACTIVE_STATUSES + INCOMING_STATUSES),
        2,
    )

    return {
        "incoming_count": incoming,
        "active_count": active,
        "completed_count": completed,
        "cancelled_count": cancelled,
        "total_revenue": total_revenue,
        "pending_value": pending_value,
    }


def next_status_for_order(order):
    transitions = STATUS_TRANSITIONS.get(order.status, set())
    workflow = ["ACCEPTED", "PREPARING", "DISPATCHED", "OUT_FOR_DELIVERY", "DELIVERED"]
    for status in workflow:
        if status in transitions:
            return status
    return None
