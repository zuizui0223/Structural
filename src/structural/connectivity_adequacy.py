"""Typed connectivity adequacy and portability audits.

This module is post-closure development infrastructure. It does not alter the
frozen A-Islands or Tanzania results.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Iterable


class SeparationOrigin(str, Enum):
    PRE_EXISTING_ISOLATION = "pre_existing_isolation"
    HABITAT_FRAGMENTATION = "habitat_fragmentation"
    OTHER = "other"


class FavorableDirection(str, Enum):
    NEGATIVE = "negative"
    POSITIVE = "positive"


class IncrementalVerdict(str, Enum):
    EARNED = "earned"
    ADVERSE = "adverse"
    INDETERMINATE = "indeterminate"


class PortabilityVerdict(str, Enum):
    NOT_TESTED = "not_tested"
    SUPPORTED_WITHIN_DECLARED_SET = "supported_within_declared_set"
    NOT_ESTABLISHED = "not_established"
    NOT_PORTABLE_IN_DECLARED_SET = "not_portable_in_declared_set"


@dataclass(frozen=True)
class ConnectivityCoordinate:
    """A connectivity representation with explicit biological semantics."""

    name: str
    operator: str
    endpoint: str
    origin: SeparationOrigin
    semantic_note: str = ""

    def __post_init__(self) -> None:
        for label, value in (
            ("name", self.name),
            ("operator", self.operator),
            ("endpoint", self.endpoint),
        ):
            if not value.strip():
                raise ValueError(f"{label} must be non-empty")


@dataclass(frozen=True)
class IncrementalEvidence:
    """Held-out candidate-minus-reference evidence for one typed coordinate."""

    coordinate: ConnectivityCoordinate
    reference_id: str
    metric: str
    effect: float
    ci_low: float
    ci_high: float
    favorable_direction: FavorableDirection
    evidence_family_id: str
    shared_reference_group: str | None = None

    def __post_init__(self) -> None:
        if not self.reference_id.strip():
            raise ValueError("reference_id must be non-empty")
        if not self.metric.strip():
            raise ValueError("metric must be non-empty")
        if not self.evidence_family_id.strip():
            raise ValueError("evidence_family_id must be non-empty")
        values = (self.effect, self.ci_low, self.ci_high)
        if not all(isfinite(v) for v in values):
            raise ValueError("effect and confidence limits must be finite")
        if self.ci_low > self.ci_high:
            raise ValueError("ci_low must be <= ci_high")
        if not (self.ci_low <= self.effect <= self.ci_high):
            raise ValueError("effect must lie inside its confidence interval")


@dataclass(frozen=True)
class PortabilitySummary:
    coordinate_name: str
    endpoint: str
    target_operators: tuple[str, ...]
    verdicts: tuple[tuple[str, IncrementalVerdict], ...]
    portability: PortabilityVerdict
    independent_evidence_families: int
    shared_reference_groups: tuple[str, ...]


def classify_incremental(evidence: IncrementalEvidence) -> IncrementalVerdict:
    """Classify the frozen interval relative to the declared favorable direction."""

    if evidence.favorable_direction is FavorableDirection.NEGATIVE:
        if evidence.ci_high < 0:
            return IncrementalVerdict.EARNED
        if evidence.ci_low > 0:
            return IncrementalVerdict.ADVERSE
        return IncrementalVerdict.INDETERMINATE

    if evidence.ci_low > 0:
        return IncrementalVerdict.EARNED
    if evidence.ci_high < 0:
        return IncrementalVerdict.ADVERSE
    return IncrementalVerdict.INDETERMINATE


def audit_portability(records: Iterable[IncrementalEvidence]) -> PortabilitySummary:
    """Audit transport of one named connectivity representation across operators."""

    rows = tuple(records)
    if not rows:
        raise ValueError("at least one evidence record is required")

    names = {r.coordinate.name for r in rows}
    endpoints = {r.coordinate.endpoint for r in rows}
    directions = {r.favorable_direction for r in rows}
    if len(names) != 1:
        raise ValueError("portability audit requires one coordinate name")
    if len(endpoints) != 1:
        raise ValueError("portability audit requires one endpoint")
    if len(directions) != 1:
        raise ValueError("portability audit requires one favorable direction")

    by_operator: dict[str, list[IncrementalVerdict]] = {}
    for row in rows:
        by_operator.setdefault(row.coordinate.operator, []).append(classify_incremental(row))

    operator_verdicts: list[tuple[str, IncrementalVerdict]] = []
    for operator in sorted(by_operator):
        vals = by_operator[operator]
        if IncrementalVerdict.ADVERSE in vals:
            verdict = IncrementalVerdict.ADVERSE
        elif IncrementalVerdict.INDETERMINATE in vals:
            verdict = IncrementalVerdict.INDETERMINATE
        else:
            verdict = IncrementalVerdict.EARNED
        operator_verdicts.append((operator, verdict))

    target_operators = tuple(op for op, _ in operator_verdicts)
    if len(target_operators) < 2:
        portability = PortabilityVerdict.NOT_TESTED
    elif any(v is IncrementalVerdict.ADVERSE for _, v in operator_verdicts):
        portability = PortabilityVerdict.NOT_PORTABLE_IN_DECLARED_SET
    elif any(v is IncrementalVerdict.INDETERMINATE for _, v in operator_verdicts):
        portability = PortabilityVerdict.NOT_ESTABLISHED
    else:
        portability = PortabilityVerdict.SUPPORTED_WITHIN_DECLARED_SET

    groups = tuple(sorted({r.shared_reference_group for r in rows if r.shared_reference_group}))
    return PortabilitySummary(
        coordinate_name=next(iter(names)),
        endpoint=next(iter(endpoints)),
        target_operators=target_operators,
        verdicts=tuple(operator_verdicts),
        portability=portability,
        independent_evidence_families=len({r.evidence_family_id for r in rows}),
        shared_reference_groups=groups,
    )


@dataclass(frozen=True)
class OperatorConnectivityState:
    """Normalized operator-specific connectivity state for a synthetic closure."""

    values: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("at least one operator value is required")
        names = [name for name, _ in self.values]
        if len(names) != len(set(names)):
            raise ValueError("operator names must be unique")
        for name, value in self.values:
            if not name.strip():
                raise ValueError("operator name must be non-empty")
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError("operator connectivity must be finite and within [0, 1]")

    @property
    def collapsed_mean(self) -> float:
        return sum(value for _, value in self.values) / len(self.values)

    def value_for(self, operator: str) -> float:
        for name, value in self.values:
            if name == operator:
                return value
        raise KeyError(operator)


@dataclass(frozen=True)
class ScalarInsufficiencyWitness:
    operator: str
    collapsed_value: float
    transition_a: float
    transition_b: float
    transition_difference: float


def declared_operator_transition(
    state: OperatorConnectivityState,
    operator: str,
) -> float:
    """Synthetic known-truth transition using the matching operator coordinate."""

    return state.value_for(operator)


def scalar_insufficiency_witness(
    state_a: OperatorConnectivityState,
    state_b: OperatorConnectivityState,
    operator: str,
    *,
    tolerance: float = 1e-12,
) -> ScalarInsufficiencyWitness:
    """Prove a collapsed connectivity mean is insufficient for one declared operator.

    The witness requires the same operator set and the same collapsed mean, while
    the declared operator-specific next-transition value differs.
    """

    operators_a = {name for name, _ in state_a.values}
    operators_b = {name for name, _ in state_b.values}
    if operators_a != operators_b:
        raise ValueError("states must expose the same operator set")

    mean_a = state_a.collapsed_mean
    mean_b = state_b.collapsed_mean
    if abs(mean_a - mean_b) > tolerance:
        raise ValueError("collapsed connectivity values must match")

    transition_a = declared_operator_transition(state_a, operator)
    transition_b = declared_operator_transition(state_b, operator)
    difference = transition_a - transition_b
    if abs(difference) <= tolerance:
        raise ValueError("operator-specific transitions must differ")

    return ScalarInsufficiencyWitness(
        operator=operator,
        collapsed_value=(mean_a + mean_b) / 2.0,
        transition_a=transition_a,
        transition_b=transition_b,
        transition_difference=difference,
    )
