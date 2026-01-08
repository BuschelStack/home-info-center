[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Vue](https://img.shields.io/badge/vue-3.x-4FC08D.svg)
![Vite](https://img.shields.io/badge/vite-5.x-646CFF.svg)


## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE) – © 2025 LWood  
Nutzung, Weitergabe und Änderung sind erlaubt, solange der ursprüngliche Lizenztext beibehalten wird.

# Dashboard Home Info Center

Ein Dashboard für den Einsatz auf einem Fernseher (z.B. in der Küche), das wichtige Informationen übersichtlich darstellt. Es zeigt aktuelle Anrufe, Termine aus mehreren Google-Kalendern sowie Wettervorhersagen an.

## Features

- **Anrufliste:** Zeigt die letzten Anrufe der FritzBox übersichtlich an (eingehend, ausgehend, verpasst, Anrufbeantworter).
- **Kalender:** Termine aus mehreren Google-Kalendern werden gruppiert nach Tag dargestellt, mit farblicher Unterscheidung je Kalender.
- **Wetter:** Stündliche Wettervorhersage für den aktuellen Tag und eine 5-Tage-Vorschau (OpenWeather API).
- **Tag/Nacht Umschaltung:** Die Anzeige schaltet mit Sonenuntergang von weis in ein helles gelb um um die Augen zu schützen. Bei Sonnenaufgang geht es wieder zurück nach weiß. Einstellbar in .env.
- **Automatische Aktualisierung:** Das Frontend holt alle 10 Sekunden die gecachten Daten vom Backend ab. Das Backend selber hot die neuen Daten in festgelegten Intervallen von den Quellen ab. Intervalle sind in der .env-Datei einstellbar
- **Responsive Design:** Auch auf Tablets und kleineren Bildschirmen nutzbar.

## Installation

1. **Repository klonen:**
   ```bash
   git clone https://github.com/BuschelStack/home-info-center.git
   cd home-info-center
   ```

2. **Raspberry Pi Locale auf Deutsch setzen (optional):**
   Für deutsche Datums- und Zeitformate empfiehlt es sich, die Locale auf Deutsch zu setzen:
   
   ```bash
   # Konfigurationstool öffnen
   sudo raspi-config
   ```
   - Navigation im Menü
   - Wähle "5 Localisation Options" (oder "Localisierung")
   - Wähle "L1 Locale"
   - Deutsche Locale aktivieren
      - Scrolle in der Liste zu "de_DE.UTF-8 UTF-8"
      - Markiere sie mit der Leertaste (ein Sternchen * erscheint)
      - Wichtig: Lasse "en_GB.UTF-8 UTF-8" ebenfalls markiert (als Fallback)
      - Standard-Locale setzen:
      - Drücke Tab und dann Enter auf "Ok"
      - Im nächsten Bildschirm wähle "de_DE.UTF-8" als Standard
      - Bestätige mit Enter - Fertig
   - Bei der Frage nach einem Neustart: "Yes"

   **Oder manuell:**
   ```bash
   # Deutsche Locale aktivieren
   sudo dpkg-reconfigure locales
   # Wähle "de_DE.UTF-8 UTF-8" aus und setze es als Standard
   
   # Oder direkt über die Konfigurationsdatei:
   sudo nano /etc/locale.gen
   # Entkommentiere die Zeile: de_DE.UTF-8 UTF-8
   
   # Locale generieren
   sudo locale-gen
   
   # Standard-Locale setzen
   sudo update-locale LANG=de_DE.UTF-8
   
   # Neustart empfohlen
   sudo reboot
   ```
   
   **Überprüfung:**
   ```bash
   locale
   # Sollte de_DE.UTF-8 anzeigen
   ```

3. **Python-Umgebung einrichten:**

   **Mit VS Code Tasks (Empfohlen):**
   ```
   Ctrl+Shift+P → "Tasks: Run Task" → "🚀 Backend: Setup komplett"
   ```
   
   **Manuell:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

4. **Abhängigkeiten installieren:**
   
   **Mit VS Code Tasks (Empfohlen):**
   - Backend: Bereits durch "🚀 Backend: Setup komplett" erledigt
   - Frontend: `Ctrl+Shift+P` → "Tasks: Run Task" → "🌐 Frontend: Dependencies installieren"
   
   **Manuell:**
   
   ***Backend***
   ```bash
   Wechsle in den `backend`-Ordner und installiere die Abhängigkeiten:
   cd backend
   pip install -r requirements.txt
   ```
   ***Frontend einrichten***
      Wechsle in den `frontend/Vue`-Ordner und installiere die Abhängigkeiten:
      ```bash
      cd ../frontend/Vue
      npm install
      ```
      Frontend bauen:
      ```bash
      npm run build
      ```

5. **.env-Datei anlegen:**  
   Lege eine Datei `.env` im Ordner `backend` an und trage deine Zugangsdaten ein:

   ```env
   # OpenWeatherMap
   OPENWEATHER_API_KEY='96243423f4'           # API Key
   WEATHER_LOCATION_LAT='48.78'               # Breitengrad deines Standortes
   WEATHER_LOCATION_LON='11.4'                # Längengrad deines Standortes

   # FritzBox
   FRITZBOX_USERNAME='testuser'               # Benutzername
   FRITZBOX_PASSWORD='lorepusum'              # Passwort
   FRITZBOX_IP_ADDRESS='192.168.178.1'        # IP-Adresse

   # Google Kalender
   GOOGLE_CALENDAR_CLIENT_SECRET_PATH='config/client_secret.json'  # Pfad zum Client Secret
   GOOGLE_CALENDAR_TOKEN_PATH='config/token.pickle'                # Pfad zum Token
   GOOGLE_CALENDAR_CONFIG_PATH='config/calendars.json'             # Pfad zur Konfiguration

   # Intervalle (in Sekunden)
   INTERVAL_CALENDAR=300                      # Kalenderaktualisierung
   INTERVAL_CALLS=75                          # Anrufliste (mind. 60 empfohlen)
   INTERVAL_WEATHER=600                       # Wetteraktualisierung

   # Weitere Einstellungen
   FRITZBOX_CALLLIST_DAYS=4                   # Tage für die Anrufliste
   TIMEZONE='Europe/Berlin'                   # Zeitzone für Wetterdaten

   # Theme
   THEME_DAY_BG='#eaeaeaff'                   # Hintergrundfarbe Tag
   THEME_DAY_TEXT='#222222'                   # Textfarbe Tag
   THEME_EVENING_BG='#ffce2dff'               # Hintergrundfarbe Abend
   THEME_EVENING_TEXT='#2c2200ff'             # Textfarbe Abend
   ```

6. **Google API einrichten:**  
   - Gehe zur [Google Cloud Console](https://console.cloud.google.com/).
   - Erstelle ein neues Projekt oder wähle ein bestehendes aus.
   - Navigiere zu **APIs & Dienste > Bibliothek** und aktiviere die **Google Calendar API**.
   - Gehe zu **APIs & Dienste > Anmeldedaten** und klicke auf **Anmeldedaten erstellen > OAuth-Client-ID**.
   - Wähle **Desktop-App** als Anwendungstyp und erstelle die Anmeldedaten.
   - Lade die Datei `client_secret.json` herunter und platziere sie im Ordner `backend/config`. Der Ordner `config` muss erstellt werden.
   - Im `config`-Ordner muss die `calendars.json` aus dem Ordner `config_example` hineinkopiert und mit den eigenen Schlüsseln der Googlekalender einfügen.
   - Der Ordner `config_example` zeigt die Struktur. Die Datei `token.pickle` wird beim ersten Mal starten des Backends automatisch erstellt. In der `calendars.json` müssen die anzuzeigenden

## Starten

### 🚀 Mit VS Code Tasks (Empfohlen)

Dieses Projekt ist mit praktischen VS Code Tasks ausgestattet, die die Entwicklung erheblich vereinfachen:

#### **Erstmalige Einrichtung:**
1. Öffnen Sie das Projekt in VS Code
2. Drücken Sie `Ctrl+Shift+P` (Command Palette)
3. Tippen Sie "task" und wählen Sie **"Tasks: Run Task"**
4. Wählen Sie **"🚀 Backend: Setup komplett (venv + requirements)"**
   - Erstellt automatisch die virtuelle Umgebung (`backend/venv/`)
   - Installiert alle Python-Dependencies aus `requirements.txt`

#### **Verfügbare Tasks:**

**🔧 Backend Setup:**
- **🔧 Backend: Virtuelle Umgebung erstellen** - Erstellt `backend/venv/`
- **📦 Backend: Requirements installieren** - Installiert Python-Pakete
- **🚀 Backend: Setup komplett** - Komplette Einrichtung in einem Schritt

**🐍 Backend Development:**
- **🐍 Backend: Terminal mit venv** - Öffnet Terminal mit aktivierter venv
- **🐍 Backend: App starten** - Startet den Python-Server

**🌐 Frontend Development:**
- **🌐 Frontend: Dependencies installieren** - Führt `npm install` aus
- **🌐 Frontend: Dev Server starten** - Startet Vite Development Server
- **🌐 Frontend: Build** - Erstellt Production Build

**🚀 Kombinierte Tasks:**
- **🚀 Beide starten (Backend + Frontend)** - Startet beide Server parallel

#### **Debugging:**
- **F5** drücken für Backend-Debugging (verwendet automatisch die venv)
- Breakpoints werden in der IDE unterstützt

#### **Workflow für Development:**
1. **Einmalig:** `🚀 Backend: Setup komplett` ausführen
2. **Daily:** `🚀 Beide starten` für paralleles Backend/Frontend Development
3. **Testing:** `🌐 Frontend: Build` für Production-Test

### 📋 Manueller Start (Alternative)

Alternativ können Sie das Projekt auch manuell starten:

```bash
Backend starten:
   cd backend
   python app.py
   besser: gunicorn --bind 0.0.0.0:8080 app:app
```

```bash
Frontend starten:
   cd frontend
   npm run dev
```

Das Dashboard ist dann unter [http://localhost:3000](http://localhost:3000) erreichbar.

## 🛠️ VS Code Development Setup

Dieses Projekt ist vollständig für VS Code optimiert:

### **Automatische Features:**
- **Virtuelle Umgebung:** Wird automatisch erkannt und aktiviert
- **Python Linting:** Flake8 mit 120-Zeichen Zeilenlänge
- **Formatierung:** Black für Python, Prettier für Frontend
- **IntelliSense:** Vollständige Code-Completion für Python und Vue
- **Debugging:** F5 startet Backend mit Breakpoint-Unterstützung

### **Ordnerstruktur der Konfigurationen:**
```
.vscode/
├── tasks.json          # Zentrale Tasks für beide Projekte
backend/.vscode/
├── settings.json       # Python-spezifische Einstellungen
├── launch.json         # Debugging-Konfiguration
└── tasks.json          # Backend-spezifische Tasks
frontend/Vue/.vscode/
├── settings.json       # Vue/JS-spezifische Einstellungen
├── launch.json         # Frontend-Debugging (Chrome)
└── tasks.json          # Frontend-spezifische Tasks
```

### **Empfohlene Erweiterungen:**
- Python (ms-python.python)
- Vue Language Features (vue.volar)
- Prettier (esbenp.prettier-vscode)
- ES6 Syntax (ms-vscode.vscode-typescript-next)

## Verzeichnisstruktur

```plaintext
Dashboard_Familie/
├── backend/
│   ├── app.py
│   ├── Calendar/
│   │   └── ...                # Kalender-Integration (Google API)
│   ├── FritzBox/
│   │   └── ...                # Anruflisten-Integration (FritzBox)
│   ├── Weather/
│   │   └── ...                # Wetterdaten (OpenWeather)
│   ├── config/
│   │   ├── client_secret.json
│   │   ├── token.pickle
│   │   └── calendars.json
│   ├── static/
│   │   └── style.css
│   └── templates/
│       └── index.html
├── frontend/
│   ├── src/
│   │   └── ...                # Quellcode des Frontends (Vue)
│   └── public/
│       └── ...                # Statische Dateien für das Frontend
├── requirements.txt
└── README.md
```
> Hinweis: Die tatsächliche Struktur kann je nach Anpassungen leicht variieren.

## Hinweise

- Die Zugangsdaten und API-Keys niemals in ein öffentliches Repository hochladen!
- Die FritzBox muss im lokalen Netzwerk erreichbar sein.
  - der FritzBox-Benutzer benötigt nur die Berechtigung auf die Einstellung: Sprachnachrichten, Faxnachrichten, FRITZ!App Fon und Anrufliste (Der Benutzer kann Sprachnachrichten abhören, empfangene Faxe und die Anrufliste ansehen und FRITZ!App Fon nutzen.)
- Für die Google-Kalender-Integration ist beim ersten Start eine Authentifizierung im  Browser notwendig.
- Wenn du ein neues Paket installierst, z. B.:
  - `pip install flask`
  - Dann aktualisiere die requirements.txt: `pip freeze > requirements.txt`
  - `git add requirements.txt`
  - `git commit -m "Add Flask to requirements"`
  - `git push`