"""
Self-validation for the NIST SP 800-22 implementation.
=======================================================

This does NOT test Aether's entropy. It tests the *test suite itself*, so the
p-values it produces can be trusted. Two independent kinds of evidence:

  1. Worked examples from SP 800-22 Rev 1a. Where the specification prints an
     expected p-value for a small reference string, we reproduce it to 6 dp.

  2. Negative controls. Deliberately non-random sequences (constant, periodic,
     biased) must FAIL the tests that are designed to catch them, and genuine
     CSPRNG output must PASS.

Run:  python -m tests.validate_nist   (or  pytest tests/validate_nist.py)
"""

import os
import math
import numpy as np

from tests import nist_sp800_22 as N


def _bits(s: str) -> np.ndarray:
    return np.array([int(c) for c in s], dtype=np.uint8)


# --- 1. Worked examples from the specification ----------------------------

def test_spec_monobit():
    # Sec 2.1.8: n=100, sum(+/-1) = -16 -> p = 0.109599
    bits = np.array([1] * 42 + [0] * 58, dtype=np.uint8)
    assert abs(N.frequency_monobit(bits).p_value - 0.109599) < 1e-5


def test_spec_runs():
    # Sec 2.3.8: 10-bit string, V=7 -> p = 0.147232
    assert abs(N.runs(_bits("1001101011")).p_value - 0.147232) < 1e-5


def test_spec_approximate_entropy():
    # Sec 2.12.8: n=10, m=3 -> p = 0.261961
    assert abs(N.approximate_entropy(_bits("0100110101"), m=3).p_value - 0.261961) < 1e-5


# --- 2. Negative controls --------------------------------------------------

def _pass_ratio(bits):
    res = N.run_suite(bits, verbose=False)
    app = [r for r in res if r.applicable]
    return sum(r.passed for r in app) / len(app)


def test_all_ones_fails():
    assert _pass_ratio(np.ones(200_000, dtype=np.uint8)) < 0.3


def test_alternating_fails():
    assert _pass_ratio(np.tile([0, 1], 100_000).astype(np.uint8)) < 0.4


def test_biased_fails_frequency():
    rng = np.random.default_rng(0)
    biased = (rng.random(200_000) < 0.55).astype(np.uint8)
    assert not N.frequency_monobit(biased).passed


def test_csprng_passes():
    raw = np.frombuffer(os.urandom(1_000_000 // 8), dtype=np.uint8)
    bits = np.unpackbits(raw)[:1_000_000]
    res = N.run_suite(bits, verbose=False)
    app = [r for r in res if r.applicable]
    # Genuine randomness should pass essentially all applicable tests.
    assert sum(r.passed for r in app) >= len(app) - 1


if __name__ == "__main__":
    print("Validating NIST SP 800-22 implementation against spec examples...\n")
    checks = [
        ("Monobit  spec example (p=0.109599)", test_spec_monobit),
        ("Runs     spec example (p=0.147232)", test_spec_runs),
        ("ApEn     spec example (p=0.261961)", test_spec_approximate_entropy),
        ("all-ones fails most tests", test_all_ones_fails),
        ("alternating 0101 fails", test_alternating_fails),
        ("55/45 biased fails frequency", test_biased_fails_frequency),
        ("CSPRNG passes all applicable", test_csprng_passes),
    ]
    ok = 0
    for label, fn in checks:
        try:
            fn()
            print(f"  [PASS] {label}")
            ok += 1
        except AssertionError:
            print(f"  [FAIL] {label}")
    print(f"\n{ok}/{len(checks)} validation checks passed.")
