"""
STEP 3 — Clean the raw synthetic data.

Reads the 6 CSVs from data/raw/, fixes the intentional data-quality issues,
and writes cleaned CSVs to data/processed/.

Cleaning rules:
  1. Remove duplicate rows.
  2. Parse mixed date formats (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY) into
     a single ISO format (YYYY-MM-DD).
  3. Fill missing values:
     - student_name   -> "Unknown Student"
     - meals_availd   -> 0
     - mess_charge    -> 0
     - amount         -> 0 (expenses)
     - checkout_date  -> blank (means "still active")
  4. Validate IDs: drop rows whose booking_id/room_number references don't exist.
  5. Coerce numeric columns to proper types.

Prints a before-vs-after row count report.

Run:  python scripts/clean_data.py   (from the hostel-dashboard folder)
"""

import os
import csv
import datetime as dt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
PROCESSED = os.path.join(BASE, "data", "processed")
os.makedirs(PROCESSED, exist_ok=True)

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")


def parse_date(s):
    """Parse a date string that may be in any of the 3 supported formats."""
    if s is None or str(s).strip() == "":
        return None
    s = str(s).strip()
    for fmt in DATE_FORMATS:
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def to_iso(d):
    """Return a date as YYYY-MM-DD string, or '' if None."""
    return d.strftime("%Y-%m-%d") if d else ""


def read_csv(filename):
    path = os.path.join(RAW, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(filename, fields, rows):
    path = os.path.join(PROCESSED, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"  wrote {filename}: {len(rows)} rows")


def dedupe(rows, key_fields):
    """Remove duplicate rows based on key_fields. Keeps first occurrence."""
    seen = set()
    out = []
    dupes = 0
    for row in rows:
        key = tuple(row[k] for k in key_fields if k in row)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        out.append(row)
    if dupes:
        print(f"    removed {dupes} duplicate row(s)")
    return out


def clean_rooms(rows):
    before = len(rows)
    seen = set()
    out = []
    for r in rows:
        key = r["room_number"]
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    print(f"  rooms: {before} -> {len(out)} rows")
    return out


def clean_bookings(rows):
    before = len(rows)
    out = []
    for r in rows:
        if not r.get("booking_id") or not r.get("room_number"):
            continue
        r["checkin_date"] = to_iso(parse_date(r["checkin_date"]))
        r["checkout_date"] = to_iso(parse_date(r["checkout_date"]))
        if not r.get("student_name") or r["student_name"].strip() == "":
            r["student_name"] = "Unknown Student"
        out.append(r)
    out = dedupe(out, ["booking_id"])
    print(f"  bookings: {before} -> {len(out)} rows")
    return out


def clean_students(rows):
    before = len(rows)
    out = []
    for r in rows:
        if not r.get("student_id"):
            continue
        if not r.get("student_name") or r["student_name"].strip() == "":
            r["student_name"] = "Unknown Student"
        out.append(r)
    out = dedupe(out, ["student_id"])
    print(f"  students: {before} -> {len(out)} rows")
    return out


def clean_mess_attendance(rows, valid_students):
    before = len(rows)
    out = []
    for r in rows:
        if r["student_id"] not in valid_students:
            continue
        r["date"] = to_iso(parse_date(r["date"]))
        try:
            r["meals_availed"] = int(r["meals_availed"]) if r.get("meals_availed", "").strip() != "" else 0
        except (ValueError, TypeError):
            r["meals_availed"] = 0
        try:
            r["mess_charge"] = float(r["mess_charge"]) if r.get("mess_charge", "").strip() != "" else 0.0
        except (ValueError, TypeError):
            r["mess_charge"] = 0.0
        out.append(r)
    out = dedupe(out, ["attendance_id"])
    print(f"  mess_attendance: {before} -> {len(out)} rows")
    return out


def clean_payments(rows, valid_bookings):
    before = len(rows)
    out = []
    for r in rows:
        r["payment_date"] = to_iso(parse_date(r["payment_date"]))
        if not r.get("amount") or str(r["amount"]).strip() == "":
            r["amount"] = "0"
        try:
            r["amount"] = float(r["amount"])
        except (ValueError, TypeError):
            r["amount"] = 0.0
        # drop payment rows that reference a booking that no longer exists
        if r.get("booking_id") and r["booking_id"] not in valid_bookings:
            continue
        out.append(r)
    out = dedupe(out, ["payment_id"])
    print(f"  payments: {before} -> {len(out)} rows")
    return out


def clean_expenses(rows):
    before = len(rows)
    out = []
    for r in rows:
        r["date"] = to_iso(parse_date(r["date"]))
        if not r.get("amount") or str(r["amount"]).strip() == "":
            r["amount"] = "0"
        try:
            r["amount"] = float(r["amount"])
        except (ValueError, TypeError):
            r["amount"] = 0.0
        out.append(r)
    out = dedupe(out, ["expense_id"])
    print(f"  expenses: {before} -> {len(out)} rows")
    return out


def main():
    print("CLEANING RAW DATA (data/raw/ -> data/processed/)\n")

    rooms = read_csv("rooms.csv")
    bookings = read_csv("bookings.csv")
    students = read_csv("students.csv")
    mess = read_csv("mess_attendance.csv")
    payments = read_csv("payments.csv")
    expenses = read_csv("expenses.csv")

    rooms = clean_rooms(rooms)
    bookings = clean_bookings(bookings)
    students = clean_students(students)

    valid_students = {s["student_id"] for s in students}
    valid_bookings = {b["booking_id"] for b in bookings}

    mess = clean_mess_attendance(mess, valid_students)
    payments = clean_payments(payments, valid_bookings)
    expenses = clean_expenses(expenses)

    # write cleaned CSVs
    write_csv("rooms.csv",
              ["room_number", "room_type", "total_beds", "block", "gender", "semester_fee"],
              rooms)
    write_csv("bookings.csv",
              ["booking_id", "student_id", "student_name", "room_number",
               "checkin_date", "checkout_date", "booking_status", "fee_payment_status"],
              bookings)
    write_csv("students.csv",
              ["student_id", "student_name", "gender", "email", "phone", "created_at"],
              students)
    write_csv("mess_attendance.csv",
              ["attendance_id", "student_id", "date", "meals_availed", "mess_charge"],
              mess)
    write_csv("payments.csv",
              ["payment_id", "booking_id", "payment_date", "amount",
               "payment_type", "status"],
              payments)
    write_csv("expenses.csv",
              ["expense_id", "date", "category", "amount"],
              expenses)

    print("\nDONE. Cleaned CSVs are in data/processed/")


if __name__ == "__main__":
    main()
