"""Unit tests for the beacon core: hash chain, signing, verification.

These run with no database, Redis or broker -- they exercise the pure logic
that everything else depends on.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import beacon as bc
from app import signing


# ---- hash chain -----------------------------------------------------------

def _make_chain(n):
    pulses, prev = [], bc.GENESIS_PREV_HASH
    for i in range(n):
        p = bc.build_pulse(i, os.urandom(32), prev)
        pulses.append(p.to_dict())
        prev = p.output_hash
    return pulses


def test_single_pulse_verifies():
    p = bc.build_pulse(0, os.urandom(32), bc.GENESIS_PREV_HASH)
    assert bc.verify_pulse(p.to_dict())


def test_intact_chain_verifies():
    pulses = _make_chain(10)
    ok, bad = bc.verify_chain(pulses)
    assert ok and bad is None


def test_tampered_entropy_detected():
    pulses = _make_chain(5)
    pulses[2]["entropy"] = "ff" * 32
    ok, bad = bc.verify_chain(pulses)
    assert not ok and bad == 2


def test_broken_link_detected():
    pulses = _make_chain(5)
    # Recompute pulse 2's own hash so it self-verifies, but the link from
    # pulse 3 now points at the old hash -> chain must break at round 3.
    pulses[2]["output_hash"] = bc.compute_output_hash(
        2, pulses[2]["timestamp"], pulses[2]["entropy"], pulses[2]["previous_hash"]
    )
    # (entropy is unchanged here, so we instead tamper then fix to force a link break)
    pulses[2]["entropy"] = "aa" * 32
    pulses[2]["output_hash"] = bc.compute_output_hash(
        2, pulses[2]["timestamp"], pulses[2]["entropy"], pulses[2]["previous_hash"]
    )
    ok, bad = bc.verify_chain(pulses)
    assert not ok and bad == 3


def test_genesis_previous_hash():
    p = bc.build_pulse(0, os.urandom(32), bc.GENESIS_PREV_HASH)
    assert p.previous_hash == "0" * 64


def test_output_hash_is_deterministic():
    e = os.urandom(32)
    p1 = bc.build_pulse(7, e, "ab" * 32, timestamp=None)
    h = bc.compute_output_hash(7, p1.timestamp, e.hex(), "ab" * 32)
    assert h == p1.output_hash


# ---- signatures -----------------------------------------------------------

def test_signature_roundtrip():
    p = bc.build_pulse(0, os.urandom(32), bc.GENESIS_PREV_HASH)
    sig = signing.sign(p.output_hash)
    pub = signing.public_key_hex()
    assert signing.verify(p.output_hash, sig, pub)


def test_signature_rejects_wrong_hash():
    p = bc.build_pulse(0, os.urandom(32), bc.GENESIS_PREV_HASH)
    sig = signing.sign(p.output_hash)
    pub = signing.public_key_hex()
    other = "00" * 32
    assert not signing.verify(other, sig, pub)
