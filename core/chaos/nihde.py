# core/chaos/nihde.py 

import numpy as np
import hashlib
import requests
import sys 
import os 

# Add current directory to path to find aether_core_rs.pyd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Rust core (Now imports directly from path)
from aether_core_rs import AetherCore 

class NIHDE:
    def __init__(self, use_live_qrng=True):
        
        # 1. PARAMETER DEFINITION
        self.a = 0.2
        self.b = 0.2
        self.dt = 0.01

        # Initial conditions and randomization of c parameter
        self.x = np.random.uniform(-1, 1) 
        self.y = np.random.uniform(-1, 1) 
        self.z = np.random.uniform(0, 10)
        self.c = 5.7 + np.random.uniform(-1, 2) # Original formula randomization

        if use_live_qrng:
            try:
                # Fetching seed from ANU Quantum Random Number Generator
                r = requests.get("https://qrng.anu.edu.au/API/jsonI.php?length=10&type=uint16", timeout=5)
                if r.json().get("success"):
                    seed = np.array(r.json()["data"])
                    # Cryptographic hash to ensure sufficient entropy for NumPy seed
                    np.random.seed(int(hashlib.sha256(seed.tobytes()).hexdigest(), 16) % 2**32)
                    print("Live QRNG seed fetched from ANU")
            except:
                print("Live QRNG unavailable -> using local entropy")

        # Further state randomization after potential QRNG seed application
        self.x += np.random.uniform(-6, 6)
        self.y += np.random.uniform(-6, 6)
        self.c += np.random.uniform(-2, 2)

        # 2. INITIALIZE RUST CORE (Pass all state variables to the highly optimized Rust kernel)
        self.core = AetherCore(
            x=self.x, y=self.y, z=self.z,
            a=self.a, b=self.b, c=self.c, dt=self.dt
        )
        
    def decide(self):
        # Delegate the decision step (50 iterations) to the Rust core
        # Iterations increased from 10 to 50 for deeper entropy extraction
        return self.core.decide_rust(iterations=50)

    def get_attractor(self, steps=15000):
        # Delegate attractor generation to the Rust core
        trajectory_flat = self.core.get_trajectory_rust(steps)
        # Reshape the 1D NumPy array received from Rust into a (steps, 3) matrix
        return trajectory_flat.reshape((-1, 3))