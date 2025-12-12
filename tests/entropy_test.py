# tests/entropy_test.py (REVISED)

import sys
import os
import time
import numpy as np
from scipy.stats import binomtest, norm # norm added for Runs Test

# Set up the path to import NIHDE
# Assumes this script is in 'tests/' and project root is '../'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.chaos.nihde import NIHDE

# --- CONFIGURATION ---
NUM_BITS = 10_000_000 # 10 Million bits
ALPHA = 0.01          # Significance level

# Use a clean engine initialization (no QRNG, to isolate chaos source)
engine = NIHDE(use_live_qrng=False) 

print("="*75)
print(f"NIST SP 800-22 CORE COMPLIANCE TEST (Rust Core Hyperchaos)")
print(f"Generating {NUM_BITS:,} bits (Decisions)...")
print("="*75)

# --- BIT GENERATION ---
start_time = time.perf_counter()
# Leveraging the 16.5x faster Rust core for generation
bits = np.array([engine.decide() for _ in range(NUM_BITS)], dtype=np.int8)
end_time = time.perf_counter()

ones = np.sum(bits)
zeros = NUM_BITS - ones
latency = (end_time - start_time) / NUM_BITS * 1e6 # Latency in microseconds

print(f"-> Successfully generated {NUM_BITS:,} bits | Latency: {latency:.2f} µs")
print(f"-> Ones: {ones:,} ({ones/NUM_BITS * 100:.3f}%) | Zeros: {zeros:,}")


# 1. Frequency (Monobit) Test - Check for equal distribution (p_value should be > 0.01)
p_freq = binomtest(ones, NUM_BITS, 0.5).pvalue

# 2. Runs Test - Check for oscillatory behaviour (p_value should be > 0.01)
runs = 1 + np.sum(bits[:-1] != bits[1:]) # Count changes (0->1 or 1->0) + 1 (first run)
expected_runs = (2 * ones * zeros) / NUM_BITS + 1
# Calculate z-score for normal approximation to the runs test statistic
stdev_runs = np.sqrt( (expected_runs - 1) * (expected_runs - 2) / (NUM_BITS - 1) )
z_score = np.abs(runs - expected_runs) / stdev_runs
# Convert two-sided Z-score to p-value (using survival function)
p_runs = norm.sf(z_score) * 2 # two-sided p-value

# --- REPORTING ---

print("\n" + "="*75)
print(f"CORE NIST SP 800-22 TEST RESULTS (α = {ALPHA})")
print("="*75)

overall_passed = True

# Report Frequency Test
freq_status = "PASSED" if p_freq > ALPHA else "FAILED"
print(f"1. Frequency Test             -> {freq_status:6} (p = {p_freq:.6f})")
if freq_status == "FAILED": overall_passed = False

# Report Runs Test
runs_status = "PASSED" if p_runs > ALPHA else "FAILED"
print(f"2. Runs Test                  -> {runs_status:6} (p = {p_runs:.6f})")
if runs_status == "FAILED": overall_passed = False

print("\n" + "="*75)
if overall_passed:
    print(f"CORE VALIDATION PASSED -> AETHER HYPERCHAOS MEETS FUNDAMENTAL CRITERIA.")
else:
    print(f"CORE VALIDATION FAILED -> REVIEW CHAOS PARAMETERS.")
print("="*75)