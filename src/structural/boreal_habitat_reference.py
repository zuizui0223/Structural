"""Deterministic response-independent habitat reference for boreal islands."""
from __future__ import annotations

import math
from typing import Sequence


class BorealHabitatReferenceError(RuntimeError):
    pass


def population_mean_sd(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        raise BorealHabitatReferenceError("empty habitat vector")
    xs = [float(x) for x in values]
    if not all(math.isfinite(x) for x in xs):
        raise BorealHabitatReferenceError("nonfinite habitat value")
    mean = sum(xs) / len(xs)
    variance = sum((x - mean) ** 2 for x in xs) / len(xs)
    sd = math.sqrt(variance)
    if not math.isfinite(sd) or sd <= 0.0:
        raise BorealHabitatReferenceError(
            "habitat variable has zero/nonfinite population SD"
        )
    return mean, sd


def standardize_columns(
    rows: Sequence[Sequence[float]],
) -> tuple[list[list[float]], list[tuple[float, float]]]:
    if not rows:
        raise BorealHabitatReferenceError("empty habitat matrix")
    width = len(rows[0])
    if width < 1:
        raise BorealHabitatReferenceError("habitat matrix has no columns")
    if any(len(row) != width for row in rows):
        raise BorealHabitatReferenceError("ragged habitat matrix")

    columns = [
        [float(row[j]) for row in rows]
        for j in range(width)
    ]
    constants = [population_mean_sd(col) for col in columns]
    zrows = []
    for row in rows:
        zrows.append([
            (float(row[j]) - constants[j][0]) / constants[j][1]
            for j in range(width)
        ])
    return zrows, constants


def correlation_matrix(
    zrows: Sequence[Sequence[float]],
) -> list[list[float]]:
    if not zrows:
        raise BorealHabitatReferenceError("empty standardized matrix")
    n = len(zrows)
    p = len(zrows[0])
    if p < 1 or any(len(row) != p for row in zrows):
        raise BorealHabitatReferenceError("invalid standardized matrix")
    out = [[0.0 for _ in range(p)] for _ in range(p)]
    for j in range(p):
        for k in range(j, p):
            value = sum(row[j] * row[k] for row in zrows) / n
            out[j][k] = value
            out[k][j] = value
    return out


def jacobi_eigh(
    matrix: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-14,
    max_iterations: int = 10000,
) -> tuple[list[float], list[list[float]], int]:
    """Deterministic symmetric eigendecomposition using Jacobi rotations.

    Eigenvectors are returned as columns in the second return value, prior to
    sorting/orientation.
    """
    n = len(matrix)
    if n < 1 or any(len(row) != n for row in matrix):
        raise BorealHabitatReferenceError(
            "Jacobi input must be a nonempty square matrix"
        )
    if tolerance <= 0 or max_iterations < 1:
        raise BorealHabitatReferenceError("invalid Jacobi controls")

    a = [[float(x) for x in row] for row in matrix]
    if not all(math.isfinite(x) for row in a for x in row):
        raise BorealHabitatReferenceError("nonfinite Jacobi matrix")
    for i in range(n):
        for j in range(n):
            if abs(a[i][j] - a[j][i]) > 1e-12:
                raise BorealHabitatReferenceError("Jacobi matrix is not symmetric")

    v = [
        [1.0 if i == j else 0.0 for j in range(n)]
        for i in range(n)
    ]

    for iteration in range(1, max_iterations + 1):
        p = 0
        q = 0
        max_offdiag = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                value = abs(a[i][j])
                if value > max_offdiag:
                    max_offdiag = value
                    p, q = i, j

        if max_offdiag <= tolerance:
            return [a[i][i] for i in range(n)], v, iteration - 1

        apq = a[p][q]
        app = a[p][p]
        aqq = a[q][q]
        tau = (aqq - app) / (2.0 * apq)
        if tau >= 0.0:
            t = 1.0 / (tau + math.sqrt(1.0 + tau * tau))
        else:
            t = -1.0 / (-tau + math.sqrt(1.0 + tau * tau))
        c = 1.0 / math.sqrt(1.0 + t * t)
        s = t * c

        for k in range(n):
            if k in (p, q):
                continue
            akp = a[k][p]
            akq = a[k][q]
            new_kp = c * akp - s * akq
            new_kq = s * akp + c * akq
            a[k][p] = new_kp
            a[p][k] = new_kp
            a[k][q] = new_kq
            a[q][k] = new_kq

        a[p][p] = app - t * apq
        a[q][q] = aqq + t * apq
        a[p][q] = 0.0
        a[q][p] = 0.0

        for k in range(n):
            vkp = v[k][p]
            vkq = v[k][q]
            v[k][p] = c * vkp - s * vkq
            v[k][q] = s * vkp + c * vkq

    raise BorealHabitatReferenceError(
        "Jacobi eigendecomposition did not converge"
    )


def _orient(vector: Sequence[float]) -> list[float]:
    values = [float(x) for x in vector]
    norm = math.sqrt(sum(x * x for x in values))
    if not math.isfinite(norm) or norm <= 0:
        raise BorealHabitatReferenceError("invalid eigenvector norm")
    values = [x / norm for x in values]

    anchor = min(
        range(len(values)),
        key=lambda i: (-abs(values[i]), i),
    )
    if values[anchor] < 0:
        values = [-x for x in values]
    return values


def deterministic_pca(
    rows: Sequence[Sequence[float]],
    *,
    variance_threshold: float = 0.80,
    jacobi_tolerance: float = 1e-14,
    jacobi_max_iterations: int = 10000,
) -> dict:
    if not 0.0 < variance_threshold <= 1.0:
        raise BorealHabitatReferenceError(
            "variance threshold must lie in (0,1]"
        )
    zrows, constants = standardize_columns(rows)
    p = len(zrows[0])
    if p < 2:
        raise BorealHabitatReferenceError(
            "PCA requires at least two habitat variables"
        )

    corr = correlation_matrix(zrows)
    raw_values, raw_vectors, iterations = jacobi_eigh(
        corr,
        tolerance=jacobi_tolerance,
        max_iterations=jacobi_max_iterations,
    )

    components = []
    for j, raw_value in enumerate(raw_values):
        value = float(raw_value)
        if value < 0 and abs(value) <= 1e-12:
            value = 0.0
        if value < -1e-12:
            raise BorealHabitatReferenceError(
                "correlation matrix produced materially negative eigenvalue"
            )
        vector = _orient([raw_vectors[i][j] for i in range(p)])
        components.append((value, vector))

    components.sort(
        key=lambda item: (
            -item[0],
            tuple(float(x).hex() for x in item[1]),
        )
    )
    eigenvalues = [item[0] for item in components]
    loadings = [item[1] for item in components]
    total = sum(eigenvalues)
    if not math.isfinite(total) or total <= 0:
        raise BorealHabitatReferenceError("nonpositive total PCA variance")

    fractions = [value / total for value in eigenvalues]
    cumulative = 0.0
    retain = 0
    for fraction in fractions:
        cumulative += fraction
        retain += 1
        if cumulative + 1e-15 >= variance_threshold:
            break

    scores = []
    for row in zrows:
        scores.append([
            sum(row[j] * loadings[k][j] for j in range(p))
            for k in range(retain)
        ])

    return {
        "standardized_rows": zrows,
        "standardization_constants": constants,
        "correlation_matrix": corr,
        "eigenvalues": eigenvalues,
        "explained_variance_fraction": fractions,
        "loadings": loadings,
        "retained_component_count": retain,
        "retained_scores": scores,
        "jacobi_iterations": iterations,
    }
