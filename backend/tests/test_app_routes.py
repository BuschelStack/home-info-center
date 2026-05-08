"""Smoke tests for Flask routes."""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def client(monkeypatch):
    # Disable scheduler start during tests
    from cache_service import cache_service

    monkeypatch.setattr(cache_service, "start", lambda: None)
    monkeypatch.setattr(cache_service, "_scheduler", _FakeScheduler())

    with (
        patch("Calendar.get_events.get_all_events", return_value={}),
        patch("FritzBox.fritzbox_calllist.get_calls_grouped", return_value={}),
        patch("Weather.weather.get_hourly_forecast", return_value={}),
        patch("Weather.weather.get_daily_forecast", return_value=[]),
    ):
        from app import create_app

        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c


class _FakeScheduler:
    running = False

    def add_job(self, *_, **__):
        pass

    def start(self):
        self.running = True

    def shutdown(self, **_):
        pass

    def get_jobs(self):
        return []


def test_health_returns_503_when_no_data(client):
    r = client.get("/api/health")
    assert r.status_code == 503
    body = r.get_json()
    assert body["status"] == "degraded"
    assert "caches" in body


def test_config_endpoint_returns_themes(client):
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.get_json()
    assert "lat" in body
    assert "theme_day_bg" in body


def test_events_endpoint_503_without_data(client):
    r = client.get("/api/events")
    assert r.status_code == 503
