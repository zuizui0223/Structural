from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from scripts.validate_independent_system_intake_v0_12 import (
    canonical_fingerprint,
    validate_intake_v0_12,
)
from structural.response_quality_attrition import (
    ResponseQualityContractStatus,
    contract_from_mapping,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    evaluate_transition_pilot_protocol,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_boreal_prepilot_contracts_v0_80.py"
CONTRACT = ROOT / "development/boreal_lake_islands_prepilot_contract_builder_v0_80.json"
STATUS = ROOT / "development/current_status_v0_80.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_80.json"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal_prepilot_v080", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_intake(spatial_sha: str):
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    return {
        "schema": "structural.independent_system_intake.v0_12",
        "status": "response_sealed_dual_isolation_intake_draft",
        "system_id": "lac_la_ronge_boreal_island_beetles_2026",
        "source_id": "doi:10.5061/dryad.tdz08kq78",
        "source_version": "dryad-v7-version-id-422440",
        "source_fingerprint": "1" * 64,
        "origin": "independent_island_network",
        "is_prior_closed_system": False,
        "response_firewall_state": "response_sealed",
        "response_values_accessed": False,
        "source_files": [
            {
                "file_id": "safe_geometry.csv",
                "sha256": "2" * 64,
                "role": "geometry",
                "opened": True,
            },
            {
                "file_id": "habitat_reference.csv",
                "sha256": "3" * 64,
                "role": "safe_metadata",
                "opened": True,
            },
            {
                "file_id": "beetles_speciesmatrix_presenceabsence.csv",
                "sha256": "4" * 64,
                "role": "response",
                "opened": False,
            },
        ],
        "freshness_metadata": {
            "temporal_replication": "no",
            "immutable_source_identity": "yes",
            "spatial_unit_id_documented": "yes",
            "coordinates_or_geometry_documented": "yes",
            "outcome_file_separable": "yes",
            "operator_semantics_declarable": "yes",
            "connectivity_question_already_published": "no",
            "response_result_seen_by_project": "no",
        },
        "selection_firewall": {
            "candidate_hunt_active": False,
            "system_selected_using_response_direction": False,
            "system_selected_using_connectivity_result": False,
            "mechanism_lanes_selected_using_response_direction": False,
            "graph_scale_selected_using_response_direction": False,
            "endpoint_selected_using_response_direction": False,
            "published_effect_direction_used_for_selection": False,
        },
        "analysis_bindings": {
            "structural_partition_contract":
                "development/transition_pilot_protocol_contract_v0_31.json",
            "response_quality_gate":
                "development/response_quality_attrition_gate_v0_42.json",
            "ecological_hypothesis":
                "development/prospective_dual_isolation_source_pool_hypothesis_v0_55.json",
        },
        "endpoint_design": {
            "mode": "static_cross_sectional_occurrence",
            "endpoint_semantics": contract[
                "required_intake_endpoint_semantics"
            ],
            "temporal_transition_required": False,
            "whole_island_occupancy_claim_authorized": False,
            "colonization_claim_authorized": False,
            "rescue_persistence_claim_authorized": False,
        },
        "mechanism_claim_requested": False,
        "requested_mechanism_lanes": [],
        "response_blind_data_support": {
            "environment_predictor_metadata_available": True,
            "safe_geometry_available": True,
            "spatial_partition_frozen": True,
            "habitat_reference_frozen": True,
            "temporal_transition_metadata_available": False,
            "genetic_sampling_metadata_available": False,
            "biological_response_values_accessed": False,
            "preintake_receipt_sha256": {
                "safe_projection_v0_74": "5" * 64,
                "spatial_partition_v0_75": spatial_sha,
                "habitat_reference_v0_76": "6" * 64,
            },
        },
    }


def valid_spatial():
    pilot = [
        "SC_000000000001",
        "SC_000000000002",
        "SC_000000000003",
    ]
    confirmatory = [
        "SC_000000000004",
        "SC_000000000005",
        "SC_000000000006",
        "SC_000000000007",
        "SC_000000000008",
        "SC_000000000009",
    ]
    return {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": "lac_la_ronge_boreal_island_beetles_2026",
        "spatial_block_count": 9,
        "pilot_block_count": 3,
        "confirmatory_block_count": 6,
        "pilot_block_ids": pilot,
        "confirmatory_block_ids": confirmatory,
        "species_occurrence_used": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }


def valid_objects():
    spatial_sha = "a" * 64
    intake = valid_intake(spatial_sha)
    code, intake_receipt = validate_intake_v0_12(intake)
    assert code == 0
    spatial = valid_spatial()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    return contract, intake, intake_receipt, spatial, spatial_sha


def test_constructor_outputs_generic_v031_and_v042_objects_that_pass():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = valid_objects()

    protocol_map, quality_map, receipt = module.build(
        intake,
        intake_receipt,
        spatial,
        spatial_receipt_sha256=spatial_sha,
        contract=contract,
    )

    protocol = protocol_from_mapping(protocol_map)
    pdecision = evaluate_transition_pilot_protocol(protocol)
    assert pdecision.status is PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT

    quality = contract_from_mapping(quality_map)
    qdecision = evaluate_response_quality_contract(
        protocol=protocol,
        contract=quality,
    )
    assert qdecision.status is ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT

    assert receipt["status"] == "V031_AND_V042_FROZEN_RESPONSE_REMAINS_SEALED"
    assert receipt["protocol_fingerprint"] == pdecision.protocol_fingerprint
    assert receipt["quality_contract_fingerprint"] == qdecision.contract_fingerprint
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["mechanism_response_authorized"] is False
    assert receipt["effect_size"] is None
    assert receipt["prediction_score"] is None
    assert receipt["predictive_denominator_contribution"] == 0
    assert receipt["counts_as_empirical_evidence"] is False


def test_protocol_uses_exact_v075_spatial_block_partitions():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = valid_objects()
    protocol, quality, receipt = module.build(
        intake,
        intake_receipt,
        spatial,
        spatial_receipt_sha256=spatial_sha,
        contract=contract,
    )

    assert protocol["pilot_partition"] == spatial["pilot_block_ids"]
    assert protocol["confirmatory_partition"] == spatial["confirmatory_block_ids"]
    assert protocol["minimum_test_rows"] == 3
    assert protocol["minimum_train_positive"] == 5
    assert protocol["minimum_train_negative"] == 5
    assert protocol["minimum_estimable_blocks"] == 3
    assert protocol["pilot_response_accessed"] is False
    assert protocol["confirmatory_response_accessed"] is False
    assert protocol["pilot_used_for_effect_estimation"] is False
    assert "at least two distinct frozen pilot islands" in protocol[
        "endpoint_semantics"
    ]
    assert quality["minimum_response_qualified_blocks"] == 3
    assert quality["parent_protocol_fingerprint"] == receipt[
        "protocol_fingerprint"
    ]


def test_intake_fingerprint_mismatch_stops():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = valid_objects()
    intake_receipt["intake_fingerprint"] = "f" * 64

    with pytest.raises(
        module.BorealPrepilotBuilderError,
        match="intake fingerprint mismatch",
    ):
        module.build(
            intake,
            intake_receipt,
            spatial,
            spatial_receipt_sha256=spatial_sha,
            contract=contract,
        )


def test_spatial_receipt_sha_mismatch_stops():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = valid_objects()

    with pytest.raises(
        module.BorealPrepilotBuilderError,
        match="receipt SHA does not match",
    ):
        module.build(
            intake,
            intake_receipt,
            spatial,
            spatial_receipt_sha256="b" * 64,
            contract=contract,
        )


def test_spatial_block_overlap_stops():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = valid_objects()
    spatial["confirmatory_block_ids"][0] = spatial["pilot_block_ids"][0]

    with pytest.raises(
        module.BorealPrepilotBuilderError,
        match="partitions overlap",
    ):
        module.build(
            intake,
            intake_receipt,
            spatial,
            spatial_receipt_sha256=spatial_sha,
            contract=contract,
        )


def test_endpoint_semantics_drift_stops_even_if_static():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = valid_objects()
    intake["endpoint_design"]["endpoint_semantics"] = "different static endpoint"
    intake_receipt["intake_fingerprint"] = canonical_fingerprint(intake)

    with pytest.raises(
        module.BorealPrepilotBuilderError,
        match="endpoint semantics drift",
    ):
        module.build(
            intake,
            intake_receipt,
            spatial,
            spatial_receipt_sha256=spatial_sha,
            contract=contract,
        )


def test_response_access_or_mechanism_request_stops():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = valid_objects()
    intake["response_values_accessed"] = True
    intake_receipt["intake_fingerprint"] = canonical_fingerprint(intake)

    with pytest.raises(
        module.BorealPrepilotBuilderError,
        match="response already accessed",
    ):
        module.build(
            intake,
            intake_receipt,
            spatial,
            spatial_receipt_sha256=spatial_sha,
            contract=contract,
        )


def test_v080_contract_and_status_keep_response_access_separate():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert contract["v0_31"]["minimum_estimable_blocks"] == 3
    assert contract["v0_42"]["minimum_response_qualified_blocks"] == 3
    assert contract["constructor_ceiling"]["pilot_response_authorized"] is False
    assert contract["constructor_ceiling"]["confirmatory_response_authorized"] is False
    assert contract["constructor_ceiling"]["counts_as_empirical_evidence"] is False

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["v0_31_protocol_built"] is False
    assert boreal["v0_42_quality_contract_built"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["pilot_response_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
