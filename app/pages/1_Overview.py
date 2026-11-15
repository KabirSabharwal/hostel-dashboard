"""
app/pages/1_Overview.py — Overview page.

KPI cards at the top, then monthly occupancy and revenue trend charts.
All sidebar filters (month, room type, block, gender, occupancy status)
are applied to the data shown.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app import db
from app import charts


def apply_filters(df, date_col="date"):
    """Apply sidebar month/room-type/block/gender filters to a DataFrame."""
    if df.empty:
        return df

    # Month filter
    months = st.session_state.get("filter_month", [])
    if months and date_col in df.columns:
        df = df.copy()
        df["_ym"] = df[date_col].str[:7]
        df = df[df["_ym"].isin(months)].drop(columns="_ym")

    return df


def render():
    st.header("Overview")
    st.write("Headline metrics and monthly trends for the hostel.")

    # ---- KPI cards ----
    kpi = db.kpi_snapshot()
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Students", kpi["total_students"])
    col2.metric("Occupancy Rate", f"{kpi['occupancy_rate']}%")
    col3.metric("Total Revenue (₹)", f"{kpi['total_revenue']:,.0f}")
    col4.metric("Room Rent Revenue (₹)", f"{kpi['room_rent']:,.0f}")
    col5.metric("Mess Fee Revenue (₹)", f"{kpi['mess_revenue']:,.0f}")
    col6.metric("Profit Margin (%)", f"{kpi['profit_margin']}%")

    st.divider()

    # ---- Monthly occupancy trend ----
    st.subheader("Monthly Occupancy Trend")
    occ = db.load_monthly_occupancy()
    occ = apply_filters(occ, date_col="year_month")
    if not occ.empty:
        st.plotly_chart(
            charts.line_chart(
                occ, x="year_month", y="avg_occupancy_percent",
                title="Average Occupancy Rate by Month",
                x_label="Month", y_label="Occupancy (%)",
            ),
            use_container_width=True,
        )
    else:
        st.info("No occupancy data for the selected filters.")

    # ---- Monthly revenue trend (grouped bar) ----
    st.subheader("Monthly Revenue Trend")
    rev = db.load_monthly_revenue()
    rev = apply_filters(rev, date_col="year_month")
    if not rev.empty:
        rev_long = rev.melt(
            id_vars=["year_month"],
            value_vars=["room_rent_revenue", "mess_fee_revenue"],
            var_name="revenue_type", value_name="amount",
        )
        rev_long["revenue_type"] = rev_long["revenue_type"].map({
            "room_rent_revenue": "Room Rent",
            "mess_fee_revenue": "Mess Fee",
        })
        st.plotly_chart(
            charts.grouped_bar_chart(
                rev_long, x="year_month", y="amount", color="revenue_type",
                title="Room Rent vs Mess Fee Revenue by Month",
                x_label="Month", y_label="Revenue (₹)",
            ),
            use_container_width=True,
        )
    else:
        st.info("No revenue data for the selected filters.")
