"""Tests run fully offline against recorded API fixtures."""

import csv
import json
from pathlib import Path

import pytest

from pipeline import storage
from pipeline.changes import detect_changes, format_change
from pipeline.client import normalize_payload
from pipeline.report import build_report, export_csv

FIXTURES = Path(__file__).parent / "fixtures"
FETCHED_1 = "2026-10-23T02:00:00+00:00"
FETCHED_2 = "2026-10-23T05:00:00+00:00"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def record(fixture: str, fetched_at: str) -> dict:
    return normalize_payload(load_fixture(fixture), location="Hanoi", fetched_at=fetched_at)


@pytest.fixture()
def conn(tmp_path):
    with storage.connect(tmp_path / "test.db") as c:
        yield c


@pytest.fixture()
def two_runs(conn):
    storage.insert_snapshot(conn, record("weather_hanoi_run1.json", FETCHED_1))
    storage.insert_snapshot(conn, record("weather_hanoi_run2.json", FETCHED_2))
    return conn


# --- client / normalization -------------------------------------------------

def test_normalize_payload_maps_fields():
    rec = record("weather_hanoi_run1.json", FETCHED_1)
    assert rec["location"] == "Hanoi"
    assert rec["fetched_at"] == FETCHED_1
    assert rec["observed_at"] == "2026-10-23T09:00"
    assert rec["temperature_c"] == 28.4
    assert rec["humidity_pct"] == 71
    assert rec["wind_kmh"] == 9.6
    assert rec["pressure_hpa"] == 1013.2
    assert rec["weather_code"] == 2


# --- storage ----------------------------------------------------------------

def test_insert_and_read_back(two_runs):
    rows = storage.all_snapshots(two_runs)
    assert len(rows) == 2
    assert rows[0]["temperature_c"] == 28.4
    assert rows[1]["temperature_c"] == 31.9
    assert storage.locations(two_runs) == ["Hanoi"]


def test_latest_snapshots_newest_first(two_runs):
    latest = storage.latest_snapshots(two_runs, "Hanoi", limit=2)
    assert [r["fetched_at"] for r in latest] == [FETCHED_2, FETCHED_1]


# --- change detection ---------------------------------------------------------

def test_detect_changes_between_runs():
    prev = record("weather_hanoi_run1.json", FETCHED_1)
    curr = record("weather_hanoi_run2.json", FETCHED_2)
    changes = {c["field"]: c for c in detect_changes(prev, curr)}
    assert changes["temperature_c"]["delta"] == pytest.approx(3.5)
    assert changes["humidity_pct"]["delta"] == pytest.approx(-8.0)
    assert changes["precipitation_mm"]["delta"] == pytest.approx(0.4)
    assert changes["weather_code"]["new"] == 61


def test_detect_changes_identical_snapshots():
    snap = record("weather_hanoi_run1.json", FETCHED_1)
    assert detect_changes(snap, snap) == []


def test_format_change_text():
    text = format_change(
        {"field": "temperature_c", "label": "Temperature", "unit": "°C",
         "old": 28.4, "new": 31.9, "delta": 3.5}
    )
    assert "Temperature" in text and "28.4" in text and "31.9" in text


# --- report & CSV -------------------------------------------------------------

def test_report_contents(two_runs):
    text = build_report(two_runs)
    assert "SUMMARY REPORT" in text
    assert "[Hanoi]" in text
    assert "31.9" in text                      # latest temperature shown
    assert "Changes since previous snapshot" in text
    assert "Temperature" in text               # change line present


def test_report_empty_db(conn):
    assert "No snapshots stored yet" in build_report(conn)


def test_csv_export(two_runs, tmp_path):
    out = tmp_path / "out.csv"
    count = export_csv(two_runs, out)
    assert count == 2
    with out.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 2
    assert rows[0]["location"] == "Hanoi"
    assert rows[1]["temperature_c"] == "31.9"
