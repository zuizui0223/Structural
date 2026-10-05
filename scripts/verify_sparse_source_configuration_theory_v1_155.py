#!/usr/bin/env python3
"""Verify the finite-source configuration-sensitivity identity used in v1.155.

No ecological response data are read.  The script compares exact enumeration of
all n-subsets against the closed-form mean and variance of summed source weights.
"""

from __future__ import annotations

from itertools import combinations
from math import fsum, isclose
from random import Random


def analytic_moments(weights: list[float], n: int) -> tuple[float, float, float]:
    m = len(weights)
    if not 1 <= n <= m:
        raise ValueError("n must satisfy 1 <= n <= number of weights")
    mu = fsum(weights) / m
    sigma2 = fsum((w - mu) ** 2 for w in weights) / m
    mean = n * mu
    variance = 0.0 if m == 1 else n * (m - n) / (m - 1) * sigma2
    cv2 = 0.0 if mean == 0.0 else variance / (mean * mean)
    return mean, variance, cv2


def exact_moments(weights: list[float], n: int) -> tuple[float, float, float]:
    totals = [fsum(weights[j] for j in idx) for idx in combinations(range(len(weights)), n)]
    mean = fsum(totals) / len(totals)
    variance = fsum((x - mean) ** 2 for x in totals) / len(totals)
    cv2 = 0.0 if mean == 0.0 else variance / (mean * mean)
    return mean, variance, cv2


def verify(weights: list[float]) -> None:
    m = len(weights)
    for n in range(1, m + 1):
        observed = exact_moments(weights, n)
        expected = analytic_moments(weights, n)
        for a, b in zip(observed, expected):
            assert isclose(a, b, rel_tol=1e-12, abs_tol=1e-12), (weights, n, observed, expected)


def verify_monotonic_relative_sensitivity(weights: list[float]) -> None:
    values = [analytic_moments(weights, n)[2] for n in range(1, len(weights) + 1)]
    assert all(a >= b - 1e-15 for a, b in zip(values, values[1:])), values


def main() -> None:
    deterministic_cases = [
        [1.0, 2.0],
        [0.2, 0.5, 1.7],
        [0.1, 0.4, 0.9, 2.0, 5.0],
        [3.0, 3.0, 3.0, 3.0],
    ]
    rng = Random(155)
    random_cases = [[0.01 + 5.0 * rng.random() for _ in range(m)] for m in range(2, 9)]

    for weights in deterministic_cases + random_cases:
        verify(weights)
        verify_monotonic_relative_sensitivity(weights)

    print("PASS: exact subset enumeration matches the v1.155 finite-source identity")
    print("PASS: relative configuration sensitivity is non-increasing with occupied-source count")


if __name__ == "__main__":
    main()
