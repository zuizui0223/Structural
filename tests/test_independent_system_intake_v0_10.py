from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from scripts.validate_independent_system_intake_v0_10 import validate_intake


ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/independent_system_intake_v0_10/valid_intake.json"


def load() -> dict:
    return json.loads(FIX.read_text(encoding="utf-8"))


def test_valid_independent_intake_advances_only_to_v031_construction():
    code, out = validate_intake(load())

    assert code == 0
    assert out["status"] == "eligible_to_construct_v0_31_partition_protocol"
    assert out["eligible_action"] == "construct_v0_31_partition_protocol_only"
    assert out["v0_31_protocol_construction_authorized"] is True
    assert out["pilot_response_authorized"] is False
    assert out["confirmatory_response_authorized"] is False
    assert out["mechanism_response_authorized"] is False
    assert out["mechanism_claim_authorized"] is False
    assert out["effect_size"] is None
    assert out["prediction_score"] is None
    assert out["predictive_denominator_contribution"] == 0
    assert out["mechanism_claim_contribution"] == 0
    assert out["ttf_handoff_authorized"] is False
    assert out["freshness_triage_status"] == "advance_to_schema_audit"
    assert len(out["intake_fingerprint"]) == 64


def test_seen_response_is_permanent_stop():
    x = load()
    x["freshness_metadata"]["response_result_seen_by_project"] = "yes"

    code, out = validate_intake(x)

    assert code == 2
    assert out["status"] == "STOP_freshness_triage"
    assert out["freshness_triage_reasons"] == [
        "response_result_already_seen_by_project"
    ]


def test_closed_historical_system_cannot_reenter():
    x = load()
    x["system_id"] = "usgs_rmnp_amphibian_surveys_1986_2022"

    code, out = validate_intake(x)

    assert code == 2
    assert out["status"] == "STOP_prior_closed_system_cannot_reenter"


def test_declared_prior_closed_system_cannot_reenter_even_with_new_id():
    x = load()
    x["is_prior_closed_system"] = True

    code, out = validate_intake(x)

    assert code == 2
    assert out["status"] == "STOP_prior_closed_system_cannot_reenter"


def test_unknown_geometry_is_hold_not_pass():
    x = load()
    x["freshness_metadata"]["coordinates_or_geometry_documented"] = "unknown"

    code, out = validate_intake(x)

    assert code == 2
    assert out["status"] == "HOLD_pending_response_blind_metadata"
    assert out["v0_31_protocol_construction_authorized"] is False
    assert "unknown_coordinates_or_geometry_documented" in (
        out["freshness_triage_reasons"]
    )


def test_opened_response_file_is_invalid_intake_before_triage():
    x = load()
    x["source_files"][2]["opened"] = True

    code, out = validate_intake(x)

    assert code == 1
    assert out["status"] == "invalid_intake_schema"
    assert "response/unknown file was opened" in out["reason"]


def test_no_response_file_is_rejected():
    x = load()
    x["source_files"] = [
        row for row in x["source_files"] if row["role"] != "response"
    ]

    code, out = validate_intake(x)

    assert code == 1
    assert "at least one response file must be identified" in out["reason"]


def test_dynamic_lane_requires_temporal_metadata():
    x = load()
    x["response_blind_data_support"][
        "temporal_transition_metadata_available"
    ] = False

    code, out = validate_intake(x)

    assert code == 2
    assert out["status"] == (
        "STOP_requested_mechanism_lane_lacks_response_blind_support"
    )
    assert "dynamic_lane_requested_without_temporal_transition_metadata" in (
        out["response_blind_data_support"]["support_reasons"]
    )


def test_M3_requires_genetic_sampling_metadata():
    x = load()
    x["response_blind_data_support"][
        "genetic_sampling_metadata_available"
    ] = False

    code, out = validate_intake(x)

    assert code == 2
    assert "M3_requested_without_genetic_sampling_metadata" in (
        out["response_blind_data_support"]["support_reasons"]
    )


def test_M4_requires_environment_metadata():
    x = load()
    x["response_blind_data_support"][
        "environment_predictor_metadata_available"
    ] = False

    code, out = validate_intake(x)

    assert code == 2
    assert "M4_requested_without_environment_predictor_metadata" in (
        out["response_blind_data_support"]["support_reasons"]
    )


def test_candidate_hunt_must_be_off():
    x = load()
    x["selection_firewall"]["candidate_hunt_active"] = True

    code, out = validate_intake(x)

    assert code == 1
    assert "candidate_hunt_active must be false" in out["reason"]


def test_response_selected_mechanism_lane_is_rejected():
    x = load()
    x["selection_firewall"][
        "mechanism_lanes_selected_using_response_direction"
    ] = True

    code, out = validate_intake(x)

    assert code == 1
    assert "selection firewall must be false" in out["reason"]


def test_hypothesis_binding_drift_is_rejected():
    x = load()
    x["hypothesis_bindings"]["ecological_hypothesis"] = (
        "development/some_new_post_outcome_threshold.json"
    )

    code, out = validate_intake(x)

    assert code == 1
    assert "hypothesis binding drift" in out["reason"]


def test_intake_fingerprint_changes_with_source_version():
    one = load()
    two = deepcopy(one)
    two["source_version"] = "v1.1"

    code1, out1 = validate_intake(one)
    code2, out2 = validate_intake(two)

    assert code1 == code2 == 0
    assert out1["intake_fingerprint"] != out2["intake_fingerprint"]


def test_unknown_mechanism_lane_is_rejected():
    x = load()
    x["requested_mechanism_lanes"].append("M5_posthoc_rescue")

    code, out = validate_intake(x)

    assert code == 1
    assert "unknown mechanism lanes" in out["reason"]


def test_response_firewall_must_start_sealed():
    x = load()
    x["response_firewall_state"] = "opened"

    code, out = validate_intake(x)

    assert code == 2
    assert out["status"] == "STOP_response_firewall_not_sealed"


def test_static_M4_only_system_can_advance_without_temporal_replication():
    x = load()
    x["freshness_metadata"]["temporal_replication"] = "no"
    x["requested_mechanism_lanes"] = ["M4_environmental_proxy"]
    x["response_blind_data_support"] = {
        "temporal_transition_metadata_available": False,
        "genetic_sampling_metadata_available": False,
        "environment_predictor_metadata_available": True,
    }

    code, out = validate_intake(x)

    assert code == 0
    assert out["status"] == "eligible_to_construct_v0_31_partition_protocol"
    assert out["freshness_triage_status"] == "advance_to_schema_audit"
    assert out["freshness_triage_reasons"] == [
        "non_temporal_endpoint_permitted_for_non_dynamic_lanes"
    ]
    assert out["v0_31_protocol_construction_authorized"] is True
    assert out["pilot_response_authorized"] is False
    assert out["confirmatory_response_authorized"] is False
