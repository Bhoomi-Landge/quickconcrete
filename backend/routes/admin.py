from flask import Blueprint, jsonify

from models import Order, Site, Supplier, User, db
from services.session_helpers import admin_required_json

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/overview")
@admin_required_json
def platform_overview(user):
    return jsonify(
        {
            "overview": {
                "contractors": User.query.filter_by(role="CONTRACTOR").count(),
                "suppliers": Supplier.query.count(),
                "sites": Site.query.count(),
                "orders": Order.query.count(),
            }
        }
    )
