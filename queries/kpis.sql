-- ===========================================================================
-- queries/kpis.sql
--
-- All KPI queries from section 6 of the business case.
-- Each query is labeled and commented so a beginner can read it line by line.
--
-- How to run (example with sqlite3 CLI):
--   sqlite3 data/hostel.db < queries/kpis.sql
--
-- Or from Python (see scripts/test_kpis.py idea):
--   import sqlite3, pandas as pd
--   conn = sqlite3.connect("data/hostel.db")
--   df = pd.read_sql_query(open("queries/kpis.sql").read().split("-- KPI: ")[1], conn)
-- ===========================================================================


-- ===========================================================================
-- KPI 1: Occupancy Rate
--   = (Occupied Beds / Total Beds) * 100
-- Uses the latest date in daily_occupancy as "today".
-- ===========================================================================
-- KPI: Occupancy Rate
SELECT
    ROUND(SUM(allocated_beds) * 100.0 / SUM(total_beds), 2) AS occupancy_rate_percent
FROM daily_occupancy
WHERE date = (SELECT MAX(date) FROM daily_occupancy);


-- ===========================================================================
-- KPI 2: Total Hostel Revenue
--   = Hostel Fee Revenue + Mess Fee Revenue
-- Sums paid hostel_fee payments and paid mess_fee payments.
-- ===========================================================================
-- KPI: Total Hostel Revenue
SELECT
    ROUND(SUM(CASE WHEN payment_type = 'hostel_fee' THEN amount ELSE 0 END), 2) AS room_rent_revenue,
    ROUND(SUM(CASE WHEN payment_type = 'mess_fee' THEN amount ELSE 0 END), 2) AS mess_fee_revenue,
    ROUND(SUM(amount), 2) AS total_hostel_revenue
FROM payments
WHERE status = 'paid';


-- ===========================================================================
-- KPI 3: Room Rent Revenue
--   = SUM(hostel fees collected in period)
-- Hostel fee payments only, status = 'paid'.
-- ===========================================================================
-- KPI: Room Rent Revenue
SELECT
    ROUND(SUM(amount), 2) AS room_rent_revenue
FROM payments
WHERE payment_type = 'hostel_fee'
  AND status = 'paid';


-- ===========================================================================
-- KPI 4: Mess Fee Revenue
--   = SUM(mess_charge for meals availed in period)
-- Sums mess_charge from mess_attendance (meals actually availed).
-- ===========================================================================
-- KPI: Mess Fee Revenue
SELECT
    ROUND(SUM(mess_charge), 2) AS mess_fee_revenue
FROM mess_attendance;


-- ===========================================================================
-- KPI 5: Revenue per Occupied Student
--   = Total Revenue / Number of Occupied Students
-- Occupied students = distinct active bookings (checkout_date is NULL).
-- ===========================================================================
-- KPI: Revenue per Occupied Student
WITH revenue AS (
    SELECT ROUND(SUM(amount), 2) AS total_revenue
    FROM payments
    WHERE status = 'paid'
),
occupied_students AS (
    SELECT COUNT(DISTINCT student_id) AS n_students
    FROM bookings
    WHERE booking_status = 'active'
      AND checkout_date IS NULL
)
SELECT
    r.total_revenue,
    o.n_students,
    CASE WHEN o.n_students > 0
         THEN ROUND(r.total_revenue / o.n_students, 2)
         ELSE 0 END AS revenue_per_occupied_student
FROM revenue r, occupied_students o;


-- ===========================================================================
-- KPI 6: Revenue per Available Bed
--   = Total Revenue / Total Available Beds
-- Total available beds = sum of total_beds across all rooms.
-- ===========================================================================
-- KPI: Revenue per Available Bed
WITH revenue AS (
    SELECT ROUND(SUM(amount), 2) AS total_revenue
    FROM payments
    WHERE status = 'paid'
),
total_beds AS (
    SELECT SUM(total_beds) AS n_beds
    FROM rooms
)
SELECT
    r.total_revenue,
    t.n_beds,
    CASE WHEN t.n_beds > 0
         THEN ROUND(r.total_revenue / t.n_beds, 2)
         ELSE 0 END AS revenue_per_available_bed
FROM revenue r, total_beds t;


-- ===========================================================================
-- KPI 7: Vacancy Rate
--   = (Vacant Beds / Total Beds) * 100
-- Uses the latest date in daily_occupancy as "today".
-- ===========================================================================
-- KPI: Vacancy Rate
SELECT
    ROUND(SUM(vacant_beds) * 100.0 / SUM(total_beds), 2) AS vacancy_rate_percent
FROM daily_occupancy
WHERE date = (SELECT MAX(date) FROM daily_occupancy);


-- ===========================================================================
-- KPI 8: Monthly Revenue Growth %
--   = ((This Month - Last Month) / Last Month) * 100
-- Compares total paid revenue of the latest month vs the previous month.
-- ===========================================================================
-- KPI: Monthly Revenue Growth %
WITH monthly AS (
    SELECT
        strftime('%Y-%m', payment_date) AS year_month,
        ROUND(SUM(amount), 2) AS revenue
    FROM payments
    WHERE status = 'paid'
    GROUP BY year_month
    ORDER BY year_month
),
ranked AS (
    SELECT
        year_month,
        revenue,
        LAG(revenue) OVER (ORDER BY year_month) AS prev_revenue
    FROM monthly
)
SELECT
    year_month AS this_month,
    LAG(year_month) OVER (ORDER BY year_month) AS last_month,
    revenue AS this_month_revenue,
    prev_revenue AS last_month_revenue,
    CASE WHEN prev_revenue IS NULL OR prev_revenue = 0
         THEN NULL
         ELSE ROUND((revenue - prev_revenue) * 100.0 / prev_revenue, 2)
    END AS monthly_revenue_growth_percent
FROM ranked
ORDER BY year_month DESC
LIMIT 1;


-- ===========================================================================
-- KPI 9: Profit Margin %
--   = ((Total Revenue - Total Expenses) / Total Revenue) * 100
-- ===========================================================================
-- KPI: Profit Margin %
WITH revenue AS (
    SELECT SUM(amount) AS total_revenue
    FROM payments
    WHERE status = 'paid'
),
expense_totals AS (
    SELECT SUM(amount) AS total_expenses
    FROM expenses
)
SELECT
    ROUND(r.total_revenue, 2) AS total_revenue,
    ROUND(e.total_expenses, 2) AS total_expenses,
    ROUND(r.total_revenue - e.total_expenses, 2) AS profit,
    CASE WHEN r.total_revenue > 0
         THEN ROUND((r.total_revenue - e.total_expenses) * 100.0 / r.total_revenue, 2)
         ELSE NULL END AS profit_margin_percent
FROM revenue r, expense_totals e;

-- ===========================================================================
-- END OF KPI QUERIES
-- ===========================================================================
