"""Tests for the cache service."""

from __future__ import annotations

from cache_service import CacheJob, CacheService


def test_cache_updates_on_new_data():
    svc = CacheService()
    counter = {"n": 0}

    def fetch():
        counter["n"] += 1
        return {"value": counter["n"]}

    job = CacheJob(name="x", fetch=fetch, interval_seconds=60)
    svc.register(job)
    svc._run_job(job)
    entry = svc.get("x")
    assert entry.data == {"value": 1}
    assert entry.etag != ""


def test_cache_etag_stable_when_data_unchanged():
    svc = CacheService()
    payload = {"a": 1}
    job = CacheJob(name="y", fetch=lambda: payload, interval_seconds=60)
    svc.register(job)
    svc._run_job(job)
    etag1 = svc.get("y").etag
    svc._run_job(job)
    etag2 = svc.get("y").etag
    assert etag1 == etag2


def test_cache_records_error_without_overwriting_data():
    svc = CacheService()
    job_ok = CacheJob(name="z", fetch=lambda: {"ok": True}, interval_seconds=60)
    svc.register(job_ok)
    svc._run_job(job_ok)
    good_data = svc.get("z").data

    def boom():
        raise RuntimeError("nope")

    job_bad = CacheJob(name="z", fetch=boom, interval_seconds=60)
    svc._run_job(job_bad)
    entry = svc.get("z")
    assert entry.data == good_data
    assert entry.last_error == "nope"


def test_subscribe_receives_publication():
    svc = CacheService()
    q = svc.subscribe()
    job = CacheJob(name="evt", fetch=lambda: {"v": 1}, interval_seconds=60)
    svc.register(job)
    svc._run_job(job)
    msg = q.get(timeout=1)
    assert msg["name"] == "evt"
    assert msg["etag"]
