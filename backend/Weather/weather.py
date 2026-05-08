"""OpenWeather One-Call API client (hourly + daily forecasts)."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings
from logging_config import get_logger

logger = get_logger(__name__)

_session = requests.Session()
_session.headers.update({"User-Agent": "home-info-center/2.0"})
_DEFAULT_TIMEOUT = 20

_BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"


class WeatherConfigError(RuntimeError):
    """Weather API configuration is incomplete."""


@retry(
    retry=retry_if_exception_type((requests.RequestException,)),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _fetch(exclude: str) -> dict:
    if not settings.openweather_api_key:
        raise WeatherConfigError("OPENWEATHER_API_KEY not set")
    params = {
        "lat": settings.weather_location_lat,
        "lon": settings.weather_location_lon,
        "exclude": exclude,
        "units": "metric",
        "lang": "de",
        "appid": settings.openweather_api_key,
    }
    try:
        response = _session.get(_BASE_URL, params=params, timeout=_DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        raise ConnectionError(f"Weather API timeout: {e}") from e
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Weather API connection error: {e}") from e
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Weather API HTTP error: {e}") from e
    return response.json()


def get_hourly_forecast() -> dict[str, list[dict]]:
    """Return hourly forecast for the next 6 hours, grouped by day (YYYY-MM-DD)."""
    data = _fetch(exclude="current,minutely,daily,alerts")
    tz = ZoneInfo(settings.timezone)
    now = datetime.now(tz)
    end = now + timedelta(hours=6)

    forecast_by_day: dict[str, list[dict]] = defaultdict(list)
    for hour in data.get("hourly", []):
        dt = datetime.fromtimestamp(hour["dt"], tz)
        if not (now <= dt <= end):
            continue
        day_iso = dt.strftime("%Y-%m-%d")
        forecast_by_day[day_iso].append(
            {
                "zeit": dt.strftime("%H:%M"),
                "beschreibung": hour["weather"][0]["description"].capitalize(),
                "temperatur": hour["temp"],
                "icon": f"https://openweathermap.org/img/wn/{hour['weather'][0]['icon']}@2x.png",
            }
        )

    return dict(sorted(forecast_by_day.items()))


def get_daily_forecast() -> list[dict]:
    """Return daily forecast for the next 4 days."""
    data = _fetch(exclude="current,minutely,hourly,alerts")
    tz = ZoneInfo(settings.timezone)
    forecast: list[dict] = []
    for day in data.get("daily", [])[:4]:
        dt = datetime.fromtimestamp(day["dt"], tz)
        forecast.append(
            {
                "tag": dt.strftime("%Y-%m-%d"),
                "beschreibung": day["weather"][0]["description"].capitalize(),
                "temp_min": round(day["temp"]["min"]),
                "temp_max": round(day["temp"]["max"]),
                "icon": f"https://openweathermap.org/img/wn/{day['weather'][0]['icon']}@4x.png",
            }
        )
    return forecast
