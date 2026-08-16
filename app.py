"""
app.py
------
Application entry point. Uses the "application factory" pattern
(create_app) rather than a bare module-level `app = Flask(__name__)`
so the app can be configured differently for testing, development,
and production, and so Blueprints can be registered cleanly as each
module of the project is built.

Run with:
    python app.py
or, for production-style serving:
    flask --app app run
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from flask import Flask, render_template, session
from flask_wtf import CSRFProtect

from config import config_by_name
from utils.db import close_db
from utils.rate_limit import limiter


def create_app(env_name=None):
    """Factory that builds and configures the Flask app instance."""

    app = Flask(__name__)

    # ---- Configuration ----
    env_name = env_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, config_by_name["development"]))

    # Ensure upload/barcode folders exist so image saves never fail
    # on a fresh checkout.
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["BARCODE_FOLDER"], exist_ok=True)

    # ---- Database teardown ----
    # Closes the per-request MySQL connection automatically, whether
    # the request succeeded or raised an exception.
    app.teardown_appcontext(close_db)

    # ---- CSRF protection ----
    # Every POST form in the app (login, register, add product, etc.)
    # must include the {{ csrf_token() }} hidden field these templates
    # already render — Flask-WTF rejects the request otherwise.
    CSRFProtect(app)

    # ---- Rate limiting ----
    # Blunts naive brute-force attempts against login/registration.
    # Per-endpoint limits are applied with @limiter.limit(...) directly
    # on the routes in routes/auth.py and routes/admin.py.
    limiter.init_app(app)

    # ---- Security headers ----
    # setdefault rather than a flat assignment, so a route that has a
    # deliberate reason to set its own value (none currently do) isn't
    # silently overridden.
    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    # ---- Production logging ----
    # The Flask dev server's console output disappears the moment the
    # terminal closes. In production (gunicorn, Docker), this writes a
    # rotating log file instead, so a deployed instance's errors are
    # actually recoverable after the fact.
    if not app.debug and not app.testing:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "counterguard.log"), maxBytes=1_000_000, backupCount=3
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("CounterGuard startup")

    # ---- Template globals ----
    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.utcnow().year, "session": session}

    # ---- Blueprints ----
    # Registered here as each module is built. Uncomment as each
    # blueprint is added in its own file under routes/.
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.product import product_bp
    from routes.scan import scan_bp
    from routes.report import report_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(product_bp, url_prefix="/admin/products")
    app.register_blueprint(scan_bp)
    app.register_blueprint(report_bp)

    # ---- Landing page ----
    @app.route("/")
    def home():
        return render_template("index.html")

    # ---- Error handlers ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="You don't have permission to view this page."), 403

    @app.errorhandler(413)
    def too_large(e):
        return render_template("error.html", code=413, message="Uploaded file is too large."), 413

    @app.errorhandler(429)
    def rate_limited(e):
        return (
            render_template(
                "error.html", code=429, message="Too many attempts. Please wait a moment and try again."
            ),
            429,
        )

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500, message="Something went wrong on our end."), 500

    return app


# Allows `python app.py` to run a dev server directly.
if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config.get("DEBUG", True), host="0.0.0.0", port=5000)
