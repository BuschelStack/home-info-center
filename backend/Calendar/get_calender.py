from googleapiclient.discovery import build
import datetime
from Calendar.calendar_auth import get_credentials

def get_upcoming_events(n=10):
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=n, singleEvents=True,
        orderBy='startTime').execute()

    events = events_result.get('items', [])
    return [(e['start'].get('dateTime', e['start'].get('date')), e.get('summary', 'Kein Titel')) for e in events]
