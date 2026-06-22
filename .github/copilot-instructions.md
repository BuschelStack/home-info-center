# Copilot Instructions für AI Agents

## Architektur-Überblick
- **Backend:** Python (Flask), unter `backend/`. Holt Daten von Google Kalender, FritzBox und OpenWeather API. Konfiguration über `.env` und `config/` (validiert via `config.py`/pydantic-settings). Hintergrund-Aktualisierung über APScheduler im zentralen `cache_service.py`.
- **Frontend:** Vue 3 mit Vite, unter `frontend/Vue/`. Reagiert auf einen Server-Sent-Events-Stream und invalidiert dann gezielt die Vue-Query-Caches. Responsive Design für TV/Tablet.
- **Kommunikation:** Backend cached die Daten und aktualisiert sie in Intervallen (einstellbar in `.env`). Die Datenendpunkte nutzen ETags (`304 Not Modified`); Live-Invalidierung läuft über `/api/stream` (SSE).
- **Docker:** Multi-Stage Build für Frontend und Backend. Läuft mit genau EINEM Gunicorn-Worker (skaliert über Threads), da Scheduler und SSE-Registry prozesslokal sind.

## Entwickler-Workflows
- **Empfohlen:** Nutze die VS Code Tasks für Setup und Entwicklung:
  - `🚀 Backend: Setup komplett` (erstellt venv, installiert requirements)
  - `🌐 Frontend: Dependencies installieren` (npm install)
  - `🚀 Beide starten` (Backend & Frontend parallel)
  - `🐍 Backend: App starten` (Python-Server)
  - `🌐 Frontend: Dev Server starten` (Vite)
- **Debugging:** F5 für Backend-Debugging (venv wird automatisch verwendet)
- **Testing:** `🌐 Frontend: Build` für Production-Test
- **Linting/Formatierung:**
  - Python: Flake8 (max. 120 Zeichen), Black
  - Frontend: Prettier
 - **Branchschutz:** Der Branch `main` ist typischerweise geschützt (kein direkter Push). Arbeite auf Feature-Branches und eröffne einen PR:
   - Neuen Branch: `git switch -c feat/<kurz-beschreibung>`
   - Commit & Push: `git add -A && git commit -m "<änderung>" && git push -u origin HEAD`
   - PR auf GitHub erstellen und Checks abwarten

## Konventionen & Besonderheiten
- **Backend:**
  - Konfigurationsdateien (`client_secret.json`, `calendars.json`, `.env`) im `backend/config/`.
  - Google-Kalender-Authentifizierung erzeugt `token.pickle` beim ersten Start. Headless/Docker: Token vorab mit `python -m Calendar.generate_token` erzeugen und mounten.
  - FritzBox-Integration benötigt lokale Netzwerkverbindung und spezielle Benutzerrechte.
- **Frontend:**
  - Nutzt VueQuery (`src/plugins/vueQuery.js`) für API-Requests und Caching; `composables/useCacheStream.js` lauscht auf den SSE-Stream und invalidiert Caches bei Änderungen.
  - Wetter-Icons: Siehe `public/weather-icons/README.md` für CSS-Klassen und Windrichtungen.
- **Secrets:** Niemals Zugangsdaten/API-Keys ins Repo pushen!
- **Dependencies:** Nach Installation neuer Python-Pakete immer `requirements.txt` aktualisieren (`pip freeze > requirements.txt`).

## Wichtige Dateien & Beispiele
- `backend/app.py`: Einstiegspunkt Backend
- `frontend/Vue/src/App.vue`: Einstiegspunkt Frontend
- `backend/Calendar/`, `FritzBox/`, `Weather/`: Datenquellen-Module
- `frontend/Vue/src/components/`: UI-Komponenten
- `frontend/Vue/public/weather-icons/README.md`: Wetter-Icon-Konventionen
- `Dockerfile`: Build- und Deployment-Logik
- `.env` (Backend): API-Keys, Intervalle, Einstellungen

## Typische Fehlerquellen
- Fehlende oder falsch platzierte Konfigurationsdateien im Backend
- Nicht ausgeführte VS Code Tasks (Setup, Dependencies)
- FritzBox nicht im lokalen Netz oder falsche Rechte
- Google-Kalender-Token fehlt (Browser-Auth nötig)

---
Feedback zu unklaren oder fehlenden Abschnitten erwünscht!