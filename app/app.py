"""
app/app.py — Streamlit entry point.

Sets page config, draws the shared sidebar filters, and routes to the 5 pages:
  1_Overview, 2_Rooms, 3_Revenue, 4_Weekday, 5_Admin

Run:  streamlit run app/app.py   (from the hostel-dashboard folder)
"""

import streamlit as st
import importlib.util
import os
import sys

# Ensure the project root is on sys.path so `from app import db` works
# when app.py is run as __main__ (otherwise app.py shadows the app package)
PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

PAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")

PAGE_FILES = {
    "1 — Overview": "1_Overview.py",
    "2 — Rooms": "2_Rooms.py",
    "3 — Revenue": "3_Revenue.py",
    "4 — Weekday Analysis": "4_Weekday.py",
    "5 — Admin": "5_Admin.py",
}


def load_page(filename):
    """Load a page module by file path (filenames start with numbers)."""
    path = os.path.join(PAGES_DIR, filename)
    spec = importlib.util.spec_from_file_location("page_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


st.set_page_config(
    page_title="Hostel Occupancy & Revenue Dashboard",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 Hostel Occupancy & Revenue Dashboard")
st.caption("Synthetic data for demonstration — no real student data is used.")

# ---------------------------------------------------------------------------
# Shared sidebar filters (affect every page)
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

# Month filter — multi-select of available months
import sqlite3
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "data", "hostel.db")
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
months = [r[0] for r in conn.execute(
    "SELECT DISTINCT strftime('%Y-%m', date) FROM daily_occupancy ORDER BY strftime('%Y-%m', date)"
)]
conn.close()

# Default: show the latest 3 months
default_months = months[-3:] if months else []

month_selection = st.sidebar.multiselect(
    "Month", options=months, default=default_months, key="sb_month"
)

room_type_selection = st.sidebar.multiselect(
    "Room type", options=["single", "double", "triple"],
    default=["single", "double", "triple"], key="sb_room_type"
)

block_selection = st.sidebar.multiselect(
    "Hostel block", options=["A", "B", "C"],
    default=["A", "B", "C"], key="sb_block"
)

gender_selection = st.sidebar.multiselect(
    "Gender", options=["boys", "girls"],
    default=["boys", "girls"], key="sb_gender"
)

occupancy_selection = st.sidebar.multiselect(
    "Occupancy status", options=["occupied", "vacant"],
    default=["occupied", "vacant"], key="sb_occupancy"
)

st.sidebar.divider()
st.sidebar.caption("Filters apply to all pages below.")

# ---------------------------------------------------------------------------
# Page router
# ---------------------------------------------------------------------------
PAGES = {}
for label, filename in PAGE_FILES.items():
    PAGES[label] = load_page(filename)

selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]

# Pass the filter values into session state so each page can read them
st.session_state["filter_month"] = month_selection
st.session_state["filter_room_type"] = room_type_selection
st.session_state["filter_block"] = block_selection
st.session_state["filter_gender"] = gender_selection
st.session_state["filter_occupancy"] = occupancy_selection

page.render()
