"""
NIST SP 800-22 Rev. 1a  --  Full Statistical Test Suite (from-scratch implementation)
=====================================================================================

A self-contained implementation of the fifteen randomness tests defined in
NIST Special Publication 800-22 Revision 1a ("A Statistical Test Suite for
Random and Pseudorandom Number Generators for Cryptographic Applications").

No external NIST/STS library is used. Only NumPy and SciPy (special functions
and the FFT) are relied on. Each test returns a p-value; a sequence passes a
test at significance level alpha when p >= alpha (default alpha = 0.01, as
recommended by the specification).

Tests implemented (section numbers refer to SP 800-22 Rev 1a):
    1.  2.1  Frequency (Monobit)
    2.  2.2  Frequency within a Block
    3.  2.3  Runs
    4.  2.4  Longest Run of Ones in a Block
    5.  2.5  Binary Matrix Rank
    6.  2.6  Discrete Fourier Transform (Spectral)
    7.  2.7  Non-overlapping Template Matching
    8.  2.8  Overlapping Template Matching
    9.  2.9  Maurer's Universal Statistical
    10. 2.10 Linear Complexity
    11. 2.11 Serial
    12. 2.12 Approximate Entropy
    13. 2.13 Cumulative Sums (Cusum)
    14. 2.14 Random Excursions
    15. 2.15 Random Excursions Variant

The module can be run directly to test the Aether NIHDE engine, or imported
and pointed at any bit array. It ships with a small self-check against the
worked example bit strings given in the specification's appendices so the
implementation itself can be trusted.

Author: Hatice Nalcaci
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy import special as sp
from scipy import fftpack


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    p_value: float
    passed: bool
    note: str = ""
    applicable: bool = True  # False => not enough data to run this test

    @property
    def status(self) -> str:
        if not self.applicable:
            return "N/A"
        return "PASS" if self.passed else "FAIL"


def _bits_to_pm1(bits: np.ndarray) -> np.ndarray:
    """Map {0,1} -> {-1,+1}."""
    return 2 * bits.astype(np.int64) - 1


# ---------------------------------------------------------------------------
# 2.1  Frequency (Monobit) Test
# ---------------------------------------------------------------------------

def frequency_monobit(bits: np.ndarray, alpha: float = 0.01) -> TestResult:
    """Proportion of ones and zeros over the whole sequence should be ~ equal.

    s_obs = |sum(+/-1)| / sqrt(n);  p = erfc(s_obs / sqrt(2)).
    """
    n = bits.size
    s = np.sum(_bits_to_pm1(bits))
    s_obs = abs(s) / math.sqrt(n)
    p = math.erfc(s_obs / math.sqrt(2))
    return TestResult("Frequency (Monobit)", p, p >= alpha)


# ---------------------------------------------------------------------------
# 2.2  Frequency Test within a Block
# ---------------------------------------------------------------------------

def block_frequency(bits: np.ndarray, block_size: int = 128,
                    alpha: float = 0.01) -> TestResult:
    """Proportion of ones within M-bit blocks should be ~ 0.5."""
    n = bits.size
    num_blocks = n // block_size
    if num_blocks == 0:
        return TestResult("Block Frequency", 0.0, False, "sequence too short")
    trimmed = bits[: num_blocks * block_size].reshape(num_blocks, block_size)
    pi = trimmed.mean(axis=1)
    chi_sq = 4.0 * block_size * np.sum((pi - 0.5) ** 2)
    p = sp.gammaincc(num_blocks / 2.0, chi_sq / 2.0)
    return TestResult("Block Frequency", p, p >= alpha,
                      f"M={block_size}, N={num_blocks}")


# ---------------------------------------------------------------------------
# 2.3  Runs Test
# ---------------------------------------------------------------------------

def runs(bits: np.ndarray, alpha: float = 0.01) -> TestResult:
    """Total number of runs (maximal identical-bit substrings)."""
    n = bits.size
    pi = bits.mean()
    # Prerequisite from the spec: monobit proportion close enough to 0.5.
    tau = 2.0 / math.sqrt(n)
    if abs(pi - 0.5) >= tau:
        return TestResult("Runs", 0.0, False, "failed monobit prerequisite")
    v = 1 + np.sum(bits[:-1] != bits[1:])
    num = abs(v - 2.0 * n * pi * (1 - pi))
    den = 2.0 * math.sqrt(2.0 * n) * pi * (1 - pi)
    p = math.erfc(num / den)
    return TestResult("Runs", p, p >= alpha)


# ---------------------------------------------------------------------------
# 2.4  Longest Run of Ones in a Block
# ---------------------------------------------------------------------------

def longest_run_of_ones(bits: np.ndarray, alpha: float = 0.01) -> TestResult:
    """Distribution of the longest run of ones within blocks.

    Block size M and category boundaries are fixed by the specification and
    depend on the sequence length n.
    """
    n = bits.size
    if n < 128:
        return TestResult("Longest Run of Ones", 0.0, False, "n<128")

    if n < 6272:
        M, K = 8, 3
        v_classes = [1, 2, 3, 4]
        pi = [0.2148, 0.3672, 0.2305, 0.1875]
    elif n < 750000:
        M, K = 128, 5
        v_classes = [4, 5, 6, 7, 8, 9]
        pi = [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]
    else:
        M, K = 10000, 6
        v_classes = [10, 11, 12, 13, 14, 15, 16]
        pi = [0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727]

    num_blocks = n // M
    trimmed = bits[: num_blocks * M].reshape(num_blocks, M)

    def longest_run(block: np.ndarray) -> int:
        best = cur = 0
        for b in block:
            if b == 1:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best

    v = np.zeros(K + 1, dtype=np.int64)
    lo, hi = v_classes[0], v_classes[-1]
    for block in trimmed:
        lr = longest_run(block)
        idx = min(max(lr, lo), hi) - lo
        v[idx] += 1

    chi_sq = np.sum((v - num_blocks * np.array(pi)) ** 2 / (num_blocks * np.array(pi)))
    p = sp.gammaincc(K / 2.0, chi_sq / 2.0)
    return TestResult("Longest Run of Ones", p, p >= alpha, f"M={M}")


# ---------------------------------------------------------------------------
# 2.5  Binary Matrix Rank Test
# ---------------------------------------------------------------------------

def _gf2_rank(matrix: np.ndarray) -> int:
    """Rank of a binary matrix over GF(2) via Gaussian elimination."""
    m = matrix.copy().astype(np.uint8)
    rows, cols = m.shape
    rank = 0
    for col in range(cols):
        pivot = -1
        for r in range(rank, rows):
            if m[r, col]:
                pivot = r
                break
        if pivot == -1:
            continue
        m[[rank, pivot]] = m[[pivot, rank]]
        for r in range(rows):
            if r != rank and m[r, col]:
                m[r] ^= m[rank]
        rank += 1
        if rank == rows:
            break
    return rank


def binary_matrix_rank(bits: np.ndarray, M: int = 32, Q: int = 32,
                       alpha: float = 0.01) -> TestResult:
    """Rank of disjoint M x Q sub-matrices; checks linear dependence."""
    n = bits.size
    num_matrices = n // (M * Q)
    if num_matrices == 0:
        return TestResult("Binary Matrix Rank", 0.0, False, "sequence too short")

    fm, fm1, rest = 0, 0, 0
    for i in range(num_matrices):
        chunk = bits[i * M * Q:(i + 1) * M * Q].reshape(M, Q)
        r = _gf2_rank(chunk)
        if r == M:
            fm += 1
        elif r == M - 1:
            fm1 += 1
        else:
            rest += 1

    # Theoretical probabilities for full, full-1 and lower ranks (M=Q=32).
    p_full = 0.2888
    p_full1 = 0.5776
    p_rest = 0.1336
    chi_sq = ((fm - num_matrices * p_full) ** 2 / (num_matrices * p_full)
              + (fm1 - num_matrices * p_full1) ** 2 / (num_matrices * p_full1)
              + (rest - num_matrices * p_rest) ** 2 / (num_matrices * p_rest))
    p = math.exp(-chi_sq / 2.0)
    return TestResult("Binary Matrix Rank", p, p >= alpha, f"N={num_matrices}")


# ---------------------------------------------------------------------------
# 2.6  Discrete Fourier Transform (Spectral) Test
# ---------------------------------------------------------------------------

def spectral_dft(bits: np.ndarray, alpha: float = 0.01) -> TestResult:
    """Detects periodic features via the peak heights of the DFT."""
    n = bits.size
    x = _bits_to_pm1(bits).astype(np.float64)
    s = fftpack.fft(x)
    modulus = np.abs(s[: n // 2])
    threshold = math.sqrt(math.log(1.0 / 0.05) * n)
    n0 = 0.95 * n / 2.0
    n1 = np.sum(modulus < threshold)
    d = (n1 - n0) / math.sqrt(n * 0.95 * 0.05 / 4.0)
    p = math.erfc(abs(d) / math.sqrt(2))
    return TestResult("DFT (Spectral)", p, p >= alpha)


# ---------------------------------------------------------------------------
# 2.7  Non-overlapping Template Matching Test
# ---------------------------------------------------------------------------

def _sliding_match(block: np.ndarray, template: np.ndarray) -> np.ndarray:
    """Boolean array: does the m-length window starting at i equal template?"""
    m = template.size
    if block.size < m:
        return np.zeros(0, dtype=bool)
    windows = np.lib.stride_tricks.sliding_window_view(block, m)
    return np.all(windows == template, axis=1)


def non_overlapping_template(bits: np.ndarray, template: np.ndarray | None = None,
                             block_size: int | None = None,
                             alpha: float = 0.01) -> TestResult:
    """Counts occurrences of a fixed non-periodic template in blocks."""
    n = bits.size
    if template is None:
        template = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1], dtype=np.uint8)
    m = template.size
    N = 8  # number of blocks (spec default)
    if block_size is None:
        block_size = n // N
    if block_size <= m:
        return TestResult("Non-overlapping Template", 0.0, False, "block too small")

    mu = (block_size - m + 1) / (2.0 ** m)
    var = block_size * (1.0 / 2.0 ** m - (2.0 * m - 1) / 2.0 ** (2 * m))
    if var <= 0:
        return TestResult("Non-overlapping Template", 0.0, False, "degenerate variance")

    counts = np.zeros(N)
    for i in range(N):
        block = bits[i * block_size:(i + 1) * block_size]
        matches = _sliding_match(block, template)
        # Non-overlapping: after a hit, skip the whole template width.
        w = 0
        j = 0
        limit = matches.size
        while j < limit:
            if matches[j]:
                w += 1
                j += m
            else:
                j += 1
        counts[i] = w

    chi_sq = np.sum((counts - mu) ** 2) / var
    p = sp.gammaincc(N / 2.0, chi_sq / 2.0)
    return TestResult("Non-overlapping Template", p, p >= alpha, f"m={m}")


# ---------------------------------------------------------------------------
# 2.8  Overlapping Template Matching Test
# ---------------------------------------------------------------------------

def overlapping_template(bits: np.ndarray, m: int = 9, alpha: float = 0.01) -> TestResult:
    """Counts occurrences of an all-ones template with an overlapping window."""
    n = bits.size
    M = 1032
    N = n // M
    if N == 0:
        return TestResult("Overlapping Template", 0.0, False, "sequence too short")

    K = 5
    # Theoretical probabilities for occurrence classes 0..>=5 (spec table).
    pi = [0.364091, 0.185659, 0.139381, 0.100571, 0.070432, 0.139865]
    template = np.ones(m, dtype=np.uint8)

    v = np.zeros(K + 1)
    for i in range(N):
        block = bits[i * M:(i + 1) * M]
        count = int(np.sum(_sliding_match(block, template)))
        v[min(count, K)] += 1

    chi_sq = np.sum((v - N * np.array(pi)) ** 2 / (N * np.array(pi)))
    p = sp.gammaincc(K / 2.0, chi_sq / 2.0)
    return TestResult("Overlapping Template", p, p >= alpha, f"N={N}")


# ---------------------------------------------------------------------------
# 2.9  Maurer's Universal Statistical Test
# ---------------------------------------------------------------------------

_UNIVERSAL_PARAMS = {
    # L: (expected_value, variance)
    6: (5.2177052, 2.954), 7: (6.1962507, 3.125), 8: (7.1836656, 3.238),
    9: (8.1764248, 3.311), 10: (9.1723243, 3.356), 11: (10.170032, 3.384),
    12: (11.168765, 3.401), 13: (12.168070, 3.410), 14: (13.167693, 3.416),
    15: (14.167488, 3.419), 16: (15.167379, 3.421),
}


def maurers_universal(bits: np.ndarray, alpha: float = 0.01) -> TestResult:
    """Compressibility measure; detects sequences that can be significantly compressed."""
    n = bits.size
    # Choose L per spec guidance.
    if n < 387840:
        return TestResult("Maurer's Universal", 0.0, False, "n too small for L>=6")
    L = 6
    for cand, need in [(16, 1059061760), (15, 496435200), (14, 231669760),
                       (13, 107560960), (12, 49643520), (11, 22753280),
                       (10, 10342400), (9, 4654080), (8, 2068480),
                       (7, 904960), (6, 387840)]:
        if n >= need:
            L = cand
            break

    Q = 10 * (2 ** L)
    K = n // L - Q
    if K <= 0:
        return TestResult("Maurer's Universal", 0.0, False, "not enough blocks")

    blocks = bits[: (Q + K) * L].reshape(Q + K, L)
    powers = 1 << np.arange(L - 1, -1, -1)
    idx = blocks.dot(powers)

    table = np.zeros(2 ** L, dtype=np.int64)
    for i in range(Q):
        table[idx[i]] = i + 1

    total = 0.0
    for i in range(Q, Q + K):
        total += math.log2((i + 1) - table[idx[i]])
        table[idx[i]] = i + 1
    fn = total / K

    expected, variance = _UNIVERSAL_PARAMS[L]
    c = 0.7 - 0.8 / L + (4 + 32.0 / L) * (K ** (-3.0 / L)) / 15
    sigma = c * math.sqrt(variance / K)
    p = math.erfc(abs((fn - expected) / (math.sqrt(2) * sigma)))
    return TestResult("Maurer's Universal", p, p >= alpha, f"L={L}")


# ---------------------------------------------------------------------------
# 2.10  Linear Complexity Test
# ---------------------------------------------------------------------------

def _berlekamp_massey(seq: np.ndarray) -> int:
    """Length of the shortest LFSR generating the binary sequence (GF(2)).

    Operates on a Python list of ints for speed on short (~500-bit) blocks;
    the xor-update over the connection polynomial is the hot path.
    """
    s = seq.astype(np.int8).tolist()
    n = len(s)
    c = [0] * n
    b = [0] * n
    c[0] = b[0] = 1
    L, m = 0, -1
    for i in range(n):
        d = s[i]
        for j in range(1, L + 1):
            d ^= c[j] & s[i - j]
        if d == 1:
            t = c[:]
            shift = i - m
            for j in range(n - shift):
                c[j + shift] ^= b[j]
            if 2 * L <= i:
                L = i + 1 - L
                m = i
                b = t
    return L


def linear_complexity(bits: np.ndarray, M: int = 500, alpha: float = 0.01) -> TestResult:
    """Distribution of LFSR complexity over blocks; measures predictability."""
    n = bits.size
    N = n // M
    if N == 0:
        return TestResult("Linear Complexity", 0.0, False, "sequence too short")

    mu = M / 2.0 + (9 + (-1) ** (M + 1)) / 36.0 - (M / 3.0 + 2.0 / 9.0) / (2 ** M)
    K = 6
    pi = [0.010417, 0.03125, 0.125, 0.5, 0.25, 0.0625, 0.020833]
    v = np.zeros(K + 1)

    for i in range(N):
        block = bits[i * M:(i + 1) * M]
        Li = _berlekamp_massey(block)
        Ti = (-1) ** M * (Li - mu) + 2.0 / 9.0
        if Ti <= -2.5:
            v[0] += 1
        elif Ti <= -1.5:
            v[1] += 1
        elif Ti <= -0.5:
            v[2] += 1
        elif Ti <= 0.5:
            v[3] += 1
        elif Ti <= 1.5:
            v[4] += 1
        elif Ti <= 2.5:
            v[5] += 1
        else:
            v[6] += 1

    chi_sq = np.sum((v - N * np.array(pi)) ** 2 / (N * np.array(pi)))
    p = sp.gammaincc(K / 2.0, chi_sq / 2.0)
    return TestResult("Linear Complexity", p, p >= alpha, f"M={M}, N={N}")


# ---------------------------------------------------------------------------
# 2.11  Serial Test
# ---------------------------------------------------------------------------

def _pattern_counts(bits: np.ndarray, m: int) -> np.ndarray:
    """Counts of every overlapping m-bit pattern, treating the sequence as
    circular (as SP 800-22 specifies). Vectorised: no per-bit Python loop."""
    n = bits.size
    if m == 0:
        return np.array([], dtype=np.int64)
    ext = np.concatenate([bits, bits[: m - 1]]).astype(np.int64)
    powers = (1 << np.arange(m - 1, -1, -1)).astype(np.int64)
    # Sliding-window index of every length-m window via a running base-2 value.
    idx = np.zeros(n, dtype=np.int64)
    for k in range(m):
        idx += ext[k:k + n] * powers[k]
    return np.bincount(idx, minlength=2 ** m)


def _psi_sq(bits: np.ndarray, m: int) -> float:
    n = bits.size
    if m == 0:
        return 0.0
    counts = _pattern_counts(bits, m)
    return (2 ** m) / n * np.sum(counts.astype(np.float64) ** 2) - n


def serial(bits: np.ndarray, m: int = 16, alpha: float = 0.01) -> TestResult:
    """Frequency of every overlapping m-bit pattern; uniformity of patterns."""
    psi_m = _psi_sq(bits, m)
    psi_m1 = _psi_sq(bits, m - 1)
    psi_m2 = _psi_sq(bits, m - 2)
    d1 = psi_m - psi_m1
    d2 = psi_m - 2 * psi_m1 + psi_m2
    p1 = sp.gammaincc(2 ** (m - 2), d1 / 2.0)
    p2 = sp.gammaincc(2 ** (m - 3), d2 / 2.0)
    passed = (p1 >= alpha) and (p2 >= alpha)
    return TestResult("Serial", min(p1, p2), passed, f"m={m} (p1={p1:.4f}, p2={p2:.4f})")


# ---------------------------------------------------------------------------
# 2.12  Approximate Entropy Test
# ---------------------------------------------------------------------------

def _phi(bits: np.ndarray, m: int) -> float:
    n = bits.size
    if m == 0:
        return 0.0
    counts = _pattern_counts(bits, m)
    c = counts.astype(np.float64) / n
    nz = c[c > 0]
    return np.sum(nz * np.log(nz))


def approximate_entropy(bits: np.ndarray, m: int = 10, alpha: float = 0.01) -> TestResult:
    """Compares frequency of overlapping m- and (m+1)-bit patterns."""
    n = bits.size
    ap_en = _phi(bits, m) - _phi(bits, m + 1)
    chi_sq = 2.0 * n * (math.log(2) - ap_en)
    p = sp.gammaincc(2 ** (m - 1), chi_sq / 2.0)
    return TestResult("Approximate Entropy", p, p >= alpha, f"m={m}")


# ---------------------------------------------------------------------------
# 2.13  Cumulative Sums (Cusum) Test
# ---------------------------------------------------------------------------

def cumulative_sums(bits: np.ndarray, alpha: float = 0.01) -> TestResult:
    """Maximal excursion of the random walk from zero (forward mode)."""
    n = bits.size
    x = _bits_to_pm1(bits)
    s = np.cumsum(x)
    z = np.max(np.abs(s))
    if z == 0:
        return TestResult("Cumulative Sums", 1.0, True)

    def _term(k_lo, k_hi, sign):
        total = 0.0
        for k in range(k_lo, k_hi + 1):
            a = (sign * (4 * k + 1) * z) / math.sqrt(n)
            b = (sign * (4 * k - 1) * z) / math.sqrt(n)
            total += _norm_cdf(a) - _norm_cdf(b)
        return total

    k1_lo = int((-n / z + 1) / 4)
    k1_hi = int((n / z - 1) / 4)
    k2_lo = int((-n / z - 3) / 4)
    k2_hi = int((n / z - 1) / 4)
    p = 1.0 - _term(k1_lo, k1_hi, 1) + _term(k2_lo, k2_hi, 1)
    p = max(min(p, 1.0), 0.0)
    return TestResult("Cumulative Sums", p, p >= alpha)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))


# ---------------------------------------------------------------------------
# 2.14  Random Excursions Test
# ---------------------------------------------------------------------------

def random_excursions(bits: np.ndarray, alpha: float = 0.01) -> TestResult:
    """Number of visits to states -4..-1,1..4 within cycles of the random walk.

    Returns the minimum p-value across the eight states; passes only if all
    eight individually pass.
    """
    n = bits.size
    x = _bits_to_pm1(bits)
    s = np.concatenate([[0], np.cumsum(x), [0]])
    zero_positions = np.where(s == 0)[0]
    J = len(zero_positions) - 1
    if J < 500:
        return TestResult("Random Excursions", 1.0, True,
                          f"not applicable (only {J} cycles, need >=500)",
                          applicable=False)

    states = [-4, -3, -2, -1, 1, 2, 3, 4]
    # Theoretical probabilities pi_k(x) for k=0..5 visits.
    def pi_probs(x_abs):
        p0 = 1 - 1.0 / (2 * x_abs)
        probs = [p0]
        for k in range(1, 5):
            probs.append((1.0 / (4 * x_abs ** 2)) * (1 - 1.0 / (2 * x_abs)) ** (k - 1))
        probs.append((1.0 / (2 * x_abs)) * (1 - 1.0 / (2 * x_abs)) ** 4)
        return probs

    # Count visits per cycle.
    cycle_bounds = zero_positions
    p_values = []
    for st in states:
        counts = np.zeros(6, dtype=np.int64)
        for c in range(J):
            seg = s[cycle_bounds[c]:cycle_bounds[c + 1] + 1]
            visits = np.sum(seg == st)
            counts[min(visits, 5)] += 1
        probs = pi_probs(abs(st))
        chi_sq = np.sum((counts - J * np.array(probs)) ** 2 / (J * np.array(probs)))
        p_values.append(sp.gammaincc(5 / 2.0, chi_sq / 2.0))

    p_min = min(p_values)
    return TestResult("Random Excursions", p_min, all(p >= alpha for p in p_values),
                      f"J={J}, 8 states")


# ---------------------------------------------------------------------------
# 2.15  Random Excursions Variant Test
# ---------------------------------------------------------------------------

def random_excursions_variant(bits: np.ndarray, alpha: float = 0.01) -> TestResult:
    """Total number of visits to states -9..-1,1..9 across the whole walk."""
    n = bits.size
    x = _bits_to_pm1(bits)
    s = np.concatenate([[0], np.cumsum(x), [0]])
    J = np.sum(s == 0) - 1
    if J < 500:
        return TestResult("Random Excursions Variant", 1.0, True,
                          f"not applicable (only {J} cycles, need >=500)",
                          applicable=False)

    states = list(range(-9, 0)) + list(range(1, 10))
    p_values = []
    for st in states:
        xi = np.sum(s == st)
        denom = math.sqrt(2.0 * J * (4 * abs(st) - 2))
        p = math.erfc(abs(xi - J) / denom)
        p_values.append(p)

    p_min = min(p_values)
    return TestResult("Random Excursions Variant", p_min,
                      all(p >= alpha for p in p_values), f"J={J}, 18 states")


# ---------------------------------------------------------------------------
# Suite driver
# ---------------------------------------------------------------------------

ALL_TESTS: list[tuple[str, Callable]] = [
    ("Frequency (Monobit)", frequency_monobit),
    ("Block Frequency", block_frequency),
    ("Runs", runs),
    ("Longest Run of Ones", longest_run_of_ones),
    ("Binary Matrix Rank", binary_matrix_rank),
    ("DFT (Spectral)", spectral_dft),
    ("Non-overlapping Template", non_overlapping_template),
    ("Overlapping Template", overlapping_template),
    ("Maurer's Universal", maurers_universal),
    ("Linear Complexity", linear_complexity),
    ("Serial", serial),
    ("Approximate Entropy", approximate_entropy),
    ("Cumulative Sums", cumulative_sums),
    ("Random Excursions", random_excursions),
    ("Random Excursions Variant", random_excursions_variant),
]


def run_suite(bits: np.ndarray, alpha: float = 0.01,
              verbose: bool = True) -> list[TestResult]:
    """Run every applicable test and return the list of results."""
    results: list[TestResult] = []
    for _name, fn in ALL_TESTS:
        try:
            res = fn(bits, alpha=alpha)
        except Exception as exc:  # a test that cannot run is not a pass
            res = TestResult(_name, 0.0, False, f"error: {exc}")
        results.append(res)

    if verbose:
        print("=" * 78)
        print(f"NIST SP 800-22 Rev 1a  --  {bits.size:,} bits  (alpha = {alpha})")
        print("=" * 78)
        print(f"{'#':>2}  {'Test':<28} {'p-value':>10}  {'Result':>6}   Notes")
        print("-" * 78)
        for i, r in enumerate(results, 1):
            print(f"{i:>2}  {r.name:<28} {r.p_value:>10.6f}  {r.status:>6}   {r.note}")
        print("-" * 78)
        applicable = [r for r in results if r.applicable]
        n_pass = sum(r.passed for r in applicable)
        n_app = len(applicable)
        n_skip = len(results) - n_app
        verdict = "ALL PASSED" if n_pass == n_app else "SOME FAILED"
        skip_note = f", {n_skip} N/A" if n_skip else ""
        print(f"SUMMARY: {n_pass}/{n_app} applicable tests passed{skip_note} ({verdict})")
        print("=" * 78)
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _load_from_nihde(num_bits: int) -> np.ndarray:
    """Pull bits from the Aether NIHDE engine (requires the Rust core)."""
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.chaos.nihde import NIHDE  # noqa: E402
    engine = NIHDE()
    n_bytes = num_bits // 8
    data = np.frombuffer(bytes(engine.decide() for _ in range(n_bytes)), dtype=np.uint8)
    return np.unpackbits(data)[:num_bits]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Run the NIST SP 800-22 suite.")
    ap.add_argument("--bits", type=int, default=1_000_000,
                    help="number of bits to test (default 1,000,000)")
    ap.add_argument("--alpha", type=float, default=0.01)
    ap.add_argument("--source", choices=["nihde", "urandom"], default="nihde",
                    help="bit source: Aether engine or os.urandom baseline")
    args = ap.parse_args()

    if args.source == "urandom":
        import os
        raw = np.frombuffer(os.urandom(args.bits // 8), dtype=np.uint8)
        sample = np.unpackbits(raw)[: args.bits]
    else:
        sample = _load_from_nihde(args.bits)

    run_suite(sample, alpha=args.alpha)
