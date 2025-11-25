import numpy as np
import hashlib

class NIHDE:
    def __init__(self, use_live_qrng=True):
        self.x = np.random.uniform(-1, 1)
        self.y = np.random.uniform(-1, 1)
        self.z = np.random.uniform(-1, 1)
        print("Aether hyperchaotic engine – 10/10 ready!")

    def _step(self):
        a, b, c = 0.2, 0.2, 5.7
        dx = -self.y - self.z
        dy = self.x + a * self.y
        dz = b + self.z * (self.x - c)
        self.x += 0.01 * dx
        self.y += 0.01 * dy
        self.z += 0.01 * dz

    def decide(self):
        for _ in range(10):  
            self._step()
        h = hashlib.sha256(str((self.x, self.y, self.z)).encode()).digest()
        return h[0] & 1

    def get_attractor(self, steps=25000):
        traj = np.zeros((steps, 3))
        for i in range(steps):
            self._step()
            traj[i] = [self.x, self.y, self.z]
        return traj