# CounterGuard production image.
#
# Docker is used (rather than a platform's native "just run pip install"
# buildpack) mainly for consistency: it runs identically on Render,
# Railway, Fly.io, or any other container host, with no surprises from
# a platform's own Python version or build detection.

FROM python:3.11-slim

WORKDIR /app

# opencv-python-headless is used specifically because it does NOT need
# libGL/libSM/etc — that's the whole point of the "headless" build, so
# no apt-get system packages are needed for barcode decoding (zxing-cpp
# ships as a self-contained compiled wheel, unlike the pyzbar approach
# this project used earlier, which needed the libzbar0 system library).

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Upload/barcode folders must exist even on a from-scratch container.
RUN mkdir -p static/uploads static/barcodes

ENV FLASK_ENV=production
EXPOSE 5000

# gunicorn, not the Flask dev server — Flask's own server prints a
# warning that it isn't meant for production, and gunicorn handles
# multiple concurrent requests properly. "app:create_app()" calls the
# application factory to get the actual Flask instance.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:create_app()"]
