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


class ConnectivityEvidenceLevel(str, Enum):
    STRUCTURAL_GEOMETRY = "structural_geometry"
    PROCESS_MODEL = "process_model"
    REALIZED_OBSERVATION = "realized_observation"


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
    evidence_level: ConnectivityEvidenceLevel = ConnectivityEvidenceLevel.STRUCTURAL_GEOMETRY
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


class AdequacyStage(str, Enum):
    STRUCTURAL_GEOMETRY = "structural_geometry"
    PROCESS_MODEL = "process_model"
    REALIZED_OBSERVATION = "realized_observation"
    ORIGIN_HISTORY = "origin_history"


class StateAdequacyVerdict(str, Enum):
    ORIGIN_NOT_TESTED = "origin_not_tested"
    STATE_ADEQUACY_EARNED = "state_adequacy_earned"
    ORIGIN_RESIDUAL_EARNED = "origin_residual_earned"
    ORIGIN_RESIDUAL_ADVERSE = "origin_residual_adverse"
    ORIGIN_RESIDUAL_INDETERMINATE = "origin_residual_indeterminate"


_STAGE_ORDER = {
    AdequacyStage.STRUCTURAL_GEOMETRY: 1,
    AdequacyStage.PROCESS_MODEL: 2,
    AdequacyStage.REALIZED_OBSERVATION: 3,
    AdequacyStage.ORIGIN_HISTORY: 4,
}


@dataclass(frozen=True)
class LadderStepEvidence:
    """One prospective candidate-minus-reference step in a state-adequacy ladder."""

    stage: AdequacyStage
    origin: SeparationOrigin
    operator: str
    endpoint: str
    reference_id: str
    metric: str
    effect: float
    ci_low: float
    ci_high: float
    favorable_direction: FavorableDirection
    evidence_family_id: str
    equivalence_margin: float | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("operator", self.operator),
            ("endpoint", self.endpoint),
            ("reference_id", self.reference_id),
            ("metric", self.metric),
            ("evidence_family_id", self.evidence_family_id),
        ):
            if not value.strip():
                raise ValueError(f"{label} must be non-empty")
        if not all(isfinite(v) for v in (self.effect, self.ci_low, self.ci_high)):
            raise ValueError("effect and confidence limits must be finite")
        if self.ci_low > self.ci_high:
            raise ValueError("ci_low must be <= ci_high")
        if not (self.ci_low <= self.effect <= self.ci_high):
            raise ValueError("effect must lie inside its confidence interval")
        if self.equivalence_margin is not None:
            if self.stage is not AdequacyStage.ORIGIN_HISTORY:
                raise ValueError("equivalence_margin is only valid for origin_history")
            if not isfinite(self.equivalence_margin) or self.equivalence_margin <= 0:
                raise ValueError("equivalence_margin must be finite and > 0")


@dataclass(frozen=True)
class StateLadderSummary:
    origin: SeparationOrigin
    operator: str
    endpoint: str
    metric: str
    stage_verdicts: tuple[tuple[AdequacyStage, IncrementalVerdict], ...]
    state_adequacy: StateAdequacyVerdict
    independent_evidence_families: int


def classify_ladder_step(step: LadderStepEvidence) -> IncrementalVerdict:
    """Classify one ladder increment without turning a null into equivalence."""

    if step.favorable_direction is FavorableDirection.NEGATIVE:
        if step.ci_high < 0:
            return IncrementalVerdict.EARNED
        if step.ci_low > 0:
            return IncrementalVerdict.ADVERSE
        return IncrementalVerdict.INDETERMINATE

    if step.ci_low > 0:
        return IncrementalVerdict.EARNED
    if step.ci_high < 0:
        return IncrementalVerdict.ADVERSE
    return IncrementalVerdict.INDETERMINATE


def audit_state_ladder(steps: Iterable[LadderStepEvidence]) -> StateLadderSummary:
    """Audit a declared geometry -> process -> realized -> origin/history ladder.

    The ladder may omit unavailable intermediate stages, but supplied stages must
    be strictly ordered. State adequacy is earned only when the origin/history
    increment has a predeclared equivalence margin and its entire confidence
    interval lies inside that margin.
    """

    rows = tuple(steps)
    if not rows:
        raise ValueError("at least one ladder step is required")

    if len({row.origin for row in rows}) != 1:
        raise ValueError("one ladder cannot mix spatial origins")
    if len({row.operator for row in rows}) != 1:
        raise ValueError("one ladder cannot mix biological operators")
    if len({row.endpoint for row in rows}) != 1:
        raise ValueError("one ladder cannot mix endpoints")
    if len({row.metric for row in rows}) != 1:
        raise ValueError("one ladder cannot mix scoring metrics")
    if len({row.favorable_direction for row in rows}) != 1:
        raise ValueError("one ladder cannot mix favorable directions")

    orders = [_STAGE_ORDER[row.stage] for row in rows]
    if any(left >= right for left, right in zip(orders, orders[1:])):
        raise ValueError("ladder stages must be unique and strictly increasing")

    stage_verdicts = tuple((row.stage, classify_ladder_step(row)) for row in rows)
    origin_rows = [row for row in rows if row.stage is AdequacyStage.ORIGIN_HISTORY]
    if not origin_rows:
        state_adequacy = StateAdequacyVerdict.ORIGIN_NOT_TESTED
    else:
        origin_step = origin_rows[0]
        margin = origin_step.equivalence_margin
        if (
            margin is not None
            and origin_step.ci_low >= -margin
            and origin_step.ci_high <= margin
        ):
            state_adequacy = StateAdequacyVerdict.STATE_ADEQUACY_EARNED
        else:
            origin_verdict = classify_ladder_step(origin_step)
            if origin_verdict is IncrementalVerdict.EARNED:
                state_adequacy = StateAdequacyVerdict.ORIGIN_RESIDUAL_EARNED
            elif origin_verdict is IncrementalVerdict.ADVERSE:
                state_adequacy = StateAdequacyVerdict.ORIGIN_RESIDUAL_ADVERSE
            else:
                state_adequacy = StateAdequacyVerdict.ORIGIN_RESIDUAL_INDETERMINATE

    first = rows[0]
    return StateLadderSummary(
        origin=first.origin,
        operator=first.operator,
        endpoint=first.endpoint,
        metric=first.metric,
        stage_verdicts=stage_verdicts,
        state_adequacy=state_adequacy,
        independent_evidence_families=len({row.evidence_family_id for row in rows}),
    )
