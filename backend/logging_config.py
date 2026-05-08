"""Structured logging setup.

Single entry-point: `configure_logging()`. Idempotent.
"""

from __future__ import annotations

import logging
import sys
from logging.config import dictConfig

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with a clear, container-friendly format."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "default",
                    "level": level,
                }
            },
            "loggers": {
                "werkzeug": {"level": "WARNING"},
                "googleapiclient": {"level": "WARNING"},
                "urllib3": {"level": "WARNING"},
                "apscheduler": {"level": "INFO"},
            },
            "root": {"handlers": ["console"], "level": level},
        }
    )
    logging.captureWarnings(True)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
