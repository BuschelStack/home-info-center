"""Standalone helper to create the Google OAuth token.

Run this once on an interactive machine (with a browser) to produce
``config/token.pickle``. The resulting token can then be mounted into a
headless deployment (e.g. Docker), where the interactive OAuth flow cannot run.

Usage::

    python -m Calendar.generate_token
"""

from __future__ import annotations

from Calendar.calendar_auth import get_credentials
from config import settings
from logging_config import configure_logging, get_logger


def main() -> None:
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    get_credentials()
    logger.info("Token written to %s", settings.calendar_token_path)


if __name__ == "__main__":
    main()
