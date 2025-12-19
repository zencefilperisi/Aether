# core/chaos/nihde.py
import os
import sys
import hashlib
import hmac
import requests
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from aether_core_rs import AetherCore
except ImportError:
    print("FATAL ERROR: Could not import aether_core_rs. Ensure the library is compiled and in the path.")
    sys.exit(1)

class NIHDE:
    """
    Nondeterministic High-Entropy Decision Engine (NIHDE).
    
    Architecture:
    1. Entropy Sources: Dual-Core Chaos (Rössler Attractors) + OS Hardware + ANU Quantum RNG
    2. Conditioner: HMAC-DRBG (NIST SP 800-90A) using SHA-256
    3. Health Monitor: Repetition count testing
    """
    
    def __init__(self):
        self.core1 = AetherCore(0.1, 0.1, 0.1, 0.1, 0.1, 14.0, 0.0072973)
        self.core2 = AetherCore(0.1, 0.1, 0.1, 0.2, 0.2, 5.7, 0.0072973)
        
        self.K = b'\x00' * 32
        self.V = b'\x01' * 32
        self.pool = bytearray()
        
        self.last_byte = -1
        self.rep_count = 0
        self.max_rep_limit = 10
        
        self.current_coords = (0.0, 0.0, 0.0)
        
        self.reseed_manual()

    def _get_anu_qrng(self, bytes_needed=32):
        try:
            url = f"https://api.quantumnumbers.anu.edu.au?length={bytes_needed}&type=uint8"
            headers = {"x-api-key": "HLa6wLS9Lb6LiPRZPoUz88MD0MTOt3r62NMRX4TG"}  
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return bytes(resp.json()["data"])
        except Exception as e:
            print(f"[WARNING] ANU QRNG failed ({e}), fallback to os.urandom")
            return os.urandom(bytes_needed)

    def _hmac_update(self, data=None):
        self.K = hmac.new(self.K, self.V + b'\x00' + (data or b''), hashlib.sha256).digest()
        self.V = hmac.new(self.K, self.V, hashlib.sha256).digest()
        if data:
            self.K = hmac.new(self.K, self.V + b'\x01' + data, hashlib.sha256).digest()
            self.V = hmac.new(self.K, self.V, hashlib.sha256).digest()

    def reseed_manual(self):
        _, _, state_hash = self.core1.decide_rust(iterations=1000)
        quantum_seed = self._get_anu_qrng(32)
        seed_material = bytes(state_hash) + os.urandom(32) + quantum_seed
        self._hmac_update(seed_material)
        self.pool = bytearray()
        print("[INFO] NIHDE: reseeded with chaotic + quantum entropy.")

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

    def decide(self):
        if not self.pool:
            self._generate_block()
        byte = self.pool.pop(0)
        if byte == self.last_byte:
            self.rep_count += 1
            if self.rep_count >= self.max_rep_limit:
                raise RuntimeError("Entropy failure: repetition detected!")
        else:
            self.rep_count = 0
        self.last_byte = byte
        return byte

    def get_raw_coordinates(self):
        return self.current_coords[:3]