# Copilot Instructions für AI Agents

## Architektur-Überblick
- **Backend:** Python (Flask), unter `backend/`. Holt Daten von Google Kalender, FritzBox und OpenWeather API. Konfiguration über `.env` und `config/`.
- **Frontend:** Vue 3 mit Vite, unter `frontend/Vue/`. Holt alle 10 Sekunden gecachte Daten vom Backend. Responsive Design für TV/Tablet.
- **Kommunikation:** Frontend fragt Backend per HTTP ab. Backend cached und aktualisiert Daten in Intervallen (einstellbar in `.env`).
- **Docker:** Multi-Stage Build für Frontend und Backend. Deutsche Locale wird im Container gesetzt.

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
  - Google-Kalender-Authentifizierung erzeugt `token.pickle` beim ersten Start.
  - FritzBox-Integration benötigt lokale Netzwerkverbindung und spezielle Benutzerrechte.
- **Frontend:**
  - Nutzt VueQuery (`src/plugins/vueQuery.js`) für API-Requests und Caching.
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