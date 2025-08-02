"""Module for interacting with FritzBox call list via HTTP and parsing XML responses."""

import os
import time
import hashlib
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from collections import defaultdict, OrderedDict

import requests
from dotenv import load_dotenv

load_dotenv()  # .env-Datei einlesen

username = os.getenv('FRITZBOX_USERNAME')
password = os.getenv('FRITZBOX_PASSWORD')
router_ip = os.getenv("FRITZBOX_IP_ADDRESS")

# --- SID Cache ---
_sid_cache = {
    'sid': None,
    'timestamp': 0
}

def get_sid(user, pwd, fritzbox_ip):
    """Holt die SID von der FritzBox."""
    url = f"http://{fritzbox_ip}/login_sid.lua"
    try:
        response = requests.get(url, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise ConnectionError(f"Verbindung zur FritzBox fehlgeschlagen: {e}")
    
    root = ET.fromstring(response.content)

    sid = root.findtext('SID')
    if sid != '0000000000000000':
        return sid

    challenge = root.findtext('Challenge')
    challenge_response = f"{challenge}-{hashlib.md5((challenge + '-' + pwd).encode('utf-16le')).hexdigest()}"

    try:
        response = requests.get(url, params={
            "username": user,
            "response": challenge_response
        }, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise ConnectionError(f"Verbindung zur FritzBox fehlgeschlagen: {e}")

    root = ET.fromstring(response.content)
    sid = root.findtext('SID')
    if sid == '0000000000000000':
        raise RuntimeError("❌ Anmeldung an FritzBox fehlgeschlagen.")

    return sid

def get_sid_cached(user, pwd, fritzbox_ip, cache_duration=300):
    """Holt die SID von der FritzBox, nutzt einen Cache um wiederholte Anfragen zu vermeiden."""    
    now = time.time()
    if _sid_cache['sid'] and (now - _sid_cache['timestamp'] < cache_duration):
        return _sid_cache['sid']
    sid = get_sid(user, pwd, fritzbox_ip)
    _sid_cache['sid'] = sid
    _sid_cache['timestamp'] = now
    timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
    print(f"🔐 Neue SID geholt - {timestamp_str}")
    return sid

def get_calls_xml(user, pwd, fritzbox_ip):
    """Holt die Anrufliste von der FritzBox als XML-Daten."""
    sid = get_sid_cached(user, pwd, fritzbox_ip)
    url = f"http://{fritzbox_ip}:49000/calllist.lua?sid={sid}"
    try:
        response = requests.get(url, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise ConnectionError(f"Verbindung zur FritzBox Anrufliste fehlgeschlagen: {e}")
    
    if response.status_code != 200:
        raise RuntimeError("❌ Fehler beim Abrufen der Anrufliste.")
    return parse_calllist_xml(response.content.decode('utf-8'))

def parse_calllist_xml(xml_data):
    """Parst die XML-Daten der Anrufliste und gibt eine Liste von Anrufen zurück."""
    if not xml_data:
        return []
    root = ET.fromstring(xml_data)
    entries = []

    now = datetime.now()
    max_days_env = os.getenv('FRITZBOX_CALLLIST_DAYS', '4')
    try:
        max_days_int = int(max_days_env)
    except ValueError:
        max_days_int = 4
    max_days = now - timedelta(days=max_days_int)

    for call in root.findall('Call'):
        date_str = call.findtext('Date')
        try:
            dt = datetime.strptime(date_str, '%d.%m.%y %H:%M')
        except ValueError:
            continue
        if dt < max_days:
            continue

        name = call.findtext('Name')
        if not name or name.strip() == "":
            name = safe_strip_sip(call.findtext('Caller'))
        if call.findtext('Device') == 'Anrufbeantworter': calltype = '11'
        else: calltype = call.findtext('Type')  
        entries.append({
            'type': calltype,
            'name': name,
            'caller': safe_strip_sip(call.findtext('CallerNumber')),
            'called': safe_strip_sip(call.findtext('Called')),
            'date': dt,
            'duration': call.findtext('Duration'),
            'audio_path': call.findtext('Path') 
        })


    entries.sort(key=lambda x: x['date'], reverse=True)
    return entries[:50]

def safe_strip_sip(number):
    """Entfernt SIP-Präfixe aus der Nummer.""" 
    if number is None:
        return ''
    return number.replace('sip:', '').replace('SIP:', '').replace('SIP', '').strip(' :')

def get_calls_grouped(user, pwd):
    """Holt die Anrufe von der FritzBox und gruppiert sie nach Tagen."""    
    calls = get_calls_xml(user, pwd, router_ip)
    grouped = defaultdict(list)
    for call in calls:
        day = call['date'].strftime('%A, %d. %B')  # z. B. Sonntag, 13. Juli
        grouped[day].append(call)

    grouped_sorted = OrderedDict()
    for day in sorted(grouped.keys(), key=lambda d: max(call['date'] for call in grouped[d]), reverse=True):
        grouped_sorted[day] = grouped[day]

    return grouped_sorted
