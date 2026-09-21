#!/usr/bin/env python3
"""Deterministic held-out known-truth benchmark for typed connectivity."""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "benchmarks/connectivity_operator_prediction_expected_v0_2.json"
SEED = 20260921
N = 320
TEST_MODULUS = 5
RIDGE = 1e-9


def solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    augmented = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(augmented[r][col]))
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        value = augmented[col][col]
        if abs(value) < 1e-12:
            raise ValueError("singular normal equation")
        for j in range(col, n + 1):
            augmented[col][j] /= value
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            for j in range(col, n + 1):
                augmented[row][j] -= factor * augmented[col][j]
    return [augmented[i][-1] for i in range(n)]


def fit_linear(x: list[list[float]], y: list[float]) -> list[float]:
    p = len(x[0])
    gram = [[0.0] * p for _ in range(p)]
    rhs = [0.0] * p
    for row, outcome in zip(x, y):
        for i in range(p):
            rhs[i] += row[i] * outcome
            for j in range(p):
                gram[i][j] += row[i] * row[j]
    for i in range(1, p):
        gram[i][i] += RIDGE
    return solve(gram, rhs)


def predict(x: list[list[float]], beta: list[float]) -> list[float]:
    return [sum(value * coef for value, coef in zip(row, beta)) for row in x]


def mse(y: list[float], fitted: list[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(y, fitted)) / len(y)


def make_rows(target_operator: str) -> list[tuple[float, float, float, float, float]]:
    if target_operator not in {"pollen_flow", "whole_individual"}:
        raise ValueError("unknown target operator")
    rng = random.Random(SEED)
    rows = []
    for _ in range(N):
        local_state = rng.random()
        pollen = rng.random()
        individual = rng.random()
        collapsed = (pollen + individual) / 2.0
        noise = (rng.random() - 0.5) * 0.08
        signal = pollen if target_operator == "pollen_flow" else individual
        outcome = 0.45 * local_state + 1.10 * signal + noise
        rows.append((local_state, pollen, individual, collapsed, outcome))
    return rows


def features(row: tuple[float, float, float, float, float], model: str) -> list[float]:
    local_state, pollen, individual, collapsed, _ = row
    if model == "reference":
        return [1.0, local_state]
    if model == "pollen":
        return [1.0, local_state, pollen]
    if model == "whole_individual":
        return [1.0, local_state, individual]
    if model == "collapsed":
        return [1.0, local_state, collapsed]
    if model == "typed_both":
        return [1.0, local_state, pollen, individual]
    raise ValueError(model)


def evaluate(target_operator: str) -> dict:
    rows = make_rows(target_operator)
    train = [row for i, row in enumerate(rows) if i % TEST_MODULUS != 0]
    test = [row for i, row in enumerate(rows) if i % TEST_MODULUS == 0]
    y_train = [row[-1] for row in train]
    y_test = [row[-1] for row in test]

    scores = {}
    for model in ("reference", "pollen", "whole_individual", "collapsed", "typed_both"):
        x_train = [features(row, model) for row in train]
        x_test = [features(row, model) for row in test]
        beta = fit_linear(x_train, y_train)
        score = mse(y_test, predict(x_test, beta))
        scores[model] = {
            "mse": round(score, 12),
            "coefficients": [round(value, 12) for value in beta],
        }

    reference = scores["reference"]["mse"]
    for model, values in scores.items():
        values["delta_mse_vs_reference"] = round(values["mse"] - reference, 12)

    return {
        "target_operator": target_operator,
        "n_train": len(train),
        "n_test": len(test),
        "scores": scores,
    }


def run() -> dict:
    return {
        "schema": "structural.connectivity_operator_prediction_known_truth.v0_2",
        "status": "synthetic_known_truth",
        "design": {
            "seed": SEED,
            "n": N,
            "test_modulus": TEST_MODULUS,
            "outcome": "0.45*local_state + 1.10*matching_operator + bounded_noise",
            "models": ["reference", "pollen", "whole_individual", "collapsed", "typed_both"],
        },
        "results": {
            "pollen_flow": evaluate("pollen_flow"),
            "whole_individual": evaluate("whole_individual"),
        },
        "claim_boundary": [
            "synthetic held-out prediction only",
            "operator matching is known by construction",
            "does not establish natural operator prevalence",
            "does not alter frozen Structural paper results",
        ],
    }


def main() -> int:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
