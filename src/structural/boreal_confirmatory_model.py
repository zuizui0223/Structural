"""Deterministic pooled ridge-logistic model for the boreal v0.55 test."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


class BorealConfirmatoryModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class RidgeLogisticFit:
    columns: tuple[str, ...]
    coefficients: tuple[float, ...]
    iterations: int
    final_max_abs_delta: float
    ridge_lambda: float


def population_mean_sd(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        raise BorealConfirmatoryModelError("empty standardization vector")
    xs = [float(value) for value in values]
    if not all(math.isfinite(value) for value in xs):
        raise BorealConfirmatoryModelError(
            "nonfinite standardization value"
        )
    mean = math.fsum(xs) / len(xs)
    variance = math.fsum(
        (value - mean) ** 2 for value in xs
    ) / len(xs)
    sd = math.sqrt(variance)
    if not math.isfinite(sd) or sd <= 0.0:
        raise BorealConfirmatoryModelError(
            "zero/nonfinite population SD"
        )
    return mean, sd


def freeze_standardization(
    rows: Sequence[Mapping[str, float]],
    columns: Sequence[str],
) -> dict[str, dict[str, float]]:
    if not rows:
        raise BorealConfirmatoryModelError(
            "cannot standardize empty rows"
        )
    result = {}
    for column in columns:
        values = []
        for row in rows:
            if column not in row:
                raise BorealConfirmatoryModelError(
                    f"missing standardization column: {column}"
                )
            value = float(row[column])
            if not math.isfinite(value):
                raise BorealConfirmatoryModelError(
                    f"nonfinite standardization column: {column}"
                )
            values.append(value)
        mean, sd = population_mean_sd(values)
        result[column] = {"mean": mean, "sd": sd}
    return result


def apply_standardization(
    row: Mapping[str, float],
    *,
    columns: Sequence[str],
    constants: Mapping[str, Mapping[str, float]],
) -> tuple[float, ...]:
    values = []
    for column in columns:
        if column not in row or column not in constants:
            raise BorealConfirmatoryModelError(
                f"missing standardized feature: {column}"
            )
        value = float(row[column])
        mean = float(constants[column]["mean"])
        sd = float(constants[column]["sd"])
        if (
            not math.isfinite(value)
            or not math.isfinite(mean)
            or not math.isfinite(sd)
            or sd <= 0.0
        ):
            raise BorealConfirmatoryModelError(
                f"invalid standardized feature: {column}"
            )
        values.append((value - mean) / sd)
    return tuple(values)


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _solve_linear_system(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
) -> list[float]:
    n = len(vector)
    if n < 1 or len(matrix) != n:
        raise BorealConfirmatoryModelError(
            "linear-system dimension mismatch"
        )
    a = [
        [float(value) for value in row] + [float(vector[i])]
        for i, row in enumerate(matrix)
    ]
    if any(len(row) != n + 1 for row in a):
        raise BorealConfirmatoryModelError(
            "linear-system matrix is not square"
        )

    for column in range(n):
        pivot_row = max(
            range(column, n),
            key=lambda row: (abs(a[row][column]), -row),
        )
        pivot = a[pivot_row][column]
        if not math.isfinite(pivot) or abs(pivot) < 1e-14:
            raise BorealConfirmatoryModelError(
                "ridge IRLS linear solve is singular"
            )
        if pivot_row != column:
            a[column], a[pivot_row] = a[pivot_row], a[column]

        pivot = a[column][column]
        for row in range(column + 1, n):
            factor = a[row][column] / pivot
            if factor == 0.0:
                continue
            a[row][column] = 0.0
            for j in range(column + 1, n + 1):
                a[row][j] -= factor * a[column][j]

    solution = [0.0] * n
    for row in range(n - 1, -1, -1):
        rhs = a[row][n] - math.fsum(
            a[row][j] * solution[j]
            for j in range(row + 1, n)
        )
        pivot = a[row][row]
        if abs(pivot) < 1e-14:
            raise BorealConfirmatoryModelError(
                "ridge IRLS backsolve is singular"
            )
        solution[row] = rhs / pivot
        if not math.isfinite(solution[row]):
            raise BorealConfirmatoryModelError(
                "nonfinite ridge IRLS solution"
            )
    return solution


def fit_ridge_logistic(
    x_rows: Sequence[Sequence[float]],
    y_values: Sequence[int],
    *,
    columns: Sequence[str],
    ridge_lambda: float = 1.0,
    max_iterations: int = 100,
    tolerance: float = 1e-8,
) -> RidgeLogisticFit:
    if ridge_lambda <= 0 or not math.isfinite(ridge_lambda):
        raise BorealConfirmatoryModelError(
            "ridge_lambda must be finite and positive"
        )
    if max_iterations < 1 or tolerance <= 0:
        raise BorealConfirmatoryModelError(
            "invalid IRLS iteration settings"
        )
    if not x_rows or len(x_rows) != len(y_values):
        raise BorealConfirmatoryModelError(
            "fit rows/targets mismatch"
        )

    p = len(columns)
    if p < 1:
        raise BorealConfirmatoryModelError(
            "fit must have at least one column"
        )
    x = []
    y = []
    for row, target in zip(x_rows, y_values):
        values = tuple(float(value) for value in row)
        if len(values) != p:
            raise BorealConfirmatoryModelError(
                "fit row width mismatch"
            )
        if not all(math.isfinite(value) for value in values):
            raise BorealConfirmatoryModelError(
                "nonfinite fit predictor"
            )
        if target not in (0, 1):
            raise BorealConfirmatoryModelError(
                "fit target must be binary"
            )
        x.append(values)
        y.append(float(target))

    beta = [0.0] * p
    final_delta = math.inf

    for iteration in range(1, max_iterations + 1):
        eta = [
            math.fsum(value * coefficient for value, coefficient in zip(row, beta))
            for row in x
        ]
        mu = [_sigmoid(value) for value in eta]
        weights = [value * (1.0 - value) for value in mu]

        gradient = []
        for j in range(p):
            score = math.fsum(
                row[j] * (target - mean)
                for row, target, mean in zip(x, y, mu)
            )
            if j != 0:
                score -= ridge_lambda * beta[j]
            gradient.append(score)

        hessian = []
        for j in range(p):
            row_values = []
            for k in range(p):
                value = math.fsum(
                    weight * row[j] * row[k]
                    for row, weight in zip(x, weights)
                )
                if j == k and j != 0:
                    value += ridge_lambda
                row_values.append(value)
            hessian.append(row_values)

        delta = _solve_linear_system(hessian, gradient)
        beta = [
            coefficient + change
            for coefficient, change in zip(beta, delta)
        ]
        final_delta = max(abs(change) for change in delta)
        if not all(math.isfinite(value) for value in beta):
            raise BorealConfirmatoryModelError(
                "nonfinite fitted coefficient"
            )
        if final_delta <= tolerance:
            return RidgeLogisticFit(
                columns=tuple(columns),
                coefficients=tuple(beta),
                iterations=iteration,
                final_max_abs_delta=float(final_delta),
                ridge_lambda=float(ridge_lambda),
            )

    raise BorealConfirmatoryModelError(
        "ridge logistic IRLS did not converge"
    )


def predict_probability(
    row: Sequence[float],
    fit: RidgeLogisticFit,
    *,
    clip: tuple[float, float] = (1e-12, 0.999999999999),
) -> float:
    values = tuple(float(value) for value in row)
    if len(values) != len(fit.coefficients):
        raise BorealConfirmatoryModelError(
            "prediction row width mismatch"
        )
    lo, hi = map(float, clip)
    if not 0.0 < lo < hi < 1.0:
        raise BorealConfirmatoryModelError(
            "invalid probability clip"
        )
    eta = math.fsum(
        value * coefficient
        for value, coefficient in zip(values, fit.coefficients)
    )
    probability = _sigmoid(eta)
    return min(hi, max(lo, probability))


def logit_jeffreys(successes: int, trials: int) -> float:
    if trials < 1 or successes < 0 or successes > trials:
        raise BorealConfirmatoryModelError(
            "invalid Jeffreys occupancy counts"
        )
    probability = (successes + 0.5) / (trials + 1.0)
    return math.log(probability / (1.0 - probability))


def fit_mapping(fit: RidgeLogisticFit) -> dict:
    return {
        "columns": list(fit.columns),
        "coefficients_hex": [
            float(value).hex() for value in fit.coefficients
        ],
        "iterations": fit.iterations,
        "final_max_abs_delta_hex": (
            float(fit.final_max_abs_delta).hex()
        ),
        "ridge_lambda_hex": float(fit.ridge_lambda).hex(),
    }
