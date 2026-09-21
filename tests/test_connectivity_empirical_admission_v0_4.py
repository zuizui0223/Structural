from __future__ import annotations

from dataclasses import replace

from structural import (
    AdmissionStatus,
    ConnectivityEmpiricalProtocol,
    FavorableDirection,
    SeparationOrigin,
    evaluate_empirical_admission,
)


def valid_protocol() -> ConnectivityEmpiricalProtocol:
    return ConnectivityEmpiricalProtocol(
        protocol_id="future-connectivity-v0.4-test",
        system_id="system-A",
        origin=SeparationOrigin.PRE_EXISTING_ISOLATION,
        endpoint="seed_set",
        heldout_unit="island",
        metric="mse",
        favorable_direction=FavorableDirection.NEGATIVE,
        source_snapshot_id="source-sha256:abc",
        reference_id="current-state-v1",
        geometry_coordinate="source_network_geometry",
        process_operator="pollen_flow",
        process_coordinate="pollen_resistance_model",
        realized_coordinate=None,
        operator_semantics="pollen transfer among islands during the focal flowering window",
        connectivity_scale_rule="freeze kernel scale from movement literature before response access",
        origin_history_variable="isolation_origin_class",
        equivalence_margin=0.01,
        state_adequacy_claim_requested=True,
        candidate_uses_outcome=False,
        response_accessed=False,
        shared_reference_dependence_declared=True,
        shared_reference_group=None,
    )


def test_complete_response_blind_protocol_qualifies():
    decision = evaluate_empirical_admission(valid_protocol())
    assert decision.status is AdmissionStatus.QUALIFIED
    assert decision.reasons == ()


def test_opened_response_stops():
    decision = evaluate_empirical_admission(
        replace(valid_protocol(), response_accessed=True)
    )
    assert decision.status is AdmissionStatus.STOP
    assert "response_already_accessed" in decision.reasons


def test_outcome_derived_candidate_stops():
    decision = evaluate_empirical_admission(
        replace(valid_protocol(), candidate_uses_outcome=True)
    )
    assert "candidate_not_response_blind" in decision.reasons


def test_process_candidate_requires_operator_identity_and_semantics():
    p = replace(valid_protocol(), process_operator=None, operator_semantics=None)
    decision = evaluate_empirical_admission(p)
    assert "missing_process_operator" in decision.reasons
    assert "missing_operator_semantics" in decision.reasons


def test_state_adequacy_claim_requires_origin_and_equivalence_margin():
    p = replace(
        valid_protocol(),
        origin_history_variable=None,
        equivalence_margin=None,
    )
    decision = evaluate_empirical_admission(p)
    assert "state_adequacy_requires_origin_history_variable" in decision.reasons
    assert "state_adequacy_requires_predeclared_equivalence_margin" in decision.reasons


def test_geometry_only_protocol_can_qualify_without_operator_semantics():
    p = replace(
        valid_protocol(),
        process_operator=None,
        process_coordinate=None,
        operator_semantics=None,
        origin_history_variable=None,
        equivalence_margin=None,
        state_adequacy_claim_requested=False,
    )
    decision = evaluate_empirical_admission(p)
    assert decision.status is AdmissionStatus.QUALIFIED


def test_no_connectivity_candidate_stops():
    p = replace(
        valid_protocol(),
        geometry_coordinate=None,
        process_coordinate=None,
        realized_coordinate=None,
    )
    decision = evaluate_empirical_admission(p)
    assert "no_connectivity_candidate_declared" in decision.reasons


def test_shared_reference_dependence_must_be_declared():
    p = replace(valid_protocol(), shared_reference_dependence_declared=False)
    decision = evaluate_empirical_admission(p)
    assert "shared_reference_dependence_not_declared" in decision.reasons


def test_invalid_equivalence_margin_fails_closed():
    p = replace(valid_protocol(), equivalence_margin=0.0)
    decision = evaluate_empirical_admission(p)
    assert "invalid_equivalence_margin" in decision.reasons
