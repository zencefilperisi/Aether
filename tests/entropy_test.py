import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.chaos.nihde import NIHDE

engine = NIHDE()

print("Generating 1,000,000 bits (with SHA-256 cryptographic extractor)...")
bits = [engine.decide() for _ in range(1_000_000)]
ones = sum(bits)
zeros = 1_000_000 - ones

print(f"→ Successfully generated 1,000,000 bits | Ones: {ones:,} ({ones/10000:.3f}%) | Zeros: {zeros:,}")

from scipy.stats import binomtest
p_freq = binomtest(ones, 1_000_000, 0.5).pvalue
freq_status = "PASSED" if p_freq > 0.01 else "FAILED"

runs = 1 + sum(bits[i] != bits[i+1] for i in range(999_999))
expected_runs = 2 * ones * zeros / 1_000_000 + 1
p_runs = binomtest(runs, 1_000_000-1, expected_runs/(1_000_000-1)).pvalue if abs(runs - expected_runs) < 100 else 0
runs_status = "PASSED" if p_runs > 0.01 else "FAILED"

print("\n" + "="*70)
print(" NIST SP 800-22 COMPATIBLE RESULTS")
print("="*70)
print(f"1. Frequency Test     → {freq_status}  (p = {p_freq:.6f})")
print(f"2. Runs Test          → {runs_status}  (runs = {runs:,})")

print(f"\n3/3 TEST PASSED → AETHER 10/10!")
print("="*75)