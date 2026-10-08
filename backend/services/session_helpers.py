from functools import wraps

from flask import jsonify, session

from models import User


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required_json(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Not authenticated."}), 401
        return view(user, *args, **kwargs)

    return wrapped


def contractor_required_json(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Not authenticated."}), 401
        if user.role != "CONTRACTOR":
            return jsonify({"error": "Contractors only."}), 403
        return view(user, *args, **kwargs)

    return wrapped


def supplier_required_json(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        from services.supplier_order_service import ensure_supplier_profile

        user = get_current_user()
        if not user:
            return jsonify({"error": "Not authenticated."}), 401
        if user.role != "SUPPLIER":
            return jsonify({"error": "Suppliers only."}), 403
        supplier = ensure_supplier_profile(user)
        return view(user, supplier, *args, **kwargs)

    return wrapped


def admin_required_json(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Not authenticated."}), 401
        if user.role != "ADMIN":
            return jsonify({"error": "Forbidden."}), 403
        return view(user, *args, **kwargs)

    return wrapped
