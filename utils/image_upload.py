"""
utils/image_upload.py
-----------------------
Handles product image uploads safely:
  - only accepts allowed extensions
  - re-opens the file with Pillow and calls .verify() so a file that's
    merely renamed to .jpg but isn't actually a valid image gets
    rejected, rather than trusted on the extension alone
  - resizes down to a sane max dimension so a 20MB phone photo doesn't
    get served back to every visitor at full size
  - saves under a random filename (never the browser-supplied name)
    so there's no path-traversal or overwrite risk
"""

import os
import uuid

from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

MAX_DIMENSION = 1000  # longest side, in pixels, after resize


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_product_image(file_storage, upload_folder, allowed_extensions):
    """
    Validate and save an uploaded product image.

    Returns the saved filename (not a full path — templates build the
    URL with url_for('static', filename='uploads/' + filename)) on
    success, or raises ValueError with a user-facing message on
    failure. Returns None if no file was actually submitted.
    """
    if not file_storage or file_storage.filename == "":
        return None

    original_name = secure_filename(file_storage.filename)
    if not allowed_file(original_name, allowed_extensions):
        raise ValueError(
            f"Unsupported file type. Allowed types: {', '.join(sorted(allowed_extensions))}."
        )

    # Verify it's actually a real image before trusting it at all.
    try:
        file_storage.stream.seek(0)
        with Image.open(file_storage.stream) as probe:
            probe.verify()
    except (UnidentifiedImageError, OSError):
        raise ValueError("The uploaded file is not a valid image.")

    # .verify() leaves the file object unusable for further reads, so
    # reopen it fresh for the actual resize/save.
    file_storage.stream.seek(0)
    image = Image.open(file_storage.stream)
    image = image.convert("RGB")  # normalize (drops alpha/CMYK weirdness) before saving as JPEG
    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

    extension = original_name.rsplit(".", 1)[1].lower()
    if extension not in ("jpg", "jpeg"):
        extension = "jpg"  # we re-encode everything as JPEG after convert("RGB")
    filename = f"{uuid.uuid4().hex}.{extension}"

    os.makedirs(upload_folder, exist_ok=True)
    image.save(os.path.join(upload_folder, filename), format="JPEG", quality=85)

    return filename


def delete_product_image(upload_folder, filename):
    """Best-effort delete of a previously-saved product image. Silently
    does nothing if the file is already gone — deleting a product
    whose image file was manually removed shouldn't raise an error."""
    if not filename:
        return
    path = os.path.join(upload_folder, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
