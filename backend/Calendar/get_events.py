# --- Google Calendar Events Fetcher ---
# Diese Datei ist Teil des Dashboards für die Familie.
import locale
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # ab Python 3.9
from collections import defaultdict
import os
import json
from googleapiclient.discovery import build
from Calendar.calendar_auth import get_credentials
from dotenv import load_dotenv

load_dotenv()  # .env-Datei einlesen

# Lokale Zeitzone
LOCAL_TZ = ZoneInfo(os.getenv("TIMEZONE", "Europe/Berlin"))
# Konfigurationsdatei für Google Kalender
calendar_config_path = os.getenv("GOOGLE_CALENDAR_CONFIG_PATH")

# Ermittle das Basisverzeichnis (z. B. für Docker und lokal)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Gehe ggf. ein Verzeichnis nach oben, falls nötig:
# BASE_DIR = os.path.dirname(BASE_DIR)

# Absoluten Pfad bauen, falls relativer Pfad angegeben ist
if not os.path.isabs(calendar_config_path):
    calendar_config_path = os.path.join(BASE_DIR, '..', calendar_config_path)
    calendar_config_path = os.path.abspath(calendar_config_path)


# Deutsche Wochentage und Monatsnamen
try:
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')  # Linux, macOS
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'deu')  # Windows (manchmal)
    except locale.Error:
        print("⚠ Achtung: Deutsche Locale konnte nicht gesetzt werden.")


def load_calendar_ids(json_path=calendar_config_path):
    """Load calendar IDs from a JSON configuration file."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Die Konfigurationsdatei '{json_path}' wurde nicht gefunden.")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def format_event_start(start_str):
    """Format the event start time to a human-readable string."""   
    try:
        dt = datetime.fromisoformat(start_str)
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        try:
            dt = datetime.strptime(start_str, "%Y-%m-%d")
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            return start_str


def get_upcoming_events(calendar_id, n=10):
    """Fetch upcoming events from a specific Google Calendar."""
    if not calendar_id:
        raise ValueError("Kein Kalender-ID angegeben")  
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    events_result = service.events().list(  # type: ignore[attr-defined]
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

        # Startzeit
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



def get_all_events(max_total=10, json_path=calendar_config_path):
    """Fetch all upcoming events from all configured Google Calendars."""
    if not os.path.exists(json_path):   
        raise FileNotFoundError(f"Die Konfigurationsdatei '{json_path}' wurde nicht gefunden.") 
    calendars = load_calendar_ids(json_path)
    raw_events = []

    for cal in calendars:
        cal_name = cal['name']
        cal_id = cal['id']
        events = get_upcoming_events(cal_id, n=50)
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

    return grouped