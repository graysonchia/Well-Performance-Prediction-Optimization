"""
Seed realistic synthetic well performance data into PostgreSQL.

Install dependencies if needed:
    pip install Faker psycopg2-binary

Update DB_URL with your PostgreSQL password before running:
    python data/seeds/seed.py
"""

from __future__ import annotations

import math
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2
from faker import Faker
from dotenv import load_dotenv
from psycopg2.extras import execute_values


load_dotenv(Path(__file__).resolve().parents[2] / "backend" / ".env")


def get_db_url() -> str:
    db_url = os.getenv("SEED_DATABASE_URL") or os.getenv("SYNC_DATABASE_URL")
    if not db_url:
        raise RuntimeError("Set SYNC_DATABASE_URL in backend/.env before seeding data.")
    return db_url.replace("postgresql+psycopg2://", "postgresql://", 1)


DB_URL = get_db_url()

FAKER = Faker("en_US")
Faker.seed(42)
random.seed(42)

FIELD_NAMES = ("Seria Field", "Dulang Field", "Bunga Field")
OPERATORS = (
    "Petronas Carigali",
    "Sarawak Shell Berhad",
    "Hibiscus Petroleum",
    "Mubadala Energy Malaysia",
    "PTTEP Malaysia",
)
WELL_TYPES = ("oil", "gas", "oil_gas", "water_injection")
WELL_STATUSES = ("active", "active", "active", "active", "inactive", "maintenance")
EVENT_TYPES = (
    "pump replacement",
    "chemical injection",
    "wellbore cleanout",
    "ESP repair",
    "choke replacement",
    "pressure test",
)
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)
BATCH_SIZE = 5_000


def daterange(start: datetime, end: datetime):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def random_spud_date() -> datetime:
    start = datetime(2015, 1, 1)
    end = datetime(2021, 12, 31)
    days = (end - start).days
    return start + timedelta(days=random.randint(0, days))


def make_wells() -> list[dict]:
    wells = []
    field_prefixes = {
        "Seria Field": "SER",
        "Dulang Field": "DUL",
        "Bunga Field": "BGA",
    }

    for index in range(20):
        field_name = FIELD_NAMES[index % len(FIELD_NAMES)]
        spud_date = random_spud_date()
        first_production_date = spud_date + timedelta(days=random.randint(180, 540))
        well_type = random.choices(WELL_TYPES, weights=(0.45, 0.15, 0.3, 0.1), k=1)[0]

        wells.append(
            {
                "well_name": f"{field_prefixes[field_name]}-{index + 1:03d}",
                "field_name": field_name,
                "operator": random.choice(OPERATORS),
                "well_type": well_type,
                "status": random.choice(WELL_STATUSES),
                "latitude": round(random.uniform(4.0, 6.5), 6),
                "longitude": round(random.uniform(112.0, 115.0), 6),
                "depth_m": round(random.uniform(1_500, 4_500), 1),
                "spud_date": spud_date,
                "first_production_date": first_production_date,
                "initial_oil_bbl": random.uniform(300, 800),
                "initial_gor": random.uniform(550, 1_350),
                "decline_rate": random.uniform(0.00045, 0.0011),
                "base_pressure": random.uniform(2_000, 4_000),
                "base_temperature": random.uniform(70, 105),
            }
        )

    return wells


def make_maintenance_events(well_id: int) -> list[dict]:
    events = []
    event_count = random.randint(3, 8)
    total_days = (END_DATE - START_DATE).days
    event_dates = sorted(
        START_DATE + timedelta(days=random.randint(15, total_days - 15))
        for _ in range(event_count)
    )

    for event_date in event_dates:
        event_type = random.choice(EVENT_TYPES)
        is_unplanned = random.random() < 0.30
        duration_hrs = round(random.uniform(4, 72), 1)
        cost_usd = round(random.uniform(5_000, 150_000), 2)
        technician = FAKER.name()
        description = (
            f"{'Unplanned' if is_unplanned else 'Planned'} {event_type} activity "
            "completed for production reliability and integrity assurance."
        )
        events.append(
            {
                "well_id": well_id,
                "event_date": event_date + timedelta(hours=random.randint(0, 23)),
                "event_type": event_type,
                "description": description,
                "cost_usd": cost_usd,
                "duration_hrs": duration_hrs,
                "technician": technician,
                "is_unplanned": is_unplanned,
            }
        )

    return events


def production_for_day(well: dict, day_index: int) -> dict:
    well_type = well["well_type"]
    decline_factor = math.exp(-well["decline_rate"] * day_index)
    downtime_hrs = round(random.uniform(2, 12), 1) if random.random() < 0.05 else 0.0
    uptime_factor = (24 - downtime_hrs) / 24
    water_cut_pct = clamp(day_index / 1_095 * random.uniform(45, 60), 0, 60)

    oil_bbl = well["initial_oil_bbl"] * decline_factor * uptime_factor
    if well_type == "gas":
        oil_bbl *= random.uniform(0.05, 0.18)
    elif well_type == "water_injection":
        oil_bbl *= random.uniform(0.0, 0.03)

    oil_bbl = max(0, oil_bbl + random.gauss(0, 12))
    water_bbl = oil_bbl * water_cut_pct / max(1, 100 - water_cut_pct)
    gor = well["initial_gor"] * random.uniform(0.85, 1.20)
    gas_mcf = oil_bbl * gor / 1_000

    if well_type == "gas":
        gas_mcf *= random.uniform(3.0, 6.0)
    elif well_type == "water_injection":
        water_bbl = random.uniform(500, 1_800)
        gas_mcf *= random.uniform(0.0, 0.1)

    tubing_pressure = clamp(
        well["base_pressure"] * (0.72 + 0.20 * decline_factor) - downtime_hrs * 18 + random.gauss(0, 70),
        800,
        4_500,
    )
    casing_pressure = clamp(tubing_pressure * random.uniform(1.05, 1.35) + random.gauss(0, 60), 1_000, 5_000)
    choke_size = round(random.choice((16, 20, 24, 28, 32, 36, 40)) + random.uniform(-1.0, 1.0), 1)

    return {
        "oil_bbl": round(oil_bbl, 2),
        "gas_mcf": round(max(0, gas_mcf), 2),
        "water_bbl": round(max(0, water_bbl), 2),
        "downtime_hrs": downtime_hrs,
        "choke_size_mm": choke_size,
        "tubing_pressure_psi": round(tubing_pressure, 2),
        "casing_pressure_psi": round(casing_pressure, 2),
        "gor": round(gor, 2),
        "water_cut_pct": round(water_cut_pct, 2),
    }


def is_near_maintenance(recorded_at: datetime, event_dates: list[datetime]) -> bool:
    return any(timedelta(0) <= event_date - recorded_at <= timedelta(days=3) for event_date in event_dates)


def insert_wells(cursor, wells: list[dict]) -> list[int]:
    rows = [
        (
            well["well_name"],
            well["field_name"],
            well["operator"],
            well["well_type"],
            well["status"],
            well["latitude"],
            well["longitude"],
            well["depth_m"],
            well["spud_date"],
            well["first_production_date"],
        )
        for well in wells
    ]
    print(f"Inserting {len(rows)} wells...")
    execute_values(
        cursor,
        """
        INSERT INTO wells (
            well_name, field_name, operator, well_type, status, latitude, longitude,
            depth_m, spud_date, first_production_date
        )
        VALUES %s
        RETURNING id
        """,
        rows,
    )
    well_ids = [row[0] for row in cursor.fetchall()]
    print("Wells inserted.")
    return well_ids


def insert_maintenance_events(cursor, well_ids: list[int]) -> dict[int, list[datetime]]:
    event_dates_by_well: dict[int, list[datetime]] = {}
    rows = []

    for well_id in well_ids:
        events = make_maintenance_events(well_id)
        event_dates_by_well[well_id] = [event["event_date"] for event in events]
        rows.extend(
            (
                event["well_id"],
                event["event_date"],
                event["event_type"],
                event["description"],
                event["cost_usd"],
                event["duration_hrs"],
                event["technician"],
                event["is_unplanned"],
            )
            for event in events
        )

    print(f"Inserting {len(rows)} maintenance events...")
    execute_values(
        cursor,
        """
        INSERT INTO maintenance_events (
            well_id, event_date, event_type, description, cost_usd,
            duration_hrs, technician, is_unplanned
        )
        VALUES %s
        """,
        rows,
    )
    print("Maintenance events inserted.")
    return event_dates_by_well


def insert_production_and_sensors(cursor, wells: list[dict], well_ids: list[int], event_dates_by_well: dict[int, list[datetime]]):
    production_rows = []
    sensor_rows = []
    production_count = 0
    sensor_count = 0
    total_days = (END_DATE - START_DATE).days + 1

    print(f"Generating and inserting production logs for {total_days} days per well...")
    print("Generating and inserting 6-hour sensor readings for the same period...")

    for well, well_id in zip(wells, well_ids):
        for day_index, log_date in enumerate(daterange(START_DATE, END_DATE)):
            production = production_for_day(well, day_index)
            production_rows.append(
                (
                    well_id,
                    log_date,
                    production["oil_bbl"],
                    production["gas_mcf"],
                    production["water_bbl"],
                    production["downtime_hrs"],
                    production["choke_size_mm"],
                    production["tubing_pressure_psi"],
                    production["casing_pressure_psi"],
                )
            )
            production_count += 1

            if len(production_rows) >= BATCH_SIZE:
                flush_production(cursor, production_rows)
                production_rows.clear()
                print(f"  Inserted {production_count:,} production logs...")

            for hour in (0, 6, 12, 18):
                recorded_at = log_date + timedelta(hours=hour)
                anomaly_boost = 1.8 if is_near_maintenance(recorded_at, event_dates_by_well[well_id]) else 1.0
                flow_rate = max(0, production["oil_bbl"] + production["water_bbl"]) * random.uniform(0.92, 1.08)
                pressure = clamp(production["tubing_pressure_psi"] * random.uniform(0.95, 1.08), 1_500, 4_500)
                temperature = clamp(well["base_temperature"] + random.gauss(0, 4), 60, 120)
                vibration = clamp(random.uniform(1.2, 4.5) * anomaly_boost + random.gauss(0, 0.25), 0.2, 12)

                sensor_rows.append(
                    (
                        well_id,
                        recorded_at,
                        round(temperature, 2),
                        round(pressure, 2),
                        round(flow_rate, 2),
                        production["gor"],
                        production["water_cut_pct"],
                        round(vibration, 2),
                    )
                )
                sensor_count += 1

                if len(sensor_rows) >= BATCH_SIZE:
                    flush_sensors(cursor, sensor_rows)
                    sensor_rows.clear()
                    print(f"  Inserted {sensor_count:,} sensor readings...")

    if production_rows:
        flush_production(cursor, production_rows)
        print(f"  Inserted {production_count:,} production logs.")

    if sensor_rows:
        flush_sensors(cursor, sensor_rows)
        print(f"  Inserted {sensor_count:,} sensor readings.")


def flush_production(cursor, rows: list[tuple]):
    execute_values(
        cursor,
        """
        INSERT INTO production_logs (
            well_id, log_date, oil_bbl, gas_mcf, water_bbl, downtime_hrs,
            choke_size_mm, tubing_pressure_psi, casing_pressure_psi
        )
        VALUES %s
        """,
        rows,
        page_size=BATCH_SIZE,
    )


def flush_sensors(cursor, rows: list[tuple]):
    execute_values(
        cursor,
        """
        INSERT INTO sensor_readings (
            well_id, recorded_at, temperature_c, pressure_psi, flow_rate_bpd,
            gas_oil_ratio, water_cut_pct, vibration_mms
        )
        VALUES %s
        """,
        rows,
        page_size=BATCH_SIZE,
    )


def main():
    wells = make_wells()

    print("Connecting to PostgreSQL database...")
    with psycopg2.connect(DB_URL) as connection:
        with connection.cursor() as cursor:
            well_ids = insert_wells(cursor, wells)
            event_dates_by_well = insert_maintenance_events(cursor, well_ids)
            insert_production_and_sensors(cursor, wells, well_ids, event_dates_by_well)

        connection.commit()

    print("Seed complete.")


if __name__ == "__main__":
    main()
