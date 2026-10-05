from math import isclose

from scripts.verify_sparse_source_configuration_theory_v1_155 import (
    analytic_moments,
    exact_moments,
    verify_monotonic_relative_sensitivity,
)


def test_exact_moments_match_closed_form():
    weights = [0.1, 0.4, 0.9, 2.0, 5.0]
    for n in range(1, len(weights) + 1):
        observed = exact_moments(weights, n)
        expected = analytic_moments(weights, n)
        assert all(
            isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
            for a, b in zip(observed, expected)
        )


def test_relative_configuration_sensitivity_declines_with_source_count():
    verify_monotonic_relative_sensitivity([0.1, 0.4, 0.9, 2.0, 5.0])


def test_uniform_weights_have_zero_configuration_variance():
    for n in range(1, 5):
        _, variance, cv2 = analytic_moments([3.0, 3.0, 3.0, 3.0], n)
        assert variance == 0.0
        assert cv2 == 0.0
