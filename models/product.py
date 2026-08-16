"""
models/product.py
-------------------
Data-access class for the `products` table. Search and pagination are
done in SQL (LIKE + LIMIT/OFFSET) rather than fetching everything and
filtering in Python — this is the pattern that keeps working even
once the catalog has thousands of rows, not just the handful you'll
seed for a demo.
"""

from utils.db import get_cursor, get_db


class Product:

    @staticmethod
    def create(name, brand, category, description, manufacturer, barcode_value,
               barcode_image_path, product_image_path, price, manufacture_date,
               expiry_date, created_by):
        cursor = get_cursor()
        cursor.execute(
            """INSERT INTO products
               (name, brand, category, description, manufacturer, barcode_value,
                barcode_image_path, product_image_path, price, manufacture_date,
                expiry_date, created_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, brand, category, description, manufacturer, barcode_value,
             barcode_image_path, product_image_path, price, manufacture_date,
             expiry_date, created_by),
        )
        get_db().commit()
        return cursor.lastrowid

    @staticmethod
    def update(product_id, name, brand, category, description, manufacturer,
               price, manufacture_date, expiry_date, status, product_image_path=None):
        """product_image_path=None means 'leave the existing image alone' —
        pass an actual filename only when the admin uploaded a new one."""
        cursor = get_cursor()
        if product_image_path is not None:
            cursor.execute(
                """UPDATE products
                   SET name=%s, brand=%s, category=%s, description=%s, manufacturer=%s,
                       price=%s, manufacture_date=%s, expiry_date=%s, status=%s,
                       product_image_path=%s
                   WHERE id=%s""",
                (name, brand, category, description, manufacturer, price,
                 manufacture_date, expiry_date, status, product_image_path, product_id),
            )
        else:
            cursor.execute(
                """UPDATE products
                   SET name=%s, brand=%s, category=%s, description=%s, manufacturer=%s,
                       price=%s, manufacture_date=%s, expiry_date=%s, status=%s
                   WHERE id=%s""",
                (name, brand, category, description, manufacturer, price,
                 manufacture_date, expiry_date, status, product_id),
            )
        get_db().commit()

    @staticmethod
    def delete(product_id):
        cursor = get_cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        get_db().commit()

    @staticmethod
    def find_by_id(product_id):
        cursor = get_cursor()
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        return cursor.fetchone()

    @staticmethod
    def find_by_barcode(barcode_value):
        cursor = get_cursor()
        cursor.execute("SELECT * FROM products WHERE barcode_value = %s", (barcode_value,))
        return cursor.fetchone()

    @staticmethod
    def barcode_exists(barcode_value):
        cursor = get_cursor()
        cursor.execute("SELECT id FROM products WHERE barcode_value = %s", (barcode_value,))
        return cursor.fetchone() is not None

    @staticmethod
    def get_all(search=None, page=1, per_page=10):
        cursor = get_cursor()
        offset = (page - 1) * per_page
        if search:
            like = f"%{search}%"
            cursor.execute(
                """SELECT * FROM products
                   WHERE name LIKE %s OR brand LIKE %s OR barcode_value LIKE %s
                   ORDER BY created_at DESC LIMIT %s OFFSET %s""",
                (like, like, like, per_page, offset),
            )
        else:
            cursor.execute(
                "SELECT * FROM products ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (per_page, offset),
            )
        return cursor.fetchall()

    @staticmethod
    def count(search=None):
        cursor = get_cursor()
        if search:
            like = f"%{search}%"
            cursor.execute(
                """SELECT COUNT(*) AS total FROM products
                   WHERE name LIKE %s OR brand LIKE %s OR barcode_value LIKE %s""",
                (like, like, like),
            )
        else:
            cursor.execute("SELECT COUNT(*) AS total FROM products")
        return cursor.fetchone()["total"]
