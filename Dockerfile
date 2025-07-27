# ----- STAGE 1: Build Vue frontend -----
FROM node:20-alpine AS frontend-builder

WORKDIR /app

COPY frontend/Vue/ ./frontend/
WORKDIR /app/frontend

RUN npm install && npm run build

# ----- STAGE 2: Build Python backend -----
FROM python:3.12-slim AS backend

# 🧩 System-Locales installieren und konfigurieren (Deutsch)
RUN apt-get update && \
    apt-get install -y --no-install-recommends locales && \
    sed -i '/de_DE.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 🌐 Setze das deutsche Locale als Standard
ENV LANG=de_DE.UTF-8 \
    LANGUAGE=de_DE:de \
    LC_ALL=de_DE.UTF-8

# Install gunicorn and flask
RUN pip install --no-cache-dir flask gunicorn

# Set workdir and copy backend
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files directly into /app/backend
COPY backend/ /app/backend/
COPY --from=frontend-builder /app/frontend/dist /app/backend/static/

WORKDIR /app/backend

# Set environment variables (optional)
ENV FLASK_APP=app.py

# Expose Flask/Gunicorn port
EXPOSE 8080

# Start Gunicorn server
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
