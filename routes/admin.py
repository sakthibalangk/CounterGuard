"""
routes/admin.py
-----------------
Admin portal blueprint. Registered in app.py with url_prefix="/admin",
so every route here is namespaced under /admin/... automatically —
there is no URL overlap with the customer portal, and no shared
session state between the two: an admin session carries
session['role'] == 'admin' and session['admin_id'], a customer
session carries session['role'] == 'customer' and session['user_id'].
Nothing here ever checks `user_id`, and nothing in auth.py ever checks
`admin_id` — the two portals cannot leak into each other by accident.

This file will keep growing in later modules (product management,
user management, reports, analytics) — for now it covers secure login
and a placeholder dashboard to prove the auth flow end-to-end.
"""

import math

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models.admin import Admin
from models.product import Product
from models.scan import Scan
from models.report import Report
from models.user import User
from models.analytics import Analytics
from utils.validators import validate_login_form, validate_profile_form, validate_password_change_form
from utils.decorators import admin_required, guest_only
from utils.rate_limit import limiter

admin_bp = Blueprint("admin", __name__)

PER_PAGE = 10


@admin_bp.route("/login", methods=["GET", "POST"])
@guest_only("admin", "admin.admin_dashboard")
@limiter.limit("5 per minute", methods=["POST"])
def admin_login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        errors = validate_login_form(identifier, password)
        admin = None if errors else Admin.find_by_identifier(identifier)

        if not errors and (admin is None or not Admin.verify_password(admin, password)):
            errors.append("Invalid administrator credentials.")

        if not errors and not admin["is_active"]:
            errors.append("This admin account has been deactivated.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("admin_login.html", identifier=identifier)

        session.clear()
        session.permanent = True
        session["admin_id"] = admin["id"]
        session["admin_username"] = admin["username"]
        session["admin_role"] = admin["role"]
        session["role"] = "admin"

        flash(f"Welcome back, {admin['full_name']}.", "success")
        return redirect(url_for("admin.admin_dashboard"))

    return render_template("admin_login.html", identifier="")


@admin_bp.route("/logout")
def admin_logout():
    session.clear()
    flash("Administrator logged out.", "success")
    return redirect(url_for("admin.admin_login"))


@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    admin = Admin.find_by_id(session["admin_id"])
    # Analytics remains the last placeholder card — everything else is
    # live now.
    product_count = Product.count()
    scan_count = Scan.count_all()
    pending_report_count = Report.count(status="pending")
    user_count = User.count()
    return render_template(
        "admin_dashboard.html",
        admin=admin,
        product_count=product_count,
        scan_count=scan_count,
        pending_report_count=pending_report_count,
        user_count=user_count,
    )


@admin_bp.route("/reports")
@admin_required
def list_reports():
    status_filter = request.args.get("status", "").strip()
    if status_filter not in ("pending", "reviewed", "resolved", "rejected"):
        status_filter = None

    page = max(1, request.args.get("page", 1, type=int))

    reports = Report.get_all(status=status_filter, page=page, per_page=PER_PAGE)
    total = Report.count(status=status_filter)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    return render_template(
        "reports.html",
        reports=reports,
        status_filter=status_filter,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@admin_bp.route("/reports/<int:report_id>/update", methods=["POST"])
@admin_required
def update_report(report_id):
    report = Report.find_by_id(report_id)
    if not report:
        flash("Report not found.", "error")
        return redirect(url_for("admin.list_reports"))

    new_status = request.form.get("status", "").strip()
    admin_notes = request.form.get("admin_notes", "").strip() or None

    if new_status not in ("pending", "reviewed", "resolved", "rejected"):
        flash("Invalid status.", "error")
        return redirect(url_for("admin.list_reports"))

    Report.update_status(report_id, new_status, session["admin_id"], admin_notes)
    flash(f"Report #{report_id} marked as {new_status}.", "success")
    return redirect(url_for("admin.list_reports"))


@admin_bp.route("/users")
@admin_required
def list_users():
    search = request.args.get("q", "").strip()
    page = max(1, request.args.get("page", 1, type=int))

    users = User.get_all(search=search or None, page=page, per_page=PER_PAGE)
    total = User.count(search=search or None)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    return render_template(
        "users.html", users=users, search=search, page=page, total_pages=total_pages, total=total
    )


@admin_bp.route("/users/<int:user_id>")
@admin_required
def view_user(user_id):
    user = User.find_by_id(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.list_users"))

    activity = User.get_activity_counts(user_id)
    recent_scans = Scan.find_by_user(user_id, limit=5)

    return render_template("user_detail.html", user=user, activity=activity, recent_scans=recent_scans)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_user_active(user_id):
    user = User.find_by_id(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.list_users"))

    new_status = not user["is_active"]
    User.set_active(user_id, new_status)

    flash(
        f"{user['full_name']}'s account has been {'reactivated' if new_status else 'deactivated'}.",
        "success",
    )
    return redirect(request.form.get("next") or url_for("admin.list_users"))


@admin_bp.route("/analytics")
@admin_required
def analytics():
    days = request.args.get("days", 14, type=int)
    if days not in (7, 14, 30):
        days = 14

    scan_labels, scan_counts = Analytics.scans_per_day(days=days)
    top_product_labels, top_product_counts = Analytics.top_scanned_products(limit=5)

    return render_template(
        "analytics.html",
        days=days,
        summary=Analytics.summary_counts(),
        scan_labels=scan_labels,
        scan_counts=scan_counts,
        result_breakdown=Analytics.scan_result_breakdown(),
        report_breakdown=Analytics.reports_by_status(),
        top_product_labels=top_product_labels,
        top_product_counts=top_product_counts,
    )


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    admin = Admin.find_by_id(session["admin_id"])

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()

        # Reuses the same validator as the customer profile form —
        # phone isn't a field admins have, so it's simply passed as
        # None and the validator skips that check.
        errors = validate_profile_form(full_name, email, None)

        if not errors and email != admin["email"] and Admin.email_taken_by_other(email, admin["id"]):
            errors.append("That email is already in use by another admin account.")

        if errors:
            for error in errors:
                flash(error, "error")
            admin = {**admin, "full_name": full_name, "email": email}
            return render_template("admin_settings.html", admin=admin)

        Admin.update_profile(admin["id"], full_name, email)
        flash("Profile updated successfully.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin_settings.html", admin=admin)


@admin_bp.route("/settings/password", methods=["GET", "POST"])
@admin_required
@limiter.limit("10 per minute", methods=["POST"])
def admin_change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = validate_password_change_form(current_password, new_password, confirm_password)

        admin = Admin.find_by_id(session["admin_id"])
        if not errors and not Admin.verify_password(admin, current_password):
            errors.append("Your current password is incorrect.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("admin_change_password.html")

        Admin.update_password(session["admin_id"], new_password)
        session.clear()
        flash("Password changed successfully. Please log in again.", "success")
        return redirect(url_for("admin.admin_login"))

    return render_template("admin_change_password.html")
