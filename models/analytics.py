"""
models/analytics.py
----------------------
Aggregate queries for the admin analytics dashboard (Module 8).
Kept separate from the individual Scan/Report/Product models since
these queries cut across tables and exist purely to feed charts —
they're not really "data access for the scans table" in the same
sense as, say, Scan.create().
"""

from datetime import date, timedelta

from utils.db import get_cursor


class Analytics:

    @staticmethod
    def scans_per_day(days=14):
        """
        Daily scan counts for the last `days` days, including days
        with zero scans (so the line chart doesn't silently skip
        gaps). Returns two parallel lists: labels (date strings) and
        counts (ints), in chronological order — exactly the shape
        Chart.js wants.
        """
        cursor = get_cursor()
        start_date = date.today() - timedelta(days=days - 1)
        cursor.execute(
            """SELECT DATE(scanned_at) AS day, COUNT(*) AS total
               FROM scans
               WHERE scanned_at >= %s
               GROUP BY DATE(scanned_at)""",
            (start_date,),
        )
        counts_by_day = {row["day"]: row["total"] for row in cursor.fetchall()}

        labels, counts = [], []
        for i in range(days):
            day = start_date + timedelta(days=i)
            labels.append(day.strftime("%d %b"))
            counts.append(counts_by_day.get(day, 0))

        return labels, counts

    @staticmethod
    def scan_result_breakdown():
        """Genuine vs not-found counts across all scans, ever."""
        cursor = get_cursor()
        cursor.execute(
            """SELECT result_status, COUNT(*) AS total
               FROM scans
               GROUP BY result_status"""
        )
        rows = {row["result_status"]: row["total"] for row in cursor.fetchall()}
        return {
            "genuine": rows.get("genuine", 0),
            "not_found": rows.get("not_found", 0),
        }

    @staticmethod
    def reports_by_status():
        """Report counts broken down by review status."""
        cursor = get_cursor()
        cursor.execute(
            """SELECT status, COUNT(*) AS total
               FROM reports
               GROUP BY status"""
        )
        rows = {row["status"]: row["total"] for row in cursor.fetchall()}
        return {
            "pending": rows.get("pending", 0),
            "reviewed": rows.get("reviewed", 0),
            "resolved": rows.get("resolved", 0),
            "rejected": rows.get("rejected", 0),
        }

    @staticmethod
    def top_scanned_products(limit=5):
        """
        The most-scanned products, by number of genuine-match scans
        logged against them. Products that exist but have never been
        scanned simply don't appear — an empty catalog or a
        brand-new product isn't a bug, just nothing to chart yet.
        """
        cursor = get_cursor()
        cursor.execute(
            """SELECT products.name, products.brand, COUNT(*) AS scan_count
               FROM scans
               JOIN products ON scans.product_id = products.id
               GROUP BY products.id, products.name, products.brand
               ORDER BY scan_count DESC
               LIMIT %s""",
            (limit,),
        )
        rows = cursor.fetchall()
        labels = [f"{row['name']} ({row['brand']})" for row in rows]
        counts = [row["scan_count"] for row in rows]
        return labels, counts

    @staticmethod
    def summary_counts():
        """Small headline numbers shown above the charts."""
        cursor = get_cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM scans")
        total_scans = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM scans WHERE DATE(scanned_at) = CURDATE()")
        scans_today = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM reports WHERE status = 'pending'")
        pending_reports = cursor.fetchone()["total"]
        cursor.execute("SELECT COUNT(*) AS total FROM products WHERE status = 'active'")
        active_products = cursor.fetchone()["total"]
        return {
            "total_scans": total_scans,
            "scans_today": scans_today,
            "pending_reports": pending_reports,
            "active_products": active_products,
        }
