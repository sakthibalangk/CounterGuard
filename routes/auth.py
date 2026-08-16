"""
routes/auth.py
----------------
Customer-facing authentication: registration, login, logout, and the
customer dashboard landing page after login. Admin authentication
lives separately in routes/admin.py — see that file's docstring for
why the two are kept apart.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models.user import User
from utils.validators import (
    validate_registration_form,
    validate_login_form,
    is_safe_next_url,
    validate_profile_form,
    validate_password_change_form,
)
from utils.decorators import login_required, guest_only
from utils.rate_limit import limiter

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@guest_only("customer", "auth.dashboard")
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = validate_registration_form(full_name, username, email, phone, password, confirm_password)

        # Only hit the database for a duplicate check if the basic
        # shape of the input is already valid — no point querying on
        # obviously-malformed data.
        if not errors and User.username_or_email_exists(username, email):
            errors.append("That username or email is already registered.")

        if errors:
            for error in errors:
                flash(error, "error")
            # Re-render with what they typed (minus the passwords) so
            # they don't have to retype everything after a typo.
            return render_template("register.html", form_data=request.form)

        User.create(full_name, username, email, phone, password)
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form_data={})


@auth_bp.route("/login", methods=["GET", "POST"])
@guest_only("customer", "auth.dashboard")
@limiter.limit("8 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        errors = validate_login_form(identifier, password)
        user = None if errors else User.find_by_identifier(identifier)

        if not errors and (user is None or not User.verify_password(user, password)):
            # Deliberately identical message whether the account
            # doesn't exist or the password is wrong — don't help an
            # attacker enumerate registered emails/usernames.
            errors.append("Invalid username/email or password.")

        if not errors and not user["is_active"]:
            errors.append("This account has been deactivated. Contact support.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("login.html", identifier=identifier)

        # Fresh session on every login — never reuse a session that
        # existed before authentication succeeded.
        session.clear()
        session.permanent = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = "customer"

        flash(f"Welcome back, {user['full_name']}!", "success")

        next_url = request.args.get("next")
        if is_safe_next_url(next_url):
            return redirect(next_url)
        return redirect(url_for("auth.dashboard"))

    return render_template("login.html", identifier="")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    user = User.find_by_id(session["user_id"])
    return render_template("dashboard.html", user=user)


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = User.find_by_id(session["user_id"])

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()

        errors = validate_profile_form(full_name, email, phone)

        if not errors and email != user["email"] and User.email_taken_by_other(email, user["id"]):
            errors.append("That email is already in use by another account.")

        if errors:
            for error in errors:
                flash(error, "error")
            # Re-render with what they typed rather than the stale DB
            # values, so a typo doesn't erase the rest of their edits.
            user = {**user, "full_name": full_name, "email": email, "phone": phone}
            return render_template("profile.html", user=user)

        User.update_profile(user["id"], full_name, email, phone)
        session["username"] = user["username"]  # unchanged, but keeps nav display consistent
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("profile.html", user=user)


@auth_bp.route("/profile/password", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per minute", methods=["POST"])
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = validate_password_change_form(current_password, new_password, confirm_password)

        user = User.find_by_id(session["user_id"])
        if not errors and not User.verify_password(user, current_password):
            errors.append("Your current password is incorrect.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("change_password.html")

        User.update_password(session["user_id"], new_password)
        session.clear()
        flash("Password changed successfully. Please log in again.", "success")
        return redirect(url_for("auth.login"))

    return render_template("change_password.html")
