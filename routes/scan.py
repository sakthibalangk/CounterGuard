"""
routes/scan.py
-----------------
Customer-facing barcode verification: the scan page (webcam, photo
upload, or manual entry), the verify endpoint that decodes the
barcode, looks it up against the product catalog, logs the attempt,
and shows the result — plus the scan history page (Module 5) that
lists everything a customer has scanned before. Every route here
requires a customer session — this is deliberately not reachable from
the admin portal at all.
"""

import base64
import binascii
import math

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models.product import Product
from models.scan import Scan
from utils.decorators import login_required
from utils.barcode_reader import decode_barcode_from_image_bytes

scan_bp = Blueprint("scan", __name__)

PER_PAGE = 10


@scan_bp.route("/scan")
@login_required
def scan_page():
    return render_template("scan.html")


@scan_bp.route("/scan/verify", methods=["POST"])
@login_required
def verify_barcode():
    """
    Accepts a barcode value from exactly one of three sources, checked
    in this priority order:
      1. manual_barcode   — typed directly into the form
      2. captured_image   — a base64 data URL from the webcam capture
      3. barcode_image    — an uploaded photo file
    Whichever produced a value gets looked up; the attempt (match or
    not) is always logged to the scans table.
    """
    barcode_value = None

    manual_value = request.form.get("manual_barcode", "").strip()
    captured_data_url = request.form.get("captured_image", "").strip()
    uploaded_file = request.files.get("barcode_image")

    if manual_value:
        if len(manual_value) > 64:
            flash("That barcode is too long — please check what you entered.", "error")
            return redirect(url_for("scan.scan_page"))
        barcode_value = manual_value

    elif captured_data_url:
        try:
            _, encoded = captured_data_url.split(",", 1)
            image_bytes = base64.b64decode(encoded)
        except (ValueError, binascii.Error):
            flash("The captured image was corrupted. Please try again.", "error")
            return redirect(url_for("scan.scan_page"))

        barcode_value = decode_barcode_from_image_bytes(image_bytes)
        if not barcode_value:
            flash(
                "No barcode could be detected in that frame. Hold the barcode "
                "steady, fill the frame, and make sure it's well lit — or try "
                "typing it in manually instead.",
                "error",
            )
            return redirect(url_for("scan.scan_page"))

    elif uploaded_file and uploaded_file.filename:
        image_bytes = uploaded_file.read()
        barcode_value = decode_barcode_from_image_bytes(image_bytes)
        if not barcode_value:
            flash(
                "No barcode could be detected in that photo. Try a clearer, "
                "closer photo — or type the barcode in manually instead.",
                "error",
            )
            return redirect(url_for("scan.scan_page"))

    else:
        flash("Please scan, upload a photo, or type in a barcode to verify.", "error")
        return redirect(url_for("scan.scan_page"))

    product = Product.find_by_barcode(barcode_value)
    result_status = "genuine" if product else "not_found"

    Scan.create(
        user_id=session["user_id"],
        product_id=product["id"] if product else None,
        barcode_value=barcode_value,
        result_status=result_status,
        ip_address=request.remote_addr,
    )

    return render_template(
        "result.html", product=product, barcode_value=barcode_value, result_status=result_status
    )


@scan_bp.route("/scan/history")
@login_required
def scan_history():
    status_filter = request.args.get("status", "").strip()
    if status_filter not in ("genuine", "not_found"):
        status_filter = None

    page = max(1, request.args.get("page", 1, type=int))

    scans = Scan.get_by_user(session["user_id"], result_status=status_filter, page=page, per_page=PER_PAGE)
    total = Scan.count_by_user(session["user_id"], result_status=status_filter)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    return render_template(
        "scan_history.html",
        scans=scans,
        status_filter=status_filter,
        page=page,
        total_pages=total_pages,
        total=total,
    )
