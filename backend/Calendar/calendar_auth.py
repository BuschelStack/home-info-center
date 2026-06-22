"""Google Calendar OAuth credential handling."""

from __future__ import annotations

import pickle
from typing import TYPE_CHECKING

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from config import settings
from logging_config import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from google.oauth2.credentials import Credentials

logger = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_credentials() -> Credentials:
    """Load cached credentials, refreshing or running OAuth flow if needed."""
    token_path: Path = settings.calendar_token_path
    client_secret_path: Path = settings.calendar_client_secret_path

    creds: Credentials | None = None
    if token_path.exists():
        with token_path.open("rb") as fh:
            creds = pickle.load(fh)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _persist(creds, token_path)
            return creds
        except Exception as e:
            logger.warning("Token refresh failed, re-authenticating: %s", e)

    if not client_secret_path.exists():
        raise FileNotFoundError(f"Google client secret not found at {client_secret_path}")

    # port=0 -> pick a free ephemeral port (avoids clashing with the app on 8080).
    # Note: ``run_local_server`` opens a browser and therefore only works on an
    # interactive machine. In headless deployments (Docker) generate the token
    # beforehand with ``python -m Calendar.generate_token`` and mount it.
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
    creds = flow.run_local_server(port=0)
    _persist(creds, token_path)
    return creds


def _persist(creds: Credentials, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        pickle.dump(creds, fh)
