# API Data Pipeline — Weather Snapshots, Change Detection & Reports

A small, production-shaped Python data pipeline that polls a public REST API
(**Open-Meteo**, free — no API key needed), stores timestamped snapshots in
**SQLite**, detects meaningful changes between runs, and produces **CSV
exports** and a **plain-text summary report**.

The same skeleton adapts to any JSON API — prices, stocks, crypto, air
quality, internal metrics: swap the client, keep storage/changes/reporting.

## What it does

1. **Fetch** — pulls current weather (temperature, feels-like, humidity,
   precipitation, wind, pressure, weather code) for a configurable list of
   locations.
2. **Store** — appends each reading as a timestamped row in SQLite
   (`data/weather.db`), so history accumulates run after run.
3. **Detect changes** — compares the two most recent snapshots per location
   and reports only meaningful deltas (per-field thresholds, e.g. pressure
   shifts under 0.3 hPa are ignored as noise).
4. **Report & export** — writes a human-readable summary (`data/report.txt`)
   and a full CSV dump (`data/snapshots.csv`) for spreadsheets/BI tools.

## Project layout

```
api-data-pipeline/
├── run.py                  # CLI entry point
├── requirements.txt
├── pipeline/
│   ├── config.py           # locations + default paths
│   ├── client.py           # Open-Meteo HTTP client + payload normalization
│   ├── storage.py          # SQLite schema and queries
│   ├── changes.py          # change detection between snapshots
│   ├── report.py           # text report builder + CSV export
│   └── cli.py              # fetch / changes / report / export commands
├── tests/
│   ├── fixtures/           # recorded API responses (tests run offline)
│   └── test_pipeline.py
└── data/                   # generated db / report / csv (gitignored)
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# 1. Fetch current weather for all configured locations
python run.py fetch

# 2. See what changed since the previous run
python run.py changes

# 3. Generate the summary report (data/report.txt)
python run.py report

# 4. Export every stored snapshot to CSV (data/snapshots.csv)
python run.py export

# Options: --db PATH (any command), --out PATH (report/export)
```

Locations are edited in `pipeline/config.py` — name + latitude/longitude.

## Sample output

`python run.py fetch`

```
[Hanoi] snapshot #1: 31.8°C, humidity 62%, wind 4.1 km/h
[Ho Chi Minh City] snapshot #2: 31.6°C, humidity 73%, wind 2.3 km/h
[Da Nang] snapshot #3: 30.9°C, humidity 60%, wind 8.0 km/h
[Singapore] snapshot #4: 33.2°C, humidity 53%, wind 8.7 km/h
```

`python run.py report` (excerpt)

```
============================================================
WEATHER DATA PIPELINE — SUMMARY REPORT
============================================================
Snapshots stored: 4 across 4 location(s)

[Hanoi]  (observed 2026-10-23T12:45, fetched 2026-10-23T05:49:12+00:00)
  Now: 31.8°C (feels 38.4°C), humidity 62.0%, wind 4.1 km/h, pressure 1008.0 hPa, rain 0.0 mm
```

`python run.py changes` (after later runs, excerpt)

```
[Hanoi]
  - Temperature: 28.4°C -> 31.9°C (▲ 3.5°C)
  - Humidity: 71% -> 63% (▼ 8.0%)
  - Precipitation: 0.0mm -> 0.4mm (▲ 0.4mm)
```

## Tests

Tests are fully offline — they replay recorded API responses from
`tests/fixtures/` and cover normalization, storage round-trips, change
detection, report contents, and CSV export.

```bash
python -m pytest tests/ -q
# 9 passed
```

## Ideas for extension

- Schedule `fetch` with cron/systemd and alert on changes (email/Telegram).
- Add locations or switch the client to another API (CoinGecko, air quality).
- Feed `snapshots.csv` into a dashboard (Metabase, Grafana, Excel).
