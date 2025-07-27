# backend/Weather/weather.py    
import os
from datetime import datetime, timedelta
from collections import defaultdict
import requests             
from dotenv import load_dotenv
import pytz

load_dotenv()  # .env-Datei einlesen


api_key = os.getenv('OPENWEATHER_API_KEY')
lat = os.getenv('WEATHER_LOCATION_LAT')
lon = os.getenv('WEATHER_LOCATION_LON')

def get_hourly_forecast(latitude=lat, longitude=lon, api_key_param=api_key):
    """Holt die stündliche Wettervorhersage für die nächsten 6 Stunden."""  
    url = (
        f'https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}'
        f'&exclude=current,minutely,daily,alerts&units=metric&lang=de&appid={api_key_param}'
    )
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    data = response.json()

    forecast_by_day = defaultdict(list)
    timezone_str = os.getenv('TIMEZONE', 'Europe/Berlin')
    tz = pytz.timezone(timezone_str)
    jetzt = datetime.now(tz)
    ende = jetzt + timedelta(hours=6)

    for hour in data['hourly']:
        dt = datetime.fromtimestamp(hour['dt'], tz)
        if not (jetzt <= dt <= ende):
            continue  # nur die nächsten 6 Stunden behalten

        tag_iso = dt.strftime('%Y-%m-%d')
        zeit = dt.strftime('%H:%M')
        beschreibung = hour['weather'][0]['description'].capitalize()
        temperatur = hour['temp']
        icon = f"http://openweathermap.org/img/wn/{hour['weather'][0]['icon']}@2x.png"

        forecast_by_day[tag_iso].append({
            'zeit': zeit,
            'beschreibung': beschreibung,
            'temperatur': temperatur,
            'icon': icon
        })

    # Reihenfolge: Heute zuerst, dann morgen, dann Rest
    heute = datetime.now(tz).strftime('%Y-%m-%d')
    morgen = (datetime.now(tz) + timedelta(days=1)).strftime('%Y-%m-%d')
    ordered = {}
    if heute in forecast_by_day:
        ordered[heute] = forecast_by_day[heute]
    if morgen in forecast_by_day:
        ordered[morgen] = forecast_by_day[morgen]
    for tag in sorted(forecast_by_day.keys()):
        if tag != heute and tag != morgen:
            ordered[tag] = forecast_by_day[tag]
    return ordered



def get_daily_forecast(latitude=lat, longitude=lon, api_key_param=api_key):
    """Holt die tägliche Wettervorhersage für die nächsten 5 Tage."""
    url = (
        f'https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}'
        f'&exclude=current,minutely,hourly,alerts&units=metric&lang=de&appid={api_key_param}'
    )
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    data = response.json()

    forecast = []
    for day in data['daily'][:4]:
        tag = datetime.fromtimestamp(day['dt']).strftime('%A, %d. %B')
        beschreibung = day['weather'][0]['description'].capitalize()
        temp_min = round(day['temp']['min'])
        temp_max = round(day['temp']['max'])
        icon = f"http://openweathermap.org/img/wn/{day['weather'][0]['icon']}@4x.png"

        forecast.append({
            'tag': tag,
            'beschreibung': beschreibung,
            'temp_min': temp_min,
            'temp_max': temp_max,
            'icon': icon
        })

    return forecast
