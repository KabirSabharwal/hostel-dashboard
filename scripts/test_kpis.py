"""
Quick verification: run each KPI query from queries/kpis.sql against data/hostel.db
and print the results.
"""
import sqlite3
import re

conn = sqlite3.connect("data/hostel.db")
cur = conn.cursor()

sql = open("queries/kpis.sql", encoding="utf-8").read()

# Split into blocks by "-- KPI: " markers
blocks = re.split(r"-- KPI: ", sql)[1:]  # skip preamble before first marker

for block in blocks:
    lines = block.strip().split("\n", 1)
    label = lines[0].strip()
    query_block = lines[1] if len(lines) > 1 else ""

    # Find the actual SQL statement start (WITH takes priority over SELECT
    # because CTE queries start with WITH)
    start = query_block.find("WITH")
    if start == -1:
        start = query_block.find("SELECT")
    if start == -1:
        print(f"--- {label}: (no SQL found, skipping)\n")
        continue

    stmt = query_block[start:]
    # Trim at comment separators
    for marker in ["-- ==", "-- END", "-- KPI:"]:
        idx = stmt.find(marker)
        if idx != -1:
            stmt = stmt[:idx]
    stmt = stmt.strip().rstrip(";") + ";"

    try:
        cur.execute(stmt)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        print(f"--- {label}")
        print(f"    columns: {cols}")
        for row in rows:
            print(f"    {row}")
        print()
    except Exception as e:
        print(f"--- {label}: ERROR -> {e}\n")

conn.close()
