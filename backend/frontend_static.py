import os

from flask import abort, send_from_directory

FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)


def register_frontend_routes(app):
    if not os.path.isdir(FRONTEND_DIST):
        app.logger.warning(
            "frontend/dist not found — run: cd frontend && npm run build"
        )
        return

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def serve_spa(path):
        if path.startswith("api/") or path == "api":
            abort(404)
        if path:
            candidate = os.path.join(FRONTEND_DIST, path)
            if os.path.isfile(candidate):
                return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")
