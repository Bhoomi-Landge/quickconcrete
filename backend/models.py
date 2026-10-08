from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

ROLES = ("CONTRACTOR", "SUPPLIER", "ADMIN")

ORDER_STATUSES = (
    "PLACED",
    "ACCEPTED",
    "PREPARING",
    "DISPATCHED",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
    "CANCELLED",
)

CONCRETE_GRADES = ("M20", "M25", "M30", "M35", "M40")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sites = db.relationship("Site", backref="contractor", lazy=True)
    supplier_profile = db.relationship("Supplier", backref="user", uselist=False, lazy=True)
    orders_as_contractor = db.relationship(
        "Order",
        foreign_keys="Order.contractor_id",
        backref="contractor",
        lazy=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Site(db.Model):
    __tablename__ = "sites"

    id = db.Column(db.Integer, primary_key=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    site_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "contractor_id": self.contractor_id,
            "site_name": self.site_name,
            "address": self.address,
            "city": self.city,
            "pincode": self.pincode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    plants = db.relationship("Plant", backref="supplier", lazy=True)
    orders = db.relationship("Order", backref="supplier", lazy=True)


class Plant(db.Model):
    __tablename__ = "plants"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    plant_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    operating_hours = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    products = db.relationship("ConcreteProduct", backref="plant", lazy=True)
    trucks = db.relationship("Truck", backref="plant", lazy=True)


class ConcreteProduct(db.Model):
    __tablename__ = "concrete_products"

    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey("plants.id"), nullable=True)
    # Legacy column kept for existing SQLite databases during plant migration.
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)
    grade = db.Column(db.String(30), nullable=False)
    price_per_m3 = db.Column(db.Float, nullable=False)
    available_quantity = db.Column(db.Float, nullable=False, default=0)
    minimum_order_m3 = db.Column(db.Float, nullable=False, default=1.0)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def supplier(self):
        if self.plant:
            return self.plant.supplier
        if self.supplier_id:
            return Supplier.query.get(self.supplier_id)
        return None

    @property
    def resolved_supplier_id(self):
        if self.plant:
            return self.plant.supplier_id
        return self.supplier_id


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    contractor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey("plants.id"), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("concrete_products.id"), nullable=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    concrete_grade = db.Column(db.String(30), nullable=False)
    quantity_m3 = db.Column(db.Float, nullable=False)
    price_per_m3 = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    delivery_time = db.Column(db.String(20), nullable=False)
    special_instructions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="PLACED")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    site = db.relationship("Site", backref="orders")
    plant = db.relationship("Plant", backref="orders")
    product = db.relationship("ConcreteProduct", backref="orders")
    delivery = db.relationship("Delivery", backref="order", uselist=False, lazy=True)


class Truck(db.Model):
    __tablename__ = "trucks"

    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey("plants.id"), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)
    truck_number = db.Column(db.String(50), nullable=False)
    driver_name = db.Column(db.String(120), nullable=False)
    driver_phone = db.Column(db.String(20), nullable=False)
    capacity_m3 = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def supplier(self):
        if self.plant:
            return self.plant.supplier
        if self.supplier_id:
            return Supplier.query.get(self.supplier_id)
        return None

    @property
    def resolved_supplier_id(self):
        if self.plant:
            return self.plant.supplier_id
        return self.supplier_id


class Delivery(db.Model):
    __tablename__ = "deliveries"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False)
    truck_id = db.Column(db.Integer, db.ForeignKey("trucks.id"), nullable=True)
    dispatched_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    current_status = db.Column(db.String(30), nullable=False, default="PLACED")

    truck = db.relationship("Truck", backref="deliveries")
