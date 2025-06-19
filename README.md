# Rishab_2025-06-19

## 🧾 Store Monitoring Backend System

This project implements a backend system that tracks the **uptime/downtime of restaurants** in the US based on periodic polling, business hours, and timezones.

The system generates CSV reports for each store's availability, considering complex overlaps between UTC data and local business hours.

---

## 📂 Tech Stack

- **Python 3.10+**
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **pandas**
- **zoneinfo** for timezone handling

---

## 📊 Features

- Load and store 3 CSV files into a relational DB:
  - Store Status (UTC timestamps)
  - Business Hours (local time)
  - Store Timezones
- Automatically handle missing values:
  - Assume 24/7 open if business hours are missing
  - Default timezone: `America/Chicago`
- Background task to **generate report** with interpolated uptime/downtime
- Store CSV in the DB (as `BLOB`)
- Stream CSV to user via API once ready

---

## 🧮 Report Schema

Each row of the CSV contains:

| Column                   | Unit     |
|--------------------------|----------|
| Store ID                 | -        |
| Last Week Uptime         | Hours    |
| Last Week Downtime       | Hours    |
| Last Day Uptime          | Hours    |
| Last Day Downtime        | Hours    |
| Last Hour Uptime         | Minutes  |
| Last Hour Downtime       | Minutes  |

---

## 🧠 Computation Logic

## 🧠 Uptime/Downtime Calculation Logic

The report generation process follows a structured and well-defined flow to compute uptime and downtime across different time intervals. Here's a detailed breakdown of the logic:

### Step 1: Identify Business Days and Hours
- For a given store and time interval (last hour/day/week), we extract each day in that range.
- For each day, we query the `menu_hours` table to fetch the configured business hours.
- If no entry is found for a store on a given day, we assume the store operates **24×7** for that day.

### Step 2: Retrieve Status Timestamps
- For each business hour interval, we query the `store_status` table to retrieve all polling timestamps (`active` or `inactive`) that fall within that interval.
- All timestamps are stored in **UTC**, so we convert business hours to UTC using the store’s local timezone (from the `timezones` table or default to `America/Chicago`).

### Step 3: Interpolate to Compute Uptime/Downtime
- To account for the sparse nature of the polling data (typically hourly), we interpolate between timestamps using a midpoint method:
  - For each timestamp, we calculate half the time to its previous and next timestamp.
  - This half-before and half-after duration is assigned to **uptime** or **downtime**, depending on the status (`active`/`inactive`) at the current timestamp.
- This results in a fair approximation of how long a store stayed in a particular state between polls.

### Step 4: Handle Missing Data
- If no status data is available within a business interval, we assume the store was **fully operational** (i.e., 100% uptime for that interval).

---

This logic ensures that:
- Uptime/downtime is calculated **only within business hours**.
- All data is timezone-aware and aligned to **local store time**.
- The interpolation accounts for time gaps between status polls in a fair and consistent way.


---

## 🔁 API Endpoints

### 1. `/trigger_report`

- **Method**: `POST`
- **Description**: Triggers generation of the report.
- **Returns**: A unique `report_id` to track report generation.

### 2. `/get_report?report_id=<id>`

- **Method**: `GET`
- **Description**: Fetches the status or file of the report.
- **Returns**:
  - If `Running`: returns a message indicating that report is being generated.
  - If `Completed`: returns CSV as a downloadable streaming response.

---

## 🚀 How to Run

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/rishab_2025-06-19.git
cd rishab_2025-06-19
