"""
utils/decorators.py
--------------------
Route-protection decorators shared by every module. Two separate
session roles are used ('customer' and 'admin') so a logged-in
customer can never accidentally — or deliberately — hit an admin-only
route just because they're logged in to *something*, and vice versa.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request


def login_required(f):
    """Require a logged-in customer session. Redirects to the
    customer login page and remembers where they were headed."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "customer" or "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Require a logged-in admin session."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin" or "admin_id" not in session:
            flash("Please log in as an administrator to continue.", "warning")
            return redirect(url_for("admin.admin_login"))
        return f(*args, **kwargs)

    return decorated


def guest_only(role, redirect_endpoint):
    """
    Decorator factory: keeps someone already logged in to a given
    portal away from that portal's own login/register pages (e.g. a
    logged-in customer hitting /login again gets bounced straight to
    their dashboard instead of seeing the form). Scoped to a single
    `role` so a logged-in customer isn't blocked from viewing the
    separate admin login page, and vice versa. Usage:

        @guest_only("customer", "auth.dashboard")
        def login(): ...
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("role") == role:
                return redirect(url_for(redirect_endpoint))
            return f(*args, **kwargs)

        return decorated

    return decorator
