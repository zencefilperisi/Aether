"""
Aether Randomness Beacon -- FastAPI application.
================================================

Endpoints:
    GET  /                     live dashboard (static HTML)
    GET  /health               liveness probe
    GET  /beacon/latest        the most recent pulse
    GET  /beacon/pulse/{i}     a pulse by round index
    GET  /beacon/chain?start&end   a contiguous slice of the chain
    POST /beacon/verify        verify a pulse or a chain submitted by the client
    GET  /beacon/pubkey        the Ed25519 public key (hex) for signature checks

A background task produces one pulse every BEACON_PERIOD_SECONDS, chaining each
to the previous one, persisting it to PostgreSQL, caching it in Redis, and
publishing a `pulse.created` event to RabbitMQ.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import beacon as beacon_core
from app import cache, db, events, signing
from app.entropy import get_entropy, entropy_source_name

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("beacon")

PERIOD = int(os.environ.get("BEACON_PERIOD_SECONDS", "10"))
ENTROPY_BYTES = int(os.environ.get("BEACON_ENTROPY_BYTES", "32"))
STATIC_DIR = Path(__file__).parent.parent / "static"


# ---- background pulse producer -------------------------------------------

async def _produce_one() -> dict:
    async with db.SessionLocal() as session:
        latest = await db.get_latest(session)
        if latest is None:
            round_index = 0
            previous_hash = beacon_core.GENESIS_PREV_HASH
        else:
            round_index = latest.round_index + 1
            previous_hash = latest.output_hash

        entropy = get_entropy(ENTROPY_BYTES)
        pulse = beacon_core.build_pulse(round_index, entropy, previous_hash)
        signature = signing.sign(pulse.output_hash)
        record = {**pulse.to_dict(), "signature": signature}

        await db.insert_pulse(session, record)

    await cache.cache_latest(record)
    await events.publish_pulse_created(record)
    log.info("pulse #%d produced (%s)", record["round_index"], record["output_hash"][:12])
    return record


async def _producer_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await _produce_one()
        except Exception as exc:
            log.exception("pulse production failed: %s", exc)
        try:
            await asyncio.wait_for(stop.wait(), timeout=PERIOD)
        except asyncio.TimeoutError:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    await events.connect()
    stop = asyncio.Event()
    task = asyncio.create_task(_producer_loop(stop))
    log.info("Beacon started: period=%ss, entropy source=%s", PERIOD, entropy_source_name())
    try:
        yield
    finally:
        stop.set()
        task.cancel()
        await events.close()


app = FastAPI(title="Aether Randomness Beacon", version="1.0", lifespan=lifespan)


# ---- schemas --------------------------------------------------------------

class VerifyRequest(BaseModel):
    pulses: list[dict]
    public_key: str | None = None


class VerifyResponse(BaseModel):
    ok: bool
    first_bad_round: int | None = None
    signatures_ok: bool | None = None
    checked: int


# ---- endpoints ------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "entropy_source": entropy_source_name(), "period_s": PERIOD}


@app.get("/beacon/pubkey")
async def pubkey():
    return {"algorithm": "Ed25519", "public_key": signing.public_key_hex()}


@app.get("/beacon/latest")
async def latest():
    cached = await cache.get_cached_latest()
    if cached:
        return cached
    async with db.SessionLocal() as session:
        row = await db.get_latest(session)
        if row is None:
            raise HTTPException(404, "no pulses yet")
        return row.to_dict()


@app.get("/beacon/pulse/{index}")
async def pulse(index: int):
    async with db.SessionLocal() as session:
        row = await db.get_by_index(session, index)
        if row is None:
            raise HTTPException(404, f"no pulse at round {index}")
        return row.to_dict()


@app.get("/beacon/chain")
async def chain(start: int = 0, end: int | None = None):
    async with db.SessionLocal() as session:
        if end is None:
            latest_row = await db.get_latest(session)
            if latest_row is None:
                return {"pulses": []}
            end = latest_row.round_index
        if end - start > 1000:
            raise HTTPException(400, "range too large (max 1000)")
        rows = await db.get_range(session, start, end)
        return {"pulses": [r.to_dict() for r in rows]}


@app.get("/beacon/recent")
async def recent(limit: int = 20):
    cached = await cache.get_cached_recent(limit)
    if cached:
        return {"pulses": cached}
    async with db.SessionLocal() as session:
        latest_row = await db.get_latest(session)
        if latest_row is None:
            return {"pulses": []}
        start = max(0, latest_row.round_index - limit + 1)
        rows = await db.get_range(session, start, latest_row.round_index)
        return {"pulses": [r.to_dict() for r in reversed(rows)]}


@app.post("/beacon/verify", response_model=VerifyResponse)
async def verify(req: VerifyRequest):
    """Verify a pulse or chain the client already holds. Pure computation --
    the server does not trust its own DB here, it recomputes from the inputs.
    """
    if not req.pulses:
        raise HTTPException(400, "no pulses supplied")
    ok, bad = beacon_core.verify_chain(req.pulses)

    sig_ok: bool | None = None
    if req.public_key:
        sig_ok = all(
            p.get("signature") and
            signing.verify(p["output_hash"], p["signature"], req.public_key)
            for p in req.pulses
        )

    return VerifyResponse(ok=ok, first_bad_round=bad,
                          signatures_ok=sig_ok, checked=len(req.pulses))


@app.get("/")
async def index():
    idx = STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return {"service": "Aether Randomness Beacon", "docs": "/docs"}
