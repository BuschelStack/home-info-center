"""Flask application entry point.

* Single ``create_app`` factory (testable).
* ETag-based cache validation – clients send ``If-None-Match`` and receive
  ``304 Not Modified`` when their copy is current. Replaces the legacy
  ``/api/<x>-version`` polling endpoints (BREAKING change).
* Server-Sent Events stream at ``/api/stream`` for live invalidation.
* Background updates run via APScheduler (see ``cache_service``).
"""

from __future__ import annotations

import atexit
import json
import time
from datetime import datetime
from queue import Empty
from typing import TYPE_CHECKING

from flask import Flask, Response, jsonify, request, send_from_directory

from cache_service import CacheJob, cache_service
from Calendar.get_events import get_all_events
from config import settings
from FritzBox.fritzbox_calllist import get_calls_grouped
from logging_config import configure_logging, get_logger
from Weather.weather import get_daily_forecast, get_hourly_forecast

if TYPE_CHECKING:
    from pathlib import Path


def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Cannot serialise {type(obj).__name__}")


def _json_response(payload, etag: str, status: int = 200) -> Response:
    """Jsonify with ETag/Cache-Control headers."""
    body = json.dumps(payload, ensure_ascii=False, default=_json_default)
    resp = Response(body, status=status, mimetype="application/json")
    if etag:
        resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "no-cache"
    return resp


def _conditional(name: str, payload_builder):
    """Helper for ETag-aware GET endpoints."""
    entry = cache_service.get(name)
    if not entry.etag:
        return _json_response(
            {"error": f"{name} not yet available", "detail": entry.last_error},
            etag="",
            status=503,
        )
    if request.headers.get("If-None-Match") == entry.etag:
        resp = Response(status=304)
        resp.headers["ETag"] = entry.etag
        return resp
    return _json_response(payload_builder(entry), entry.etag)


def _register_jobs() -> None:
    cache_service.register(
        CacheJob(
            name="events",
            fetch=get_all_events,
            interval_seconds=settings.interval_calendar,
        )
    )
    cache_service.register(
        CacheJob(
            name="calls",
            fetch=get_calls_grouped,
            interval_seconds=settings.interval_calls,
        )
    )
    cache_service.register(
        CacheJob(
            name="weather",
            fetch=lambda: {
                "weekly_weather": get_hourly_forecast(),
                "daily_weather": get_daily_forecast(),
            },
            interval_seconds=settings.interval_weather,
        )
    )


def create_app() -> Flask:
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    app = Flask(__name__, static_folder="static", static_url_path="")

    _register_jobs()
    cache_service.start()
    atexit.register(cache_service.shutdown)
    logger.info("home-info-center backend ready")

    # --- static / SPA fallback ---------------------------------------------------

    @app.route("/")
    def index() -> Response:
        return send_from_directory("static", "index.html")

    @app.errorhandler(404)
    def _spa_fallback(_e):
        return send_from_directory("static", "index.html")

    # --- data endpoints ----------------------------------------------------------

    @app.route("/api/events")
    def api_events():
        return _conditional("events", lambda e: {"data": e.data, "etag": e.etag})

    @app.route("/api/calls")
    def api_calls():
        return _conditional("calls", lambda e: {"calls": e.data, "etag": e.etag})

    @app.route("/api/weather")
    def api_weather():
        return _conditional("weather", lambda e: {**e.data, "etag": e.etag})

    @app.route("/api/calendars")
    def api_calendars() -> Response:
        path: Path = settings.calendar_config_path
        if not path.exists():
            return Response('{"error":"calendars.json not found"}', status=404, mimetype="application/json")
        return send_from_directory(str(path.parent), path.name, mimetype="application/json")

    @app.route("/api/config")
    def api_config():
        return jsonify(
            {
                "lat": settings.weather_location_lat,
                "lon": settings.weather_location_lon,
                "theme_day_bg": settings.theme_day_bg,
                "theme_day_text": settings.theme_day_text,
                "theme_evening_bg": settings.theme_evening_bg,
                "theme_evening_text": settings.theme_evening_text,
            }
        )

    # --- health & observability -------------------------------------------------

    @app.route("/api/health")
    def api_health():
        snapshot = cache_service.snapshot()
        all_ready = all(v["has_data"] for v in snapshot.values())
        status = 200 if all_ready else 503
        return jsonify({"status": "ok" if all_ready else "degraded", "caches": snapshot}), status

    # --- live update stream (SSE) -----------------------------------------------

    @app.route("/api/stream")
    def api_stream():
        def event_generator():
            queue = cache_service.subscribe()
            try:
                # Initial keep-alive comment
                yield ": connected\n\n"
                while True:
                    try:
                        msg = queue.get(timeout=25)
                        yield (f"event: cache-updated\ndata: {json.dumps(msg)}\n\n")
                    except Empty:
                        # heartbeat to keep the connection alive
                        yield f": ping {int(time.time())}\n\n"
            finally:
                cache_service.unsubscribe(queue)

        return Response(
            event_generator(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=False)
