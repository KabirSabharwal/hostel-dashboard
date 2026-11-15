"""
app/pages/3_Revenue.py — Revenue page.

Revenue breakdown pie (room rent vs mess fee), revenue per occupied student
and per available bed by month, and expense breakdown by category.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app import db
from app import charts


def render():
    st.header("Revenue")
    st.write("Where the money comes from and how it compares to costs.")

    # ---- Revenue breakdown pie ----
    st.subheader("Revenue Breakdown")
    kpi = db.kpi_snapshot()
    pie_df = pd.DataFrame({
        "source": ["Room Rent", "Mess Fee"],
        "amount": [kpi["room_rent"], kpi["mess_revenue"]],
    })
    st.plotly_chart(
        charts.pie_chart(
            pie_df, values="amount", names="source",
            title="Room Rent vs Mess Fee Revenue",
        ),
        use_container_width=True,
    )

    # ---- Revenue per occupied student / per available bed by month ----
    st.subheader("Revenue per Student and per Bed by Month")
    # Build month-by-month metrics from payments + occupancy
    monthly_rev = db.load_monthly_revenue()
    if not monthly_rev.empty:
        monthly_rev["total_revenue"] = (
            monthly_rev["room_rent_revenue"] + monthly_rev["mess_fee_revenue"]
        )
        # occupied students per month (approx: distinct active bookings in that month)
        conn = db.get_connection()
        try:
            students_sql = """
                SELECT strftime('%Y-%m', checkin_date) AS year_month,
                       COUNT(DISTINCT student_id) AS n_students
                FROM bookings
                WHERE booking_status = 'active' AND checkout_date IS NULL
                GROUP BY year_month
            """
            students_df = pd.read_sql_query(students_sql, conn)
        finally:
            conn.close()

        merged = monthly_rev.merge(students_df, on="year_month", how="left")
        merged["revenue_per_student"] = (
            merged["total_revenue"] / merged["n_students"]
        ).round(2)
        merged["revenue_per_bed"] = (
            merged["total_revenue"] / 300
        ).round(2)  # 300 total beds

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                charts.bar_chart(
                    merged, x="year_month", y="revenue_per_student",
                    title="Revenue per Occupied Student by Month",
                    x_label="Month", y_label="₹ per Student",
                ),
                use_container_width=True,
            )
        with col2:
            st.plotly_chart(
                charts.bar_chart(
                    merged, x="year_month", y="revenue_per_bed",
                    title="Revenue per Available Bed by Month",
                    x_label="Month", y_label="₹ per Bed",
                ),
                use_container_width=True,
            )
    else:
        st.info("No revenue data available.")

    st.divider()

    # ---- Expense breakdown ----
    st.subheader("Expense Breakdown")
    exp = db.load_expenses_by_category()
    if not exp.empty:
        st.plotly_chart(
            charts.pie_chart(
                exp, values="total_amount", names="category",
                title="Expenses by Category",
            ),
            use_container_width=True,
        )
        st.dataframe(
            exp.rename(columns={
                "category": "Category",
                "total_amount": "Total Amount (₹)",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No expense data available.")
