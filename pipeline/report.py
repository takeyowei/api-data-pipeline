"""Plain-text summary reports and CSV export."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from . import storage
from .changes import detect_changes, format_change

CSV_FIELDS = ["id"] + storage.COLUMNS


def export_csv(conn: sqlite3.Connection, out_path: str | Path) -> int:
    """Write every snapshot to CSV. Returns the number of rows written."""
    rows = storage.all_snapshots(conn)
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in CSV_FIELDS})
    return len(rows)


def build_report(conn: sqlite3.Connection) -> str:
    """Build a plain-text report: latest snapshot per location + recent changes."""
    lines = ["=" * 60, "WEATHER DATA PIPELINE — SUMMARY REPORT", "=" * 60]
    locs = storage.locations(conn)
    if not locs:
        lines.append("No snapshots stored yet. Run a fetch first.")
        return "\n".join(lines) + "\n"

    total = conn.execute("SELECT COUNT(*) AS n FROM snapshots").fetchone()["n"]
    lines.append(f"Snapshots stored: {total} across {len(locs)} location(s)")
    lines.append("")

    for loc in locs:
        latest_two = storage.latest_snapshots(conn, loc, limit=2)
        current = latest_two[0]
        lines.append(f"[{loc}]  (observed {current['observed_at']}, fetched {current['fetched_at']})")
        lines.append(
            f"  Now: {current['temperature_c']}°C (feels {current['apparent_c']}°C), "
            f"humidity {current['humidity_pct']}%, wind {current['wind_kmh']} km/h, "
            f"pressure {current['pressure_hpa']} hPa, rain {current['precipitation_mm']} mm"
        )
        if len(latest_two) == 2:
            changes = detect_changes(latest_two[1], latest_two[0])
            if changes:
                lines.append("  Changes since previous snapshot:")
                for change in changes:
                    lines.append(f"    - {format_change(change)}")
            else:
                lines.append("  No significant changes since previous snapshot.")
        else:
            lines.append("  Only one snapshot so far — no comparison available.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
