"""
STEP 2 — Generate synthetic hostel data.

Creates 6 CSVs in data/raw/:
  rooms.csv, bookings.csv, mess_attendance.csv, payments.csv, expenses.csv, students.csv

Patterns encoded (per the business case):
  - 300 beds across single / double / triple rooms
  - ~90% occupancy overall; triple ~95%, double ~85%, single ~90%
  - Mess attendance drops Fri evening through Mon lunch
  - Hostel fees billed once per semester; mess fees daily
  - ~12 months of booking history
  - Intentional data-quality issues: duplicate rows, missing values,
    inconsistent date formats (so the cleaning step is meaningful)

Run:  python scripts/generate_data.py   (from the hostel-dashboard folder)
"""

import os
import csv
import random
import datetime as dt
from datetime import date, timedelta
from collections import defaultdict
from faker import Faker

random.seed(42)
Faker.seed(42)
fake = Faker("en_IN")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
os.makedirs(RAW, exist_ok=True)

TODAY = date(2026, 11, 15)
START = TODAY - timedelta(days=365)          # ~12 months of booking history
MESS_START = TODAY - timedelta(days=120)     # daily mess for last ~4 months

MEAL_RATE = 40                               # ₹ per meal
SEMESTER_FEE = {"single": 40000, "double": 28000, "triple": 20000}
OCCUPANCY_RATE = {"single": 0.90, "double": 0.85, "triple": 0.95}

# weekday (Mon=0..Sun=6) -> weights for meals_availed = 0,1,2,3
MEAL_WEIGHTS = {
    0: [0.05, 0.10, 0.20, 0.65],   # Mon
    1: [0.02, 0.05, 0.10, 0.83],   # Tue
    2: [0.02, 0.05, 0.10, 0.83],   # Wed
    3: [0.02, 0.05, 0.10, 0.83],   # Thu
    4: [0.05, 0.15, 0.40, 0.40],   # Fri (dinner drops - students leave)
    5: [0.50, 0.25, 0.15, 0.10],   # Sat (most go home)
    6: [0.50, 0.25, 0.15, 0.10],   # Sun (most away / return Mon lunch)
}

TRIPLES_PER_BLOCK_GENDER = {
    ("A", "boys"): 4, ("A", "girls"): 3,
    ("B", "boys"): 4, ("B", "girls"): 3,
    ("C", "boys"): 3, ("C", "girls"): 3,
}

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")


def rand_date_str(d, mix=False):
    """Return a date as string. If mix, randomly use an inconsistent format."""
    if not mix:
        return d.strftime("%Y-%m-%d")
    r = random.random()
    if r < 0.33:
        return d.strftime("%d/%m/%Y")   # DD/MM/YYYY
    if r < 0.66:
        return d.strftime("%m/%d/%Y")   # MM/DD/YYYY
    return d.strftime("%Y-%m-%d")


def parse_date(s):
    """Parse a date string that may be in any of the 3 supported formats."""
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in DATE_FORMATS:
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def write_csv(filename, fields, rows):
    path = os.path.join(RAW, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"  wrote {filename}: {len(rows)} rows")


def build_rooms():
    rooms = []
    for block in ["A", "B", "C"]:
        for gender in ["boys", "girls"]:
            # single rooms: 10 per block-gender -> 60 rooms, 60 beds
            for i in range(10):
                rooms.append({
                    "room_number": f"{block}{gender[0]}{100+i}",
                    "room_type": "single", "total_beds": 1,
                    "block": block, "gender": gender,
                    "semester_fee": SEMESTER_FEE["single"],
                })
            # double rooms: 15 per block-gender -> 90 rooms, 180 beds
            for i in range(15):
                rooms.append({
                    "room_number": f"{block}{gender[0]}{200+i}",
                    "room_type": "double", "total_beds": 2,
                    "block": block, "gender": gender,
                    "semester_fee": SEMESTER_FEE["double"],
                })
            # triple rooms
            n = TRIPLES_PER_BLOCK_GENDER[(block, gender)]
            for i in range(n):
                rooms.append({
                    "room_number": f"{block}{gender[0]}{300+i}",
                    "room_type": "triple", "total_beds": 3,
                    "block": block, "gender": gender,
                    "semester_fee": SEMESTER_FEE["triple"],
                })
    return rooms


def build_bookings(rooms):
    bookings = []
    bid = 1
    sid = 1
    room_info = {r["room_number"]: r for r in rooms}
    total_beds_by_type = {"single": 0, "double": 0, "triple": 0}
    occupied_by_type = {"single": 0, "double": 0, "triple": 0}

    for room in rooms:
        rt = room["room_type"]
        total_beds_by_type[rt] += room["total_beds"]
        rate = OCCUPANCY_RATE[rt]

        # Each bed is occupied independently with probability = rate.
        # This yields per-type occupancy close to the target (~90/85/95%).
        for bed_idx in range(room["total_beds"]):
            if random.random() < rate:
                # bed currently occupied -> active booking, no checkout
                checkin = START + timedelta(days=random.randint(0, 365))
                checkout = None
                status = "active"
            else:
                # bed currently vacant; 30% chance it had a past completed booking
                if random.random() < 0.30:
                    checkin = START + timedelta(days=random.randint(0, 300))
                    checkout = checkin + timedelta(days=random.randint(5, 60))
                    if checkout > TODAY:
                        checkout = TODAY
                    status = "completed"
                else:
                    continue  # truly vacant, no booking record
            pay_status = random.choices(
                ["paid", "pending", "partial"], weights=[70, 20, 10])[0]

            bookings.append({
                "booking_id": f"BK{bid:04d}",
                "student_id": f"STU{sid:04d}",
                "student_name": fake.name(),
                "room_number": room["room_number"],
                "checkin_date": rand_date_str(checkin, mix=True),
                "checkout_date": rand_date_str(checkout, mix=True) if checkout else "",
                "booking_status": status,
                "fee_payment_status": pay_status,
                "_room_type": rt,      # helper, removed before writing
                "_gender": room["gender"],
            })
            occupied_by_type[rt] += 1
            bid += 1
            sid += 1

    # ---- intentional data quality issues ----
    # duplicate 3 whole rows (incl. duplicate booking_id -> PK conflict)
    for row in random.sample(bookings, 3):
        bookings.append(dict(row))
    # 5 bookings with missing student name
    for row in random.sample(bookings, 5):
        row["student_name"] = ""

    print("  occupancy by room type:")
    for rt in ["single", "double", "triple"]:
        tb = total_beds_by_type[rt]
        ob = occupied_by_type[rt]
        print(f"    {rt}: {ob}/{tb} beds = {ob/tb*100:.1f}%")

    # strip helper fields before returning
    for b in bookings:
        b.pop("_room_type", None)
        b.pop("_gender", None)
    return bookings, room_info


def build_students(bookings, room_info):
    seen = {}
    students = []
    for b in bookings:
        if b["student_id"] in seen:
            continue
        seen[b["student_id"]] = True
        room = room_info.get(b["room_number"], {})
        students.append({
            "student_id": b["student_id"],
            "student_name": b["student_name"] or f"Student {b['student_id']}",
            "gender": room.get("gender", random.choice(["boys", "girls"])),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "created_at": rand_date_str(START),
        })
    return students


def build_mess_attendance(bookings):
    rows = []
    aid = 1
    for b in bookings:
        if b["booking_status"] != "active":
            continue
        checkin = parse_date(b["checkin_date"])
        if checkin is None:
            continue
        start = max(checkin, MESS_START)
        d = start
        while d <= TODAY:
            weights = MEAL_WEIGHTS[d.weekday()]
            meals = random.choices([0, 1, 2, 3], weights=weights)[0]
            rows.append({
                "attendance_id": f"MS{aid:04d}",
                "student_id": b["student_id"],
                "date": rand_date_str(d, mix=True),
                "meals_availed": meals,
                "mess_charge": round(meals * MEAL_RATE, 2),
            })
            aid += 1
            d += timedelta(days=1)

    # duplicate a few attendance rows
    for row in random.sample(rows, 5):
        rows.append(dict(row))
    # blank a few meal values
    for row in random.sample(rows, 5):
        row["meals_availed"] = ""
        row["mess_charge"] = ""
    return rows


def build_payments(bookings, room_info, mess_by_student_month):
    rows = []
    pid = 1
    for b in bookings:
        checkin = parse_date(b["checkin_date"])
        if checkin is None:
            continue
        pay_date = checkin + timedelta(days=random.randint(0, 10))
        rt = room_info[b["room_number"]]["room_type"]
        status = random.choices(["paid", "pending", "partial"], weights=[75, 15, 10])[0]
        rows.append({
            "payment_id": f"PY{pid:04d}",
            "booking_id": b["booking_id"],
            "payment_date": rand_date_str(pay_date, mix=True),
            "amount": SEMESTER_FEE[rt],
            "payment_type": "hostel_fee",
            "status": status,
        })
        pid += 1

    # one mess_fee payment per student per month (last 4 months)
    for (student_id, month), total in mess_by_student_month.items():
        if total <= 0:
            continue
        pay_date = date(month.year, month.month, 28) + timedelta(days=random.randint(0, 2))
        status = random.choices(["paid", "pending"], weights=[80, 20])[0]
        rows.append({
            "payment_id": f"PY{pid:04d}",
            "booking_id": "",           # mess payments not tied to a single booking
            "payment_date": rand_date_str(pay_date, mix=True),
            "amount": round(total, 2),
            "payment_type": "mess_fee",
            "status": status,
        })
        pid += 1
    return rows


def build_expenses():
    rows = []
    eid = 1
    categories = ["electricity", "maintenance", "staff", "water", "other"]
    d = START
    while d <= TODAY:
        for _ in range(random.randint(1, 2)):   # 1-2 expenses per day on average
            rows.append({
                "expense_id": f"EX{eid:04d}",
                "date": rand_date_str(d, mix=True),
                "category": random.choice(categories),
                "amount": round(random.uniform(500, 50000), 2),
            })
            eid += 1
        d += timedelta(days=1)
    # a few expenses with missing amount
    for row in random.sample(rows, 3):
        row["amount"] = ""
    return rows


def main():
    rooms = build_rooms()
    write_csv("rooms.csv",
              ["room_number", "room_type", "total_beds", "block", "gender", "semester_fee"],
              rooms)

    bookings, room_info = build_bookings(rooms)
    write_csv("bookings.csv",
              ["booking_id", "student_id", "student_name", "room_number",
               "checkin_date", "checkout_date", "booking_status", "fee_payment_status"],
              bookings)

    students = build_students(bookings, room_info)
    write_csv("students.csv",
              ["student_id", "student_name", "gender", "email", "phone", "created_at"],
              students)

    active_bookings = [b for b in bookings if b["checkout_date"] == ""]
    mess = build_mess_attendance(active_bookings)
    write_csv("mess_attendance.csv",
              ["attendance_id", "student_id", "date", "meals_availed", "mess_charge"],
              mess)

    # mess totals per student per month (first of month as the month key)
    mess_by_month = defaultdict(float)
    for m in mess:
        if m["mess_charge"] == "":
            continue
        day = parse_date(m["date"])
        if day is None:
            continue
        mess_by_month[(m["student_id"], day.replace(day=1))] += float(m["mess_charge"])

    payments = build_payments(bookings, room_info, mess_by_month)
    write_csv("payments.csv",
              ["payment_id", "booking_id", "payment_date", "amount",
               "payment_type", "status"],
              payments)

    expenses = build_expenses()
    write_csv("expenses.csv",
              ["expense_id", "date", "category", "amount"],
              expenses)

    # ---- verification summary ----
    total_beds = sum(r["total_beds"] for r in rooms)
    occupied = sum(1 for b in bookings if b["booking_status"] == "active")
    print(f"\nVERIFICATION")
    print(f"  total beds        : {total_beds}")
    print(f"  active bookings   : {occupied}  ({occupied/total_beds*100:.1f}% occupancy)")
    print(f"  mess rows         : {len(mess)}")
    print(f"  expense rows      : {len(expenses)}")
    print(f"  payment rows      : {len(payments)}")
    print(f"\nSample row from each CSV:")
    for fname in ["rooms.csv", "bookings.csv", "mess_attendance.csv",
                  "payments.csv", "expenses.csv", "students.csv"]:
        with open(os.path.join(RAW, fname), encoding="utf-8") as f:
            first = next(csv.DictReader(f), None)
        print(f"  {fname}: {first}")


if __name__ == "__main__":
    main()
