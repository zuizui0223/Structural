from __future__ import annotations

from structural.transition_estimability import (
    PilotDecision,
    PilotObservation,
    audit_transition_pilot,
)


def obs(block: str, values):
    return [PilotObservation(block, value) for value in values]


def test_balanced_pilot_can_qualify_multiple_blocks():
    rows = (
        obs("A", [1, 0, 1, 0, 1]) +
        obs("B", [1, 0, 1, 0, 0]) +
        obs("C", [1, 0, 1, 0, 1]) +
        obs("D", [1, 0, 1, 0, 0])
    )
    result = audit_transition_pilot(
        rows,
        minimum_test_rows=3,
        minimum_train_positive=5,
        minimum_train_negative=5,
        minimum_estimable_blocks=3,
    )
    assert result.decision is PilotDecision.QUALIFIED
    assert result.estimable_blocks == 4


def test_pnw_like_positive_collapse_stops():
    rows = (
        obs("A", [1] * 20 + [0]) +
        obs("B", [1] * 20 + [0]) +
        obs("C", [1] * 20 + [0])
    )
    result = audit_transition_pilot(
        rows,
        minimum_test_rows=3,
        minimum_train_positive=5,
        minimum_train_negative=5,
        minimum_estimable_blocks=2,
    )
    assert result.decision is PilotDecision.STOP
    assert result.negative == 3
    assert result.estimable_blocks == 0


def test_rmnp_like_negative_collapse_stops():
    rows = (
        obs("A", [0] * 20 + [1]) +
        obs("B", [0] * 20 + [1]) +
        obs("C", [0] * 20 + [1])
    )
    result = audit_transition_pilot(
        rows,
        minimum_test_rows=3,
        minimum_train_positive=5,
        minimum_train_negative=5,
        minimum_estimable_blocks=2,
    )
    assert result.decision is PilotDecision.STOP
    assert result.positive == 3
    assert result.estimable_blocks == 0


def test_non_estimable_pilot_rows_do_not_become_absences():
    rows = (
        obs("A", [1, 0, None, None]) +
        obs("B", [1, 0, 1, 0]) +
        obs("C", [1, 0, 1, 0])
    )
    result = audit_transition_pilot(
        rows,
        minimum_test_rows=2,
        minimum_train_positive=2,
        minimum_train_negative=2,
        minimum_estimable_blocks=2,
    )
    assert result.non_estimable == 2
    assert result.applicable_rows == 10


def test_pilot_pass_is_not_predictive_evidence():
    result = audit_transition_pilot(
        obs("A", [1,0,1]) + obs("B", [0,1,0]) + obs("C", [1,0,1]),
        minimum_test_rows=2,
        minimum_train_positive=2,
        minimum_train_negative=2,
        minimum_estimable_blocks=2,
    )
    assert result.decision in {PilotDecision.QUALIFIED, PilotDecision.STOP}
    assert not hasattr(result, "effect_size")
    assert not hasattr(result, "prediction_score")
