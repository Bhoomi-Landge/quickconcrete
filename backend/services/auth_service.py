from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db


class AuthError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def register_user(name, email, password, role, phone=None):
    email = (email or "").strip().lower()
    name = (name or "").strip()
    role = (role or "").strip().upper()

    if not name:
        raise AuthError("Name is required.")
    if not email or "@" not in email:
        raise AuthError("A valid email is required.")
    if not password or len(password) < 6:
        raise AuthError("Password must be at least 6 characters.")
    if role not in ("CONTRACTOR", "SUPPLIER"):
        raise AuthError("Role must be CONTRACTOR or SUPPLIER.")

    if User.query.filter_by(email=email).first():
        raise AuthError("An account with this email already exists.", 409)

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        phone=(phone or "").strip() or None,
    )
    db.session.add(user)
    db.session.commit()

    if role == "SUPPLIER":
        from services.supplier_order_service import ensure_supplier_profile

        ensure_supplier_profile(user)

    return user


def authenticate_user(email, password):
    email = (email or "").strip().lower()
    if not email or not password:
        raise AuthError("Email and password are required.", 401)

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(user.password_hash, password):
        raise AuthError("Invalid email or password.", 401)

    return user


def create_admin_if_missing(email, password, name="Platform Admin"):
    email = email.strip().lower()
    existing = User.query.filter_by(email=email).first()
    if existing:
        return existing

    admin = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="ADMIN",
        phone=None,
    )
    db.session.add(admin)
    db.session.commit()
    return admin
