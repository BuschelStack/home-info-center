"""Centralised cache + scheduler service.

* One generic ``CacheJob`` definition replaces three duplicated update loops.
* ``APScheduler`` drives all background jobs (graceful shutdown, observability).
* Each cache entry has an ETag (sha256 of the JSON payload). Endpoints can
  return ``304 Not Modified`` when the client already has the current version.
* SSE subscribers are notified on every successful change.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from queue import Empty, Queue
from typing import TYPE_CHECKING, Any

from apscheduler.schedulers.background import BackgroundScheduler

from logging_config import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

logger = get_logger(__name__)


def _default_serialiser(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj).__name__} not JSON serialisable")


def _compute_etag(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=_default_serialiser, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class CacheEntry:
    name: str
    data: Any = None
    etag: str = ""
    updated_at: datetime | None = None
    last_error: str | None = None


@dataclass
class CacheJob:
    """Definition of a single periodic cache refresh."""

    name: str
    fetch: Callable[[], Any]
    interval_seconds: int
    initial_delay: int = 0
    error_value: Any = field(default_factory=dict)


class CacheService:
    """Thread-safe cache store with pub/sub and APScheduler integration."""

    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._scheduler = BackgroundScheduler(daemon=True)
        self._subscribers: list[Queue] = []
        self._sub_lock = threading.Lock()

    # -- public API --------------------------------------------------------

    def register(self, job: CacheJob) -> None:
        with self._lock:
            self._entries.setdefault(job.name, CacheEntry(name=job.name, data=job.error_value))

        def _runner() -> None:
            self._run_job(job)

        self._scheduler.add_job(
            _runner,
            trigger="interval",
            seconds=job.interval_seconds,
            next_run_time=datetime.now(UTC),
            id=job.name,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("CacheService started (%d jobs)", len(self._scheduler.get_jobs()))

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def get(self, name: str) -> CacheEntry:
        with self._lock:
            return self._entries[name]

    def snapshot(self) -> dict[str, dict]:
        """Lightweight overview for /api/health."""
        with self._lock:
            return {
                name: {
                    "etag": e.etag,
                    "updated_at": e.updated_at.isoformat() if e.updated_at else None,
                    "last_error": e.last_error,
                    "has_data": bool(e.data),
                }
                for name, e in self._entries.items()
            }

    # -- pub/sub for SSE ---------------------------------------------------

    def subscribe(self) -> Queue:
        q: Queue = Queue(maxsize=100)
        with self._sub_lock:
            self._subscribers.append(q)
        # Kick-off snapshot of current versions
        with self._lock:
            for entry in self._entries.values():
                if entry.etag:
                    with contextlib.suppress(Exception):
                        q.put_nowait({"name": entry.name, "etag": entry.etag})
        return q

    def unsubscribe(self, q: Queue) -> None:
        with self._sub_lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def _publish(self, name: str, etag: str) -> None:
        msg = {"name": name, "etag": etag}
        with self._sub_lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(msg)
                except Exception:
                    # Drop slow subscribers
                    try:
                        q.get_nowait()
                        q.put_nowait(msg)
                    except Empty:
                        pass

    # -- internal ----------------------------------------------------------

    def _run_job(self, job: CacheJob) -> None:
        try:
            data = job.fetch()
        except Exception as exc:
            logger.warning("Cache job '%s' failed: %s", job.name, exc)
            with self._lock:
                self._entries[job.name].last_error = str(exc)
            return

        new_etag = _compute_etag(data)
        with self._lock:
            entry = self._entries[job.name]
            if entry.etag == new_etag:
                entry.last_error = None
                return
            entry.data = data
            entry.etag = new_etag
            entry.updated_at = datetime.now(UTC)
            entry.last_error = None
        logger.info("Cache '%s' updated (etag=%s)", job.name, new_etag)
        self._publish(job.name, new_etag)


cache_service = CacheService()
