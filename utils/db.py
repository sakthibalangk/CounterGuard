"""
utils/db.py
-----------
Small helper layer around mysql-connector-python.

Design choice: rather than opening a fresh connection in every model
method, we open ONE connection per incoming request and stash it on
Flask's request-scoped `g` object. `close_db` (registered as a
teardown handler in app.py) closes it automatically at the end of the
request, so no route or model ever has to remember to close a cursor
or connection manually.
"""

import mysql.connector
from mysql.connector import Error
from flask import g, current_app


def get_db():
    """
    Return a live MySQL connection for the current request, creating
    one on first use and reusing it for the rest of the request.
    """
    if "db" not in g:
        connect_kwargs = dict(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            autocommit=False,
        )

        # Managed MySQL hosts (Aiven, PlanetScale-style providers, etc.)
        # generally require TLS and give you a CA certificate to verify
        # against. DB_SSL_CA is None for local development, so this is a
        # no-op unless it's configured for a deployed environment.
        ssl_ca = current_app.config.get("DB_SSL_CA")
        if ssl_ca:
            connect_kwargs["ssl_ca"] = ssl_ca
            connect_kwargs["ssl_verify_cert"] = True

        try:
            g.db = mysql.connector.connect(**connect_kwargs)
        except Error as exc:
            # Surface a clear error rather than a raw traceback — this is
            # almost always a wrong password/host or MySQL not running.
            raise RuntimeError(f"Could not connect to MySQL: {exc}") from exc
    return g.db


def close_db(exception=None):
    """Close the request-scoped connection, if one was opened."""
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def get_cursor(dictionary=True):
    """
    Convenience helper: returns a cursor on the current request's
    connection. dictionary=True makes rows come back as {column: value}
    dicts instead of plain tuples, which is far easier to use in
    templates and JSON responses.
    """
    return get_db().cursor(dictionary=dictionary)
