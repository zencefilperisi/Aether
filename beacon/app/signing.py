"""Ed25519 signing for beacon pulses.

Each pulse's output_hash is signed so consumers can verify a pulse genuinely
came from this beacon, not just that its internal hash is self-consistent.

The private key is loaded from BEACON_SIGNING_KEY (hex) if set, otherwise an
ephemeral key is generated at startup and its public key logged. In a real
deployment the key would live in a secrets manager; the env var keeps this
honest and never hard-codes a key.
"""

from __future__ import annotations

import logging
import os

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization

log = logging.getLogger("beacon.signing")

_private_key: Ed25519PrivateKey | None = None


def _load_or_create_key() -> Ed25519PrivateKey:
    global _private_key
    if _private_key is not None:
        return _private_key
    hex_key = os.environ.get("BEACON_SIGNING_KEY")
    if hex_key:
        _private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(hex_key))
        log.info("Loaded beacon signing key from environment")
    else:
        _private_key = Ed25519PrivateKey.generate()
        log.warning("No BEACON_SIGNING_KEY set; generated an ephemeral key "
                    "(pulses will not verify across restarts)")
    return _private_key


def public_key_hex() -> str:
    pk = _load_or_create_key().public_key()
    raw = pk.public_bytes(serialization.Encoding.Raw,
                          serialization.PublicFormat.Raw)
    return raw.hex()


def sign(output_hash_hex: str) -> str:
    sig = _load_or_create_key().sign(bytes.fromhex(output_hash_hex))
    return sig.hex()


def verify(output_hash_hex: str, signature_hex: str, public_hex: str) -> bool:
    try:
        pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex))
        pk.verify(bytes.fromhex(signature_hex), bytes.fromhex(output_hash_hex))
        return True
    except Exception:
        return False
