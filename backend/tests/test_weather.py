"""Tests for the OpenWeather client parsing/grouping logic."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import settings
from Weather import weather


def _unix(dt: datetime) -> int:
    return int(dt.timestamp())


def test_hourly_forecast_groups_and_filters(monkeypatch):
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)

    payload = {
        "hourly": [
            {
                "dt": _unix(now + timedelta(hours=1)),
                "weather": [{"description": "klarer himmel", "icon": "01d"}],
                "temp": 20.5,
            },
            {
                "dt": _unix(now + timedelta(hours=2)),
                "weather": [{"description": "leichter regen", "icon": "10d"}],
                "temp": 18.0,
            },
            {
                # outside the 6h window -> must be dropped
                "dt": _unix(now + timedelta(hours=10)),
                "weather": [{"description": "bewölkt", "icon": "03d"}],
                "temp": 15.0,
            },
        ]
    }
    monkeypatch.setattr(weather, "_fetch", lambda **_: payload)

    result = weather.get_hourly_forecast()
    all_entries = [item for entries in result.values() for item in entries]
    assert len(all_entries) == 2
    first = all_entries[0]
    assert first["beschreibung"] == "Klarer himmel"  # capitalised
    assert first["temperatur"] == 20.5
    assert first["icon"].endswith("01d@2x.png")


def test_daily_forecast_limited_to_four_days(monkeypatch):
    tz = ZoneInfo(settings.timezone)
    base = datetime.now(tz)

    payload = {
        "daily": [
            {
                "dt": _unix(base + timedelta(days=i)),
                "weather": [{"description": "sonnig", "icon": "01d"}],
                "temp": {"min": 5.4, "max": 12.6},
            }
            for i in range(7)
        ]
    }
    monkeypatch.setattr(weather, "_fetch", lambda **_: payload)

    result = weather.get_daily_forecast()
    assert len(result) == 4
    assert result[0]["beschreibung"] == "Sonnig"
    assert result[0]["temp_min"] == 5
    assert result[0]["temp_max"] == 13
    assert result[0]["icon"].endswith("01d@4x.png")


def test_hourly_forecast_handles_empty_payload(monkeypatch):
    monkeypatch.setattr(weather, "_fetch", lambda **_: {})
    assert weather.get_hourly_forecast() == {}
