"""Command-line interface.

Usage:
    python run.py fetch                 # fetch current weather for all locations
    python run.py changes               # show changes between the last two runs
    python run.py report                # write data/report.txt (+ print it)
    python run.py export                # write data/snapshots.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import storage
from .changes import detect_changes, format_change
from .client import WeatherClient
from .config import DEFAULT_CSV, DEFAULT_DB, DEFAULT_REPORT, LOCATIONS
from .report import build_report, export_csv


def cmd_fetch(args: argparse.Namespace) -> int:
    client = WeatherClient()
    with storage.connect(args.db) as conn:
        for loc in LOCATIONS:
            record = client.fetch_current(loc["name"], loc["latitude"], loc["longitude"])
            row_id = storage.insert_snapshot(conn, record)
            print(
                f"[{loc['name']}] snapshot #{row_id}: {record['temperature_c']}°C, "
                f"humidity {record['humidity_pct']}%, wind {record['wind_kmh']} km/h"
            )
    return 0


def cmd_changes(args: argparse.Namespace) -> int:
    with storage.connect(args.db) as conn:
        locs = storage.locations(conn)
        if not locs:
            print("No snapshots stored yet.")
            return 0
        for loc in locs:
            latest_two = storage.latest_snapshots(conn, loc, limit=2)
            print(f"[{loc}]")
            if len(latest_two) < 2:
                print("  Only one snapshot — nothing to compare yet.")
                continue
            changes = detect_changes(latest_two[1], latest_two[0])
            if not changes:
                print("  No significant changes.")
            for change in changes:
                print(f"  - {format_change(change)}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    with storage.connect(args.db) as conn:
        text = build_report(conn)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"Report written to {out}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    with storage.connect(args.db) as conn:
        count = export_csv(conn, args.out)
    print(f"Exported {count} snapshot(s) to {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weather data pipeline")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="Fetch current weather for all locations").set_defaults(func=cmd_fetch)
    sub.add_parser("changes", help="Show changes between the last two snapshots").set_defaults(func=cmd_changes)

    p_report = sub.add_parser("report", help="Generate the plain-text summary report")
    p_report.add_argument("--out", default=DEFAULT_REPORT)
    p_report.set_defaults(func=cmd_report)

    p_export = sub.add_parser("export", help="Export all snapshots to CSV")
    p_export.add_argument("--out", default=DEFAULT_CSV)
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
