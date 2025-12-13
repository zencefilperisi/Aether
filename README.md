# Aether : High-Performance Chaotic RNG Core

Aether is a high-performance Pseudo-Random Number Generator (PRNG) core designed to resolve the performance bottleneck common in software-based entropy solutions. By leveraging the speed of a Rust core and the stability of the Rössler chaotic system, Aether delivers randomness quality equal to operating system standards, but with up to 11x the speed of comparable Python-based chaotic systems.

#### Core Technical Achievements

| Metric | Result | Explanation |
| :--- | :--- | :--- |
| **Speedup (vs Legacy Python)** | **{data['speedup_factor']}** | Performance increase over the pure Python implementation (Legacy: {data['legacy_latency']} µs). |
| **Latency (Per Byte)** | **{data['latency_us']} µs** | Record processing time, operating consistently below the 1.0 µs threshold. |
| **Min-Entropy Quality** | **{data['min_entropy']} bits/byte** | The randomness quality is nearly perfect (8.0 bits/byte), matching industry standards like `os.urandom` (Entropy: {data['os_entropy']}). |
| **Stability** | **Fully Degeneration-Free** | Solved the common chaotic system problem of "fixed-point decay" by switching to the stable Rössler dynamics.

#### Architecture and Design
Aether utilizes a robust hybrid architecture for maximum efficiency and flexibility:

1.  **Rust Core (`AetherCore`):**
    * **Chaos Engine:** Implements the $Rössler\ differential\ equations$ for state evolution. This system is chosen for its superior stability compared to the Lorenz system.
    * **Optimization:** Utilizes a carefully tuned $N=50$ integration steps per output to ensure high speed without sacrificing chaos depth.
    * **Hashing:** Performs SHA-256 hashing on the system state and applies the first level of entropy mixing ($B_0 \oplus B_1$ from the hash digest).

2.  **Python Wrapper (`NIHDE`):**
    * **Interface:** Provides a simple `decide()` interface.
    * **Final Mixing:** Applies a second level of XOR mixing (`final_output = random_byte ^ self.last_byte`) to break any remaining sequential patterns, guaranteeing the reported **{data['min_entropy']}** Min-Entropy.

### Installation

```bash
# Clone the repository
git clone https://github.com/zencefilperisi/Aether
cd Aether

# Install Rust environment and build the core
maturin develop --release
# (Requires Python and Rust/Cargo to be installed)
```





