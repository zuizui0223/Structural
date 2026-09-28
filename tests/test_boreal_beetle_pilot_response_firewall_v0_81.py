from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from scripts.build_boreal_prepilot_contracts_v0_80 import build as build_v080
from scripts.run_transition_pilot_v0_32 import run as run_v032
from scripts.validate_independent_system_intake_v0_12 import canonical_fingerprint
from structural.boreal_beetle_pilot_router import (
    BorealBeetlePilotRouterError,
    build_boreal_beetle_pilot_surface,
)


ROOT = Path(__file__).resolve().parents[1]
AUTH_SCRIPT = ROOT / "scripts/authorize_boreal_beetle_pilot_response_v0_81.py"
AUTH_CONTRACT = ROOT / "development/boreal_beetle_pilot_response_authorization_contract_v0_81.json"
V080_CONTRACT = ROOT / "development/boreal_lake_islands_prepilot_contract_builder_v0_80.json"
METADATA = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
STATUS = ROOT / "development/current_status_v0_81.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_81.json"


def load_auth():
    spec = importlib.util.spec_from_file_location("boreal_auth_v081", AUTH_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_router_inputs():
    pilot = ("P1", "P2", "P3")
    confirmatory = ("C1", "C2", "C3")
    islands = ("I1", "I2", "I3", "I4", "I5", "I6", "J1", "J2", "J3")
    mapping = {
        "I1": "P1", "I2": "P1",
        "I3": "P2", "I4": "P2",
        "I5": "P3", "I6": "P3",
        "J1": "C1", "J2": "C2", "J3": "C3",
    }
    raw = (
        b"Island,sp1,sp2,sp3,sp4\n"
        b"I1,1,0,1,0\n"
        b"I2,1,1,0,0\n"
        b"I3,1,0,1,0\n"
        b"I4,0,1,1,0\n"
        b"I5,0,1,1,0\n"
        b"I6,1,0,0,0\n"
        b"J1,\xff,\xfe,\xff,\xfe\n"
        b"J2,\xfe,\xff,\xfe,\xff\n"
        b"J3,\xff,\xff,\xfe,\xfe\n"
    )
    return raw, mapping, pilot, confirmatory, islands


def test_router_never_decodes_confirmatory_occurrence_bytes():
    raw, mapping, pilot, confirmatory, islands = synthetic_router_inputs()

    routed = build_boreal_beetle_pilot_surface(
        response_csv_bytes=raw,
        island_to_block=mapping,
        pilot_partition=pilot,
        confirmatory_partition=confirmatory,
        expected_islands=islands,
        expected_species_count=4,
    )

    assert routed.source_response_rows_seen == 9
    assert routed.routing_island_fields_decoded == 9
    assert routed.pilot_island_rows_semantically_parsed == 6
    assert routed.pilot_target_values_parsed == 24
    assert routed.confirmatory_target_values_parsed == 0
    assert routed.header_species_names_parsed == 4
    assert routed.pilot_species_universe == ("sp1", "sp2", "sp3")
    assert routed.pilot_species_universe_count == 3
    assert routed.confirmatory_island_count == 3
    assert routed.pilot_block_count == 3
    assert set(row.split(",")[0] for row in routed.csv_text.splitlines()[1:]) == {
        "P1", "P2", "P3"
    }
    assert "\ufffd" not in routed.csv_text


def test_router_surface_runs_through_generic_v032(tmp_path: Path):
    raw, mapping, pilot, confirmatory, islands = synthetic_router_inputs()
    routed = build_boreal_beetle_pilot_surface(
        response_csv_bytes=raw,
        island_to_block=mapping,
        pilot_partition=pilot,
        confirmatory_partition=confirmatory,
        expected_islands=islands,
        expected_species_count=4,
    )

    protocol = {
        "protocol_id": "synthetic-boreal",
        "system_id": "synthetic",
        "partition_axis": "response_independent_spatial_components_v075",
        "pilot_partition": list(pilot),
        "confirmatory_partition": list(confirmatory),
        "endpoint_id": "fixed_pilot_supported_beetle_plot_occurrence",
        "endpoint_semantics": "synthetic fixed common universe",
        "heldout_design_id": "leave_one_spatial_component_out_fixed_pilot_supported_species_universe",
        "minimum_test_rows": 3,
        "minimum_train_positive": 2,
        "minimum_train_negative": 2,
        "minimum_estimable_blocks": 3,
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
        "pilot_used_for_effect_estimation": False,
    }
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    p.write_text(json.dumps(protocol), encoding="utf-8")
    c.write_text(routed.csv_text, encoding="utf-8")

    code, receipt = run_v032(p, c)
    assert code == 0
    assert receipt["status"] == "qualified_for_new_confirmatory_protocol"
    assert receipt["total_blocks"] == 3
    assert receipt["estimable_blocks"] == 3
    assert receipt["confirmatory_response_row_count_seen"] == 0
    assert receipt["effect_size"] is None
    assert receipt["prediction_score"] is None


def test_invalid_pilot_occurrence_is_semantically_opened_and_stops():
    raw, mapping, pilot, confirmatory, islands = synthetic_router_inputs()
    raw = raw.replace(b"I1,1,0,1,0", b"I1,1,X,1,0")
    with pytest.raises(
        BorealBeetlePilotRouterError,
        match="unexpected pilot occurrence value",
    ):
        build_boreal_beetle_pilot_surface(
            response_csv_bytes=raw,
            island_to_block=mapping,
            pilot_partition=pilot,
            confirmatory_partition=confirmatory,
            expected_islands=islands,
            expected_species_count=4,
        )


def test_router_species_rule_is_two_distinct_pilot_islands_not_blocks():
    raw, mapping, pilot, confirmatory, islands = synthetic_router_inputs()
    # sp4 is detected on two islands in the same pilot block P1.
    raw = raw.replace(b"I1,1,0,1,0", b"I1,1,0,1,1")
    raw = raw.replace(b"I2,1,1,0,0", b"I2,1,1,0,1")
    routed = build_boreal_beetle_pilot_surface(
        response_csv_bytes=raw,
        island_to_block=mapping,
        pilot_partition=pilot,
        confirmatory_partition=confirmatory,
        expected_islands=islands,
        expected_species_count=4,
    )
    assert routed.pilot_species_universe == ("sp1", "sp2", "sp3", "sp4")


def make_authorization_inputs():
    auth_contract = json.loads(AUTH_CONTRACT.read_text(encoding="utf-8"))
    v080_contract = json.loads(V080_CONTRACT.read_text(encoding="utf-8"))
    candidate = auth_contract["candidate_id"]
    spatial_sha = "a" * 64

    pilot_blocks = ["P1", "P2", "P3"]
    confirmatory_blocks = [f"C{i}" for i in range(1, 7)]
    block_ids = pilot_blocks + confirmatory_blocks
    islands = [f"I{i:02d}" for i in range(1, 43)]
    mapping = {}
    for idx, island in enumerate(islands):
        mapping[island] = block_ids[idx % len(block_ids)]

    intake = {
        "schema": "structural.independent_system_intake.v0_12",
        "status": "response_sealed_dual_isolation_intake_draft",
        "system_id": candidate,
        "response_firewall_state": "response_sealed",
        "response_values_accessed": False,
        "mechanism_claim_requested": False,
        "requested_mechanism_lanes": [],
        "endpoint_design": {
            "mode": "static_cross_sectional_occurrence",
            "endpoint_semantics": v080_contract[
                "required_intake_endpoint_semantics"
            ],
        },
        "source_files": [
            {
                "file_id": "safe_geometry.csv",
                "sha256": "b" * 64,
                "role": "geometry",
                "opened": True,
            },
            {
                "file_id": "habitat_reference.csv",
                "sha256": "c" * 64,
                "role": "safe_metadata",
                "opened": True,
            },
            {
                "file_id": auth_contract["response_file"]["name"],
                "sha256": auth_contract["response_file"]["expected_sha256"],
                "role": "response",
                "opened": False,
            },
        ],
        "response_blind_data_support": {
            "preintake_receipt_sha256": {
                "safe_projection_v0_74": "d" * 64,
                "spatial_partition_v0_75": spatial_sha,
                "habitat_reference_v0_76": "e" * 64,
            }
        },
    }
    intake_receipt = {
        "schema": "structural.independent_system_intake_receipt.v0_12",
        "status": "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts",
        "system_id": candidate,
        "intake_fingerprint": canonical_fingerprint(intake),
        "v0_31_protocol_construction_authorized": True,
        "v0_42_quality_contract_construction_authorized": True,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "mechanism_response_authorized": False,
        "mechanism_claim_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
    }
    spatial = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "pilot_block_ids": pilot_blocks,
        "confirmatory_block_ids": confirmatory_blocks,
        "pilot_block_count": 3,
        "confirmatory_block_count": 6,
        "spatial_block_count": 9,
        "island_to_block": mapping,
        "species_occurrence_used": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }
    protocol, quality, prepilot = build_v080(
        intake,
        intake_receipt,
        spatial,
        spatial_receipt_sha256=spatial_sha,
        contract=v080_contract,
    )
    metadata = {
        "focal_files": {
            auth_contract["response_file"]["name"]: {
                "file_id": auth_contract["response_file"]["dryad_file_id"],
                "size": auth_contract["response_file"]["expected_size_bytes"],
                "sha256": auth_contract["response_file"]["expected_sha256"],
                "role": "primary_response",
            }
        }
    }
    return (
        auth_contract,
        v080_contract,
        intake,
        intake_receipt,
        protocol,
        quality,
        prepilot,
        spatial,
        spatial_sha,
        metadata,
    )


def test_authorization_exact_replays_v080_and_opens_pilot_only():
    module = load_auth()
    (
        auth_contract,
        v080_contract,
        intake,
        intake_receipt,
        protocol,
        quality,
        prepilot,
        spatial,
        spatial_sha,
        metadata,
    ) = make_authorization_inputs()

    result = module.authorize(
        intake,
        intake_receipt,
        protocol,
        quality,
        prepilot,
        spatial,
        contract=auth_contract,
        v080_contract=v080_contract,
        metadata=metadata,
        spatial_receipt_sha256=spatial_sha,
    )

    assert result["status"] == "AUTHORIZED_ONE_SHOT_BURNED_PILOT_RESPONSE"
    assert result["pilot_response_authorized"] is True
    assert result["confirmatory_response_authorized"] is False
    assert result["allowed_semantic_access"][
        "confirmatory_island_occurrence_cells"
    ] is False
    assert result["response_file"]["sha256"] == (
        auth_contract["response_file"]["expected_sha256"]
    )
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["predictive_denominator_contribution"] == 0
    assert result["counts_as_empirical_evidence"] is False
    assert result["authorization_consumed"] is False


def test_authorization_rejects_tampered_v031_even_if_receipt_is_unchanged():
    module = load_auth()
    args = list(make_authorization_inputs())
    protocol = dict(args[4])
    protocol["minimum_test_rows"] += 1
    args[4] = protocol
    with pytest.raises(
        module.BorealPilotAuthorizationError,
        match="does not exact-replay v0.80",
    ):
        module.authorize(
            args[2], args[3], args[4], args[5], args[6], args[7],
            contract=args[0],
            v080_contract=args[1],
            metadata=args[9],
            spatial_receipt_sha256=args[8],
        )


def test_authorization_rejects_forged_v080_receipt():
    module = load_auth()
    args = list(make_authorization_inputs())
    prepilot = dict(args[6])
    prepilot["pilot_block_count"] = 999
    args[6] = prepilot
    with pytest.raises(
        module.BorealPilotAuthorizationError,
        match="receipt does not exact-replay",
    ):
        module.authorize(
            args[2], args[3], args[4], args[5], args[6], args[7],
            contract=args[0],
            v080_contract=args[1],
            metadata=args[9],
            spatial_receipt_sha256=args[8],
        )


def test_real_v081_response_identity_matches_frozen_v065_metadata():
    contract = json.loads(AUTH_CONTRACT.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    frozen = metadata["focal_files"][contract["response_file"]["name"]]
    assert frozen["file_id"] == contract["response_file"]["dryad_file_id"]
    assert frozen["size"] == contract["response_file"]["expected_size_bytes"]
    assert frozen["sha256"] == contract["response_file"]["expected_sha256"]
    assert frozen["role"] == "primary_response"
    assert contract["replay_requirements"]["v0_80_exact_replay_required"] is True
    assert contract["execution_authorized_now"] is False


def test_v081_status_keeps_actual_pilot_unopened():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["pilot_response_authorization_issued"] is False
    assert boreal["pilot_response_consumed"] is False
    assert boreal["confirmatory_response_values_opened"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
