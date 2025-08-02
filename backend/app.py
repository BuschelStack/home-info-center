# --- Backend Flask App ---
# Diese Datei ist Teil des Dashboards für die Familie.
import traceback        
import os
import time
import threading
from collections import OrderedDict
import json
from flask import Flask, Response, jsonify, send_from_directory
from dotenv import load_dotenv
from FritzBox.fritzbox_calllist import get_calls_grouped, get_sid_cached
from Calendar.get_events import get_all_events
from Weather.weather import get_hourly_forecast, get_daily_forecast

# --- .env laden ---
load_dotenv()

username = os.getenv('FRITZBOX_USERNAME')
password = os.getenv('FRITZBOX_PASSWORD')
router_ip = os.getenv("FRITZBOX_IP_ADDRESS")

interval_calendar = int(os.getenv("INTERVAL_CALENDAR", "120"))
interval_calls = int(os.getenv("INTERVAL_CALLS", "300"))
interval_weather = int(os.getenv("INTERVAL_WEATHER", "600"))

# --- Flask App ---
app = Flask(__name__)

# --- Cache ---
cache = {
    'events': {},
    'events_version': 0,
    'calls': {},
    'calls_version': 0,
    'sid': None,
    'weather_hourly': {},
    'weather_daily': [],
    'weather_version': 0,
    'last_update': 0
}
cache_lock = threading.Lock()

# --- Cache Updater Threads ---
def update_calendar_cache():
    """Update the calendar cache with events from Google Calendar."""
    while True:
        try:
            events = get_all_events()
            today_str = time.strftime('%Y-%m-%d', time.localtime())
            with cache_lock:
                # Extrahiere das Datum aus der aktuellen Version (falls gesetzt)
                last_version_date = str(cache['events_version'])[:10] if cache['events_version'] else None
                # Wenn sich Events geändert haben ODER das Datum gewechselt hat, aktualisiere Cache
                if events != cache['events'] or last_version_date != today_str:
                    cache['events'] = events
                    cache['events_version'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        except ConnectionError as e:
            print(f"⚠ Fehler beim Abrufen von Kalender: Keine Internetverbindung verfügbar - {e}")
        except (ValueError, RuntimeError) as e:
            print(f"⚠ Fehler beim Kalenderabruf: {e}")
        except Exception as e:
            print(f"⚠ Unerwarteter Fehler beim Kalenderabruf: {e}")
        time.sleep(interval_calendar)

def update_calls_cache():
    """Update the call cache with grouped calls from FritzBox."""
    while True:
        try:
            sid = get_sid_cached(username, password, router_ip)
            calls = get_calls_grouped(username, password)
            today_str = time.strftime('%Y-%m-%d', time.localtime())
            with cache_lock:
                last_version_date = str(cache['calls_version'])[:10] if cache['calls_version'] else None
                # Aktualisiere, wenn sich Calls/SID geändert haben ODER das Datum gewechselt hat
                if calls != cache['calls'] or sid != cache['sid'] or last_version_date != today_str:
                    cache['sid'] = sid
                    cache['calls'] = calls
                    cache['calls_version'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        except ConnectionError as e:
            print(f"⚠ Netzwerkfehler beim FritzBox-Abruf: {e}")
        except (ValueError, RuntimeError) as e:
            print(f"⚠ Fehler beim FritzBox-Abruf: {e}")
        except Exception as e:
            print(f"⚠ Unerwarteter Fehler beim FritzBox-Abruf: {e}")
        time.sleep(interval_calls)

def update_weather_cache():
    """Update the weather cache with hourly and daily forecasts."""
    while True:
        try:
            hourly = get_hourly_forecast()
            daily = get_daily_forecast()
            today_str = time.strftime('%Y-%m-%d', time.localtime())
            with cache_lock:
                last_version_date = str(cache['weather_version'])[:10] if cache['weather_version'] else None
                # Aktualisiere, wenn sich Wetterdaten geändert haben ODER das Datum gewechselt hat
                if hourly != cache['weather_hourly'] or daily != cache['weather_daily'] or last_version_date != today_str:
                    cache['weather_hourly'] = hourly
                    cache['weather_daily'] = daily
                    cache['weather_version'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        except ConnectionError as e:
            print(f"⚠ Netzwerkfehler beim Wetterabruf: {e}")
        except (ValueError, RuntimeError) as e:
            print(f"⚠ Fehler beim Wetterabruf: {e}")
        except Exception as e:
            print(f"⚠ Unerwarteter Fehler beim Wetterabruf: {e}")
        time.sleep(interval_weather)

# Threads starten
threading.Thread(target=update_calendar_cache, daemon=True).start()
threading.Thread(target=update_calls_cache, daemon=True).start()
threading.Thread(target=update_weather_cache, daemon=True).start()

# --- Flask Routes ---
@app.route('/')
def index():
    """Render the main index page."""   
    return send_from_directory("static", "index.html")

@app.route('/<path:path>')
def static_proxy(path):
    """Statische Dateien ausliefern (z.B. für JS, CSS, Icons)."""
    return send_from_directory('static', path)

@app.errorhandler(404)
def not_found(e):
    """Fehlerseite für nicht gefundene Ressourcen."""
    return send_from_directory("static", "index.html")


# --- Version Endpunkte ---
@app.route('/api/events-version')
def api_events_version():
    """Return the version of the cached events data.""" 
    with cache_lock:
        return jsonify({'version': cache['events_version']})

@app.route('/api/calls-version')
def api_calls_version():
    """Return the version of the cached calls data."""  
    with cache_lock:
        return jsonify({'version': cache['calls_version']})

@app.route('/api/weather-version')
def api_weather_version():
    """Return the version of the cached weather data."""
    with cache_lock:
        return jsonify({'version': cache['weather_version']})

@app.route('/api/events')
def api_events():
    """Return the cached calendar events as JSON."""
    with cache_lock:
        return jsonify({
            'data': cache['events'],
            'version': cache['events_version']
        })

@app.route('/api/calls')
def api_calls():
    """Return the cached FritzBox calls as JSON."""
    with cache_lock:
        sid = cache['sid']
        grouped_calls = cache['calls']
        version = cache['calls_version']
    try:
        serialized = OrderedDict()
        for day, calls in grouped_calls.items():
            serialized[day] = []
            for call in calls:
                c = call.copy()
                if hasattr(c['date'], 'isoformat'):
                    c['date'] = c['date'].isoformat()
                serialized[day].append(c)
        return Response(json.dumps({'sid': sid, 'calls': serialized, 'version': version}, ensure_ascii=False), mimetype='application/json')
    except (TypeError, AttributeError, KeyError) as e:
        print("Fehler in /api/calls:", e)
        traceback.print_exc()
        return Response('{"error":"Interner Serverfehler"}', status=500, mimetype='application/json')

@app.route('/api/weather')
def api_weather():
    """Return the cached weather data as JSON."""
    if not cache['weather_hourly'] or not cache['weather_daily']:
        return Response('{"error":"Wetterdaten nicht verfügbar"}', status=503, mimetype='application/json')
    with cache_lock:
        return jsonify({
            'weekly_weather': cache['weather_hourly'],
            'daily_weather': cache['weather_daily'],
            'version': cache['weather_version']
        })

@app.route('/api/config')
def get_config():
    """Return the current weather location configuration with console logging for env values."""
    lat = os.environ.get("WEATHER_LOCATION_LAT", 48.137)
    lon = os.environ.get("WEATHER_LOCATION_LON", 11.575)
    theme_day_bg = os.environ.get("THEME_DAY_BG", '#eaeaeaff')
    theme_day_text = os.environ.get("THEME_DAY_TEXT", '#222222')
    theme_evening_bg = os.environ.get("THEME_EVENING_BG", '#ffeebbff')
    theme_evening_text = os.environ.get("THEME_EVENING_TEXT", '#3a2c00')
    return jsonify({
        "lat": float(lat),
        "lon": float(lon),
        "theme_day_bg": theme_day_bg,
        "theme_day_text": theme_day_text,
        "theme_evening_bg": theme_evening_bg,
        "theme_evening_text": theme_evening_text,
    })

@app.route('/api/calendars')
def get_calendars():
    """Return the calendars configuration as JSON."""
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    return send_from_directory(config_dir, 'calendars.json', mimetype='application/json')

if __name__ == '__main__':
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=8080)
