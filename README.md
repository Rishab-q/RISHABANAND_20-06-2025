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

## 🧠 Interpolation Logic

When computing uptime/downtime:

- Data is only considered **within business hours**
- For sparse polling (e.g. only 2 timestamps per day), we interpolate by:
  - Taking half the duration before and after each observation
  - Assigning that block to the corresponding `status` (active/inactive)
  - Capping the block inside business hours + time range

---

## 🔁 API Endpoints

### 1. `/trigger_report`

- **Method**: `POST`
- **Description**: Triggers asynchronous generation of the report.
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
