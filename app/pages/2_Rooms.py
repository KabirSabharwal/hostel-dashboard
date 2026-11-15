"""
app/pages/2_Rooms.py — Rooms page.

Room type comparison (occupancy % and revenue per student) plus a table of
every room with total beds, occupied, vacant. Rooms with high vacancy are
highlighted.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app import db
from app import charts


def render():
    st.header("Rooms")
    st.write("How each room type (single / double / triple) is performing.")

    # ---- Room type comparison ----
    st.subheader("Room Type Comparison")
    rt = db.load_occupancy_by_room_type()
    rt_df = pd.DataFrame(rt)

    if not rt_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                charts.bar_chart(
                    rt_df, x="room_type", y="occupancy_rate_percent",
                    title="Occupancy Rate by Room Type",
                    x_label="Room Type", y_label="Occupancy (%)",
                ),
                use_container_width=True,
            )
        with col2:
            st.plotly_chart(
                charts.bar_chart(
                    rt_df, x="room_type", y="revenue_per_student",
                    title="Revenue per Student by Room Type",
                    x_label="Room Type", y_label="Revenue per Student (₹)",
                ),
                use_container_width=True,
            )

        # Summary table
        st.dataframe(
            rt_df.rename(columns={
                "room_type": "Room Type",
                "occupancy_rate_percent": "Occupancy Rate (%)",
                "occupied_beds": "Occupied Beds",
                "total_beds": "Total Beds",
                "n_students": "Students",
                "room_revenue": "Room Revenue (₹)",
                "revenue_per_student": "Revenue per Student (₹)",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No room data available.")

    st.divider()

    # ---- Room availability table ----
    st.subheader("Room Availability Table")
    rooms = db.load_room_availability()
    rooms_df = pd.DataFrame(rooms)

    if not rooms_df.empty:
        st.dataframe(
            rooms_df.rename(columns={
                "room_number": "Room",
                "room_type": "Type",
                "total_beds": "Total Beds",
                "block": "Block",
                "gender": "Gender",
                "allocated_beds": "Occupied",
                "vacant_beds": "Vacant",
                "occupancy_rate_percent": "Occupancy (%)",
            }),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("🔴 Pink rows have at least one vacant bed.")
    else:
        st.info("No room data available.")


render()
