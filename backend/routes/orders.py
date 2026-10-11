from flask import Blueprint, jsonify, request

from services.marketplace_service import get_marketplace_plants
from services.order_service import (
    OrderError,
    create_order,
    estimate_order,
    get_catalog,
    get_order_for_contractor,
    list_orders_for_contractor,
    order_to_dict,
    update_order_for_contractor,
)
from services.quotation_service import compare_plant_offers
from services.session_helpers import contractor_required_json

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@orders_bp.get("/marketplace")
@contractor_required_json
def marketplace(user):
    return jsonify({"plants": get_marketplace_plants()})


@orders_bp.get("/catalog")
@contractor_required_json
def catalog(user):
    return jsonify({"grades": get_catalog()})


@orders_bp.post("/estimate")
@contractor_required_json
def estimate(user):
    data = request.get_json(silent=True) or {}
    try:
        result = estimate_order(user.id, data)
        return jsonify({"estimate": result})
    except OrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@orders_bp.post("/compare")
@contractor_required_json
def compare_offers(user):
    data = request.get_json(silent=True) or {}
    try:
        result = compare_plant_offers(user.id, data)
        return jsonify(result)
    except OrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@orders_bp.post("")
@contractor_required_json
def place_order(user):
    data = request.get_json(silent=True) or {}
    try:
        order = create_order(user.id, data)
        return jsonify({"order": order_to_dict(order)}), 201
    except OrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@orders_bp.get("")
@contractor_required_json
def list_orders(user):
    orders = list_orders_for_contractor(user.id)
    return jsonify({"orders": [order_to_dict(o) for o in orders]})


@orders_bp.get("/<int:order_id>")
@contractor_required_json
def get_order(user, order_id):
    try:
        order = get_order_for_contractor(user.id, order_id)
        return jsonify({"order": order_to_dict(order)})
    except OrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@orders_bp.patch("/<int:order_id>")
@contractor_required_json
def patch_order(user, order_id):
    data = request.get_json(silent=True) or {}
    try:
        order = update_order_for_contractor(user.id, order_id, data)
        return jsonify({"order": order_to_dict(order)})
    except OrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
