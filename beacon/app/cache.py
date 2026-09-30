"""Redis cache for the beacon.

Caches the latest pulse and recent pulses so the hot read paths (`/beacon/latest`,
the live dashboard poll) don't hit PostgreSQL on every request. Every read and
write is wrapped so a Redis outage degrades to a straight DB read rather than
taking the service down.
"""

from __future__ import annotations

import json
import logging
import os

import redis.asyncio as redis

log = logging.getLogger("beacon.cache")

REDIS_URL = os.environ.get("BEACON_REDIS_URL", "redis://localhost:6379/0")
LATEST_KEY = "beacon:latest"
RECENT_KEY = "beacon:recent"      # a capped list of recent pulses
RECENT_MAX = 100

_client: redis.Redis | None = None


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


async def cache_latest(pulse: dict) -> None:
    try:
        c = get_client()
        await c.set(LATEST_KEY, json.dumps(pulse))
        await c.lpush(RECENT_KEY, json.dumps(pulse))
        await c.ltrim(RECENT_KEY, 0, RECENT_MAX - 1)
    except Exception as exc:
        log.warning("cache_latest failed (%s); continuing without cache", exc)


async def get_cached_latest() -> dict | None:
    try:
        c = get_client()
        raw = await c.get(LATEST_KEY)
        return json.loads(raw) if raw else None
    except Exception as exc:
        log.warning("get_cached_latest failed (%s)", exc)
        return None


async def get_cached_recent(limit: int = 20) -> list[dict]:
    try:
        c = get_client()
        raw = await c.lrange(RECENT_KEY, 0, limit - 1)
        return [json.loads(r) for r in raw]
    except Exception as exc:
        log.warning("get_cached_recent failed (%s)", exc)
        return []
