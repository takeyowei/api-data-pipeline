"""SQLite storage for weather snapshots."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    location         TEXT NOT NULL,
    fetched_at       TEXT NOT NULL,
    observed_at      TEXT,
    temperature_c    REAL,
    apparent_c       REAL,
    humidity_pct     REAL,
    precipitation_mm REAL,
    wind_kmh         REAL,
    pressure_hpa     REAL,
    weather_code     INTEGER
);
CREATE INDEX IF NOT EXISTS idx_snapshots_loc_time
    ON snapshots (location, fetched_at);
"""

COLUMNS = [
    "location",
    "fetched_at",
    "observed_at",
    "temperature_c",
    "apparent_c",
    "humidity_pct",
    "precipitation_mm",
    "wind_kmh",
    "pressure_hpa",
    "weather_code",
]


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_snapshot(conn: sqlite3.Connection, record: dict) -> int:
    placeholders = ", ".join("?" for _ in COLUMNS)
    sql = f"INSERT INTO snapshots ({', '.join(COLUMNS)}) VALUES ({placeholders})"
    cur = conn.execute(sql, [record.get(c) for c in COLUMNS])
    conn.commit()
    return int(cur.lastrowid)


def all_snapshots(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM snapshots ORDER BY fetched_at, location").fetchall()
    return [dict(r) for r in rows]


def locations(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT location FROM snapshots ORDER BY location").fetchall()
    return [r["location"] for r in rows]


def latest_snapshots(conn: sqlite3.Connection, location: str, limit: int = 2) -> list[dict]:
    """Most recent snapshots for a location, newest first."""
    rows = conn.execute(
        "SELECT * FROM snapshots WHERE location = ? ORDER BY fetched_at DESC, id DESC LIMIT ?",
        (location, limit),
    ).fetchall()
    return [dict(r) for r in rows]
