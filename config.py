"""
config.py
---------
Centralized application configuration for CounterGuard.

All secrets and environment-specific values are read from environment
variables (via a local .env file loaded with python-dotenv) rather than
hard-coded, so the same codebase can move from development to production
without code changes.
"""

import os
from dotenv import load_dotenv

# Load variables from a .env file (if present) into the process environment.
load_dotenv()

# Absolute path to the project root — used to build safe absolute file paths
# for uploads, barcode images, etc.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by every environment."""

    # --- Flask core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-not-secure-change-me")
    SESSION_COOKIE_HTTPONLY = True          # JS cannot read the session cookie
    SESSION_COOKIE_SAMESITE = "Lax"         # CSRF-hardening for cookies
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 4  # 4 hours

    # --- MySQL database ---
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "counterguard_db")
    # Path to a CA certificate file, only needed for managed MySQL hosts
    # (Aiven, etc.) that require TLS. Leave unset for local development.
    DB_SSL_CA = os.environ.get("DB_SSL_CA") or None

    # --- File uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.environ.get("UPLOAD_FOLDER", "static/uploads"))
    BARCODE_FOLDER = os.path.join(BASE_DIR, os.environ.get("BARCODE_FOLDER", "static/barcodes"))
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 5)) * 1024 * 1024

    # --- Admin bootstrap (only used by scripts/seed_admin.py) ---
    DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@counterguard.local")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "Admin@12345")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # allow cookies over plain http on localhost


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True   # cookies only sent over https


# Maps the FLASK_ENV value to a config class. app.py picks the right one.
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
