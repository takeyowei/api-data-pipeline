"""Change detection between consecutive snapshots of the same location."""

from __future__ import annotations

# field -> (label, unit, minimum absolute delta worth reporting)
TRACKED_FIELDS = {
    "temperature_c": ("Temperature", "°C", 0.1),
    "apparent_c": ("Feels like", "°C", 0.1),
    "humidity_pct": ("Humidity", "%", 1.0),
    "precipitation_mm": ("Precipitation", "mm", 0.1),
    "wind_kmh": ("Wind speed", "km/h", 0.5),
    "pressure_hpa": ("Pressure", "hPa", 0.3),
    "weather_code": ("Weather code", "", 0),
}


def detect_changes(previous: dict, current: dict) -> list[dict]:
    """Return a list of meaningful changes between two snapshot records."""
    changes = []
    for field, (label, unit, threshold) in TRACKED_FIELDS.items():
        old, new = previous.get(field), current.get(field)
        if old is None or new is None or old == new:
            continue
        delta = round(float(new) - float(old), 2)
        if abs(delta) < threshold:
            continue
        changes.append(
            {
                "field": field,
                "label": label,
                "unit": unit,
                "old": old,
                "new": new,
                "delta": delta,
            }
        )
    return changes


def format_change(change: dict) -> str:
    arrow = "▲" if change["delta"] > 0 else "▼"
    unit = change["unit"]
    return (
        f"{change['label']}: {change['old']}{unit} -> {change['new']}{unit} "
        f"({arrow} {abs(change['delta'])}{unit})"
    )
