# core/chaos/nihde.py
"""
NIHDE -- Nondeterministic High-entropy Injection & Decision Engine
==================================================================

Conditioning layer that sits on top of the Rust chaotic core. It combines
three entropy sources and conditions them with an HMAC-DRBG (the construction
described in NIST SP 800-90A), and runs a lightweight health check on the
output stream.

Entropy sources:
    1. Dual Rossler chaotic cores (Rust: aether_core_rs)
    2. OS CSPRNG (os.urandom)
    3. ANU Quantum RNG over HTTPS (optional; falls back to OS on any failure)

Design notes:
    * This module NEVER calls sys.exit or prints fatal banners on import --
      it is a library. If the compiled Rust core is missing it raises
      AetherCoreNotBuilt, which callers can catch.
    * The ANU QRNG API key is read from the environment (ANU_QRNG_API_KEY),
      loaded from a local .env if python-dotenv is installed. No secret is
      ever hard-coded. If no key is present, the quantum source is simply
      skipped and the engine runs on chaos + OS entropy.
"""

import os
import hashlib
import hmac

import numpy as np

try:  # optional: load .env if python-dotenv is available
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    import requests
except Exception:  # requests is only needed for the optional QRNG source
    requests = None


class AetherCoreNotBuilt(ImportError):
    """Raised when the compiled Rust core (aether_core_rs) is unavailable."""


try:
    from aether_core_rs import AetherCore
except ImportError as exc:  # pragma: no cover - depends on build environment
    _IMPORT_ERROR = exc
    AetherCore = None
else:
    _IMPORT_ERROR = None


ANU_QRNG_URL = "https://api.quantumnumbers.anu.edu.au"


class NIHDE:
    """
    Architecture:
        1. Entropy sources: dual chaotic Rossler cores + OS CSPRNG + ANU QRNG
        2. Conditioner: HMAC-DRBG (NIST SP 800-90A) with SHA-256
        3. Health monitor: repetition count test on the output stream
    """

    def __init__(self, use_quantum: bool = True):
        if AetherCore is None:
            raise AetherCoreNotBuilt(
                "aether_core_rs is not built. Run: "
                "cd core/chaos/aether_core_rs && maturin develop --release"
            ) from _IMPORT_ERROR

        self.core1 = AetherCore(0.1, 0.1, 0.1, 0.1, 0.1, 14.0, 0.0072973)
        self.core2 = AetherCore(0.1, 0.1, 0.1, 0.2, 0.2, 5.7, 0.0072973)

        self.K = b"\x00" * 32
        self.V = b"\x01" * 32
        self.pool = bytearray()

        self.last_byte = -1
        self.rep_count = 0
        self.max_rep_limit = 10

        self.current_coords = (0.0, 0.0, 0.0)
        self._use_quantum = use_quantum

        self.reseed_manual()

    # -- entropy sources ----------------------------------------------------

    def _get_anu_qrng(self, bytes_needed: int = 32) -> bytes | None:
        """Fetch quantum random bytes from ANU. Returns None (never raises)
        if the key is absent, requests is missing, or the call fails, so the
        engine degrades gracefully to chaos + OS entropy."""
        api_key = os.environ.get("ANU_QRNG_API_KEY")
        if not api_key or requests is None or not self._use_quantum:
            return None
        try:
            resp = requests.get(
                ANU_QRNG_URL,
                params={"length": bytes_needed, "type": "uint8"},
                headers={"x-api-key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            return bytes(resp.json()["data"])
        except Exception:
            return None

    # -- HMAC-DRBG (SP 800-90A) --------------------------------------------

    def _hmac_update(self, data: bytes | None = None):
        self.K = hmac.new(self.K, self.V + b"\x00" + (data or b""), hashlib.sha256).digest()
        self.V = hmac.new(self.K, self.V, hashlib.sha256).digest()
        if data:
            self.K = hmac.new(self.K, self.V + b"\x01" + data, hashlib.sha256).digest()
            self.V = hmac.new(self.K, self.V, hashlib.sha256).digest()

    def reseed_manual(self):
        _, _, state_hash = self.core1.decide_rust(iterations=1000)
        seed_material = bytes(state_hash) + os.urandom(32)
        quantum_seed = self._get_anu_qrng(32)
        if quantum_seed:
            seed_material += quantum_seed
        self._hmac_update(seed_material)
        self.pool = bytearray()

    def _generate_block(self):
        temp_output = bytearray()
        while len(temp_output) < 1024:
            _, _, state_tuple = self.core1.decide_rust(iterations=1)
            self.current_coords = state_tuple
            self.V = hmac.new(self.K, self.V, hashlib.sha256).digest()
            temp_output.extend(self.V)
        _, _, state2 = self.core2.decide_rust(iterations=128)
        self._hmac_update(bytes(state2))
        self.pool = temp_output[:1024]

    # -- output + health check ---------------------------------------------

    def decide(self) -> int:
        if not self.pool:
            self._generate_block()
        byte = self.pool.pop(0)
        if byte == self.last_byte:
            self.rep_count += 1
            if self.rep_count >= self.max_rep_limit:
                raise RuntimeError("Entropy health check failed: repetition detected")
        else:
            self.rep_count = 0
        self.last_byte = byte
        return byte

    def generate_bytes(self, n: int) -> bytes:
        """Convenience: return n conditioned bytes as a bytes object."""
        return bytes(self.decide() for _ in range(n))

    def get_raw_coordinates(self):
        return self.current_coords[:3]
