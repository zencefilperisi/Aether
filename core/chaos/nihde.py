# core/chaos/nihde.py

import os
import sys
import struct 

# Add the project root directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from aether_core_rs import AetherCore
    RUST_CORE_AVAILABLE = True
except ImportError as e:
    print(f"FATAL ERROR: Could not import aether_core_rs: {e}")
    RUST_CORE_AVAILABLE = False


class NIHDE:
    """
    Nondeterministic High-Entropy Decision Engine (NIHDE).
    Optimized random number generator based on the Rössler chaotic system.
    Continuous Health Check (CHC) has been removed for maximum performance.
    """
    def __init__(self, use_live_qrng=False):
        
        # Aether/Rössler stable parameters (a=0.1, b=0.1, c=14.0)
        self.core = AetherCore(0.1, 0.1, 0.1, 0.1, 0.1, 14.0, 0.01)
        
        # Reseed counter (for information purposes only)
        self.reseed_count = 0
        
        # Stores the last byte for double XOR (to break static patterns)
        self.last_byte = 0
        # ------------------------------------------------------------------

    # Manual reseed method is kept for external calls if needed.
    def reseed_manual(self):
        """Manually reseeds the system using os.urandom for maximum stability."""
        try:
            random_data = os.urandom(24)
            
            raw_x = struct.unpack('<d', random_data[0:8])[0]
            raw_y = struct.unpack('<d', random_data[8:16])[0]
            raw_z = struct.unpack('<d', random_data[16:24])[0]

            # Normalize to the [-100.0, 100.0) range
            new_x = (abs(raw_x) % 200.0) - 100.0
            new_y = (abs(raw_y) % 200.0) - 100.0
            new_z = (abs(raw_z) % 200.0) - 100.0
            
            # Prevent overly small initial values
            if abs(new_x) < 0.1: new_x += 0.1 
            if abs(new_y) < 0.1: new_y += 0.1
            if abs(new_z) < 0.1: new_z += 0.1

            self.core.reseed_rust(new_x, new_y, new_z)
            self.reseed_count += 1
            print(f"[INFO] System manually reseeded (Count: {self.reseed_count}).")
        
        except Exception as e:
            print(f"[CRITICAL] Manual reseeding failed: {e}")


    # CORE METHOD: decide (N=50 Iterations and Double XOR)
    def decide(self):
        """Fetches entropy from the Rust core and applies double XOR."""
        
        # 1. Get byte from the Rust core (N=50 iterations for speed)
        random_byte = self.core.decide_rust(iterations=50) 
        
        # 2. Double XOR: Current byte XORed with the previous byte.
        final_output = random_byte ^ self.last_byte
        self.last_byte = random_byte 

        # 3. Return the final, high-entropy byte.
        return final_output
    

    #test change