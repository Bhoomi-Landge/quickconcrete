from flask import Blueprint, jsonify, request

from services.access_control import AccessError
from services.order_service import order_to_dict
from services.plant_service import (
    PlantError,
    bulk_import_products_for_plant,
    create_plant_for_supplier,
    create_product_for_plant,
    get_plant_for_supplier,
    get_product_for_supplier,
    get_truck_for_supplier,
    list_plants_for_supplier,
    list_products_for_plant,
    plant_to_dict,
    product_to_dict,
    truck_to_dict,
    delete_plant_for_supplier,
    delete_product_for_supplier,
    update_plant_for_supplier,
    update_product_for_supplier,
)
from services.rate_sheet_parser import parse_upload
from services.supplier_order_service import (
    SupplierOrderError,
    accept_order,
    get_order_for_supplier,
    get_revenue_summary,
    list_supplier_orders,
    next_status_for_order,
    reject_order,
    update_order_status,
)
from services.session_helpers import supplier_required_json

supplier_bp = Blueprint("supplier", __name__, url_prefix="/api/supplier")


def _order_payload(order):
    payload = order_to_dict(order, for_supplier=True)
    payload["next_status"] = next_status_for_order(order)
    return payload


@supplier_bp.get("/summary")
@supplier_required_json
def summary(user, supplier):
    return jsonify({"summary": get_revenue_summary(supplier.id)})


@supplier_bp.get("/orders")
@supplier_required_json
def list_orders(user, supplier):
    view = request.args.get("view", "all")
    try:
        orders = list_supplier_orders(supplier.id, view)
        return jsonify({"orders": [_order_payload(o) for o in orders]})
    except SupplierOrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.get("/orders/<int:order_id>")
@supplier_required_json
def get_order(user, supplier, order_id):
    try:
        order = get_order_for_supplier(supplier.id, order_id)
        return jsonify({"order": _order_payload(order)})
    except SupplierOrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.post("/orders/<int:order_id>/accept")
@supplier_required_json
def accept(user, supplier, order_id):
    try:
        order = accept_order(supplier.id, order_id)
        return jsonify({"order": _order_payload(order)})
    except SupplierOrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.post("/orders/<int:order_id>/reject")
@supplier_required_json
def reject(user, supplier, order_id):
    try:
        order = reject_order(supplier.id, order_id)
        return jsonify({"order": _order_payload(order)})
    except SupplierOrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.patch("/orders/<int:order_id>/status")
@supplier_required_json
def patch_status(user, supplier, order_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status is required."}), 400
    try:
        order = update_order_status(supplier.id, order_id, new_status)
        return jsonify({"order": _order_payload(order)})
    except SupplierOrderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.get("/plants")
@supplier_required_json
def list_plants(user, supplier):
    plants = list_plants_for_supplier(supplier.id)
    return jsonify({"plants": [plant_to_dict(p, include_summary=True) for p in plants]})


@supplier_bp.post("/plants")
@supplier_required_json
def add_plant(user, supplier):
    data = request.get_json(silent=True) or {}
    try:
        plant = create_plant_for_supplier(supplier.id, data)
        return jsonify({"plant": plant_to_dict(plant, include_summary=True)}), 201
    except PlantError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.get("/plants/<int:plant_id>")
@supplier_required_json
def get_plant(user, supplier, plant_id):
    try:
        plant = get_plant_for_supplier(supplier.id, plant_id)
        return jsonify({"plant": plant_to_dict(plant, include_summary=True)})
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.delete("/plants/<int:plant_id>")
@supplier_required_json
def remove_plant(user, supplier, plant_id):
    try:
        delete_plant_for_supplier(supplier.id, plant_id)
        return jsonify({"ok": True})
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except PlantError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.put("/plants/<int:plant_id>")
@supplier_required_json
def edit_plant(user, supplier, plant_id):
    data = request.get_json(silent=True) or {}
    try:
        plant = update_plant_for_supplier(supplier.id, plant_id, data)
        return jsonify({"plant": plant_to_dict(plant, include_summary=True)})
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except PlantError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.get("/plants/<int:plant_id>/products")
@supplier_required_json
def list_plant_products(user, supplier, plant_id):
    try:
        products = list_products_for_plant(supplier.id, plant_id)
        return jsonify({"products": [product_to_dict(p) for p in products]})
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.post("/plants/<int:plant_id>/products")
@supplier_required_json
def add_plant_product(user, supplier, plant_id):
    data = request.get_json(silent=True) or {}
    try:
        product = create_product_for_plant(supplier.id, plant_id, data)
        return jsonify({"product": product_to_dict(product)}), 201
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except PlantError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.post("/plants/<int:plant_id>/products/bulk")
@supplier_required_json
def bulk_products(user, supplier, plant_id):
    data = request.get_json(silent=True) or {}
    rows = data.get("products") or data.get("rows") or []
    if not isinstance(rows, list) or not rows:
        return jsonify({"error": "products array is required."}), 400
    try:
        result = bulk_import_products_for_plant(supplier.id, plant_id, rows)
        return jsonify(result)
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except PlantError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.post("/plants/<int:plant_id>/rate-sheet/upload")
@supplier_required_json
def upload_rate_sheet(user, supplier, plant_id):
    try:
        get_plant_for_supplier(supplier.id, plant_id)
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    upload = request.files.get("file")
    if not upload:
        return jsonify({"error": "file is required."}), 400

    file_bytes = upload.read()
    filename = upload.filename or ""

    try:
        plant = get_plant_for_supplier(supplier.id, plant_id)
        rows = parse_upload(file_bytes, filename, plant)
        result = bulk_import_products_for_plant(supplier.id, plant_id, rows)
        result["imported_rows"] = len(rows)
        return jsonify(result)
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except PlantError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.get("/products/<int:product_id>")
@supplier_required_json
def get_product(user, supplier, product_id):
    try:
        product = get_product_for_supplier(supplier.id, product_id)
        return jsonify({"product": product_to_dict(product)})
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.delete("/products/<int:product_id>")
@supplier_required_json
def remove_product(user, supplier, product_id):
    try:
        delete_product_for_supplier(supplier.id, product_id)
        return jsonify({"ok": True})
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except PlantError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.patch("/products/<int:product_id>")
@supplier_required_json
def patch_product(user, supplier, product_id):
    data = request.get_json(silent=True) or {}
    try:
        product = update_product_for_supplier(supplier.id, product_id, data)
        return jsonify({"product": product_to_dict(product)})
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except PlantError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@supplier_bp.get("/trucks/<int:truck_id>")
@supplier_required_json
def get_truck(user, supplier, truck_id):
    try:
        truck = get_truck_for_supplier(supplier.id, truck_id)
        return jsonify({"truck": truck_to_dict(truck)})
    except AccessError as exc:
        return jsonify({"error": exc.message}), exc.status_code
