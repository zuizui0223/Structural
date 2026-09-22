"""Burned-pilot estimability gate for future dynamic connectivity protocols."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class PilotDecision(str, Enum):
    QUALIFIED = "qualified_for_new_confirmatory_protocol"
    STOP = "stop_endpoint_variation"


@dataclass(frozen=True)
class PilotObservation:
    block: str
    target: int | None

    def __post_init__(self) -> None:
        if not self.block.strip():
            raise ValueError("block must be non-empty")
        if self.target not in (0, 1, None):
            raise ValueError("target must be 0, 1, or None")


@dataclass(frozen=True)
class PilotBlockAudit:
    block: str
    test_rows: int
    test_positive: int
    test_negative: int
    train_rows: int
    train_positive: int
    train_negative: int
    estimable: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class TransitionPilotAudit:
    decision: PilotDecision
    applicable_rows: int
    positive: int
    negative: int
    non_estimable: int
    total_blocks: int
    estimable_blocks: int
    minimum_estimable_blocks: int
    block_audits: tuple[PilotBlockAudit, ...]


def audit_transition_pilot(
    observations: Iterable[PilotObservation],
    *,
    minimum_test_rows: int,
    minimum_train_positive: int,
    minimum_train_negative: int,
    minimum_estimable_blocks: int,
) -> TransitionPilotAudit:
    """Audit a permanently burned pilot using the exact planned heldout gates.

    The pilot is feasibility-only. Passing this gate never counts as predictive
    evidence and never authorizes access to the confirmatory target by itself.
    """

    rows = tuple(observations)
    if not rows:
        raise ValueError("pilot must contain at least one observation")
    if minimum_test_rows < 1:
        raise ValueError("minimum_test_rows must be >=1")
    if minimum_train_positive < 1 or minimum_train_negative < 1:
        raise ValueError("minimum training class counts must be >=1")
    if minimum_estimable_blocks < 1:
        raise ValueError("minimum_estimable_blocks must be >=1")

    applicable = tuple(row for row in rows if row.target in (0, 1))
    positive = sum(row.target == 1 for row in applicable)
    negative = sum(row.target == 0 for row in applicable)
    non_estimable = len(rows) - len(applicable)

    blocks = tuple(sorted({row.block for row in rows}))
    audits: list[PilotBlockAudit] = []
    for block in blocks:
        test = tuple(row for row in applicable if row.block == block)
        train = tuple(row for row in applicable if row.block != block)
        test_pos = sum(row.target == 1 for row in test)
        test_neg = sum(row.target == 0 for row in test)
        train_pos = sum(row.target == 1 for row in train)
        train_neg = sum(row.target == 0 for row in train)

        reasons: list[str] = []
        if len(test) < minimum_test_rows:
            reasons.append("test_rows_below_minimum")
        if train_pos < minimum_train_positive:
            reasons.append("training_positive_count_below_minimum")
        if train_neg < minimum_train_negative:
            reasons.append("training_negative_count_below_minimum")

        audits.append(
            PilotBlockAudit(
                block=block,
                test_rows=len(test),
                test_positive=test_pos,
                test_negative=test_neg,
                train_rows=len(train),
                train_positive=train_pos,
                train_negative=train_neg,
                estimable=not reasons,
                reasons=tuple(reasons),
            )
        )

    estimable_blocks = sum(a.estimable for a in audits)
    decision = (
        PilotDecision.QUALIFIED
        if estimable_blocks >= minimum_estimable_blocks
        else PilotDecision.STOP
    )
    return TransitionPilotAudit(
        decision=decision,
        applicable_rows=len(applicable),
        positive=positive,
        negative=negative,
        non_estimable=non_estimable,
        total_blocks=len(audits),
        estimable_blocks=estimable_blocks,
        minimum_estimable_blocks=minimum_estimable_blocks,
        block_audits=tuple(audits),
    )
