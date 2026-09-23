"""Burned-pilot estimability audit for prospective mechanism transition lanes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


M1 = "M1_contemporary_colonization"
M2 = "M2_rescue_persistence"


@dataclass(frozen=True)
class MechanismTransitionObservation:
    block: str
    z_t: int | None
    z_t1: int | None

    def __post_init__(self) -> None:
        if not self.block.strip():
            raise ValueError("block must be non-empty")
        for label, value in (("z_t", self.z_t), ("z_t1", self.z_t1)):
            if value not in (None, 0, 1):
                raise ValueError(f"{label} must be 0/1/None")


@dataclass(frozen=True)
class MechanismBlockAudit:
    block: str
    test_rows_m1: int
    test_rows_m2: int
    train_0_to_0: int
    train_0_to_1: int
    train_1_to_0: int
    train_1_to_1: int
    m1_estimable: bool
    m2_estimable: bool
    m1_reasons: tuple[str, ...]
    m2_reasons: tuple[str, ...]


@dataclass(frozen=True)
class MechanismLaneAudit:
    lane: str
    requested: bool
    estimable_blocks: int
    minimum_estimable_blocks: int
    qualified: bool


@dataclass(frozen=True)
class MechanismTransitionAudit:
    total_rows: int
    applicable_rows: int
    non_estimable_rows: int
    transition_counts: dict[str, int]
    block_audits: tuple[MechanismBlockAudit, ...]
    lane_audits: tuple[MechanismLaneAudit, ...]


def _transition_key(row: MechanismTransitionObservation) -> str | None:
    if row.z_t is None or row.z_t1 is None:
        return None
    return f"{row.z_t}_to_{row.z_t1}"


def _count_transitions(
    rows: Iterable[MechanismTransitionObservation],
) -> dict[str, int]:
    counts = {
        "0_to_0": 0,
        "0_to_1": 0,
        "1_to_0": 0,
        "1_to_1": 0,
    }
    for row in rows:
        key = _transition_key(row)
        if key is not None:
            counts[key] += 1
    return counts


def audit_mechanism_transition_pilot(
    observations: Iterable[MechanismTransitionObservation],
    *,
    requested_lanes: Iterable[str],
    minimum_test_rows_m1: int,
    minimum_test_rows_m2: int,
    minimum_train_0_to_0: int,
    minimum_train_0_to_1: int,
    minimum_train_1_to_0: int,
    minimum_train_1_to_1: int,
    minimum_estimable_blocks_m1: int,
    minimum_estimable_blocks_m2: int,
) -> MechanismTransitionAudit:
    rows = tuple(observations)
    requested = tuple(dict.fromkeys(requested_lanes))
    unknown = sorted(set(requested) - {M1, M2})
    if unknown:
        raise ValueError("unknown dynamic mechanism lanes: " + ", ".join(unknown))
    if not requested:
        raise ValueError("at least one dynamic mechanism lane must be requested")

    minima = {
        "minimum_test_rows_m1": minimum_test_rows_m1,
        "minimum_test_rows_m2": minimum_test_rows_m2,
        "minimum_train_0_to_0": minimum_train_0_to_0,
        "minimum_train_0_to_1": minimum_train_0_to_1,
        "minimum_train_1_to_0": minimum_train_1_to_0,
        "minimum_train_1_to_1": minimum_train_1_to_1,
        "minimum_estimable_blocks_m1": minimum_estimable_blocks_m1,
        "minimum_estimable_blocks_m2": minimum_estimable_blocks_m2,
    }
    for label, value in minima.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{label} must be an integer >=1")

    blocks = sorted({row.block for row in rows})
    if len(blocks) < 2:
        raise ValueError("mechanism transition pilot requires at least two blocks")

    block_audits: list[MechanismBlockAudit] = []
    for block in blocks:
        test = tuple(row for row in rows if row.block == block)
        train = tuple(row for row in rows if row.block != block)
        train_counts = _count_transitions(train)

        test_rows_m1 = sum(
            row.z_t == 0 and row.z_t1 in (0, 1)
            for row in test
        )
        test_rows_m2 = sum(
            row.z_t == 1 and row.z_t1 in (0, 1)
            for row in test
        )

        m1_reasons: list[str] = []
        if test_rows_m1 < minimum_test_rows_m1:
            m1_reasons.append("insufficient_test_rows_starting_0")
        if train_counts["0_to_1"] < minimum_train_0_to_1:
            m1_reasons.append("insufficient_train_0_to_1")
        if train_counts["0_to_0"] < minimum_train_0_to_0:
            m1_reasons.append("insufficient_train_0_to_0")

        m2_reasons: list[str] = []
        if test_rows_m2 < minimum_test_rows_m2:
            m2_reasons.append("insufficient_test_rows_starting_1")
        if train_counts["1_to_0"] < minimum_train_1_to_0:
            m2_reasons.append("insufficient_train_1_to_0")
        if train_counts["1_to_1"] < minimum_train_1_to_1:
            m2_reasons.append("insufficient_train_1_to_1")

        block_audits.append(
            MechanismBlockAudit(
                block=block,
                test_rows_m1=test_rows_m1,
                test_rows_m2=test_rows_m2,
                train_0_to_0=train_counts["0_to_0"],
                train_0_to_1=train_counts["0_to_1"],
                train_1_to_0=train_counts["1_to_0"],
                train_1_to_1=train_counts["1_to_1"],
                m1_estimable=not m1_reasons,
                m2_estimable=not m2_reasons,
                m1_reasons=tuple(m1_reasons),
                m2_reasons=tuple(m2_reasons),
            )
        )

    m1_estimable = sum(row.m1_estimable for row in block_audits)
    m2_estimable = sum(row.m2_estimable for row in block_audits)
    lane_audits = (
        MechanismLaneAudit(
            lane=M1,
            requested=M1 in requested,
            estimable_blocks=m1_estimable,
            minimum_estimable_blocks=minimum_estimable_blocks_m1,
            qualified=(M1 not in requested or m1_estimable >= minimum_estimable_blocks_m1),
        ),
        MechanismLaneAudit(
            lane=M2,
            requested=M2 in requested,
            estimable_blocks=m2_estimable,
            minimum_estimable_blocks=minimum_estimable_blocks_m2,
            qualified=(M2 not in requested or m2_estimable >= minimum_estimable_blocks_m2),
        ),
    )

    counts = _count_transitions(rows)
    applicable_rows = sum(counts.values())
    return MechanismTransitionAudit(
        total_rows=len(rows),
        applicable_rows=applicable_rows,
        non_estimable_rows=len(rows) - applicable_rows,
        transition_counts=counts,
        block_audits=tuple(block_audits),
        lane_audits=lane_audits,
    )
