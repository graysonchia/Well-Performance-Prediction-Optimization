# Well Performance Prediction & Optimization

Oil and gas analytics portfolio project for synthetic well performance monitoring, production forecasting, anomaly detection, and operational dashboarding.

## Project Overview

This project simulates a Malaysian offshore oil field analytics workflow. It includes a PostgreSQL database, FastAPI backend, synthetic seed data, Jupyter analysis notebook, and Expo React Native frontend.

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy 2.0 async
- Alembic
- PostgreSQL
- psycopg2
- pandas, scipy, scikit-learn, Prophet
- Jupyter Notebook
- React Native Expo
- Axios
- React Navigation
- React Native Chart Kit

## Project Structure

```text
backend/                 FastAPI backend, SQLAlchemy models, Alembic migrations
data/seeds/seed.py       Synthetic oil field data generator
analytics/notebooks/     Jupyter notebook for EDA, forecasting, clustering, anomaly detection
analytics/outputs/       Saved analysis charts
frontend/                Expo React Native frontend
```

## Database

Database name:

```text
wellanalytics
```

Main tables:

```text
wells
production_logs
sensor_readings
maintenance_events
users
```

## Backend Setup

From the `backend` folder, ensure `.env` contains:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/wellanalytics
SYNC_DATABASE_URL=postgresql+psycopg2://postgres:yourpassword@localhost:5432/wellanalytics
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Run migrations:

```powershell
cd backend
alembic upgrade head
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

API base URL:

```text
http://127.0.0.1:8000/api/v1
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Seed Data

Update the password placeholder in:

```text
data/seeds/seed.py
```

Then run:

```powershell
python data/seeds/seed.py
```

The script creates realistic synthetic wells, production logs, sensor readings, and maintenance events.

## Create Login User

Register a user:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/auth/register" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"username":"admin","email":"admin@example.com","password":"admin123"}'
```

Login credentials:

```text
Username: admin
Password: admin123
```

## Analytics Notebook

Notebook:

```text
analytics/notebooks/well_analysis.ipynb
```

It includes:

- Dataset overview
- Exploratory data analysis
- Production decline curve fitting
- 12-month well production forecast
- Water cut analysis
- Isolation Forest anomaly detection
- Prophet field production forecasting
- K-Means well performance clustering
- Maintenance impact analysis

Charts are saved to:

```text
analytics/outputs/
```

## Frontend Setup

Because the project path contains `&`, `npx expo start` may fail on Windows. Use the helper scripts instead.

Start mobile Expo:

```powershell
cd frontend
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-expo.ps1
```

Start web:

```powershell
cd frontend
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start-web.ps1
```

Web URL:

```text
http://localhost:8082
```

## Frontend Features

- Login with JWT storage
- Dashboard summary cards
- Top producers chart
- Field comparison chart
- Wells list with status badges
- Well detail production and water cut trends
- Sensor summary
- Maintenance history
- Analytics charts for production trend, downtime, and decline curve

## Notes

- Replace all `yourpassword` placeholders with your local PostgreSQL password.
- Ensure the backend API is running before using the frontend.
- For Android emulator API calls, the frontend uses `http://10.0.2.2:8000/api/v1`.
- For web and iOS, it uses `http://localhost:8000/api/v1`.
