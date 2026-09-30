"""RabbitMQ event publishing.

When a new pulse is produced, the beacon publishes a `pulse.created` event to
a fanout exchange. Downstream services (e.g. the audit worker) subscribe
independently -- this is the event-driven seam that decouples pulse production
from anything that reacts to it.

Publishing is best-effort: a broker outage must never block pulse production,
so failures are logged and swallowed.
"""

from __future__ import annotations

import json
import logging
import os

import aio_pika

log = logging.getLogger("beacon.events")

RABBITMQ_URL = os.environ.get("BEACON_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_NAME = "beacon.events"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None


async def connect() -> None:
    global _connection, _exchange
    try:
        _connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await _connection.channel()
        _exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.FANOUT, durable=True
        )
        log.info("Connected to RabbitMQ exchange %s", EXCHANGE_NAME)
    except Exception as exc:
        log.warning("RabbitMQ connect failed (%s); events disabled", exc)
        _connection = _exchange = None


async def publish_pulse_created(pulse: dict) -> None:
    if _exchange is None:
        return
    try:
        msg = aio_pika.Message(
            body=json.dumps({"event": "pulse.created", "pulse": pulse}).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await _exchange.publish(msg, routing_key="")
    except Exception as exc:
        log.warning("publish_pulse_created failed (%s)", exc)


async def close() -> None:
    if _connection is not None:
        await _connection.close()
