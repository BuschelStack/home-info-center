"""Centralised application configuration via pydantic-settings.

All env-driven values are validated at startup, fail-fast.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Typed application settings.

    Values are read from environment variables (or `.env` file).
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # FritzBox
    fritzbox_username: str | None = Field(default=None)
    fritzbox_password: str | None = Field(default=None)
    fritzbox_ip_address: str | None = Field(default=None)
    fritzbox_calllist_days: int = Field(default=4, ge=1, le=365)

    # Google Calendar
    google_calendar_client_secret_path: str = Field(default="config/client_secret.json")
    google_calendar_token_path: str = Field(default="config/token.pickle")
    google_calendar_config_path: str = Field(default="config/calendars.json")

    # OpenWeather
    openweather_api_key: str | None = Field(default=None)
    weather_location_lat: float = Field(default=48.137)
    weather_location_lon: float = Field(default=11.575)

    # Update intervals (seconds)
    interval_calendar: int = Field(default=300, ge=30)
    interval_calls: int = Field(default=120, ge=30)
    interval_weather: int = Field(default=600, ge=60)

    # Timezone & locale
    timezone: str = Field(default="Europe/Berlin")

    # Theme colours
    theme_day_bg: str = Field(default="#eaeaeaff")
    theme_day_text: str = Field(default="#222222")
    theme_evening_bg: str = Field(default="#ffeebbff")
    theme_evening_text: str = Field(default="#3a2c00")

    # Server
    log_level: str = Field(default="INFO")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080, ge=1, le=65535)

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return v.upper()

    def absolute_path(self, relative: str) -> Path:
        """Resolve a path relative to backend directory."""
        p = Path(relative)
        if p.is_absolute():
            return p
        return (BASE_DIR / p).resolve()

    @property
    def calendar_config_path(self) -> Path:
        return self.absolute_path(self.google_calendar_config_path)

    @property
    def calendar_token_path(self) -> Path:
        return self.absolute_path(self.google_calendar_token_path)

    @property
    def calendar_client_secret_path(self) -> Path:
        return self.absolute_path(self.google_calendar_client_secret_path)


settings = Settings()
