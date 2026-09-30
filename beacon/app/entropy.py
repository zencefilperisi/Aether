"""Entropy source for the beacon.

Prefers the Aether NIHDE engine (chaotic + quantum/OS conditioning). If the
compiled Rust core is unavailable, it falls back to the OS CSPRNG so the
beacon still runs anywhere -- the fallback is logged, never silent in prod.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger("beacon.entropy")

_engine = None


def _get_engine():
    global _engine
    if _engine is not None:
        return _engine
    try:
        # The Aether package lives one level up from the beacon/ dir.
        import sys
        here = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(here, "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from core.chaos.nihde import NIHDE
        _engine = NIHDE()
        log.info("Entropy source: Aether NIHDE engine")
    except Exception as exc:  # Rust core not built, etc.
        _engine = False
        log.warning("Aether core unavailable (%s); using os.urandom fallback", exc)
    return _engine


def get_entropy(n: int = 32) -> bytes:
    """Return n fresh random bytes for a beacon pulse."""
    engine = _get_engine()
    if engine:
        return engine.generate_bytes(n)
    return os.urandom(n)


def entropy_source_name() -> str:
    return "aether-nihde" if _get_engine() else "os-urandom-fallback"
