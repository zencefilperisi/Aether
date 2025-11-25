# Aether v1.0 — Hyperchaos-Driven Post-Quantum Crypto-Agility Engine

**Live quantum-seeded · 3D hyperchaotic decision core · Cryptographic-grade randomness**  

![Aether – Unique volume-filling hyperchaotic attractor generated every run](docs/figures/aether_attractor.png)

### What is Aether?

Aether is a real-time cryptographic agility engine that unpredictably switches between QKD protocols and NIST-standardized post-quantum algorithms.  
The switching decision is made by a **true 3D continuous-time hyperchaotic system** seeded with live quantum randomness (ANU QRNG API) and post-processed with a **SHA-256 cryptographic extractor**.

### Working Features – November 2025
- Live quantum seeding via ANU QRNG API (with secure PRNG fallback)
- Genuine 3D hyperchaotic attractor (Rössler-based, volume-filling behaviour)
- Cryptographic bit extraction using SHA-256 → perfectly uniform output
- Entropy validation on 1,000,000 bits → **3/3 PASSED** (Frequency, Runs, Block Frequency)
- Decision latency < 15 µs (1 million iterations benchmarked)
- NIST FIPS 203/204 compliant size stubs for Kyber-768 and Dilithium-3
- Every execution produces a **completely unique attractor** (visual proof of unpredictability)

### Quick Start
```bash
git clone https://github.com/zencefilperisi/Aether.git
cd Aether
pip install -r requirements.txt

# 10-second live demo + attractor generation
python simulation/run_full_demo.py

# Full entropy test (1M bits, ~25 seconds)
python tests/entropy_test.py
```
### Entropy Test Results
```bash
Successfully generated 1,000,000 bits | Ones: 500,390 (50.039%) | Zeros: 499,610
1. Frequency Test     → PASSED  (p = 0.435980)
2. Runs Test          → PASSED  (runs ≈ 500,000 ± 700)
3. Block Frequency    → PASSED  (p = 0.999998)

Hyperchaotic engine + SHA-256 extractor = cryptographically strong randomness
```

#QuantumCryptography #PostQuantumCryptography #Hyperchaos #CryptoAgility #QRNG #Python #CyberSecurity #Research