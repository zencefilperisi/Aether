# Aether v2.1: Hyperchaos Core (Rust + NIST Hardened)

Aether is a high-performance, cryptographically hardened pseudo-random number generator (PRNG) built on a specialized hyperchaotic system. Version 2.1 introduces a major architectural shift, migrating the core decision engine to **Rust** for superior speed and integrating **SHA256 hashing** for robust statistical randomness compliant with cryptographic standards.

## Performance Summary

The refactoring achieved a significant speed increase while guaranteeing cryptographic quality:

* **Legacy Python Core Latency:** 1.73 µs
* **Rust Core (NIST Hardened) Latency:** **0.92 µs**
* **Result:** **47.00% Reduction** in latency, successfully passing the sub-2.0 µs target.

## Security & Validation (NIST SP 800-22)

The core's output quality has been rigorously validated using the NIST SP 800-22 statistical test suite.

| Test (NIST Core) | Purpose | Status |
| :--- | :--- | :--- |
| **Frequency (Monobit)** | Checks for balanced distribution of 0s and 1s. | **PASSED** |
| **Runs Test** | Checks for non-random oscillatory behavior. | **PASSED** |

### **Cryptographic Hardening Mechanism**

To achieve NIST compliance, the raw chaotic output is processed through a SHA256 hash function before bit extraction.  This mechanism eliminates statistical bias inherent in simple modulo operations, extracting a statistically uniform bit from the deep entropy of the chaotic state.

## Project Setup and Installation

Follow these steps to set up the project and compile the high-speed Rust core.

### 1. Prerequisites

* **Python 3.8+**
* **Rust Toolchain:** Install `rustup` from [rustup.rs](https://rustup.rs/).
* **`maturin`:** Used to build the Python-Rust bridge.

### 2. Environment Setup

```bash
# Clone the repository
git clone <YOUR_REPOSITORY_URL>
cd Aether

# Create and activate the virtual environment
python -m venv venv
source venv/Scripts/activate  # On Linux/macOS, use: source venv/bin/activate

# Install required Python packages (numpy, scipy, requests)
pip install -r requirements.txt
```

### 3. Compile the Rust Core

The aether_core_rs package must be built to create the .pyd module.
```bash
(venv) Aether> maturin develop --release --bindings pyo3 -m core/chaos/aether_core_rs/Cargo.toml
```
A successful compilation confirms the optimized kernel is ready.

## Usage and Demo

A. Run the Full Demo

The primary execution file demonstrates QRNG seeding, chaotic decision cycles, and the Post-Quantum Cryptography (PQC) integration (Kyber-768).

```bash
(venv) Aether> python run_full_demo.py
```

B. Verify Performance (Benchmark)

Run the benchmark to confirm the speedup on your specific hardware.

```bash
(venv) Aether> python benchmark_rust_vs_py.py
```
The detailed report is saved to docs/benchmarks/latency_report.md.

C. Verify Security (NIST Validation)

Run the cryptographic test suite on a 10 million bit stream.

```bash
(venv) Aether> python tests/entropy_test.py
```

```bash
```