"""
models/scan.py
----------------
Data-access class for the `scans` table. Every barcode verification
attempt gets logged here — whether it matched a real product or not —
which is what Module 5 (scan history) and Module 8 (analytics) will
read from.
"""

from utils.db import get_cursor, get_db


class Scan:

    @staticmethod
    def create(user_id, product_id, barcode_value, result_status, ip_address):
        cursor = get_cursor()
        cursor.execute(
            """INSERT INTO scans (user_id, product_id, barcode_value, result_status, ip_address)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, product_id, barcode_value, result_status, ip_address),
        )
        get_db().commit()
        return cursor.lastrowid

    @staticmethod
    def find_by_user(user_id, limit=50):
        """Most recent scans for one customer, newest first, with the
        matched product's name/brand joined in when there was a match.
        Kept for callers that just want a quick recent list without
        pagination — Module 5's history page uses get_by_user instead."""
        cursor = get_cursor()
        cursor.execute(
            """SELECT scans.*, products.name AS product_name, products.brand AS product_brand
               FROM scans
               LEFT JOIN products ON scans.product_id = products.id
               WHERE scans.user_id = %s
               ORDER BY scans.scanned_at DESC
               LIMIT %s""",
            (user_id, limit),
        )
        return cursor.fetchall()

    @staticmethod
    def get_by_user(user_id, result_status=None, page=1, per_page=10):
        """Paginated scan history for one customer, optionally filtered
        to only 'genuine' or only 'not_found' results."""
        cursor = get_cursor()
        offset = (page - 1) * per_page
        if result_status:
            cursor.execute(
                """SELECT scans.*, products.name AS product_name, products.brand AS product_brand
                   FROM scans
                   LEFT JOIN products ON scans.product_id = products.id
                   WHERE scans.user_id = %s AND scans.result_status = %s
                   ORDER BY scans.scanned_at DESC
                   LIMIT %s OFFSET %s""",
                (user_id, result_status, per_page, offset),
            )
        else:
            cursor.execute(
                """SELECT scans.*, products.name AS product_name, products.brand AS product_brand
                   FROM scans
                   LEFT JOIN products ON scans.product_id = products.id
                   WHERE scans.user_id = %s
                   ORDER BY scans.scanned_at DESC
                   LIMIT %s OFFSET %s""",
                (user_id, per_page, offset),
            )
        return cursor.fetchall()

    @staticmethod
    def count_by_user(user_id, result_status=None):
        cursor = get_cursor()
        if result_status:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM scans WHERE user_id = %s AND result_status = %s",
                (user_id, result_status),
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM scans WHERE user_id = %s", (user_id,)
            )
        return cursor.fetchone()["total"]

    @staticmethod
    def count_all():
        cursor = get_cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM scans")
        return cursor.fetchone()["total"]

    @staticmethod
    def count_by_status(result_status):
        cursor = get_cursor()
        cursor.execute(
            "SELECT COUNT(*) AS total FROM scans WHERE result_status = %s",
            (result_status,),
        )
        return cursor.fetchone()["total"]
