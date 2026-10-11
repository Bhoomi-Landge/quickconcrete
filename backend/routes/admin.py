from flask import Blueprint, jsonify

from flask import current_app

from models import Order, Site, Supplier, User, db
from services.session_helpers import admin_required_json

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

_ACTIVE_STATUSES = ("ACCEPTED", "PREPARING", "DISPATCHED", "OUT_FOR_DELIVERY")


@admin_bp.get("/overview")
@admin_required_json
def platform_overview(user):
    recent_users = (
        User.query.order_by(User.created_at.desc()).limit(25).all()
    )
    return jsonify(
        {
            "overview": {
                "contractors": User.query.filter_by(role="CONTRACTOR").count(),
                "suppliers": Supplier.query.count(),
                "sites": Site.query.count(),
                "orders": Order.query.count(),
                "active_deliveries": Order.query.filter(
                    Order.status.in_(_ACTIVE_STATUSES)
                ).count(),
            },
            "database_uri": current_app.config.get("SQLALCHEMY_DATABASE_URI", ""),
            "recent_users": [u.to_dict() for u in recent_users],
        }
    )
