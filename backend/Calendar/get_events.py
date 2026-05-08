"""Google Calendar event aggregation."""

from __future__ import annotations

import json
import locale
import socket
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from google.auth.exceptions import TransportError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from Calendar.calendar_auth import get_credentials
from config import settings
from logging_config import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)

LOCAL_TZ = ZoneInfo(settings.timezone)

# Best-effort German locale (for `%A`, `%B`); fall back silently.
for _candidate in ("de_DE.UTF-8", "deu", "German"):
    try:
        locale.setlocale(locale.LC_TIME, _candidate)
        break
    except locale.Error:
        continue
else:
    logger.warning("German locale not available")


def _internet_available() -> bool:
    """Quick DNS-based reachability check."""
    socket.setdefaulttimeout(5)
    try:
        socket.gethostbyname("google.com")
        return True
    except OSError:
        return False
    finally:
        socket.setdefaulttimeout(None)


def load_calendar_ids(json_path: Path | None = None) -> list[dict]:
    path = json_path or settings.calendar_config_path
    if not path.exists():
        raise FileNotFoundError(f"Calendar config not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@retry(
    retry=retry_if_exception_type((TransportError, HttpError, ConnectionError)),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def get_upcoming_events(calendar_id: str, n: int = 10) -> list[dict]:
    """Fetch upcoming events from one Google Calendar (with retries)."""
    if not calendar_id:
        raise ValueError("Calendar ID required")
    if not _internet_available():
        raise ConnectionError("No internet connection")

    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now_utc,
            maxResults=n,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events: list[dict] = []
    for e in result.get("items", []):
        start_raw = e["start"].get("dateTime", e["start"].get("date"))
        end_raw = e["end"].get("dateTime", e["end"].get("date"))
        is_all_day = "date" in e["start"]

        if is_all_day:
            start_dt = datetime.strptime(start_raw, "%Y-%m-%d")
            end_dt = datetime.strptime(end_raw, "%Y-%m-%d")
        else:
            start_dt = _to_local_naive(start_raw)
            end_dt = _to_local_naive(end_raw)

        events.append(
            {
                "start": start_dt,
                "end": end_dt,
                "title": e.get("summary", "Kein Titel"),
                "all_day": is_all_day,
            }
        )
    return events


def _to_local_naive(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo:
        dt = dt.astimezone(LOCAL_TZ).replace(tzinfo=None)
    return dt


# --- RAM fallback cache (1h) ---
_cached_events: dict | None = None
_last_success: datetime | None = None
_CACHE_MAX_AGE = timedelta(hours=1)


def get_all_events(max_total: int = 10) -> dict[str, list[dict]]:
    """Aggregate events from all configured calendars, grouped by ISO date."""
    global _cached_events, _last_success

    calendars = load_calendar_ids()
    raw_events: list[dict] = []

    try:
        for cal in calendars:
            cal_name = cal.get("name", "?")
            cal_id = cal.get("id")
            try:
                events = get_upcoming_events(cal_id, n=50)
            except Exception as e:
                logger.warning("Calendar '%s' fetch failed: %s", cal_name, e)
                continue
            for ev in events:
                raw_events.append({**ev, "calendar": cal_name})

        raw_events.sort(key=lambda e: e["start"])

        if len(raw_events) <= max_total:
            limited = raw_events
        else:
            limited = raw_events[:max_total]
            last_date = limited[-1]["start"].date()
            for ev in raw_events[max_total:]:
                if ev["start"].date() == last_date:
                    limited.append(ev)
                else:
                    break

        grouped: dict[str, list[dict]] = defaultdict(list)
        for ev in limited:
            date_key = ev["start"].strftime("%Y-%m-%d")
            if ev["all_day"]:
                start_time, end_time = "Ganztägig", ""
            else:
                start_time = ev["start"].strftime("%H:%M")
                end_time = (
                    ev["end"].strftime("%H:%M")
                    if ev["start"].date() == ev["end"].date()
                    else ev["end"].strftime("%d.%m.%Y %H:%M")
                )
            grouped[date_key].append(
                {
                    "start_time": start_time,
                    "end_time": end_time,
                    "title": ev["title"],
                    "calendar": ev["calendar"],
                }
            )

        _cached_events = dict(grouped)
        _last_success = datetime.now()
        return _cached_events

    except Exception as err:
        logger.error("Calendar aggregation failed: %s", err)
        if (
            _cached_events is not None
            and _last_success is not None
            and (datetime.now() - _last_success) <= _CACHE_MAX_AGE
        ):
            logger.info("Returning cached calendar events")
            return _cached_events
        raise
