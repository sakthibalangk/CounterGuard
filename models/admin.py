"""
models/admin.py
-----------------
Data-access class for the `admins` table. Deliberately separate
from models/user.py — admins are a distinct account type with a
`role` column (super_admin / admin) rather than "a user with a flag",
which keeps privilege escalation bugs harder to introduce by
construction: there is no shared table or shared row an attacker
could flip a bit on to become an admin.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_cursor, get_db


class Admin:

    @staticmethod
    def create(full_name, username, email, password, role="admin"):
        """Insert a new admin account. Returns the new admin's id."""
        password_hash = generate_password_hash(password)
        cursor = get_cursor()
        cursor.execute(
            """INSERT INTO admins (full_name, username, email, password_hash, role)
               VALUES (%s, %s, %s, %s, %s)""",
            (full_name, username, email, password_hash, role),
        )
        get_db().commit()
        return cursor.lastrowid

    @staticmethod
    def find_by_identifier(identifier):
        cursor = get_cursor()
        cursor.execute(
            "SELECT * FROM admins WHERE username = %s OR email = %s LIMIT 1",
            (identifier, identifier),
        )
        return cursor.fetchone()

    @staticmethod
    def find_by_id(admin_id):
        cursor = get_cursor()
        cursor.execute("SELECT * FROM admins WHERE id = %s", (admin_id,))
        return cursor.fetchone()

    @staticmethod
    def username_or_email_exists(username, email):
        cursor = get_cursor()
        cursor.execute(
            "SELECT id FROM admins WHERE username = %s OR email = %s LIMIT 1",
            (username, email),
        )
        return cursor.fetchone() is not None

    @staticmethod
    def verify_password(admin_row, password):
        return check_password_hash(admin_row["password_hash"], password)

    @staticmethod
    def email_taken_by_other(email, admin_id):
        cursor = get_cursor()
        cursor.execute(
            "SELECT id FROM admins WHERE email = %s AND id != %s LIMIT 1", (email, admin_id)
        )
        return cursor.fetchone() is not None

    @staticmethod
    def update_profile(admin_id, full_name, email):
        """Username and role are deliberately not editable here — role
        changes go through direct DB access only, not a self-service
        form, so an admin can never escalate their own privileges."""
        cursor = get_cursor()
        cursor.execute(
            "UPDATE admins SET full_name = %s, email = %s WHERE id = %s",
            (full_name, email, admin_id),
        )
        get_db().commit()

    @staticmethod
    def update_password(admin_id, new_password):
        password_hash = generate_password_hash(new_password)
        cursor = get_cursor()
        cursor.execute(
            "UPDATE admins SET password_hash = %s WHERE id = %s", (password_hash, admin_id)
        )
        get_db().commit()
