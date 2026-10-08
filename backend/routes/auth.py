from flask import Blueprint, jsonify, request, session

from models import User
from services.auth_service import AuthError, authenticate_user, register_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    try:
        user = register_user(
            name=data.get("name"),
            email=data.get("email"),
            password=data.get("password"),
            role=data.get("role"),
            phone=data.get("phone"),
        )
        session["user_id"] = user.id
        return jsonify({"user": user.to_dict()}), 201
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    try:
        user = authenticate_user(data.get("email"), data.get("password"))
        session["user_id"] = user.id
        return jsonify({"user": user.to_dict()})
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@auth_bp.post("/logout")
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out."})


@auth_bp.get("/me")
def me():
    user = _current_user()
    if not user:
        return jsonify({"error": "Not authenticated."}), 401
    return jsonify({"user": user.to_dict()})
