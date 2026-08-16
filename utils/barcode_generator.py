"""
utils/barcode_generator.py
----------------------------
Generates a unique barcode value for each new product and renders it
as a scannable Code128 barcode image (Code128 is used rather than
EAN-13 because it accepts our alphanumeric "CG-XXXXXXXXXX" values
directly, with no checksum-digit gymnastics).
"""

import os
import random
import string

import barcode
from barcode.writer import ImageWriter

from models.product import Product

CODE128 = barcode.get_barcode_class("code128")


def generate_unique_barcode_value(prefix="CG"):
    """
    Generate a barcode value guaranteed not to collide with an
    existing product, by generating and checking against the database
    until a free one turns up (collisions are astronomically rare
    with 10 random digits, so this almost always succeeds on the
    first try).
    """
    for _ in range(20):
        candidate = prefix + "".join(random.choices(string.digits, k=10))
        if not Product.barcode_exists(candidate):
            return candidate
    # Practically unreachable, but fail loudly rather than silently
    # returning a colliding value if it ever does happen.
    raise RuntimeError("Could not generate a unique barcode value after 20 attempts.")


def generate_barcode_image(barcode_value, barcode_folder):
    """
    Render `barcode_value` as a Code128 barcode PNG under
    `barcode_folder`. Returns the saved filename (not a full path).
    """
    os.makedirs(barcode_folder, exist_ok=True)
    writer_options = {
        "module_height": 12.0,
        "font_size": 10,
        "text_distance": 3,
        "quiet_zone": 2,
    }
    code = CODE128(barcode_value, writer=ImageWriter())
    # .save() appends the writer's extension (.png) itself, and
    # returns the full path it wrote to — we only want the filename.
    saved_path = code.save(os.path.join(barcode_folder, barcode_value), options=writer_options)
    return os.path.basename(saved_path)
