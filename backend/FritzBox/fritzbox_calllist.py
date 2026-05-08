"""FritzBox call-list client.

* Uses persistent ``requests.Session`` (TCP-Keep-Alive)
* SID cached up to 1h (avoids brute-force lockout)
* Tenacity-based retries with exponential backoff
* Pure functions – no module-level secrets
"""

from __future__ import annotations

import hashlib
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
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

_DEFAULT_TIMEOUT = 10
_SID_TTL = 3600  # 1 hour
_INVALID_SID = "0000000000000000"


@dataclass(slots=True)
class _SidCache:
    sid: str | None = None
    timestamp: float = 0.0


_sid_cache = _SidCache()


class FritzBoxAuthError(RuntimeError):
    """Authentication against FritzBox failed."""


def _md5_challenge(challenge: str, password: str) -> str:
    digest = hashlib.md5(f"{challenge}-{password}".encode("utf-16le")).hexdigest()
    return f"{challenge}-{digest}"


@retry(
    retry=retry_if_exception_type((requests.RequestException,)),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _http_get(url: str, **kwargs) -> requests.Response:
    return _session.get(url, timeout=_DEFAULT_TIMEOUT, **kwargs)


def get_sid(user: str, password: str, fritzbox_ip: str) -> str:
    """Authenticate against FritzBox and return a SID."""
    url = f"http://{fritzbox_ip}/login_sid.lua"
    try:
        response = _http_get(url)
    except requests.RequestException as e:
        raise ConnectionError(f"FritzBox unreachable: {e}") from e

    root = ET.fromstring(response.content)
    sid = root.findtext("SID") or _INVALID_SID
    if sid != _INVALID_SID:
        return sid

    challenge = root.findtext("Challenge")
    if not challenge:
        raise FritzBoxAuthError("FritzBox login_sid.lua returned no challenge")

    try:
        response = _http_get(
            url,
            params={"username": user, "response": _md5_challenge(challenge, password)},
        )
    except requests.RequestException as e:
        raise ConnectionError(f"FritzBox unreachable on auth: {e}") from e

    sid = ET.fromstring(response.content).findtext("SID") or _INVALID_SID
    if sid == _INVALID_SID:
        raise FritzBoxAuthError("FritzBox login refused (wrong credentials?)")
    return sid


def get_sid_cached(user: str, password: str, fritzbox_ip: str, ttl: int = _SID_TTL) -> str:
    """Return a cached SID; renew when older than ``ttl`` seconds."""
    now = time.time()
    if _sid_cache.sid and (now - _sid_cache.timestamp) < ttl:
        return _sid_cache.sid

    sid = get_sid(user, password, fritzbox_ip)
    _sid_cache.sid = sid
    _sid_cache.timestamp = now
    logger.info("FritzBox: new SID acquired")
    return sid


def _safe_strip_sip(number: str | None) -> str:
    if not number:
        return ""
    return number.replace("sip:", "").replace("SIP:", "").replace("SIP", "").strip(" :")


def parse_calllist_xml(xml_data: str | bytes, max_days: int | None = None) -> list[dict]:
    """Parse FritzBox calllist XML into a list of normalised call dicts."""
    if not xml_data:
        return []

    root = ET.fromstring(xml_data)
    days = max_days if max_days is not None else settings.fritzbox_calllist_days
    tz = ZoneInfo(settings.timezone)
    cutoff = datetime.now(tz) - timedelta(days=days)

    entries: list[dict] = []
    for call in root.findall("Call"):
        date_str = call.findtext("Date")
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%d.%m.%y %H:%M").replace(tzinfo=tz)
        except ValueError:
            continue
        if dt < cutoff:
            continue

        name = (call.findtext("Name") or "").strip()
        if not name:
            name = _safe_strip_sip(call.findtext("Caller"))

        device = call.findtext("Device") or ""
        calltype = "11" if device == "Anrufbeantworter" else (call.findtext("Type") or "")

        entries.append(
            {
                "type": calltype,
                "name": name,
                "caller": _safe_strip_sip(call.findtext("CallerNumber")),
                "called": _safe_strip_sip(call.findtext("Called")),
                "date": dt,
                "duration": call.findtext("Duration"),
                "audio_path": call.findtext("Path"),
            }
        )

    entries.sort(key=lambda x: x["date"], reverse=True)
    return entries[:50]


def get_calls_xml(user: str, password: str, fritzbox_ip: str) -> list[dict]:
    """Fetch and parse the FritzBox call list."""
    sid = get_sid_cached(user, password, fritzbox_ip)
    # calllist.lua is served on the TR-064 port (49000), not on the regular web UI port.
    url = f"http://{fritzbox_ip}:49000/calllist.lua?sid={sid}&max=50"
    try:
        response = _http_get(url)
    except requests.RequestException as e:
        raise ConnectionError(f"FritzBox calllist unreachable: {e}") from e

    if response.status_code != 200:
        raise RuntimeError(f"FritzBox calllist HTTP {response.status_code}")
    return parse_calllist_xml(response.content)


def get_calls_grouped(
    user: str | None = None,
    password: str | None = None,
    fritzbox_ip: str | None = None,
) -> dict[str, list[dict]]:
    """Return calls grouped by day key (``YYYY-MM-DD``)."""
    user = user or settings.fritzbox_username
    password = password or settings.fritzbox_password
    fritzbox_ip = fritzbox_ip or settings.fritzbox_ip_address
    if not (user and password and fritzbox_ip):
        raise ValueError("FritzBox credentials missing in settings")

    calls = get_calls_xml(user, password, fritzbox_ip)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for call in calls:
        day_key = call["date"].strftime("%Y-%m-%d")
        grouped[day_key].append(call)

    return dict(sorted(grouped.items(), key=lambda kv: kv[0], reverse=True))
