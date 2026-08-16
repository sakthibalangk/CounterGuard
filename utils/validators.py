"""
utils/validators.py
--------------------
Server-side form validation. Client-side HTML5 validation (required,
type="email", minlength, etc.) is a nice UX layer, but it can always
be bypassed — these functions are the real gate, since they run on
the server no matter what submitted the request.

Each validate_* function returns a list of human-readable error
strings. An empty list means the input is valid.
"""

import re

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s]{7,15}$")


def validate_registration_form(full_name, username, email, phone, password, confirm_password):
    """Validate all fields for the customer registration form."""
    errors = []

    if not full_name or len(full_name.strip()) < 2:
        errors.append("Please enter your full name.")

    if not username or not USERNAME_RE.match(username):
        errors.append("Username must be 3-30 characters: letters, numbers, and underscores only.")

    if not email or not EMAIL_RE.match(email):
        errors.append("Please enter a valid email address.")

    if phone and not PHONE_RE.match(phone):
        errors.append("Please enter a valid phone number.")

    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    elif not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one letter and one number.")

    if password != confirm_password:
        errors.append("Passwords do not match.")

    return errors


def validate_login_form(identifier, password):
    """Validate the (very minimal) shape of a login submission."""
    errors = []
    if not identifier or not identifier.strip():
        errors.append("Please enter your username or email.")
    if not password:
        errors.append("Please enter your password.")
    return errors


def is_safe_next_url(next_url):
    """
    Guard against open-redirect attacks via a ?next= query parameter.
    Only allow relative paths that start with a single '/', never a
    scheme-relative URL like '//evil.com' or an absolute URL.
    """
    return bool(next_url) and next_url.startswith("/") and not next_url.startswith("//")


def validate_product_form(name, brand, price, manufacture_date, expiry_date):
    """
    Validate the admin add/edit product form. Dates are expected as
    strings in 'YYYY-MM-DD' format (what an <input type="date"> posts)
    or empty. Returns a list of error strings.
    """
    from datetime import datetime

    errors = []

    if not name or len(name.strip()) < 2:
        errors.append("Please enter a product name.")

    if not brand or len(brand.strip()) < 1:
        errors.append("Please enter a brand.")

    parsed_manufacture = None
    if price:
        try:
            price_value = float(price)
            if price_value < 0:
                errors.append("Price cannot be negative.")
        except ValueError:
            errors.append("Price must be a number.")

    if manufacture_date:
        try:
            parsed_manufacture = datetime.strptime(manufacture_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Manufacture date is not a valid date.")

    if expiry_date:
        try:
            parsed_expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
            if parsed_manufacture and parsed_expiry < parsed_manufacture:
                errors.append("Expiry date cannot be before the manufacture date.")
        except ValueError:
            errors.append("Expiry date is not a valid date.")

    return errors


def validate_report_form(barcode_value, description):
    """Validate the customer counterfeit-report form."""
    errors = []

    if not barcode_value or not barcode_value.strip():
        errors.append("A barcode value is required.")
    elif len(barcode_value) > 64:
        errors.append("That barcode is too long — please check what you entered.")

    if not description or len(description.strip()) < 10:
        errors.append("Please describe the issue in at least 10 characters.")
    elif len(description) > 2000:
        errors.append("Description is too long (max 2000 characters).")

    return errors


def validate_profile_form(full_name, email, phone):
    """Validate the customer profile-edit form. Username is deliberately
    not editable here — it's used across the app as a stable identifier
    (login, display in nav, etc.) and changing it is out of scope."""
    errors = []

    if not full_name or len(full_name.strip()) < 2:
        errors.append("Please enter your full name.")

    if not email or not EMAIL_RE.match(email):
        errors.append("Please enter a valid email address.")

    if phone and not PHONE_RE.match(phone):
        errors.append("Please enter a valid phone number.")

    return errors


def validate_password_change_form(current_password, new_password, confirm_password):
    """Validate the change-password form. Does NOT check whether
    current_password is actually correct — that requires a DB lookup,
    which the route handles separately with User.verify_password()."""
    errors = []

    if not current_password:
        errors.append("Please enter your current password.")

    if not new_password or len(new_password) < 8:
        errors.append("New password must be at least 8 characters long.")
    elif not re.search(r"[A-Za-z]", new_password) or not re.search(r"[0-9]", new_password):
        errors.append("New password must contain at least one letter and one number.")

    if new_password != confirm_password:
        errors.append("New passwords do not match.")

    if current_password and new_password and current_password == new_password:
        errors.append("New password must be different from your current password.")

    return errors
