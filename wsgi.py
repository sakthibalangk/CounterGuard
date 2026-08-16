"""
wsgi.py
--------
Entry point for a production WSGI server (gunicorn). app.py's
create_app() factory needs to be called once at import time here,
since gunicorn imports this module and looks for a module-level `app`
object — it never runs app.py's `if __name__ == "__main__"` block,
which only starts Flask's own dev server.

Run locally with:
    gunicorn wsgi:app --bind 0.0.0.0:5000

This is also what the Dockerfile's CMD uses in production.
"""

from app import create_app

app = create_app()
