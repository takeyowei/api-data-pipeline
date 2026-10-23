"""HTTP client for the Open-Meteo API (free, no API key required).

Docs: https://open-meteo.com/en/docs
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

API_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_FIELDS = ",".join(
    [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "weather_code",
        "wind_speed_10m",
        "pressure_msl",
    ]
)


def normalize_payload(payload: dict, location: str, fetched_at: str | None = None) -> dict:
    """Convert a raw Open-Meteo response into a flat snapshot record."""
    current = payload["current"]
    return {
        "location": location,
        "fetched_at": fetched_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "observed_at": current.get("time"),
        "temperature_c": current.get("temperature_2m"),
        "apparent_c": current.get("apparent_temperature"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "precipitation_mm": current.get("precipitation"),
        "wind_kmh": current.get("wind_speed_10m"),
        "pressure_hpa": current.get("pressure_msl"),
        "weather_code": current.get("weather_code"),
    }


class WeatherClient:
    def __init__(self, timeout: float = 15.0, session: requests.Session | None = None):
        self.timeout = timeout
        self.session = session or requests.Session()

    def fetch_current(self, name: str, latitude: float, longitude: float) -> dict:
        """Fetch current weather for one location and return a snapshot record."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": CURRENT_FIELDS,
            "timezone": "auto",
        }
        response = self.session.get(API_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        return normalize_payload(response.json(), location=name)
