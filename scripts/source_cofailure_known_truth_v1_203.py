#!/usr/bin/env python3
"""Synthetic known-truth diagnostic. No ecology/source/response/prediction files read."""
from fractions import Fraction
from itertools import product
import json

STATE_UNIVERSE = tuple(product((0, 1), repeat=3))

def scenario(name):
    if name == "independent":
        return {s: Fraction(1, 8) for s in STATE_UNIVERSE}
    if name == "even_parity":
        return {s: Fraction(1, 4) for s in STATE_UNIVERSE if sum(s) % 2 == 0}
    if name == "odd_parity":
        return {s: Fraction(1, 4) for s in STATE_UNIVERSE if sum(s) % 2 == 1}
    raise ValueError(name)

def moments(distribution):
    assert sum(distribution.values(), Fraction(0)) == 1
    mean = [
        sum((p * s[i] for s, p in distribution.items()), Fraction(0))
        for i in range(3)
    ]
    pair_cross_moment = [
        sum((p * s[i] * s[j] for s, p in distribution.items()), Fraction(0))
        for i, j in ((0, 1), (0, 2), (1, 2))
    ]
    covariances = [
        value - mean[i] * mean[j]
        for value, (i, j) in zip(pair_cross_moment, ((0, 1), (0, 2), (1, 2)))
    ]
    expected_input = sum(
        (p * Fraction(sum(s), 3) for s, p in distribution.items()), Fraction(0)
    )
    input_variance = sum(
        (p * (Fraction(sum(s), 3) - expected_input) ** 2
         for s, p in distribution.items()), Fraction(0)
    )
    no_active_sources = distribution.get((0, 0, 0), Fraction(0))
    all_active_sources = distribution.get((1, 1, 1), Fraction(0))
    return {
        "marginal_activity_probabilities": [str(v) for v in mean],
        "pairwise_joint_activity": [str(v) for v in pair_cross_moment],
        "pairwise_covariance": [str(v) for v in covariances],
        "equal_weight_expected_source_input": str(expected_input),
        "equal_weight_source_input_variance": str(input_variance),
        "zero_active_source_probability": str(no_active_sources),
        "three_active_source_probability": str(all_active_sources),
        "positive_source_probability": str(1 - no_active_sources),
    }

def build_receipt():
    scenarios = {name: moments(scenario(name)) for name in
                 ("independent", "even_parity", "odd_parity")}
    shared_fields = (
        "marginal_activity_probabilities",
        "pairwise_joint_activity",
        "pairwise_covariance",
        "equal_weight_expected_source_input",
        "equal_weight_source_input_variance",
    )
    baseline = scenarios["independent"]
    assert all(all(v[key] == baseline[key] for key in shared_fields)
               for v in scenarios.values())
    assert {name: v["zero_active_source_probability"]
            for name, v in scenarios.items()} == {
                "independent": "1/8", "even_parity": "1/4", "odd_parity": "0"
            }
    return {
        "schema": "structural.source_cofailure_known_truth.v1_203",
        "status": "SYNTHETIC_THREE_SOURCE_IDENTIFIABILITY_COUNTEREXAMPLE",
        "source_file_access": {
            "ecological_observations_read": False,
            "published_response_values_read": False,
            "prediction_binaries_read": False,
        },
        "assumption": "three exchangeable binary source-to-target effective-delivery indicators with equal fixed weights 1/3",
        "scenarios": scenarios,
        "equal_through_pairwise_and_input_variance": True,
        "differing_zero_delivery_probability": True,
        "proof_identity": "P(X1=X2=X3=0) = 1 - sum_i E(Xi) + sum_i<j E(Xi Xj) - E(X1 X2 X3)",
        "interpretation": "Identical source count, mean access, covariance and even total-input variance cannot determine risk of zero incoming viable sources when >=3 sources have higher-order dependence.",
        "not_established": [
            "empirical higher-order source dependence",
            "ecological colonization probability",
            "dispersal mechanism in original mammal range-map graph",
            "effect of conservation intervention",
        ],
    }

if __name__ == "__main__":
    print(json.dumps(build_receipt(), sort_keys=True, indent=2))
