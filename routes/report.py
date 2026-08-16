"""
routes/report.py
-------------------
Customer-facing counterfeit reporting: submitting a new report (with
an optional evidence photo) and viewing the customer's own report
history and its review status. Admin review of these reports lives in
routes/admin.py, since it's part of the same admin session/permission
model as the rest of the admin portal.
"""

import math

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app

from models.report import Report
from models.product import Product
from utils.decorators import login_required
from utils.rate_limit import limiter
from utils.validators import validate_report_form
from utils.image_upload import save_product_image

report_bp = Blueprint("report", __name__)

PER_PAGE = 10


@report_bp.route("/report", methods=["GET", "POST"])
@login_required
@limiter.limit("15 per hour", methods=["POST"])
def submit_report():
    if request.method == "POST":
        barcode_value = request.form.get("barcode_value", "").strip()
        description = request.form.get("description", "").strip()

        errors = validate_report_form(barcode_value, description)

        evidence_filename = None
        if not errors:
            try:
                evidence_filename = save_product_image(
                    request.files.get("evidence_image"),
                    current_app.config["UPLOAD_FOLDER"],
                    current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
                )
            except ValueError as exc:
                errors.append(str(exc))

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("report_form.html", barcode_value=barcode_value, description=description)

        # A report can reference a product that DID match in the
        # catalog — the customer might believe the physical item in
        # their hand is fake even though its barcode is registered.
        product = Product.find_by_barcode(barcode_value)

        Report.create(
            user_id=session["user_id"],
            product_id=product["id"] if product else None,
            barcode_value=barcode_value,
            description=description,
            evidence_image=evidence_filename,
        )

        flash("Thanks — your report has been submitted and will be reviewed by our team.", "success")
        return redirect(url_for("report.report_history"))

    barcode_value = request.args.get("barcode", "").strip()
    return render_template("report_form.html", barcode_value=barcode_value, description="")


@report_bp.route("/report/history")
@login_required
def report_history():
    page = max(1, request.args.get("page", 1, type=int))

    reports = Report.get_by_user(session["user_id"], page=page, per_page=PER_PAGE)
    total = Report.count_by_user(session["user_id"])
    total_pages = max(1, math.ceil(total / PER_PAGE))

    return render_template(
        "report_history.html", reports=reports, page=page, total_pages=total_pages, total=total
    )
