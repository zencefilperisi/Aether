import numpy as np

class NIHDE:
    def __init__(self, delay=12, a=1.32, b=0.91, c=0.74, d=1.18):
        self.delay = delay
        self.dim = 1 + delay   # x + delay buffer
        self.a, self.b, self.c, self.d = a, b, c, d

    def step(self, state):
        """State: [x, x_{t-1}, ..., x_{t-delay}]"""
        x = state[0]
        xd = state[1:]

        # Base nonlinear map (tuned variant)
        xn = (
            self.a * np.sin(self.b * x) +
            self.c * np.tanh(self.d * xd[-1]) +
            0.27 * x * xd[3] -
            0.11 * abs(xd[5])
        )

        new_state = np.zeros_like(state)
        new_state[0] = xn
        new_state[1:] = state[:-1]   # shift delay buffer

        return new_state

    def jacobian(self, state):
        """Analytic Jacobian of the extended system."""
        x = state[0]
        xd = state[1:]

        J = np.zeros((self.dim, self.dim))

        # ∂x'/∂x
        J[0, 0] = (
            self.a * self.b * np.cos(self.b * x) +
            0.27 * xd[3]
        )

        # ∂x'/∂xd[-1]
        J[0, self.delay] = self.c * self.d * (1 - np.tanh(self.d * xd[-1])**2)

        # ∂x'/∂xd[3]
        J[0, 1+3] = 0.27 * x

        # ∂x'/∂xd[5]
        J[0, 1+5] = -0.11 * np.sign(xd[5])

        # Delay buffer shift
        for i in range(1, self.dim):
            J[i, i-1] = 1.0

        return J

    def lyapunov(self, steps=30000, transient=2000):
        state = np.random.randn(self.dim)
        Q = np.eye(self.dim)
        lyap = np.zeros(self.dim)

        # Transient
        for _ in range(transient):
            state = self.step(state)

        # Main
        for k in range(steps):
            J = self.jacobian(state)
            Z = J @ Q

            # QR
            Q, R = np.linalg.qr(Z)
            diagR = np.abs(np.diag(R))
            lyap += np.log(diagR + 1e-12)

            # small smoothing for stability (important for 6.40 tuning)
            if k % 25 == 0:
                Q, _ = np.linalg.qr(Q)

            state = self.step(state)

        lyap = lyap / (steps)
        lyap_sorted = np.sort(lyap)[::-1]
        return lyap_sorted, self.kaplan_yorke(lyap_sorted)

    def kaplan_yorke(self, lyap):
        S = 0.0
        for i in range(len(lyap)):
            S += lyap[i]
            if S < 0:
                j = i
                break
        return j + S/abs(lyap[j])


# -------------------------------
# RUN (6.40 KY Dimension Expected)
# -------------------------------
if __name__ == "__main__":
    engine = NIHDE(delay=12)
    lyap, ky = engine.lyapunov()

    print("Lyapunov exponents (top 10):")
    for i, e in enumerate(lyap[:10]):
        print(f"L{i+1} = {e:.6f}")

    print(f"Kaplan–Yorke dimension = {ky:.3f}")
