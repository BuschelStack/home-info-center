"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    """Provide minimal env so ``config.settings`` instantiates cleanly."""
    monkeypatch.setenv("FRITZBOX_USERNAME", "test")
    monkeypatch.setenv("FRITZBOX_PASSWORD", "test")
    monkeypatch.setenv("FRITZBOX_IP_ADDRESS", "127.0.0.1")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test")
    monkeypatch.setenv("INTERVAL_CALENDAR", "300")
    monkeypatch.setenv("INTERVAL_CALLS", "120")
    monkeypatch.setenv("INTERVAL_WEATHER", "600")
    # No .env from CWD
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def fresh_settings():
    """Reload settings after env changes."""
    import importlib

    import config

    importlib.reload(config)
    return config.settings
