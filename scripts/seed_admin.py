"""
scripts/seed_admin.py
-----------------------
Creates the first administrator account using the DEFAULT_ADMIN_*
values from .env, so you never have to hand-write an INSERT with a
manually-computed password hash.

Run once, from the project root (with your venv active):

    python scripts/seed_admin.py

Safe to run again later — it checks for an existing admin with the
same username/email first and refuses to create a duplicate.
"""

import os
import sys

# Allow running this script directly from the scripts/ folder while
# still importing config.py and models/ from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models.admin import Admin


def main():
    app = create_app()

    with app.app_context():
        username = app.config["DEFAULT_ADMIN_USERNAME"]
        email = app.config["DEFAULT_ADMIN_EMAIL"]
        password = app.config["DEFAULT_ADMIN_PASSWORD"]

        if Admin.username_or_email_exists(username, email):
            print(f"An admin with username '{username}' or email '{email}' already exists. Nothing to do.")
            return

        Admin.create(
            full_name="System Administrator",
            username=username,
            email=email,
            password=password,
            role="super_admin",
        )
        print("Admin account created:")
        print(f"  Username: {username}")
        print(f"  Email:    {email}")
        print(f"  Password: {password}  (change this after your first login!)")


if __name__ == "__main__":
    main()
