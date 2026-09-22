from __future__ import annotations

from dataclasses import replace

from structural import (
    AdmissionStatus,
    ConnectivityEmpiricalProtocol,
    FavorableDirection,
    SeparationOrigin,
    evaluate_empirical_admission,
)


def base_protocol() -> ConnectivityEmpiricalProtocol:
    return ConnectivityEmpiricalProtocol(
        protocol_id="temporal-v0.14",
        system_id="dynamic-system",
        origin=SeparationOrigin.PRE_EXISTING_ISOLATION,
        endpoint="future_occupancy",
        heldout_unit="site",
        metric="log_loss",
        favorable_direction=FavorableDirection.NEGATIVE,
        source_snapshot_id="source-sha",
        reference_id="current-state-reference-v1",
        geometry_coordinate="baseline_geometry",
        process_operator="whole_individual",
        process_coordinate="lagged_source_connectivity",
        realized_coordinate=None,
        operator_semantics="whole-individual dispersal among breeding sites",
        connectivity_scale_rule="frozen scale worldset",
        origin_history_variable=None,
        equivalence_margin=None,
        state_adequacy_claim_requested=False,
        candidate_uses_outcome=False,
        response_accessed=False,
        shared_reference_dependence_declared=True,
        shared_reference_group=None,
    )


def test_lagged_state_requires_temporal_contract():
    p = replace(
        base_protocol(),
        candidate_uses_lagged_state=True,
        lagged_state_contract_id=None,
    )
    d = evaluate_empirical_admission(p)
    assert d.status is AdmissionStatus.STOP
    assert "lagged_state_requires_temporal_access_contract" in d.reasons


def test_lagged_state_is_allowed_when_temporal_contract_is_frozen():
    p = replace(
        base_protocol(),
        candidate_uses_lagged_state=True,
        lagged_state_contract_id="temporal_response_firewall_v0.14",
    )
    d = evaluate_empirical_admission(p)
    assert d.status is AdmissionStatus.QUALIFIED
    assert d.reasons == ()


def test_future_target_use_remains_forbidden():
    p = replace(
        base_protocol(),
        candidate_uses_outcome=True,
        candidate_uses_lagged_state=True,
        lagged_state_contract_id="temporal_response_firewall_v0.14",
    )
    d = evaluate_empirical_admission(p)
    assert d.status is AdmissionStatus.STOP
    assert "candidate_not_response_blind" in d.reasons
    assert "candidate_uses_future_or_heldout_target" in d.reasons
