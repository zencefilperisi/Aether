"""
Audit worker -- an independent microservice that consumes pulse events.
=======================================================================

Subscribes to the `beacon.events` fanout exchange and maintains its own
tamper-evident audit log of every pulse it sees, entirely separate from the
beacon's own database. This is the second, independent record: if the beacon's
primary store were altered, the audit log (written by a different service,
ideally on different storage) would still hold the original hashes.

The audit log itself is hash-chained the same way the beacon is, so the
worker's output is independently verifiable too.

Run standalone:  python -m worker.audit_worker
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path

import aio_pika

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("audit-worker")

RABBITMQ_URL = os.environ.get("BEACON_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_NAME = "beacon.events"
AUDIT_LOG_PATH = Path(os.environ.get("AUDIT_LOG_PATH", "audit_log.jsonl"))


def _audit_hash(prev: str, pulse: dict) -> str:
    payload = (prev + pulse["output_hash"] + pulse["timestamp"]).encode()
    return hashlib.sha256(payload).hexdigest()


class AuditLog:
    """Append-only, hash-chained audit log persisted as JSON lines."""

    def __init__(self, path: Path):
        self.path = path
        self.prev = "0" * 64
        if path.exists():
            for line in path.read_text().splitlines():
                if line.strip():
                    self.prev = json.loads(line)["audit_hash"]

    def append(self, pulse: dict) -> dict:
        audit_hash = _audit_hash(self.prev, pulse)
        entry = {
            "round_index": pulse["round_index"],
            "output_hash": pulse["output_hash"],
            "timestamp": pulse["timestamp"],
            "prev_audit_hash": self.prev,
            "audit_hash": audit_hash,
        }
        with self.path.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        self.prev = audit_hash
        return entry


async def main() -> None:
    audit = AuditLog(AUDIT_LOG_PATH)
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.FANOUT, durable=True
    )
    queue = await channel.declare_queue("audit.pulses", durable=True)
    await queue.bind(exchange)
    log.info("Audit worker listening on %s", EXCHANGE_NAME)

    async with queue.iterator() as it:
        async for message in it:
            async with message.process():
                data = json.loads(message.body)
                pulse = data.get("pulse", {})
                entry = audit.append(pulse)
                log.info("audited pulse #%s -> audit_hash %s",
                         entry["round_index"], entry["audit_hash"][:12])


if __name__ == "__main__":
    asyncio.run(main())
