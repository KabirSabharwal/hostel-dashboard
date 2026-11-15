# 📚 HOSTEL OCCUPANCY & REVENUE DASHBOARD — Complete Study Guide

**For absolute beginners (zero coding experience required)**

---

## Table of Contents

1. [What Is This Project?](#what-is-this-project)
2. [What You Need Before Starting](#what-you-need-before-starting)
3. [Step-by-Step: How the Project Was Built](#step-by-step-how-the-project-was-built)
   - Step 1: Set Up Your Computer
   - Step 2: Generate Fake Data
   - Step 3: Clean the Data
   - Step 4: Build the Database
   - Step 5: Write KPI Queries
   - Step 6: Build the Website (Streamlit App)
   - Step 7: Test the Admin Page
   - Step 8: Push to GitHub
   - Step 9: Deploy to the Internet (Streamlit Cloud)
4. [Explanation of Every File](#explanation-of-every-file)
5. [Explanation of KPIs](#explanation-of-kpis)
6. [How to Run the Project Locally](#how-to-run-the-project-locally)
7. [How to Add New Data Through the Admin Page](#how-to-add-new-data-through-the-admin-page)
8. [Troubleshooting](#troubleshooting)
9. [Important Data Disclosure](#important-data-disclosure)

---

## 1. What Is This Project?

This is a working website (dashboard) that shows information about a college hostel:

- **How many beds are occupied vs empty** (occupancy rate percentage)
- **How much money came in** from room rent and mess (food) fees
- **Which months had high or low occupancy**
- **Which room types (single/double/triple) perform best**
- **Which weekdays have low mess attendance** (students go home on weekends)

It is a **real web application**, not a fake picture. It uses a real database (SQLite) and real Python code.

The data is **synthetic** (fake but realistic). No real student information was used.

---

## 2. What You Need Before Starting

You need only these things on your computer:

| What You Need | Why You Need It |
|--------------|-----------------|
| Windows 10 or 11 (or Mac/Linux) | The operating system to run everything |
| Python 3.11 or newer | The programming language the project uses |
| Internet connection | To download packages and upload to GitHub |
| A web browser (Chrome, Edge, Firefox) | To view the dashboard website |
| A GitHub account (free) | To save your code online |

### How to Check If Python Is Installed

Open Command Prompt or PowerShell and type:

```cmd
python --version
```

If you see something like `Python 3.11.x`, you are good. If not, download Python from https://python.org and install it. During installation, **check the box that says "Add Python to PATH"**.

---

## 3. Step-by-Step: How the Project Was Built

This section explains exactly how the project was created, step by step. You can follow these steps yourself to rebuild it from scratch.

---

### Step 1: Set Up Your Computer

**What this step does:** Creates a folder for the project and installs all the tools needed to run it.

#### 1a. Create the project folder

Open Command Prompt or PowerShell and type:

```cmd
mkdir hostel-dashboard
cd hostel-dashboard
```

- `mkdir` = "make directory" (creates a new folder)
- `cd` = "change directory" (goes inside that folder)

#### 1b. Create all subfolders

Type this (all at once on Windows PowerShell):

```powershell
$dirs = @('data/raw','data/processed','scripts','queries','app/pages','docs/screenshots'); foreach($d in $dirs){ New-Item -ItemType Directory -Path $d -Force | Out-Null }
```

This creates all the folders the project needs:
- `data/raw/` — where the fake data CSVs start
- `data/processed/` — where cleaned data goes
- `scripts/` — Python scripts that create and clean data
- `queries/` — SQL queries that calculate KPI numbers
- `app/pages/` — the 5 website pages
- `docs/screenshots/` — place for dashboard pictures

#### 1c. Create requirements.txt

Create a file named `requirements.txt` with this exact text:

```
streamlit
pandas
plotly
faker
sqlalchemy
```

**What this does:** Lists the 5 Python packages needed. One command installs them all.

#### 1d. Create .gitignore

Create a file named `.gitignore` with this text:

```
data/hostel.db
__pycache__/
.streamlit/secrets.toml
```

**What this does:** Tells Git not to upload the database file (it's fake data you can regenerate), temporary Python files, or secret settings.

#### 1e. Create a virtual environment

```cmd
python -m venv venv
```

**What this does:** Creates an isolated folder `venv/` with its own copy of Python. This keeps your project separate from other Python projects on your computer.

#### 1f. Activate the virtual environment

**Windows:**
```cmd
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` appear at the start of your command prompt. This means you are now using the project's own Python.

#### 1g. Install the packages

```cmd
pip install -r requirements.txt
```

**What this does:** Downloads and installs streamlit, pandas, plotly, faker, and sqlalchemy.

#### 1h. Verify installation

```cmd
python -c "import streamlit, pandas, plotly, faker, sqlalchemy; print('All packages installed successfully.')"
```

If you see `All packages installed successfully.`, Step 1 is done.

---

### Step 2: Generate Fake Data

**What this step does:** Creates 6 CSV files with realistic-looking (but fake) hostel data.

The data follows real patterns:
- 300 total beds across single, double, and triple rooms
- ~90% occupancy (most beds filled)
- Triple rooms have highest occupancy (~95%), double ~85%, single ~90%
- Mess attendance drops Friday through Monday (students go home on weekends)
- Hostel fees billed twice a year; mess fees charged daily
- Some intentional mistakes (duplicates, missing names, mixed date formats) so the cleaning step has something to fix

**Command:**
```cmd
python scripts/generate_data.py
```

**What you should see:** The script prints how many rows were written to each file and shows occupancy percentages by room type.

**Files created in `data/raw/`:**
- `rooms.csv` — 170 rooms (building blocks A, B, C; boys/girls)
- `bookings.csv` — student bookings with check-in/check-out dates
- `students.csv` — student information
- `mess_attendance.csv` — daily meal records
- `payments.csv` — fee payments
- `expenses.csv` — electricity, maintenance, staff, water costs

---

### Step 3: Clean the Data

**What this step does:** Fixes the intentional mistakes from Step 2:
- Removes duplicate rows
- Converts mixed date formats (DD/MM/YYYY, MM/DD/YYYY) to one standard format (YYYY-MM-DD)
- Fills missing values (blank names become "Unknown Student", missing meals become 0)
- Validates that IDs match between tables

**Command:**
```cmd
python scripts/clean_data.py
```

**What you should see:** A "before vs after" row count report showing how many duplicates were removed.

**Files created in `data/processed/`:** Same 6 CSV files but cleaned and ready for the database.

---

### Step 4: Build the Database

**What this step does:** Creates a SQLite database file (`data/hostel.db`) — a single file that holds all the data. It:
- Creates 7 tables (rooms, students, bookings, daily_occupancy, mess_attendance, payments, expenses)
- Loads the cleaned CSVs into the tables
- Derives `daily_occupancy` by walking through each booking day-by-day (explained below)
- Creates indexes for fast searching

**The trickiest part — daily_occupancy:**
The database doesn't store occupancy for every day directly. Instead, it starts from bookings. For each active booking, the script walks day by day from check-in to check-out (or today if still active) and marks one bed as occupied for each day. This creates one row per room per day showing how many beds are occupied vs vacant.

**Command:**
```cmd
python scripts/build_database.py
```

**What you should see:** A verification report showing row counts for every table and confirming occupancy is ~86% on today's date.

---

### Step 5: Write KPI Queries

**What this step does:** Creates SQL queries that calculate the key performance indicators (business metrics).

File: `queries/kpis.sql`

Contains 9 queries:
1. **Occupancy Rate** — (Occupied Beds / Total Beds) × 100
2. **Total Hostel Revenue** — Room Rent + Mess Fee
3. **Room Rent Revenue** — Hostel fees collected
4. **Mess Fee Revenue** — Money from meals
5. **Revenue per Occupied Student** — Total Revenue ÷ Number of Students
6. **Revenue per Available Bed** — Total Revenue ÷ Total Beds
7. **Vacancy Rate** — (Empty Beds / Total Beds) × 100
8. **Monthly Revenue Growth %** — This month vs last month
9. **Profit Margin %** — (Revenue − Expenses) ÷ Revenue

**Command to test:**
```cmd
python scripts/test_kpis.py
```

This runs every query against the database and prints the results so you can see the numbers.

---

### Step 6: Build the Website (Streamlit App)

**What this step does:** Creates a real website using Streamlit (Python). No HTML, CSS, or JavaScript needed.

**Files created:**
- `app/app.py` — The main entry point. Sets up the page, shows sidebar filters, and routes between pages.
- `app/db.py` — Database helpers. Connects to SQLite and returns data as tables (DataFrames).
- `app/charts.py` — Reusable chart functions (line charts, bar charts, pie charts).
- `app/pages/1_Overview.py` — KPI cards + monthly trend charts
- `app/pages/2_Rooms.py` — Room type comparison + room availability table
- `app/pages/3_Revenue.py` — Revenue breakdown pie + per-student metrics + expenses
- `app/pages/4_Weekday.py` — Weekday occupancy + mess revenue + Friday-Monday callout
- `app/pages/5_Admin.py` — Forms to add new bookings and mess entries

**Sidebar filters** (shared across all pages):
- Month selector
- Room type filter (single/double/triple)
- Hostel block filter (A/B/C)
- Gender filter (boys/girls)
- Occupancy status filter (occupied/vacant)

**Command to run:**
```cmd
streamlit run app/app.py
```

The website opens at `http://localhost:8501` in your web browser.

---

### Step 7: Test the Admin Page

**What this step does:** Proves the website is live (not a frozen snapshot) by adding new data through a form.

1. Go to page **5 — Admin**
2. Fill in the "Add Booking" form (booking ID, student ID, name, room, dates)
3. Click "Add Booking"
4. You see a success message
5. Go to page **1 — Overview** — the KPI numbers update slightly
6. Go to page **2 — Rooms** — your new booking appears in the table

This proves the app can add data in real-time.

---

### Step 8: Push to GitHub

**What this step does:** Saves your code online so others can see it and you can deploy it.

**Commands:**
```cmd
git init
git add .
git commit -m "First commit: complete hostel dashboard project"
git branch -M main
git remote add origin https://github.com/YOURUSERNAME/hostel-dashboard.git
git push -u origin main
```

Replace `YOURUSERNAME` with your actual GitHub username.

**On GitHub.com:**
1. Click "New repository"
2. Name it `hostel-dashboard`
3. Set it to **Public** (required for free Streamlit Cloud)
4. Do NOT check "Add README" or "Add .gitignore" (we already have them)
5. Click Create repository

---

### Step 9: Deploy to the Internet (Streamlit Cloud)

**What this step does:** Makes your dashboard available at a public web address anyone can visit.

1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click "New app"
4. Select your `hostel-dashboard` repository
5. Branch: `main`
6. Main file path: `app/app.py`
7. Click **Deploy**

In a few minutes, you get a public URL like `https://your-app.streamlit.app`.

---

## 4. Explanation of Every File

| File | What It Does (Plain English) |
|------|------------------------------|
| `README.md` | The project's front page — explains what it is and how to run it |
| `requirements.txt` | List of Python packages to install |
| `.gitignore` | Files that should NOT be uploaded to GitHub |
| `data/raw/rooms.csv` | Fake room data (170 rooms, 300 beds) |
| `data/raw/bookings.csv` | Fake booking records with dates |
| `data/raw/students.csv` | Fake student information |
| `data/raw/mess_attendance.csv` | Daily meal attendance records |
| `data/raw/payments.csv` | Fee payment records |
| `data/raw/expenses.csv` | Daily expense records |
| `data/processed/*.csv` | Cleaned versions of the above CSVs |
| `data/hostel.db` | The SQLite database (one file, all data) |
| `scripts/generate_data.py` | Creates the fake CSVs |
| `scripts/clean_data.py` | Fixes mistakes in the CSVs |
| `scripts/build_database.py` | Creates hostel.db from cleaned CSVs |
| `scripts/test_kpis.py` | Tests that all KPI queries work |
| `queries/kpis.sql` | SQL queries for all 9 business metrics |
| `app/__init__.py` | Makes the app folder a proper Python package |
| `app/app.py` | Main website entry point with sidebar filters |
| `app/db.py` | Functions to read data from the database |
| `app/charts.py` | Functions to create charts (Plotly) |
| `app/pages/1_Overview.py` | Page 1: KPI cards and monthly trends |
| `app/pages/2_Rooms.py` | Page 2: Room comparison and availability table |
| `app/pages/3_Revenue.py` | Page 3: Revenue breakdown and per-student metrics |
| `app/pages/4_Weekday.py` | Page 4: Weekday occupancy and mess analysis |
| `app/pages/5_Admin.py` | Page 5: Forms to add new bookings/mess entries |
| `docs/executive_summary.md` | One-page business summary with real numbers |

---

## 5. Explanation of KPIs

| KPI | Formula | Plain English Meaning |
|-----|---------|----------------------|
| Occupancy Rate | (Occupied Beds ÷ Total Beds) × 100 | What percentage of beds are filled |
| Total Hostel Revenue | Room Rent + Mess Fee | All money coming in |
| Room Rent Revenue | Sum of hostel fees paid | Money from room rentals |
| Mess Fee Revenue | Sum of meal charges | Money from food |
| Revenue per Occupied Student | Total Revenue ÷ Number of Students | How much each student pays on average |
| Revenue per Available Bed | Total Revenue ÷ Total Beds | How much each bed earns on average |
| Vacancy Rate | (Empty Beds ÷ Total Beds) × 100 | What percentage of beds are empty |
| Monthly Revenue Growth % | (This Month − Last Month) ÷ Last Month × 100 | Is revenue going up or down month to month |
| Profit Margin % | (Revenue − Expenses) ÷ Revenue × 100 | How much profit is left after expenses |

---

## 6. How to Run the Project Locally

If you already have the project folder and want to run it:

### Option A: Everything is already set up
```cmd
cd hostel-dashboard
venv\Scripts\activate
streamlit run app/app.py
```
Then open `http://localhost:8501` in your browser.

### Option B: You need to rebuild everything from scratch
```cmd
cd hostel-dashboard
venv\Scripts\activate
python scripts/generate_data.py
python scripts/clean_data.py
python scripts/build_database.py
streamlit run app/app.py
```

---

## 7. How to Add New Data Through the Admin Page

1. Run the app: `streamlit run app/app.py`
2. Open `http://localhost:8501`
3. On the left sidebar, click "5 — Admin"
4. **To add a booking:** Fill in Booking ID, Student ID, Student Name, select a Room Number, pick Check-in Date, choose Booking Status and Fee Payment Status, then click "Add Booking"
5. **To add a mess entry:** Fill in Attendance ID, select a Student ID, pick a Date, choose Meals Availed (0-3), then click "Add Mess Entry"
6. After submitting, you'll see a green success message
7. Click on other pages (Overview, Rooms, Revenue, Weekday) — your new data appears immediately

---

## 8. Troubleshooting

| Problem | Possible Cause | Fix |
|---------|---------------|-----|
| `python` is not recognized | Python not installed or not in PATH | Install Python from python.org, check "Add to PATH" |
| `ModuleNotFoundError` | Packages not installed | Run `pip install -r requirements.txt` |
| `Port 8501 is not available` | Another app using that port | Close other Streamlit apps, or use `--server.port 8502` |
| `no such table: students` | Database not rebuilt | Run `python scripts/build_database.py` again |
| Blank pages in Streamlit | Import error | Make sure `app/__init__.py` exists and all page files have `render()` at the bottom |
| `StreamlitDuplicateElementKey` | Duplicate widget keys | Make sure each sidebar widget has a unique `key=` value |

---

## 9. Important Data Disclosure

⚠️ **ALL DATA IN THIS PROJECT IS SYNTHETIC (FAKE).**

- No real student names, IDs, or personal information
- No real room numbers from an actual hostel
- No real payment or financial data
- The data was generated by a Python script using the Faker library
- Intentional mistakes (duplicates, missing values, mixed date formats) were added to demonstrate data cleaning

This project is for **educational and demonstration purposes only**. If you want to use it with real hostel data, you must:
- Get permission from the hostel administration
- Anonymize all student data (remove names, IDs, contact info)
- Follow data privacy laws in your country

---

## 10. Summary Checklist

Before you consider the project complete, make sure:

- [ ] `python scripts/generate_data.py` creates 6 CSVs
- [ ] `python scripts/clean_data.py` produces cleaned CSVs and prints a report
- [ ] `python scripts/build_database.py` creates `data/hostel.db` with all tables
- [ ] `python scripts/test_kpis.py` runs all 9 KPI queries
- [ ] `streamlit run app/app.py` opens a working dashboard with 5 pages
- [ ] Sidebar filters change the data on every page
- [ ] Admin page can add a booking and mess entry that appear elsewhere
- [ ] Code is pushed to GitHub (public repository)
- [ ] App is deployed on Streamlit Cloud (optional, gives a public URL)
- [ ] README.md has setup instructions and data disclosure
- [ ] docs/executive_summary.md has real numbers from the data

---

## 🎓 What You Learned

By building this project, you learned:

1. **Python** — A programming language used for data and websites
2. **Virtual environments** — Keeping projects separate
3. **CSV files** — Simple data files that Excel can open
4. **Data cleaning** — Fixing messy data before using it
5. **SQLite** — A database stored in a single file
6. **SQL** — Language for asking questions of a database
7. **Streamlit** — Building websites with only Python
8. **Plotly** — Creating interactive charts
9. **GitHub** — Saving code online
10. **Deployment** — Making a website available on the internet

You built a real, working web application with zero prior coding experience. Congratulations!
