"""
routes/product.py
--------------------
Admin-only product management. Every route here requires an admin
session (@admin_required) — there is no customer-facing route in this
file. Customers reach product data indirectly, through the barcode
scan/verify flow built in Module 4, which reads from the same
Product model but never lets a customer create, edit, or delete a
row.
"""

import math
import os

from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, current_app
)

from models.product import Product
from utils.decorators import admin_required
from utils.validators import validate_product_form
from utils.image_upload import save_product_image, delete_product_image
from utils.barcode_generator import generate_unique_barcode_value, generate_barcode_image

product_bp = Blueprint("product", __name__)

PER_PAGE = 10


@product_bp.route("/")
@admin_required
def list_products():
    search = request.args.get("q", "").strip()
    page = max(1, request.args.get("page", 1, type=int))

    products = Product.get_all(search=search or None, page=page, per_page=PER_PAGE)
    total = Product.count(search=search or None)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    return render_template(
        "view_products.html",
        products=products,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@product_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_product():
    if request.method == "POST":
        form = request.form
        name = form.get("name", "").strip()
        brand = form.get("brand", "").strip()
        category = form.get("category", "").strip() or None
        description = form.get("description", "").strip() or None
        manufacturer = form.get("manufacturer", "").strip() or None
        price = form.get("price", "").strip() or None
        manufacture_date = form.get("manufacture_date", "").strip() or None
        expiry_date = form.get("expiry_date", "").strip() or None

        errors = validate_product_form(name, brand, price, manufacture_date, expiry_date)

        product_image_filename = None
        if not errors:
            try:
                product_image_filename = save_product_image(
                    request.files.get("product_image"),
                    current_app.config["UPLOAD_FOLDER"],
                    current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
                )
            except ValueError as exc:
                errors.append(str(exc))

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_product.html", form_data=form)

        # Barcode assignment: auto-generate a unique value and render
        # it as an actual scannable image — this is what Module 4's
        # scanner will read back.
        barcode_value = generate_unique_barcode_value()
        barcode_image_filename = generate_barcode_image(
            barcode_value, current_app.config["BARCODE_FOLDER"]
        )

        Product.create(
            name=name,
            brand=brand,
            category=category,
            description=description,
            manufacturer=manufacturer,
            barcode_value=barcode_value,
            barcode_image_path=barcode_image_filename,
            product_image_path=product_image_filename,
            price=price,
            manufacture_date=manufacture_date,
            expiry_date=expiry_date,
            created_by=session["admin_id"],
        )

        flash(f"Product '{name}' created with barcode {barcode_value}.", "success")
        return redirect(url_for("product.list_products"))

    return render_template("add_product.html", form_data={})


@product_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = Product.find_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("product.list_products"))

    if request.method == "POST":
        form = request.form
        name = form.get("name", "").strip()
        brand = form.get("brand", "").strip()
        category = form.get("category", "").strip() or None
        description = form.get("description", "").strip() or None
        manufacturer = form.get("manufacturer", "").strip() or None
        price = form.get("price", "").strip() or None
        manufacture_date = form.get("manufacture_date", "").strip() or None
        expiry_date = form.get("expiry_date", "").strip() or None
        status = form.get("status", "active")

        errors = validate_product_form(name, brand, price, manufacture_date, expiry_date)

        new_image_filename = None
        if not errors and request.files.get("product_image") and request.files["product_image"].filename:
            try:
                new_image_filename = save_product_image(
                    request.files.get("product_image"),
                    current_app.config["UPLOAD_FOLDER"],
                    current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
                )
            except ValueError as exc:
                errors.append(str(exc))

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("edit_product.html", product=product, form_data=form)

        Product.update(
            product_id=product_id,
            name=name,
            brand=brand,
            category=category,
            description=description,
            manufacturer=manufacturer,
            price=price,
            manufacture_date=manufacture_date,
            expiry_date=expiry_date,
            status=status,
            product_image_path=new_image_filename,  # None = keep existing image
        )

        # Only remove the old image file after the update succeeds,
        # and only if a new one actually replaced it.
        if new_image_filename:
            delete_product_image(current_app.config["UPLOAD_FOLDER"], product["product_image_path"])

        flash(f"Product '{name}' updated.", "success")
        return redirect(url_for("product.list_products"))

    return render_template("edit_product.html", product=product, form_data=product)


@product_bp.route("/delete/<int:product_id>", methods=["POST"])
@admin_required
def delete_product(product_id):
    product = Product.find_by_id(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("product.list_products"))

    Product.delete(product_id)

    # Clean up the files on disk now that no row references them.
    delete_product_image(current_app.config["UPLOAD_FOLDER"], product["product_image_path"])
    delete_product_image(current_app.config["BARCODE_FOLDER"], product["barcode_image_path"])

    flash(f"Product '{product['name']}' deleted.", "success")
    return redirect(url_for("product.list_products"))
