"""
STEP 4 — Build the SQLite database from the cleaned CSVs.

Reads the cleaned CSVs from data/processed/, creates all tables per the
schema in section 5, loads the data, derives the daily_occupancy table by
expanding each booking across its date range, creates indexes, and verifies
the result.

Database: data/hostel.db  (a single file — zero server setup)

Tables created:
  rooms, bookings, daily_occupancy, mess_attendance, payments, expenses

Run:  python scripts/build_database.py   (from the hostel-dashboard folder)
"""

import os
import csv
import sqlite3
import datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE, "data", "processed")
DB_PATH = os.path.join(BASE, "data", "hostel.db")
TODAY = dt.date(2026, 11, 15)

# Remove any existing DB so we start fresh
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ---------------------------------------------------------------------------
# 1. Create tables per the schema (section 5)
# ---------------------------------------------------------------------------
cur.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE rooms (
    room_number    TEXT PRIMARY KEY,
    room_type      TEXT,
    total_beds     INTEGER,
    block          TEXT,
    gender         TEXT,
    semester_fee   REAL
);

CREATE TABLE bookings (
    booking_id          TEXT PRIMARY KEY,
    student_id          TEXT,
    student_name        TEXT,
    room_number         TEXT REFERENCES rooms(room_number),
    checkin_date        DATE,
    checkout_date       DATE,
    booking_status      TEXT,
    fee_payment_status  TEXT
);

CREATE TABLE daily_occupancy (
    date           DATE,
    room_number    TEXT,
    total_beds     INTEGER,
    allocated_beds INTEGER,
    vacant_beds    INTEGER,
    occupancy_rate REAL
);

CREATE TABLE mess_attendance (
    attendance_id  TEXT PRIMARY KEY,
    student_id     TEXT,
    date           DATE,
    meals_availed  INTEGER,
    mess_charge    REAL
);

CREATE TABLE payments (
    payment_id     TEXT PRIMARY KEY,
    booking_id     TEXT REFERENCES bookings(booking_id),
    payment_date   DATE,
    amount         REAL,
    payment_type   TEXT,
    status         TEXT
);

CREATE TABLE expenses (
    expense_id  TEXT PRIMARY KEY,
    date        DATE,
    category    TEXT,
    amount      REAL
);
""")

# ---------------------------------------------------------------------------
# 2. Load cleaned CSVs into their tables
# ---------------------------------------------------------------------------
def load_csv(table, filename, fields):
    path = os.path.join(PROCESSED, filename)
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            # Convert empty strings to SQL NULL (needed for foreign-key
            # columns like payments.booking_id when a payment isn't tied
            # to a single booking).
            rows.append(tuple((r.get(f, "") or None) for f in fields))
    placeholders = ",".join("?" for _ in fields)
    cur.executemany(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({placeholders})", rows)
    print(f"  loaded {table}: {len(rows)} rows")
    return len(rows)


load_csv("rooms", "rooms.csv",
         ["room_number", "room_type", "total_beds", "block", "gender", "semester_fee"])
load_csv("bookings", "bookings.csv",
         ["booking_id", "student_id", "student_name", "room_number",
          "checkin_date", "checkout_date", "booking_status", "fee_payment_status"])
load_csv("mess_attendance", "mess_attendance.csv",
         ["attendance_id", "student_id", "date", "meals_availed", "mess_charge"])
load_csv("payments", "payments.csv",
         ["payment_id", "booking_id", "payment_date", "amount",
          "payment_type", "status"])
load_csv("expenses", "expenses.csv",
         ["expense_id", "date", "category", "amount"])

conn.commit()

# ---------------------------------------------------------------------------
# 3. Derive daily_occupancy
#
# How it works (the trickiest step, explained):
#   For every room and every day from the history start to today, we start
#   with 0 allocated beds. Then for each booking, we walk each day from its
#   checkin_date to its checkout_date (or today if it's still active) and
#   add 1 to allocated_beds for that room on that day — because that bed is
#   occupied on each of those days.
#   vacant_beds   = total_beds - allocated_beds
#   occupancy_rate= allocated_beds / total_beds   (0.0 to 1.0)
# ---------------------------------------------------------------------------
# History start = earliest checkin among bookings
cur.execute("SELECT MIN(checkin_date) FROM bookings")
start_row = cur.fetchone()[0]
HISTORY_START = dt.date.fromisoformat(start_row) if start_row else TODAY - dt.timedelta(days=365)

# Build a map: room_number -> total_beds
cur.execute("SELECT room_number, total_beds FROM rooms")
room_beds = {r[0]: r[1] for r in cur.fetchall()}

# Build allocation counts: (date, room_number) -> allocated_beds
allocations = {}
cur.execute("""
    SELECT room_number, checkin_date,
           COALESCE(checkout_date, ?) AS end_date
    FROM bookings
    WHERE booking_status = 'active'
""", (TODAY.isoformat(),))
for room_number, checkin_str, end_str in cur.fetchall():
    checkin = dt.date.fromisoformat(checkin_str)
    end = dt.date.fromisoformat(end_str) if end_str else TODAY
    d = checkin
    while d <= end:
        key = (d.isoformat(), room_number)
        allocations[key] = allocations.get(key, 0) + 1
        d += dt.timedelta(days=1)

# Now write one row per room per day
occupancy_rows = []
d = HISTORY_START
while d <= TODAY:
    day_iso = d.isoformat()
    for room_number, total_beds in room_beds.items():
        allocated = allocations.get((day_iso, room_number), 0)
        # Cap allocated at total_beds (defensive, shouldn't happen)
        if allocated > total_beds:
            allocated = total_beds
        vacant = total_beds - allocated
        rate = allocated / total_beds if total_beds else 0.0
        occupancy_rows.append((day_iso, room_number, total_beds, allocated, vacant, round(rate, 4)))
    d += dt.timedelta(days=1)

cur.executemany("""
    INSERT INTO daily_occupancy (date, room_number, total_beds, allocated_beds, vacant_beds, occupancy_rate)
    VALUES (?, ?, ?, ?, ?, ?)
""", occupancy_rows)
conn.commit()
print(f"  derived daily_occupancy: {len(occupancy_rows)} rows "
      f"({HISTORY_START} to {TODAY})")

# ---------------------------------------------------------------------------
# 4. Create indexes
# ---------------------------------------------------------------------------
cur.executescript("""
CREATE INDEX idx_daily_occupancy_date       ON daily_occupancy(date);
CREATE INDEX idx_daily_occupancy_room       ON daily_occupancy(room_number);
CREATE INDEX idx_bookings_room              ON bookings(room_number);
CREATE INDEX idx_mess_attendance_date       ON mess_attendance(date);
CREATE INDEX idx_mess_attendance_student    ON mess_attendance(student_id);
""")
conn.commit()
print("  created indexes")

# ---------------------------------------------------------------------------
# 5. Verification
# ---------------------------------------------------------------------------
print("\nVERIFICATION")
tables = ["rooms", "bookings", "daily_occupancy", "mess_attendance", "payments", "expenses"]
counts = {}
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    counts[t] = cur.fetchone()[0]
    print(f"  {t}: {counts[t]} rows")

# Occupancy on today's date
cur.execute("""
    SELECT SUM(allocated_beds), SUM(total_beds)
    FROM daily_occupancy
    WHERE date = ?
""", (TODAY.isoformat(),))
alloc, total = cur.fetchone()
occ = alloc / total * 100 if total else 0
print(f"\n  occupancy on {TODAY}: {alloc}/{total} beds = {occ:.1f}%")

if not (85 <= occ <= 95):
    print(f"  WARNING: occupancy {occ:.1f}% is outside the 85-95% target range")
else:
    print(f"  OK: occupancy ~90% on today's date")

conn.close()
print(f"\nDatabase created at {DB_PATH}")
