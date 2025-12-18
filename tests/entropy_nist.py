import sys
import os
import numpy as np
from scipy.fft import fft 
from scipy.special import erfc 
from scipy.stats import chi2

# --- PATH SETUP ---
sys.path.append(os.getcwd())
try:
    from core.chaos.nihde import NIHDE
except ImportError:
    print("Error: Could not find core.chaos.nihde. Run from the project root.")
    sys.exit(1)

# --- DATA GENERATION ---
print("Aether – Generating 1,000,000 bits for NIST validation...")
engine = NIHDE()
# Collect 125,000 bytes = 1,000,000 bits
raw_bytes = np.array([engine.decide() for _ in range(125_000)], dtype=np.uint8)

# CONVERSION: Convert to float immediately to avoid uint8 underflow (0-1 = 255)
bits = np.unpackbits(raw_bytes).astype(float)

# --- NIST STATISTICAL TESTS ---

def frequency_monobit_test(b):
    """Checks the overall balance of 0s and 1s."""
    n = len(b)
    # Transform bits 0,1 to -1,1
    s_n = np.sum(2 * b - 1)
    s_obs = abs(s_n) / np.sqrt(n)
    p_value = erfc(s_obs / np.sqrt(2))
    return "PASSED" if p_value > 0.01 else "FAILED", p_value

def runs_test(b):
    """Checks if the frequency of transitions is random."""
    n = len(b)
    pi = np.sum(b) / n
    # Prerequisite: Frequency test must not be too far off
    if abs(pi - 0.5) >= (2 / np.sqrt(n)):
        return "FAILED (Imbalance)", 0.0
    
    v_n_obs = np.sum(b[:-1] != b[1:]) + 1
    numerator = abs(v_n_obs - 2 * n * pi * (1 - pi))
    denominator = 2 * np.sqrt(2 * n) * pi * (1 - pi)
    p_value = erfc(numerator / denominator)
    return "PASSED" if p_value > 0.01 else "FAILED", p_value

def spectral_dft_test(b):
    """Checks for periodic patterns (The most difficult test)."""
    n = len(b)
    x = 2 * b - 1
    s = fft(x)
    m = np.abs(s)[:n//2] # Only the first half of frequencies
    
    t = np.sqrt(np.log(1/0.05) * n) # Threshold
    n0 = 0.95 * (n / 2)            # Expected peaks under threshold
    v = np.sum(m < t)              # Observed peaks under threshold
    
    d = (v - n0) / np.sqrt(n * 0.95 * 0.05 / 4)
    p_value = erfc(abs(d) / np.sqrt(2))
    return "PASSED" if p_value > 0.01 else "FAILED", p_value

def block_frequency_test(b, block_size=128):
    """Checks balance within local blocks."""
    n = len(b)
    num_blocks = n // block_size
    # Reshape into blocks and calculate proportion of ones
    blocks = b[:num_blocks * block_size].reshape(num_blocks, block_size)
    pi = np.sum(blocks, axis=1) / block_size
    chi_sq = 4 * block_size * np.sum((pi - 0.5)**2)
    p_value = chi2.sf(chi_sq, df=num_blocks)
    return "PASSED" if p_value > 0.01 else "FAILED", p_value

# --- EXECUTION ---

print("\n" + "="*60)
print("NIST SP 800-22 STATISTICAL SUITE")
print("="*60)

results = [
    ("Frequency (Monobit)", frequency_monobit_test(bits)),
    ("Runs Test", runs_test(bits)),
    ("Spectral (DFT) Test", spectral_dft_test(bits)),
    ("Block Frequency", block_frequency_test(bits))
]

failed = False
for name, (status, p) in results:
    print(f"{name:<25}: {status} (p = {p:.6f})")
    if status != "PASSED": failed = True

print("="*60)
if not failed:
    print("OVERALL RESULT: PASSED - Entropy is statistically sound.")
else:
    print("OVERALL RESULT: FAILED - Patterns detected.")
print("="*60)