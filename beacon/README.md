# Aether Randomness Beacon

A **verifiable, hash-chained public randomness beacon** built on top of the
Aether chaotic entropy engine. It emits one signed *pulse* per period; anyone
can pull the history and prove — in their own browser or with their own code —
that no past value was altered.

This is the service layer that turns Aether from a desktop entropy tool into a
live, distributed system. It exists to demonstrate real backend engineering:
an async API, a relational store, a cache, an event-driven worker, containers,
and tests — around a genuinely non-trivial cryptographic core.

## How a pulse works

Every pulse commits to its contents and to the pulse before it:

```
output_hash = SHA-256( round_index | timestamp | entropy | previous_hash )
```

Because each pulse's `previous_hash` is the prior pulse's `output_hash`, the
whole history is a tamper-evident chain: alter any past entropy value and every
later hash stops matching. Each `output_hash` is also signed with **Ed25519**,
so consumers can confirm a pulse really came from this beacon.

The entropy itself comes from the **Aether NIHDE engine** (chaotic Rössler core
+ HMAC-DRBG conditioning + optional quantum seed). If the Rust core isn't
built, the beacon falls back to the OS CSPRNG and says so on `/health`.

## Architecture

```
                 ┌───────────────┐   pulse.created   ┌────────────────┐
   HTTP clients  │  Beacon API   │ ────────────────► │  Audit worker  │
   ────────────► │  (FastAPI)    │   (RabbitMQ)      │  independent    │
                 │               │                    │  hash-chained   │
                 │  producer ⏱   │                    │  audit log      │
                 └───┬───────┬───┘                    └────────────────┘
                     │       │
              Postgres│       │Redis
             (history)│       │(hot cache)
```

- **Beacon API** (`app/`) — produces a pulse every `BEACON_PERIOD_SECONDS`,
  persists it to PostgreSQL, caches the latest in Redis, and publishes a
  `pulse.created` event.
- **Audit worker** (`worker/`) — a separate microservice that consumes those
  events and maintains its **own** independent, hash-chained audit log, so the
  beacon's primary store can be cross-checked against a second record.
- **Redis** caches the hot read paths; a Redis outage degrades to a DB read.
- **RabbitMQ** is the event seam; a broker outage never blocks pulse production.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | live dashboard (recomputes the chain in your browser) |
| GET | `/health` | status + which entropy source is active |
| GET | `/beacon/latest` | most recent pulse |
| GET | `/beacon/pulse/{i}` | a pulse by round index |
| GET | `/beacon/chain?start=&end=` | a slice of the chain (≤1000) |
| GET | `/beacon/recent?limit=` | the most recent N pulses |
| GET | `/beacon/pubkey` | the Ed25519 public key |
| POST | `/beacon/verify` | verify pulses/chain the client supplies |

`/beacon/verify` recomputes everything from the submitted inputs — it does not
trust the server's own database — which is the whole point of a *verifiable*
beacon.

## Running it

Full stack (API + worker + Postgres + Redis + RabbitMQ):

```bash
cd beacon
docker compose up --build
# open http://localhost:8000
```

Locally without containers (uses the os.urandom fallback unless the Aether
core is installed, and SQLite if you point it there):

```bash
cd beacon
pip install -r requirements.txt
BEACON_DATABASE_URL="sqlite+aiosqlite:///./beacon.db" \
  uvicorn app.main:app --reload
```

## Tests

```bash
cd beacon
pytest -q            # hash chain, tamper detection, signatures
```

The core logic (`app/beacon.py`) has no web/DB/broker dependency, so the chain
and signature guarantees are unit-tested in isolation and run anywhere.

## Security & scope

This is a portfolio project, not an audited production beacon. The signing key
is read from `BEACON_SIGNING_KEY` (hex); without it an ephemeral key is used
and pulses won't verify across restarts. Do not rely on this for anything where
real money or safety depends on the randomness.
