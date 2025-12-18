import os
import sys
import hashlib
import hmac

# Ensure the Rust core can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from aether_core_rs import AetherCore
except ImportError:
    print("FATAL ERROR: Could not import aether_core_rs. Ensure the library is compiled and in the path.")

class NIHDE:
    """
    Nondeterministic High-Entropy Decision Engine (NIHDE).
    
    Architecture:
    1. Entropy Source: Dual-Core Chaos (Rössler Attractors) + OS Hardware Entropy.
    2. Conditioner: HMAC-DRBG (NIST SP 800-90A) using SHA-256.
    3. Health Monitor: Continuous repetition count testing to detect entropy failure.
    """
    
    def __init__(self):
        # Chaos Engine Parameters (Rössler Attractors)
        self.core1 = AetherCore(0.1, 0.1, 0.1, 0.1, 0.1, 14.0, 0.0072973)
        self.core2 = AetherCore(0.1, 0.1, 0.1, 0.2, 0.2, 5.7, 0.0072973)
        
        # HMAC-DRBG Internal State
        self.K = b'\x00' * 32  # 256-bit Key
        self.V = b'\x01' * 32  # 256-bit Value
        self.pool = bytearray()
        
        # Health Monitor State
        self.last_byte = -1
        self.rep_count = 0
        self.max_rep_limit = 10 # Halt if the same byte repeats 10 times
        
        # Coordinate tracking for visualization
        self.current_coords = (0.0, 0.0, 0.0)
        
        # Initial seeding
        self.reseed_manual()

    def _hmac_update(self, data=None):
        """Internal HMAC_DRBG Update function as per NIST SP 800-90A."""
        self.K = hmac.new(self.K, self.V + b'\x00' + (data or b''), hashlib.sha256).digest()
        self.V = hmac.new(self.K, self.V, hashlib.sha256).digest()
        if data:
            self.K = hmac.new(self.K, self.V + b'\x01' + data, hashlib.sha256).digest()
            self.V = hmac.new(self.K, self.V, hashlib.sha256).digest()

    def reseed_manual(self):
        """Gathers entropy from Chaos Core 1 and OS to refresh the internal state."""
        # Evolve core to a high-entropy state
        _, _, state_hash = self.core1.decide_rust(iterations=1000)
        
        # Combine Chaos with Hardware Entropy
        seed_material = bytes(state_hash) + os.urandom(32)
        self._hmac_update(seed_material)
        
        self.pool = bytearray()
        print("[INFO] NIHDE: HMAC-DRBG state reseeded with chaotic entropy.")

    def _generate_block(self):
        """Produces 1024 bytes of whitened entropy."""
        temp_output = bytearray()
        
        while len(temp_output) < 1024:
            # Advance core 1 and capture coordinates for visualizer
            # Assuming decide_rust returns (val1, val2, state_tuple)
            _, _, state_tuple = self.core1.decide_rust(iterations=1)
            self.current_coords = (state_tuple[0], state_tuple[1], state_tuple[2])
            
            # HMAC-DRBG Generation step
            self.V = hmac.new(self.K, self.V, hashlib.sha256).digest()
            temp_output.extend(self.V)
        
        # Periodic perturbation using Core 2 to ensure non-determinism
        _, _, state2 = self.core2.decide_rust(iterations=128)
        self._hmac_update(bytes(state2))
        
        self.pool = temp_output[:1024]

    def decide(self):
        """Returns one byte with real-time health monitoring."""
        if not self.pool:
            self._generate_block()
        
        byte = self.pool.pop(0)

        # --- RUNTIME HEALTH MONITOR ---
        if byte == self.last_byte:
            self.rep_count += 1
            if self.rep_count >= self.max_rep_limit:
                raise RuntimeError("CRITICAL FAILURE: Entropy health check failed (Repetition Detected)!")
        else:
            self.rep_count = 0
        
        self.last_byte = byte
        return byte

    def get_raw_coordinates(self):
        """Returns the current X, Y, Z coordinates for 3D visualization."""
        return self.current_coords