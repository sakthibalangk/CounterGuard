"""
utils/rate_limit.py
----------------------
A single shared Flask-Limiter instance, created here rather than
inline in app.py so route modules can import it and decorate
individual endpoints (login, admin login, registration) without a
circular import back to app.py's create_app().

Storage backend is in-memory (Flask-Limiter's default), which is
fine for a single-process deployment like this project's — every
gunicorn worker would track its own counts independently, which is
an acknowledged limitation, not a bug: the goal here is to blunt
naive brute-force attempts, not to be a bulletproof, distributed
rate limiter. A real high-traffic deployment would point this at
Redis instead (`storage_uri="redis://..."`), a one-line change.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["300 per hour"])
