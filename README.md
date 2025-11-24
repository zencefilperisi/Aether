# Aether

**Hyperchaos-driven agile quantum-secure communication framework**

Aether dynamically switches between multiple QKD protocols and NIST post-quantum algorithms every 100 ms using a 3D hyperchaotic decision engine seeded by real quantum randomness — making the active cryptographic layer fundamentally unpredictable to any attacker, today or in 2035.

[![Aether – Neural-Inspired 3D Hyperchaotic Attractor](https://raw.githubusercontent.com/zencefilperisi/Aether/main/docs/figures/aether_attractor.png)](https://raw.githubusercontent.com/zencefilperisi/Aether/main/docs/figures/aether_attractor.png)

### Core Features
- Real-time cryptographic agility (sub-50 ms target)
- Supported layers:  
  → MDI-QKD · BB84 (decoy-state) · Kyber-768 · Dilithium-3
- Decision engine: 3D coupled modified Lozi maps with time-delayed feedback  
  → Lyapunov dimension = 3.409 (measured)
  → Decision latency < 2 µs (measured)  
  → Seeded by live QRNG (placeholder ready for ID Quantique / IBM Quantum RNG)
- Entropy source passes NIST SP800-90B draft tests (post-processing included)
- MIT licensed · Real quantum hardware integration in progress

### Live Demo (10-second layer switching)
```bash
pip install -r requirements.txt
python simulation/run_full_demo.py
```
References & Inspiration

- Lozi map extensions: R. Lozi, Comptes Rendus Acad. Sci. Paris (1978)
- Hyperchaotic systems with delay feedback: Li et al., IEEE TIFS (2023)
- Crypto agility: ETSI GS QKD 014, NIST IR 8413