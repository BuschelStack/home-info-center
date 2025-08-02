# --- Google Calendar Events Fetcher ---
# Diese Datei ist Teil des Dashboards für die Familie.

import locale
import socket
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo  # ab Python 3.9
from collections import defaultdict
import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import TransportError
from Calendar.calendar_auth import get_credentials
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

load_dotenv()  # .env-Datei einlesen

LOCAL_TZ = ZoneInfo(os.getenv("TIMEZONE", "Europe/Berlin"))
calendar_config_path = os.getenv("GOOGLE_CALENDAR_CONFIG_PATH")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if not os.path.isabs(calendar_config_path):
    calendar_config_path = os.path.join(BASE_DIR, '..', calendar_config_path)
    calendar_config_path = os.path.abspath(calendar_config_path)

# Deutsche Wochentage und Monatsnamen
try:
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'deu')
    except locale.Error:
        print("⚠ Achtung: Deutsche Locale konnte nicht gesetzt werden.")

def internet_verfügbar():
    """Prüft, ob Internetverbindung durch Namensauflösung verfügbar ist."""
    try:
        # Set a timeout for socket operations to avoid hanging
        socket.setdefaulttimeout(5)
        socket.gethostbyname("google.com")
        return True
    except socket.error:
        return False
    finally:
        # Reset timeout to default
        socket.setdefaulttimeout(None)

def load_calendar_ids(json_path=calendar_config_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Die Konfigurationsdatei '{json_path}' wurde nicht gefunden.")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def format_event_start(start_str):
    try:
        dt = datetime.fromisoformat(start_str)
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        try:
            dt = datetime.strptime(start_str, "%Y-%m-%d")
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            return start_str

@retry(
    retry=retry_if_exception_type((TransportError, HttpError, ConnectionError)),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(5),
    reraise=True
)
def get_upcoming_events(calendar_id, n=10):
    """Fetch upcoming events from a specific Google Calendar, mit Retry."""
    if not calendar_id:
        raise ValueError("Kein Kalender-ID angegeben")  

    if not internet_verfügbar():
        raise ConnectionError("Keine Internetverbindung verfügbar")

    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    events_result = service.events().list(
        calendarId=calendar_id, timeMin=now,
        maxResults=n, singleEvents=True,
        orderBy='startTime').execute()

    events = events_result.get('items', [])
    formatted_events = []

    for e in events:
        start_raw = e['start'].get('dateTime', e['start'].get('date'))
        end_raw = e['end'].get('dateTime', e['end'].get('date'))
        summary = e.get('summary', 'Kein Titel')
        is_all_day = 'date' in e['start']

        if is_all_day:
            start_dt = datetime.strptime(start_raw, "%Y-%m-%d")
            end_dt = datetime.strptime(end_raw, "%Y-%m-%d")
        else:
            start_dt = datetime.fromisoformat(start_raw)
            if start_dt.tzinfo:
                start_dt = start_dt.astimezone(LOCAL_TZ).replace(tzinfo=None)
            else:
                start_dt = start_dt.replace(tzinfo=None)

            end_dt = datetime.fromisoformat(end_raw)
            if end_dt.tzinfo:
                end_dt = end_dt.astimezone(LOCAL_TZ).replace(tzinfo=None)
            else:
                end_dt = end_dt.replace(tzinfo=None)

        formatted_events.append({
            'start': start_dt,
            'end': end_dt,
            'title': summary,
            'all_day': is_all_day
        })

    return formatted_events

# RAM-basierter Fallback-Cache (global)
_cached_events = None
_last_success_timestamp = None
_CACHE_MAX_AGE = timedelta(hours=1)  # 1 Stunde

def get_all_events(max_total=10, json_path=calendar_config_path):
    global _cached_events, _last_success_timestamp

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Die Konfigurationsdatei '{json_path}' wurde nicht gefunden.")
    
    calendars = load_calendar_ids(json_path)
    raw_events = []

    try:
        for cal in calendars:
            cal_name = cal['name']
            cal_id = cal['id']
            try:
                events = get_upcoming_events(cal_id, n=50)
            except Exception as e:
                print(f"⚠ Fehler beim Abrufen von Kalender '{cal_name}': {e}")
                continue
            for e in events:
                raw_events.append({
                    'calendar': cal_name,
                    'start': e['start'],
                    'end': e['end'],
                    'title': e['title'],
                    'all_day': e['all_day']
                })

        raw_events.sort(key=lambda e: e['start'])

        if len(raw_events) <= max_total:
            limited_events = raw_events
        else:
            limited_events = raw_events[:max_total]
            last_date = limited_events[-1]['start'].date()
            for e in raw_events[max_total:]:
                if e['start'].date() == last_date:
                    limited_events.append(e)
                else:
                    break

        grouped = defaultdict(list)
        for e in limited_events:
            date_str = e['start'].strftime("%Y-%m-%d")
            if e['all_day']:
                start_time = "Ganztägig"
                end_time = ""
            else:
                start_time = e['start'].strftime("%H:%M")
                end_time = (
                    e['end'].strftime("%H:%M")
                    if e['start'].date() == e['end'].date()
                    else e['end'].strftime("%d.%m.%Y %H:%M")
                )

            grouped[date_str].append({
                'start_time': start_time,
                'end_time': end_time,
                'title': e['title'],
                'calendar': e['calendar']
            })

        _cached_events = grouped
        _last_success_timestamp = datetime.now()
        return grouped

    except Exception as err:
        print(f"⚠ Fehler beim Abrufen aller Kalenderdaten: {err}")

        if _cached_events is not None and _last_success_timestamp is not None:
            age = datetime.now() - _last_success_timestamp
            if age <= _CACHE_MAX_AGE:
                print(f"📁 Nutze Fallback-Cache aus dem Arbeitsspeicher (Alter: {age})")
                return _cached_events
            else:
                print(f"⚠ RAM-Cache ist älter als 1 Stunde ({age}) – wird verworfen.")

        raise RuntimeError("Keine aktuellen Kalenderdaten verfügbar und kein gültiger Cache vorhanden.") from err
