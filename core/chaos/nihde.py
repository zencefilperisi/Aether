import numpy as np
import hashlib
import requests

class NIHDE:
    def __init__(self, use_live_qrng=True):
        self.x = np.random.uniform(-1, 1)
        self.y = np.random.uniform(-1, 1)
        self.z = np.random.uniform(0, 10)
        self.a = 0.2
        self.b = 0.2
        self.c = 5.7 + np.random.uniform(-1, 2)

        if use_live_qrng:
            try:
                r = requests.get("https://qrng.anu.edu.au/API/jsonI.php?length=10&type=uint16", timeout=5)
                if r.json().get("success"):
                    seed = np.array(r.json()["data"])
                    np.random.seed(int(hashlib.sha256(seed.tobytes()).hexdigest(), 16) % 2**32)
                    print("Live QRNG seed fetched from ANU")
            except:
                print("Live QRNG unavailable → using local entropy")

        self.x += np.random.uniform(-6, 6)
        self.y += np.random.uniform(-6, 6)
        self.c += np.random.uniform(-2, 2)

    def _step(self):
        dx = -self.y - self.z
        dy = self.x + self.a * self.y
        dz = self.b + self.z * (self.x - self.c)
        self.x += 0.01 * dx
        self.y += 0.01 * dy
        self.z += 0.01 * dz

    def decide(self):
        for _ in range(10):
            self._step()
        return int(self.z * 1000) % 2

    def get_attractor(self, steps=15000):
        traj = np.zeros((steps, 3))
        for i in range(steps):
            self._step()
            traj[i] = [self.x, self.y, self.z]
        return traj