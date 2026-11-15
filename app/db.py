"""
app/db.py — shared database connection helpers.

Every function opens a read-only connection to data/hostel.db, runs a query,
returns a pandas DataFrame, and closes the connection. Keeping all SQL in one
place makes the app easier to read and maintain.
"""

import os
import sqlite3
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "data", "hostel.db")


def get_connection():
    """Open a read-only connection to the SQLite database."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    return conn


def query(sql, params=None):
    """Run a SQL query and return a pandas DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn, params=params or {})
    finally:
        conn.close()
    return df


# ---------------------------------------------------------------------------
# Helper queries used by the dashboard pages
# ---------------------------------------------------------------------------

def load_rooms():
    """All rooms with their capacity and block/gender."""
    return query("SELECT * FROM rooms ORDER BY room_number")


def load_bookings():
    """All bookings."""
    return query("SELECT * FROM bookings ORDER BY booking_id")


def load_mess_attendance():
    """All mess attendance records."""
    return query("SELECT * FROM mess_attendance ORDER BY date")


def load_payments():
    """All payments."""
    return query("SELECT * FROM payments ORDER BY payment_date")


def load_expenses():
    """All expenses."""
    return query("SELECT * FROM expenses ORDER BY date")


def load_daily_occupancy():
    """The full daily_occupancy table (one row per room per day)."""
    return query("SELECT * FROM daily_occupancy ORDER BY date, room_number")


def load_occupancy_by_date(selected_date):
    """
    Occupancy summary for a single date.
    Returns total beds, allocated beds, vacant beds, and occupancy rate %.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT SUM(total_beds), SUM(allocated_beds), SUM(vacant_beds)
            FROM daily_occupancy
            WHERE date = ?
        """, (selected_date,))
        row = cur.fetchone()
    finally:
        conn.close()
    if not row or row[0] is None:
        return 0, 0, 0, 0.0
    total, allocated, vacant = row
    rate = (allocated / total * 100) if total else 0.0
    return total, allocated, vacant, round(rate, 2)


def load_monthly_occupancy():
    """
    Monthly occupancy trend.
    Returns year-month, avg occupancy rate %, total beds, allocated beds.
    """
    return query("""
        SELECT
            strftime('%Y-%m', date) AS year_month,
            ROUND(AVG(occupancy_rate) * 100, 2) AS avg_occupancy_percent,
            SUM(total_beds) AS total_beds,
            SUM(allocated_beds) AS allocated_beds
        FROM daily_occupancy
        GROUP BY year_month
        ORDER BY year_month
    """)


def load_monthly_revenue():
    """
    Monthly revenue split into room rent vs mess fee.
    Returns year-month, room_rent_revenue, mess_fee_revenue.
    """
    return query("""
        SELECT
            strftime('%Y-%m', payment_date) AS year_month,
            ROUND(SUM(CASE WHEN payment_type = 'hostel_fee' THEN amount ELSE 0 END), 2) AS room_rent_revenue,
            ROUND(SUM(CASE WHEN payment_type = 'mess_fee' THEN amount ELSE 0 END), 2) AS mess_fee_revenue
        FROM payments
        WHERE status = 'paid'
        GROUP BY year_month
        ORDER BY year_month
    """)


def load_occupancy_by_room_type():
    """
    Current occupancy rate and revenue per student by room type.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        # latest occupancy per room type
        cur.execute("""
            SELECT r.room_type,
                   ROUND(SUM(d.allocated_beds) * 100.0 / SUM(d.total_beds), 2) AS occupancy_rate_percent,
                   SUM(d.allocated_beds) AS occupied_beds,
                   SUM(d.total_beds) AS total_beds
            FROM daily_occupancy d
            JOIN rooms r ON r.room_number = d.room_number
            WHERE d.date = (SELECT MAX(date) FROM daily_occupancy)
            GROUP BY r.room_type
        """)
        occ_rows = cur.fetchall()

        # revenue per occupied student per room type
        cur.execute("""
            SELECT r.room_type,
                   COUNT(DISTINCT b.student_id) AS n_students,
                   ROUND(SUM(p.amount), 2) AS room_revenue
            FROM bookings b
            JOIN rooms r ON r.room_number = b.room_number
            LEFT JOIN payments p ON p.booking_id = b.booking_id AND p.status = 'paid'
            WHERE b.booking_status = 'active' AND b.checkout_date IS NULL
            GROUP BY r.room_type
        """)
        rev_rows = cur.fetchall()
    finally:
        conn.close()

    occ_map = {row[0]: {"occupancy_rate_percent": row[1],
                        "occupied_beds": row[2], "total_beds": row[3]}
               for row in occ_rows}
    rev_map = {row[0]: {"n_students": row[1], "room_revenue": row[2] or 0}
               for row in rev_rows}

    result = []
    for rt in ["single", "double", "triple"]:
        o = occ_map.get(rt, {"occupancy_rate_percent": 0, "occupied_beds": 0, "total_beds": 0})
        v = rev_map.get(rt, {"n_students": 0, "room_revenue": 0})
        rps = round(v["room_revenue"] / v["n_students"], 2) if v["n_students"] else 0
        result.append({
            "room_type": rt,
            "occupancy_rate_percent": o["occupancy_rate_percent"],
            "occupied_beds": o["occupied_beds"],
            "total_beds": o["total_beds"],
            "n_students": v["n_students"],
            "room_revenue": v["room_revenue"],
            "revenue_per_student": rps,
        })
    return result


def load_room_availability():
    """
    Every room: total beds, occupied, vacant, occupancy rate % (latest date).
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.room_number, r.room_type, r.total_beds, r.block, r.gender,
                   COALESCE(d.allocated_beds, 0) AS allocated_beds,
                   COALESCE(d.vacant_beds, r.total_beds) AS vacant_beds,
                   COALESCE(ROUND(d.occupancy_rate * 100, 2), 0) AS occupancy_rate_percent
            FROM rooms r
            LEFT JOIN daily_occupancy d
              ON d.room_number = r.room_number
             AND d.date = (SELECT MAX(date) FROM daily_occupancy)
            ORDER BY r.room_number
        """)
        rows = cur.fetchall()
    finally:
        conn.close()
    return [dict(zip(
        ["room_number", "room_type", "total_beds", "block", "gender",
         "allocated_beds", "vacant_beds", "occupancy_rate_percent"], row))
            for row in rows]


def load_revenue_by_month():
    """Total paid revenue per month (all types combined)."""
    return query("""
        SELECT
            strftime('%Y-%m', payment_date) AS year_month,
            ROUND(SUM(amount), 2) AS total_revenue
        FROM payments
        WHERE status = 'paid'
        GROUP BY year_month
        ORDER BY year_month
    """)


def load_expenses_by_category():
    """Total expenses per category."""
    return query("""
        SELECT category, ROUND(SUM(amount), 2) AS total_amount
        FROM expenses
        GROUP BY category
        ORDER BY total_amount DESC
    """)


def load_mess_by_weekday():
    """
    Mess revenue grouped by weekday (Mon=0..Sun=6) for the latest month
    of mess data.
    """
    return query("""
        WITH max_date AS (
            SELECT MAX(date) AS max_d FROM mess_attendance
        ),
        recent AS (
            SELECT *
            FROM mess_attendance m, max_date
            WHERE date(m.date) >= date(max_d.max_d, '-1 month')
        )
        SELECT
            CAST(strftime('%w', date) AS INTEGER) AS weekday,
            CASE strftime('%w', date)
                WHEN '0' THEN 'Sun'
                WHEN '1' THEN 'Mon'
                WHEN '2' THEN 'Tue'
                WHEN '3' THEN 'Wed'
                WHEN '4' THEN 'Thu'
                WHEN '5' THEN 'Fri'
                WHEN '6' THEN 'Sat'
            END AS weekday_name,
            ROUND(SUM(mess_charge), 2) AS mess_revenue,
            SUM(meals_availed) AS total_meals
        FROM recent
        GROUP BY weekday
        ORDER BY weekday
    """)


def load_occupancy_by_weekday():
    """
    Average occupancy rate by weekday (Mon=0..Sun=6) across all dates.
    """
    return query("""
        SELECT
            CAST(strftime('%w', date) AS INTEGER) AS weekday,
            CASE strftime('%w', date)
                WHEN '0' THEN 'Sun'
                WHEN '1' THEN 'Mon'
                WHEN '2' THEN 'Tue'
                WHEN '3' THEN 'Wed'
                WHEN '4' THEN 'Thu'
                WHEN '5' THEN 'Fri'
                WHEN '6' THEN 'Sat'
            END AS weekday_name,
            ROUND(AVG(occupancy_rate) * 100, 2) AS avg_occupancy_percent
        FROM daily_occupancy
        GROUP BY weekday
        ORDER BY weekday
    """)


def kpi_snapshot():
    """
    Returns a dict of headline KPIs for the Overview page cards.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        # total students (active bookings)
        cur.execute("""
            SELECT COUNT(DISTINCT student_id)
            FROM bookings
            WHERE booking_status = 'active' AND checkout_date IS NULL
        """)
        total_students = cur.fetchone()[0] or 0

        # occupancy on latest date
        cur.execute("""
            SELECT SUM(allocated_beds), SUM(total_beds)
            FROM daily_occupancy
            WHERE date = (SELECT MAX(date) FROM daily_occupancy)
        """)
        row = cur.fetchone()
        occ_rate = round(row[0] * 100.0 / row[1], 1) if row and row[1] else 0.0

        # total revenue
        cur.execute("SELECT SUM(amount) FROM payments WHERE status = 'paid'")
        total_revenue = cur.fetchone()[0] or 0

        # room rent revenue
        cur.execute("""
            SELECT SUM(amount) FROM payments
            WHERE payment_type = 'hostel_fee' AND status = 'paid'
        """)
        room_rent = cur.fetchone()[0] or 0

        # mess fee revenue
        cur.execute("SELECT SUM(mess_charge) FROM mess_attendance")
        mess_revenue = cur.fetchone()[0] or 0

        # profit margin
        cur.execute("SELECT SUM(amount) FROM payments WHERE status = 'paid'")
        rev = cur.fetchone()[0] or 0
        cur.execute("SELECT SUM(amount) FROM expenses")
        exp = cur.fetchone()[0] or 0
        profit_margin = round((rev - exp) * 100.0 / rev, 1) if rev else 0.0
    finally:
        conn.close()

    return {
        "total_students": total_students,
        "occupancy_rate": occ_rate,
        "total_revenue": round(total_revenue, 2),
        "room_rent": round(room_rent, 2),
        "mess_revenue": round(mess_revenue, 2),
        "profit_margin": profit_margin,
    }


def add_booking(booking_id, student_id, student_name, room_number,
                checkin_date, checkout_date, booking_status, fee_payment_status):
    """Insert a new booking. Returns True on success."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO bookings
            (booking_id, student_id, student_name, room_number,
             checkin_date, checkout_date, booking_status, fee_payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (booking_id, student_id, student_name, room_number,
              checkin_date, checkout_date or None, booking_status, fee_payment_status))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def add_mess_attendance(attendance_id, student_id, date_str, meals_availed):
    """Insert a new mess attendance row. mess_charge = meals * 40. Returns True on success."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        mess_charge = round(meals_availed * 40, 2)
        cur.execute("""
            INSERT INTO mess_attendance
            (attendance_id, student_id, date, meals_availed, mess_charge)
            VALUES (?, ?, ?, ?, ?)
        """, (attendance_id, student_id, date_str, meals_availed, mess_charge))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
