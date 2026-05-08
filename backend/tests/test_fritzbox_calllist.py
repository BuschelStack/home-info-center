"""Tests for FritzBox calllist parsing."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from FritzBox.fritzbox_calllist import _safe_strip_sip, parse_calllist_xml


def _build_xml(entries: list[dict]) -> str:
    items = "".join(
        f"<Call>"
        f"<Type>{e.get('type', '1')}</Type>"
        f"<Date>{e['date']}</Date>"
        f"<Caller>{e.get('caller', '')}</Caller>"
        f"<CallerNumber>{e.get('caller_number', '')}</CallerNumber>"
        f"<Called>{e.get('called', '')}</Called>"
        f"<Name>{e.get('name', '')}</Name>"
        f"<Duration>{e.get('duration', '0:00')}</Duration>"
        f"<Device>{e.get('device', 'Telefon')}</Device>"
        f"<Path>{e.get('path', '')}</Path>"
        f"</Call>"
        for e in entries
    )
    return f'<?xml version="1.0"?><root>{items}</root>'


def test_parse_empty_xml_returns_empty_list():
    assert parse_calllist_xml("") == []


def test_parse_recent_call_is_kept():
    today = datetime.now().strftime("%d.%m.%y %H:%M")
    xml = _build_xml([{"date": today, "name": "Mama"}])
    out = parse_calllist_xml(xml, max_days=4)
    assert len(out) == 1
    assert out[0]["name"] == "Mama"


def test_parse_old_call_is_dropped():
    old = (datetime.now() - timedelta(days=10)).strftime("%d.%m.%y %H:%M")
    xml = _build_xml([{"date": old}])
    assert parse_calllist_xml(xml, max_days=4) == []


def test_voicemail_device_marked_as_type_11():
    today = datetime.now().strftime("%d.%m.%y %H:%M")
    xml = _build_xml([{"date": today, "device": "Anrufbeantworter"}])
    out = parse_calllist_xml(xml, max_days=4)
    assert out[0]["type"] == "11"


def test_invalid_date_is_skipped():
    xml = _build_xml([{"date": "not-a-date"}])
    assert parse_calllist_xml(xml, max_days=4) == []


def test_strip_sip_prefix():
    assert _safe_strip_sip("sip:0123") == "0123"
    assert _safe_strip_sip(None) == ""
    assert _safe_strip_sip("SIP:foo") == "foo"


def test_dates_are_timezone_aware():
    today = datetime.now().strftime("%d.%m.%y %H:%M")
    xml = _build_xml([{"date": today}])
    out = parse_calllist_xml(xml, max_days=4)
    assert out[0]["date"].tzinfo is not None
    assert isinstance(out[0]["date"].tzinfo, ZoneInfo)


def test_results_capped_at_50():
    today = datetime.now().strftime("%d.%m.%y %H:%M")
    xml = _build_xml([{"date": today} for _ in range(80)])
    assert len(parse_calllist_xml(xml, max_days=4)) == 50
