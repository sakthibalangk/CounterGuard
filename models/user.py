"""
models/user.py
---------------
Data-access class for the `users` table (customer accounts).

Kept as plain static methods over parameterized SQL rather than a
full ORM — this is a final-year/portfolio project, and this style
makes it obvious to a reviewer exactly what SQL runs for every
operation, with no hidden query generation.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_cursor, get_db


class User:

    @staticmethod
    def create(full_name, username, email, phone, password):
        """Insert a new customer, hashing the password first. Returns the new user's id."""
        password_hash = generate_password_hash(password)
        cursor = get_cursor()
        cursor.execute(
            """INSERT INTO users (full_name, username, email, phone, password_hash)
               VALUES (%s, %s, %s, %s, %s)""",
            (full_name, username, email, phone, password_hash),
        )
        get_db().commit()
        return cursor.lastrowid

    @staticmethod
    def find_by_identifier(identifier):
        """Look up a customer by username OR email — used at login,
        since we let people sign in with either."""
        cursor = get_cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = %s OR email = %s LIMIT 1",
            (identifier, identifier),
        )
        return cursor.fetchone()

    @staticmethod
    def find_by_id(user_id):
        cursor = get_cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()

    @staticmethod
    def username_or_email_exists(username, email):
        """Used during registration to reject duplicate usernames/emails
        with a clear message instead of a raw MySQL duplicate-key error."""
        cursor = get_cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s LIMIT 1",
            (username, email),
        )
        return cursor.fetchone() is not None

    @staticmethod
    def verify_password(user_row, password):
        return check_password_hash(user_row["password_hash"], password)

    # -----------------------------------------------------------
    # Self-service profile management (Module 9)
    # -----------------------------------------------------------

    @staticmethod
    def email_taken_by_other(email, user_id):
        """Used when a customer changes their own email — must stay
        unique, but obviously shouldn't collide with their own
        existing row."""
        cursor = get_cursor()
        cursor.execute(
            "SELECT id FROM users WHERE email = %s AND id != %s LIMIT 1",
            (email, user_id),
        )
        return cursor.fetchone() is not None

    @staticmethod
    def update_profile(user_id, full_name, email, phone):
        cursor = get_cursor()
        cursor.execute(
            "UPDATE users SET full_name = %s, email = %s, phone = %s WHERE id = %s",
            (full_name, email, phone, user_id),
        )
        get_db().commit()

    @staticmethod
    def update_password(user_id, new_password):
        password_hash = generate_password_hash(new_password)
        cursor = get_cursor()
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user_id),
        )
        get_db().commit()

    # -----------------------------------------------------------
    # Admin-facing queries (Module 7 — user management)
    # -----------------------------------------------------------

    @staticmethod
    def get_all(search=None, page=1, per_page=10):
        """Paginated customer list for the admin portal, optionally
        filtered by a search term matched against name/username/email."""
        cursor = get_cursor()
        offset = (page - 1) * per_page
        if search:
            like = f"%{search}%"
            cursor.execute(
                """SELECT * FROM users
                   WHERE full_name LIKE %s OR username LIKE %s OR email LIKE %s
                   ORDER BY created_at DESC
                   LIMIT %s OFFSET %s""",
                (like, like, like, per_page, offset),
            )
        else:
            cursor.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (per_page, offset),
            )
        return cursor.fetchall()

    @staticmethod
    def count(search=None):
        cursor = get_cursor()
        if search:
            like = f"%{search}%"
            cursor.execute(
                """SELECT COUNT(*) AS total FROM users
                   WHERE full_name LIKE %s OR username LIKE %s OR email LIKE %s""",
                (like, like, like),
            )
        else:
            cursor.execute("SELECT COUNT(*) AS total FROM users")
        return cursor.fetchone()["total"]

    @staticmethod
    def set_active(user_id, is_active):
        """Activate or deactivate a customer account. A deactivated
        account still exists (and its scan/report history is kept
        intact) but can no longer log in — see login() in
        routes/auth.py, which checks is_active after verifying the
        password."""
        cursor = get_cursor()
        cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (is_active, user_id))
        get_db().commit()

    @staticmethod
    def get_activity_counts(user_id):
        """Scan and report counts for one customer — shown on their
        admin detail view. Two small queries rather than one join is
        simpler to read and this is a low-traffic admin-only page."""
        cursor = get_cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM scans WHERE user_id = %s", (user_id,))
        scan_count = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM reports WHERE user_id = %s", (user_id,))
        report_count = cursor.fetchone()["total"]
        return {"scan_count": scan_count, "report_count": report_count}
