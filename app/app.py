"""
app/app.py — Streamlit entry point.

Sets page config, draws the shared sidebar filters, and routes to the 5 pages
using st.navigation (the modern Streamlit multipage API).

Run:  streamlit run app/app.py   (from the hostel-dashboard folder)
"""

import streamlit as st
import os
import sqlite3

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

# Store filter values in session state so pages can read them
st.session_state["filter_month"] = month_selection
st.session_state["filter_room_type"] = room_type_selection
st.session_state["filter_block"] = block_selection
st.session_state["filter_gender"] = gender_selection
st.session_state["filter_occupancy"] = occupancy_selection

# ---------------------------------------------------------------------------
# Navigation — st.navigation is the standard Streamlit multipage API
# ---------------------------------------------------------------------------
pg = st.navigation({
    "Overview": [
        st.Page("app/pages/1_Overview.py", title="Overview", icon="📊"),
        st.Page("app/pages/2_Rooms.py", title="Rooms", icon="🏠"),
        st.Page("app/pages/3_Revenue.py", title="Revenue", icon="💰"),
        st.Page("app/pages/4_Weekday.py", title="Weekday", icon="📅"),
        st.Page("app/pages/5_Admin.py", title="Admin", icon="➕"),
    ]
})

pg.run()
