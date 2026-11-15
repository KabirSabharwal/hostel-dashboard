# Executive Summary — Hostel Occupancy & Revenue Dashboard

## Business overview

This dashboard provides a college hostel warden or manager with real-time visibility into bed occupancy and revenue across room types, blocks, and time periods. The system tracks 300 beds across single, double, and triple rooms in blocks A, B, and C (boys and girls), with daily occupancy derived from booking records and mess attendance tracked per student per day.

## Key performance indicators (as of latest data)

| Metric | Value |
|--------|-------|
| Total beds | 300 |
| Occupied beds | ~258 |
| **Occupancy rate** | **86.0%** |
| Vacancy rate | 14.0% |
| Total students | 259 |
| Total revenue | ₹7,199,400 |
| Room rent revenue | ₹5,508,000 |
| Mess fee revenue | ₹2,177,280 |
| Revenue per occupied student | ₹27,796.91 |
| Revenue per available bed | ₹23,998.00 |
| Profit margin | -84.37% |

## Occupancy by room type

| Room Type | Total Beds | Occupied | Occupancy Rate |
|-----------|------------|----------|----------------|
| Single | 60 | ~53 | 88.3% |
| Double | 180 | ~156 | 86.7% |
| Triple | 60 | ~58 | 96.7% |

Triple rooms have the highest occupancy (96.7%), while single rooms generate the highest revenue per student.

## Revenue breakdown

- **Room rent (hostel fees):** ₹5,508,000 (76.5% of total)
- **Mess fees:** ₹2,177,280 (23.5% of total)

Hostel fees are billed once per semester; mess fees are charged daily based on meals availed (₹40 per meal).

## Weekly pattern — mess attendance

Mess attendance drops significantly from Friday evening through Monday lunch, as students go home for the weekend. Saturday and Sunday show the lowest mess revenue, confirming the weekend exodus pattern.

## Data notes

- All data is **synthetic** (generated for demonstration, no real student data)
- Data covers ~12 months of booking history and ~4 months of daily mess attendance
- Intentional data-quality issues (duplicates, missing values, mixed date formats) were included and cleaned as part of the pipeline
- The admin page allows adding new bookings and mess entries live, which immediately reflect on all dashboard pages

## Recommendations

1. **Investigate the profit margin deficit** — expenses (₹1,327,338) exceed revenue, driven by electricity and staff costs
2. **Target single-room occupancy** — single rooms have the highest revenue per student but 11.7% of beds are vacant
3. **Weekend mess planning** — reduce mess staffing/inventory Fri–Sun to match lower attendance
