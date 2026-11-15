"""
app/pages/5_Admin.py — Admin page.

Simple forms to add a new booking and a new mess attendance entry directly
into SQLite. After a successful insert, the change appears immediately on
the other pages (proving the app is live, not a static snapshot).
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import db


def render():
    st.header("Admin — Add New Records")
    st.write("Add a new booking or a new mess attendance entry. Changes are "
             "written to SQLite and appear immediately on the other pages.")

    tab1, tab2 = st.tabs(["➕ Add Booking", "🍽️ Add Mess Entry"])

    # ------------------------------------------------------------------
    # Tab 1: Add a new booking
    # ------------------------------------------------------------------
    with tab1:
        st.subheader("New Booking")

        rooms = db.load_rooms()
        room_options = rooms["room_number"].tolist() if not rooms.empty else []

        with st.form("add_booking_form"):
            col1, col2 = st.columns(2)
            with col1:
                booking_id = st.text_input("Booking ID", value=f"BK{9000 + len(rooms) + 1:04d}")
                student_id = st.text_input("Student ID", value="STU9999")
                student_name = st.text_input("Student Name")
                room_number = st.selectbox("Room Number", options=room_options)
            with col2:
                checkin_date = st.date_input("Check-in Date", value=date.today())
                checkout_date = st.date_input(
                    "Check-out Date", value=None,
                    help="Leave empty if the student is still active",
                )
                booking_status = st.selectbox(
                    "Booking Status", ["active", "confirmed", "completed", "cancelled"],
                    index=0,
                )
                fee_payment_status = st.selectbox(
                    "Fee Payment Status", ["paid", "pending", "partial"], index=0
                )

            submitted = st.form_submit_button("Add Booking")

        if submitted:
            if not booking_id or not student_id or not student_name or not room_number:
                st.error("Please fill in all required fields.")
            else:
                co = str(checkout_date) if checkout_date else ""
                ok = db.add_booking(
                    booking_id, student_id, student_name, room_number,
                    str(checkin_date), co, booking_status, fee_payment_status
                )
                if ok:
                    st.success(f"Booking {booking_id} added successfully!")
                    st.rerun()
                else:
                    st.error(f"Booking ID {booking_id} already exists. Use a different ID.")

    # ------------------------------------------------------------------
    # Tab 2: Add mess attendance
    # ------------------------------------------------------------------
    with tab2:
        st.subheader("New Mess Attendance Entry")

        students = db.query("SELECT student_id, student_name FROM students ORDER BY student_id")
        student_options = students["student_id"].tolist() if not students.empty else []

        with st.form("add_mess_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                attendance_id = st.text_input(
                    "Attendance ID", value=f"MS{90000 + len(students) + 1:04d}"
                )
                mess_student_id = st.selectbox("Student ID", options=student_options)
            with col2:
                mess_date = st.date_input("Date", value=date.today())
            with col3:
                meals = st.selectbox("Meals Availed", options=[0, 1, 2, 3], index=3)

            submitted_m = st.form_submit_button("Add Mess Entry")

        if submitted_m:
            if not attendance_id or not mess_student_id:
                st.error("Please fill in all required fields.")
            else:
                ok = db.add_mess_attendance(
                    attendance_id, mess_student_id, str(mess_date), int(meals)
                )
                if ok:
                    st.success(f"Mess entry {attendance_id} added successfully!")
                    st.rerun()
                else:
                    st.error(f"Attendance ID {attendance_id} already exists. Use a different ID.")

    # ------------------------------------------------------------------
    # Show the most recent records so the user can verify
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("Recent Records (verification)")

    col1, col2 = st.columns(2)
    with col1:
        st.write("Latest bookings:")
        recent_bookings = db.query("""
            SELECT booking_id, student_name, room_number, checkin_date,
                   checkout_date, booking_status
            FROM bookings
            ORDER BY checkin_date DESC
            LIMIT 5
        """)
        st.dataframe(recent_bookings, use_container_width=True, hide_index=True)

    with col2:
        st.write("Latest mess entries:")
        recent_mess = db.query("""
            SELECT attendance_id, student_id, date, meals_availed, mess_charge
            FROM mess_attendance
            ORDER BY date DESC
            LIMIT 5
        """)
        st.dataframe(recent_mess, use_container_width=True, hide_index=True)


render()
