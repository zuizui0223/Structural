from __future__ import annotations

import pytest

from structural import (
    AdequacyStage,
    FavorableDirection,
    IncrementalVerdict,
    LadderStepEvidence,
    SeparationOrigin,
    StateAdequacyVerdict,
    audit_state_ladder,
)


def step(
    stage: AdequacyStage,
    effect: float,
    lo: float,
    hi: float,
    *,
    operator: str = "pollen_flow",
    endpoint: str = "seed_set",
    family: str = "family-a",
    margin: float | None = None,
):
    return LadderStepEvidence(
        stage=stage,
        origin=SeparationOrigin.PRE_EXISTING_ISOLATION,
        operator=operator,
        endpoint=endpoint,
        reference_id=f"reference_before_{stage.value}",
        metric="mse",
        effect=effect,
        ci_low=lo,
        ci_high=hi,
        favorable_direction=FavorableDirection.NEGATIVE,
        evidence_family_id=family,
        equivalence_margin=margin,
    )


def test_state_adequacy_requires_explicit_equivalence_margin():
    rows = [
        step(AdequacyStage.STRUCTURAL_GEOMETRY, -0.04, -0.06, -0.02),
        step(AdequacyStage.PROCESS_MODEL, -0.03, -0.05, -0.01),
        step(AdequacyStage.ORIGIN_HISTORY, -0.002, -0.008, 0.006),
    ]
    out = audit_state_ladder(rows)
    assert out.state_adequacy is StateAdequacyVerdict.ORIGIN_RESIDUAL_INDETERMINATE

    rows[-1] = step(
        AdequacyStage.ORIGIN_HISTORY,
        -0.002,
        -0.008,
        0.006,
        margin=0.01,
    )
    out = audit_state_ladder(rows)
    assert out.state_adequacy is StateAdequacyVerdict.STATE_ADEQUACY_EARNED


def test_too_tight_equivalence_margin_does_not_close_state():
    rows = [
        step(AdequacyStage.PROCESS_MODEL, -0.03, -0.05, -0.01),
        step(
            AdequacyStage.ORIGIN_HISTORY,
            -0.002,
            -0.008,
            0.006,
            margin=0.005,
        ),
    ]
    out = audit_state_ladder(rows)
    assert out.state_adequacy is StateAdequacyVerdict.ORIGIN_RESIDUAL_INDETERMINATE


def test_residual_origin_information_keeps_state_open():
    rows = [
        step(AdequacyStage.STRUCTURAL_GEOMETRY, -0.03, -0.05, -0.01),
        step(AdequacyStage.PROCESS_MODEL, -0.02, -0.04, -0.01),
        step(
            AdequacyStage.ORIGIN_HISTORY,
            -0.03,
            -0.05,
            -0.02,
            margin=0.01,
        ),
    ]
    out = audit_state_ladder(rows)
    assert out.state_adequacy is StateAdequacyVerdict.ORIGIN_RESIDUAL_EARNED
    assert dict(out.stage_verdicts)[AdequacyStage.ORIGIN_HISTORY] is IncrementalVerdict.EARNED


def test_origin_can_be_adverse_without_becoming_equivalence():
    rows = [
        step(AdequacyStage.PROCESS_MODEL, -0.03, -0.05, -0.01),
        step(
            AdequacyStage.ORIGIN_HISTORY,
            +0.02,
            +0.01,
            +0.04,
            margin=0.005,
        ),
    ]
    out = audit_state_ladder(rows)
    assert out.state_adequacy is StateAdequacyVerdict.ORIGIN_RESIDUAL_ADVERSE


def test_ladder_can_stop_before_origin_history():
    rows = [
        step(AdequacyStage.STRUCTURAL_GEOMETRY, -0.03, -0.05, -0.01),
        step(AdequacyStage.REALIZED_OBSERVATION, -0.01, -0.03, 0.01),
    ]
    out = audit_state_ladder(rows)
    assert out.state_adequacy is StateAdequacyVerdict.ORIGIN_NOT_TESTED


def test_ladder_stage_order_is_strict():
    rows = [
        step(AdequacyStage.PROCESS_MODEL, -0.02, -0.04, -0.01),
        step(AdequacyStage.STRUCTURAL_GEOMETRY, -0.03, -0.05, -0.01),
    ]
    with pytest.raises(ValueError, match="strictly increasing"):
        audit_state_ladder(rows)


def test_one_ladder_cannot_mix_operators_or_endpoints():
    with pytest.raises(ValueError, match="operators"):
        audit_state_ladder([
            step(AdequacyStage.STRUCTURAL_GEOMETRY, -0.03, -0.05, -0.01),
            step(
                AdequacyStage.PROCESS_MODEL,
                -0.02,
                -0.04,
                -0.01,
                operator="whole_individual",
            ),
        ])

    with pytest.raises(ValueError, match="endpoints"):
        audit_state_ladder([
            step(AdequacyStage.STRUCTURAL_GEOMETRY, -0.03, -0.05, -0.01),
            step(
                AdequacyStage.PROCESS_MODEL,
                -0.02,
                -0.04,
                -0.01,
                endpoint="occupancy",
            ),
        ])


def test_equivalence_margin_only_belongs_to_origin_history():
    with pytest.raises(ValueError, match="only valid"):
        step(
            AdequacyStage.PROCESS_MODEL,
            -0.01,
            -0.02,
            0.00,
            margin=0.01,
        )
