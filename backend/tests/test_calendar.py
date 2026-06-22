"""Tests for Google Calendar event aggregation/grouping."""

from __future__ import annotations

from datetime import datetime

from Calendar import get_events
from Calendar.get_events import _to_local_naive, get_all_events


def test_to_local_naive_strips_timezone():
    dt = _to_local_naive("2026-06-22T10:00:00+00:00")
    assert dt.tzinfo is None
    # Europe/Berlin is UTC+2 in summer
    assert dt.hour == 12


def test_get_all_events_groups_by_day(monkeypatch):
    monkeypatch.setattr(
        get_events,
        "load_calendar_ids",
        lambda: [{"name": "Familie", "id": "cal-1"}],
    )

    events = [
        {
            "start": datetime(2026, 6, 22, 14, 0),
            "end": datetime(2026, 6, 22, 15, 0),
            "title": "Meeting",
            "all_day": False,
        },
        {
            "start": datetime(2026, 6, 23, 0, 0),
            "end": datetime(2026, 6, 24, 0, 0),
            "title": "Urlaub",
            "all_day": True,
        },
    ]
    monkeypatch.setattr(get_events, "get_upcoming_events", lambda *_a, **_kw: events)

    grouped = get_all_events()
    assert set(grouped.keys()) == {"2026-06-22", "2026-06-23"}

    meeting = grouped["2026-06-22"][0]
    assert meeting["title"] == "Meeting"
    assert meeting["start_time"] == "14:00"
    assert meeting["end_time"] == "15:00"
    assert meeting["calendar"] == "Familie"

    holiday = grouped["2026-06-23"][0]
    assert holiday["start_time"] == "Ganztägig"
    assert holiday["end_time"] == ""


def test_get_all_events_skips_failing_calendar(monkeypatch):
    monkeypatch.setattr(
        get_events,
        "load_calendar_ids",
        lambda: [{"name": "Broken", "id": "cal-x"}],
    )

    def boom(*_a, **_kw):
        raise ConnectionError("offline")

    monkeypatch.setattr(get_events, "get_upcoming_events", boom)

    assert get_all_events() == {}


def test_multiday_event_shows_end_date(monkeypatch):
    monkeypatch.setattr(
        get_events,
        "load_calendar_ids",
        lambda: [{"name": "Arbeit", "id": "cal-1"}],
    )
    events = [
        {
            "start": datetime(2026, 6, 22, 9, 0),
            "end": datetime(2026, 6, 23, 17, 0),
            "title": "Konferenz",
            "all_day": False,
        }
    ]
    monkeypatch.setattr(get_events, "get_upcoming_events", lambda *_a, **_kw: events)

    grouped = get_all_events()
    entry = grouped["2026-06-22"][0]
    assert entry["start_time"] == "09:00"
    assert entry["end_time"] == "23.06.2026 17:00"
