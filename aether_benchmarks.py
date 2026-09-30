"""
Aether benchmark suite
======================

Measures the Aether NIHDE engine against *real*, industry-standard byte
generators -- not a strawman. Every generator here is something a developer
would genuinely reach for, so the numbers mean something:

  - os.urandom          : the OS CSPRNG (getrandom/BCryptGenRandom). The
                          practical gold standard for cryptographic bytes.
  - secrets             : Python's high-level CSPRNG wrapper (secrets.token_bytes).
  - numpy PCG64         : NumPy's default_rng -- fast, high-quality, NON-crypto.
  - numpy MT19937       : the classic Mersenne Twister -- fast, NON-crypto.
  - Pure-Python Rossler : the SAME chaotic core as Aether, but implemented in
                          pure Python with RK4. This is the honest "before"
                          number that isolates exactly what the Rust port buys.

For each generator we report:
  * throughput  (MB/s) and per-byte latency
  * min-entropy (bits/byte)  via the SP 800-90B most-common-value estimate
  * whether the output is cryptographically intended (context, not a score)

Aether is measured last (requires the compiled Rust core). If the core is not
built, the script still runs and prints the baselines, and clearly marks
Aether as SKIPPED with the build instructions -- it never fabricates a number.

Run:  python aether_benchmarks.py [--bytes 1000000]
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import time
from collections import Counter

import numpy as np


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def min_entropy_mcv(data: bytes) -> float:
    """SP 800-90B most-common-value min-entropy estimate (bits per byte).

    H_min = -log2(p_max) where p_max is the frequency of the most common byte.
    A perfect source scores 8.0; any bias lowers it.
    """
    if not data:
        return 0.0
    counts = Counter(data)
    p_max = max(counts.values()) / len(data)
    return -np.log2(p_max)


# ---------------------------------------------------------------------------
# Generators under test. Each returns `n` bytes.
# ---------------------------------------------------------------------------

class PurePythonRossler:
    """The same dual-Rossler + SHA-256 extraction as Aether's Rust core, but
    written in pure Python. This is the apples-to-apples 'before Rust' baseline.
    """

    def __init__(self):
        import hashlib
        self._sha = hashlib.sha256
        self.x, self.y, self.z = 0.1, 0.1, 0.1
        self.a, self.b, self.c, self.dt = 0.1, 0.1, 14.0, 0.0072973

    def _step(self):
        x, y, z, a, b, c, dt = self.x, self.y, self.z, self.a, self.b, self.c, self.dt

        def d(x, y, z):
            return (-y - z, x + a * y, b + z * (x - c))

        k1 = d(x, y, z)
        k2 = d(x + 0.5 * dt * k1[0], y + 0.5 * dt * k1[1], z + 0.5 * dt * k1[2])
        k3 = d(x + 0.5 * dt * k2[0], y + 0.5 * dt * k2[1], z + 0.5 * dt * k2[2])
        k4 = d(x + dt * k3[0], y + dt * k3[1], z + dt * k3[2])
        self.x += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        self.y += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        self.z += dt / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])

    def bytes(self, n: int) -> bytes:
        out = bytearray()
        import struct
        while len(out) < n:
            self._step()
            packed = struct.pack("<ddd", self.x, self.y, self.z)
            out.extend(self._sha(packed).digest())
        return bytes(out[:n])


def gen_os_urandom(n): return os.urandom(n)
def gen_secrets(n): return secrets.token_bytes(n)
def gen_numpy_pcg64(n): return np.random.default_rng().integers(0, 256, n, dtype=np.uint8).tobytes()
def gen_numpy_mt(n): return np.random.RandomState().randint(0, 256, n, dtype=np.uint8).tobytes()


def gen_aether(n):
    """Aether NIHDE -- requires the compiled Rust core (aether_core_rs)."""
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from core.chaos.nihde import NIHDE
    engine = NIHDE()
    return bytes(engine.decide() for _ in range(n))


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

BASELINES = [
    ("os.urandom (OS CSPRNG)", gen_os_urandom, True),
    ("secrets.token_bytes", gen_secrets, True),
    ("numpy PCG64 (default_rng)", gen_numpy_pcg64, False),
    ("numpy MT19937", gen_numpy_mt, False),
    ("Pure-Python Rossler (pre-Rust)", lambda n: PurePythonRossler().bytes(n), True),
]


def measure(name, fn, n, crypto):
    t0 = time.perf_counter()
    data = fn(n)
    dt = time.perf_counter() - t0
    mbps = (n / 1e6) / dt if dt > 0 else float("inf")
    lat_ns = dt / n * 1e9
    return {
        "name": name,
        "mbps": mbps,
        "lat_ns": lat_ns,
        "min_entropy": min_entropy_mcv(data),
        "crypto": crypto,
        "seconds": dt,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bytes", type=int, default=1_000_000,
                    help="bytes to generate per source (default 1,000,000)")
    args = ap.parse_args()
    n = args.bytes

    print("=" * 92)
    print(f"AETHER BENCHMARK  --  {n:,} bytes per source  --  honest comparison vs real generators")
    print("=" * 92)
    print(f"{'Generator':<34} {'Throughput':>12} {'Latency':>12} {'Min-Entropy':>12} {'Crypto?':>9}")
    print(f"{'':<34} {'(MB/s)':>12} {'(ns/byte)':>12} {'(bits/byte)':>12} {'':>9}")
    print("-" * 92)

    results = []
    for name, fn, crypto in BASELINES:
        try:
            r = measure(name, fn, n, crypto)
            results.append(r)
            print(f"{r['name']:<34} {r['mbps']:>12.2f} {r['lat_ns']:>12.1f} "
                  f"{r['min_entropy']:>12.4f} {'yes' if crypto else 'no':>9}")
        except Exception as exc:
            print(f"{name:<34}  ERROR: {exc}")

    # Aether last -- may not be built.
    print("-" * 92)
    try:
        r = measure("Aether NIHDE (Rust core)", gen_aether, n, True)
        results.append(r)
        print(f"{r['name']:<34} {r['mbps']:>12.2f} {r['lat_ns']:>12.1f} "
              f"{r['min_entropy']:>12.4f} {'yes':>9}")

        # Honest speedup line: Aether vs the pure-Python version of the SAME core.
        pre = next((x for x in results if "Pure-Python" in x["name"]), None)
        if pre:
            speedup = pre["lat_ns"] / r["lat_ns"]
            print("-" * 92)
            print(f"-> Rust port speedup over the SAME core in pure Python: {speedup:.1f}x")
            print(f"   (This is the honest 'what Rust bought us' number.)")
        # Context vs os.urandom, without pretending to beat it.
        osr = next((x for x in results if "os.urandom" in x["name"]), None)
        if osr:
            print(f"-> For reference, os.urandom runs at {osr['mbps']:.0f} MB/s; Aether trades "
                  f"raw speed for an\n   auditable chaotic+quantum construction, not the other way around.")
    except Exception as exc:
        print(f"{'Aether NIHDE (Rust core)':<34}  SKIPPED -- Rust core not built ({exc})")
        print()
        print("   To include Aether, build the core first:")
        print("     cd core/chaos/aether_core_rs && maturin develop --release && cd -")
        print("   then re-run this script.")

    print("=" * 92)
    print("Notes:")
    print("  * 'Crypto?' marks whether a source is *intended* for cryptographic use.")
    print("    numpy PCG64/MT19937 are fast but MUST NOT be used for keys.")
    print("  * Min-entropy is the SP 800-90B most-common-value estimate on this sample;")
    print("    it is a smoke test, not a substitute for the full NIST SP 800-22 suite")
    print("    (see tests/nist_sp800_22.py).")
    print("=" * 92)


if __name__ == "__main__":
    main()
