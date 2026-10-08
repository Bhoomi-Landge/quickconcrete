from flask import Blueprint, jsonify, request

from services.session_helpers import contractor_required_json
from services.site_service import SiteError, create_site, delete_site, get_site_for_contractor, list_sites_for_contractor, update_site

sites_bp = Blueprint("sites", __name__, url_prefix="/api/sites")


@sites_bp.get("")
@contractor_required_json
def list_sites(user):
    sites = list_sites_for_contractor(user.id)
    return jsonify({"sites": [site.to_dict() for site in sites]})


@sites_bp.post("")
@contractor_required_json
def add_site(user):
    data = request.get_json(silent=True) or {}
    try:
        site = create_site(user.id, data)
        return jsonify({"site": site.to_dict()}), 201
    except SiteError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@sites_bp.get("/<int:site_id>")
@contractor_required_json
def get_site(user, site_id):
    try:
        site = get_site_for_contractor(user.id, site_id)
        return jsonify({"site": site.to_dict()})
    except SiteError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@sites_bp.put("/<int:site_id>")
@contractor_required_json
def edit_site(user, site_id):
    data = request.get_json(silent=True) or {}
    try:
        site = update_site(user.id, site_id, data)
        return jsonify({"site": site.to_dict()})
    except SiteError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@sites_bp.delete("/<int:site_id>")
@contractor_required_json
def remove_site(user, site_id):
    try:
        delete_site(user.id, site_id)
        return jsonify({"message": "Site deleted."})
    except SiteError as exc:
        return jsonify({"error": exc.message}), exc.status_code
