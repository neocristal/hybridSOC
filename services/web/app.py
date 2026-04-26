"""HybridSOC Web — Flask application factory."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from .config import Config
from .db import close_connection, get_db, run_migrations


def create_app(config: Config | None = None) -> Flask:
    cfg = config or Config.from_env()

    app = Flask(__name__, static_folder=None)
    app.config.from_object(cfg)
    app.logger.setLevel(logging.INFO)

    # Run migrations on startup so the schema is always current
    with app.app_context():
        run_migrations(get_db(), cfg.MIGRATIONS_DIR)

    app.teardown_appcontext(close_connection)

    # Register blueprints
    from .blueprints.auth import bp as auth_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.dashboard import bp as dashboard_bp
    from .blueprints.risk import bp as risk_bp
    from .blueprints.grc import bp as grc_bp
    from .blueprints.audit import bp as audit_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(risk_bp, url_prefix="/api/risk")
    app.register_blueprint(grc_bp, url_prefix="/api/grc")
    app.register_blueprint(audit_bp, url_prefix="/api/audit")

    @app.get("/api/health")
    def health():
        return jsonify(
            status="ok",
            service="hybridsoc-web",
            version="2.0.0",
            db=str(cfg.DATABASE_PATH),
        )

    # Serve the built frontend (Vite output) when present
    frontend_dist = Path(cfg.FRONTEND_DIST)

    @app.get("/")
    @app.get("/<path:path>")
    def spa(path: str = ""):
        if not frontend_dist.exists():
            return (
                "<h1>HybridSOC Web</h1>"
                "<p>Frontend not built. Run <code>npm install &amp;&amp; npm run build</code> "
                "in <code>services/web/frontend</code>.</p>",
                200,
            )
        candidate = frontend_dist / path
        if path and candidate.is_file():
            return send_from_directory(frontend_dist, path)
        return send_from_directory(frontend_dist, "index.html")

    return app


if __name__ == "__main__":
    create_app().run(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
