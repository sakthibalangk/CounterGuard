"""
models/report.py
-------------------
Data-access class for the `reports` table — customer-submitted
counterfeit reports and the admin review workflow around them.

A report always carries the barcode value that was scanned, and
*optionally* a product_id when the report was raised against a
barcode that WAS found in the catalog (a customer can also report a
product they believe is fake even if it scanned as "genuine" — the
barcode matching a database row doesn't mean the physical item in
their hand is real).
"""

from utils.db import get_cursor, get_db


class Report:

    @staticmethod
    def create(user_id, product_id, barcode_value, description, evidence_image):
        cursor = get_cursor()
        cursor.execute(
            """INSERT INTO reports (user_id, product_id, barcode_value, description, evidence_image)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, product_id, barcode_value, description, evidence_image),
        )
        get_db().commit()
        return cursor.lastrowid

    @staticmethod
    def find_by_id(report_id):
        cursor = get_cursor()
        cursor.execute(
            """SELECT reports.*, users.full_name AS reporter_name, users.email AS reporter_email,
                      products.name AS product_name, products.brand AS product_brand
               FROM reports
               LEFT JOIN users ON reports.user_id = users.id
               LEFT JOIN products ON reports.product_id = products.id
               WHERE reports.id = %s""",
            (report_id,),
        )
        return cursor.fetchone()

    @staticmethod
    def get_by_user(user_id, page=1, per_page=10):
        cursor = get_cursor()
        offset = (page - 1) * per_page
        cursor.execute(
            """SELECT reports.*, products.name AS product_name, products.brand AS product_brand
               FROM reports
               LEFT JOIN products ON reports.product_id = products.id
               WHERE reports.user_id = %s
               ORDER BY reports.reported_at DESC
               LIMIT %s OFFSET %s""",
            (user_id, per_page, offset),
        )
        return cursor.fetchall()

    @staticmethod
    def count_by_user(user_id):
        cursor = get_cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM reports WHERE user_id = %s", (user_id,))
        return cursor.fetchone()["total"]

    @staticmethod
    def get_all(status=None, page=1, per_page=10):
        cursor = get_cursor()
        offset = (page - 1) * per_page
        if status:
            cursor.execute(
                """SELECT reports.*, users.full_name AS reporter_name, users.email AS reporter_email,
                          products.name AS product_name, products.brand AS product_brand
                   FROM reports
                   LEFT JOIN users ON reports.user_id = users.id
                   LEFT JOIN products ON reports.product_id = products.id
                   WHERE reports.status = %s
                   ORDER BY reports.reported_at DESC
                   LIMIT %s OFFSET %s""",
                (status, per_page, offset),
            )
        else:
            cursor.execute(
                """SELECT reports.*, users.full_name AS reporter_name, users.email AS reporter_email,
                          products.name AS product_name, products.brand AS product_brand
                   FROM reports
                   LEFT JOIN users ON reports.user_id = users.id
                   LEFT JOIN products ON reports.product_id = products.id
                   ORDER BY reports.reported_at DESC
                   LIMIT %s OFFSET %s""",
                (per_page, offset),
            )
        return cursor.fetchall()

    @staticmethod
    def count(status=None):
        cursor = get_cursor()
        if status:
            cursor.execute("SELECT COUNT(*) AS total FROM reports WHERE status = %s", (status,))
        else:
            cursor.execute("SELECT COUNT(*) AS total FROM reports")
        return cursor.fetchone()["total"]

    @staticmethod
    def update_status(report_id, status, admin_id, admin_notes):
        cursor = get_cursor()
        cursor.execute(
            """UPDATE reports
               SET status = %s, reviewed_by = %s, admin_notes = %s, reviewed_at = NOW()
               WHERE id = %s""",
            (status, admin_id, admin_notes, report_id),
        )
        get_db().commit()
