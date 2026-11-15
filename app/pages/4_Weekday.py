"""
app/pages/4_Weekday.py — Weekday Analysis page.

Weekday occupancy and weekday mess revenue bar charts, plus a callout
explaining the Friday–Monday drop (students go home on weekends).
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import db
import charts


def render():
    st.header("Weekday Analysis")
    st.write("How occupancy and mess attendance vary across the week.")

    col1, col2 = st.columns(2)

    # ---- Weekday occupancy ----
    with col1:
        st.subheader("Occupancy by Weekday")
        occ = db.load_occupancy_by_weekday()
        if not occ.empty:
            st.plotly_chart(
                charts.bar_chart(
                    occ, x="weekday_name", y="avg_occupancy_percent",
                    title="Average Occupancy Rate by Weekday",
                    x_label="Weekday", y_label="Occupancy (%)",
                ),
                use_container_width=True,
            )
        else:
            st.info("No occupancy data available.")

    # ---- Weekday mess revenue ----
    with col2:
        st.subheader("Mess Revenue by Weekday")
        mess = db.load_mess_by_weekday()
        if not mess.empty:
            st.plotly_chart(
                charts.bar_chart(
                    mess, x="weekday_name", y="mess_revenue",
                    title="Mess Revenue by Weekday",
                    x_label="Weekday", y_label="Revenue (₹)",
                ),
                use_container_width=True,
            )
        else:
            st.info("No mess data available.")

    st.divider()

    # ---- Callout ----
    st.info(
        "📉 **Friday–Monday drop:** Mess attendance falls sharply from Friday "
        "evening through Monday lunch, because many students go home for the "
        "weekend. You can see this in the mess revenue chart above — Friday, "
        "Saturday, and Sunday show lower revenue than Monday through Thursday. "
        "This is normal for college hostels and is already baked into the "
        "synthetic data pattern."
    )


render()
