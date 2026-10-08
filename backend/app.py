import os
import sys

from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from frontend_static import register_frontend_routes
from models import db
from routes import admin_bp, auth_bp, orders_bp, sites_bp, supplier_bp
from services.auth_service import create_admin_if_missing
from services.db_migrate import migrate_plant_management_fields, migrate_to_plant_architecture, seed_second_demo_plant_if_applicable
from services.seed_service import seed_demo_supplier_catalog

# Allow running as `python app.py` from backend/
sys.path.insert(0, os.path.dirname(__file__))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    serve_frontend = (
        os.environ.get("SERVE_FRONTEND") == "1"
        or bool(os.environ.get("RENDER"))
        or bool(os.environ.get("RAILWAY_ENVIRONMENT"))
    )

    if serve_frontend:
        # HTTPS hosting (Render / Railway / tunnel) — secure cookies + proxy headers
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        app.config["PREFERRED_URL_SCHEME"] = "https"
        secret = os.environ.get("SECRET_KEY")
        if secret:
            app.config["SECRET_KEY"] = secret
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        CORS(app, supports_credentials=True, origins=r".*")
    else:
        CORS(
            app,
            origins=["http://localhost:5173", "http://127.0.0.1:5173"],
            supports_credentials=True,
        )

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(sites_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        migrate_plant_management_fields()
        migrate_to_plant_architecture()
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@quickconcrete.local")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        create_admin_if_missing(admin_email, admin_password)
        seed_demo_supplier_catalog()
        seed_second_demo_plant_if_applicable()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    if serve_frontend:
        register_frontend_routes(app)

    return app


app = create_app()

if __name__ == "__main__":
    share = (
        os.environ.get("SERVE_FRONTEND") == "1"
        or bool(os.environ.get("RENDER"))
        or bool(os.environ.get("RAILWAY_ENVIRONMENT"))
    )
    app.run(
        host="0.0.0.0" if share else "127.0.0.1",
        port=int(os.environ.get("PORT", 5000)),
        debug=not share,
        use_reloader=not share,
    )
