# backend/Calendar/calendar_auth.py
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()  # .env-Datei einlesen


SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_abs_path(path_from_env):
    """Convert a relative path from the environment variable to an absolute path."""
    if not os.path.isabs(path_from_env):
        return os.path.abspath(os.path.join(BASE_DIR, '..', path_from_env))
    return path_from_env

token_path = get_abs_path(os.getenv("GOOGLE_CALENDAR_TOKEN_PATH"))
client_secret_path = get_abs_path(os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET_PATH"))

def get_credentials():
    """Holt die Google Calendar API Anmeldeinformationen."""
    creds = None

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        creds = flow.run_local_server(port=8080)  # Browser sollte sich öffnen
        # Ordner ggf. erstellen, falls nicht vorhanden
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    return creds