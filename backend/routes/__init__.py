from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.orders import orders_bp
from routes.sites import sites_bp
from routes.supplier import supplier_bp

__all__ = ["auth_bp", "sites_bp", "orders_bp", "supplier_bp", "admin_bp"]
