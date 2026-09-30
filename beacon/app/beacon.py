"""
Beacon core: round construction and the verifiable hash chain.
===============================================================

A beacon emits one *pulse* (round) per period. Each pulse commits to:

    round_index          monotonically increasing counter
    timestamp            UTC time the pulse was produced
    entropy              fresh random bytes from the Aether engine
    previous_hash        the output_hash of the pulse before it
    output_hash = SHA-256( round_index || timestamp || entropy || previous_hash )

Because every pulse chains the previous pulse's hash, the whole history is
tamper-evident: change any past pulse and every subsequent output_hash breaks.
This mirrors the design of public randomness beacons (e.g. NIST's beacon and
Cloudflare's League of Entropy) at a scale suitable for a portfolio project.

This module is deliberately free of any web/DB/async dependency so it can be
unit-tested in isolation and reused by the API, the scheduler and the tests.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

GENESIS_PREV_HASH = "0" * 64  # previous_hash of the very first pulse


def _sha256_hex(*parts: bytes) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.hexdigest()


def compute_output_hash(round_index: int, timestamp_iso: str,
                        entropy_hex: str, previous_hash: str) -> str:
    """The canonical hash binding a pulse to its contents and its predecessor.

    Inputs are serialised in a fixed order with length-independent separators
    so the hash is unambiguous and reproducible by any verifier.
    """
    payload = (
        f"{round_index}".encode()
        + b"|" + timestamp_iso.encode()
        + b"|" + entropy_hex.encode()
        + b"|" + previous_hash.encode()
    )
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class Pulse:
    round_index: int
    timestamp: str          # ISO-8601 UTC
    entropy: str            # hex-encoded random bytes
    previous_hash: str
    output_hash: str
    signature: str | None = None

    def to_dict(self) -> dict:
        return {
            "round_index": self.round_index,
            "timestamp": self.timestamp,
            "entropy": self.entropy,
            "previous_hash": self.previous_hash,
            "output_hash": self.output_hash,
            "signature": self.signature,
        }


def build_pulse(round_index: int, entropy: bytes, previous_hash: str,
                timestamp: datetime | None = None) -> Pulse:
    """Construct the next pulse from fresh entropy and the previous hash."""
    ts = (timestamp or datetime.now(timezone.utc)).isoformat()
    entropy_hex = entropy.hex()
    output_hash = compute_output_hash(round_index, ts, entropy_hex, previous_hash)
    return Pulse(
        round_index=round_index,
        timestamp=ts,
        entropy=entropy_hex,
        previous_hash=previous_hash,
        output_hash=output_hash,
    )


def verify_pulse(pulse: dict) -> bool:
    """Recompute a single pulse's output_hash and check it matches."""
    expected = compute_output_hash(
        pulse["round_index"], pulse["timestamp"],
        pulse["entropy"], pulse["previous_hash"],
    )
    return expected == pulse["output_hash"]


def verify_chain(pulses: list[dict]) -> tuple[bool, int | None]:
    """Verify a contiguous list of pulses ordered by round_index.

    Returns (ok, first_bad_index). Checks both that each pulse's own hash is
    correct and that previous_hash links to the prior pulse's output_hash.
    """
    prev_hash = None
    for p in pulses:
        if not verify_pulse(p):
            return False, p["round_index"]
        if prev_hash is not None and p["previous_hash"] != prev_hash:
            return False, p["round_index"]
        prev_hash = p["output_hash"]
    return True, None
