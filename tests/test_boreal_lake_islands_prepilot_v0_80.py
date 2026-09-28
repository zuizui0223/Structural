from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from scripts.run_transition_pilot_v0_32 import run as run_v032
from scripts.validate_independent_system_intake_v0_12 import canonical_fingerprint
from structural.response_quality_attrition import (
    contract_fingerprint,
    contract_from_mapping,
)
from structural.transition_pilot_protocol import (
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_boreal_v031_v042_v0_80.py"
CONTRACT = ROOT / "development/boreal_lake_islands_prepilot_contract_builder_v0_80.json"
STATUS = ROOT / "development/current_status_v0_80.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_80.json"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal_v080", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_inputs():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    candidate = contract["candidate_id"]
    islands = [f"I{i:02d}" for i in range(1, 43)]
    block_sizes = [5, 5, 5, 5, 5, 5, 4, 4, 4]
    block_ids = [f"SC_BLOCK_{i}" for i in range(1, 10)]
    island_to_block = {}
    blocks = []
    cursor = 0
    for bid, size in zip(block_ids, block_sizes):
        members = islands[cursor:cursor + size]
        cursor += size
        blocks.append({
            "block_id": bid,
            "islands": members,
            "rank_sha256": (str(len(blocks) + 1) * 64)[:64],
        })
        for island in members:
            island_to_block[island] = bid

    pilot_blocks = block_ids[:3]
    confirmatory_blocks = block_ids[3:]
    pilot_islands = [
        island for island in islands
        if island_to_block[island] in set(pilot_blocks)
    ]
    confirmatory_islands = [
        island for island in islands
        if island_to_block[island] in set(confirmatory_blocks)
    ]
    spatial_sha = "a" * 64

    intake = {
        "schema": "structural.independent_system_intake.v0_12",
        "status": "response_sealed_dual_isolation_intake_draft",
        "system_id": candidate,
        "response_firewall_state": "response_sealed",
        "response_values_accessed": False,
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
                "file_id": "beetles_speciesmatrix_presenceabsence.csv",
                "sha256": "d" * 64,
                "role": "response",
                "opened": False,
            },
        ],
        "response_blind_data_support": {
            "preintake_receipt_sha256": {
                "safe_projection_v0_74": "e" * 64,
                "spatial_partition_v0_75": spatial_sha,
                "habitat_reference_v0_76": "f" * 64,
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
        "ttf_handoff_authorized": False,
    }
    spatial = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "spatial_block_count": 9,
        "blocks": blocks,
        "island_to_block": island_to_block,
        "pilot_block_count": 3,
        "confirmatory_block_count": 6,
        "pilot_block_ids": pilot_blocks,
        "confirmatory_block_ids": confirmatory_blocks,
        "pilot_islands": pilot_islands,
        "confirmatory_islands": confirmatory_islands,
        "species_occurrence_used": False,
        "richness_used": False,
        "habitat_values_used": False,
        "counts_as_empirical_evidence": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }
    return contract, intake, intake_receipt, spatial, spatial_sha


def test_v080_builds_fingerprint_bound_generic_components():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = make_inputs()

    result = module.build(
        intake,
        intake_receipt,
        spatial,
        contract=contract,
        spatial_receipt_sha256=spatial_sha,
    )

    assert result["status"] == "V031_V042_COMPONENTS_FROZEN_RESPONSE_REMAINS_SEALED"
    p = result["v0_31_protocol"]
    q = result["v0_42_quality_contract"]

    assert p["pilot_partition"] == spatial["pilot_islands"]
    assert p["confirmatory_partition"] == spatial["confirmatory_islands"]
    assert set(p["pilot_partition"]).isdisjoint(p["confirmatory_partition"])
    assert p["minimum_estimable_blocks"] == 3
    assert "static" not in p["partition_axis"]
    assert "whole-island occupancy" in p["endpoint_semantics"].lower()

    parsed_p = protocol_from_mapping(p)
    parsed_q = contract_from_mapping(q)
    assert result["v0_31_protocol_fingerprint"] == protocol_fingerprint(parsed_p)
    assert q["parent_protocol_fingerprint"] == result["v0_31_protocol_fingerprint"]
    assert result["v0_42_quality_contract_fingerprint"] == contract_fingerprint(parsed_q)
    assert q["minimum_response_qualified_blocks"] == 3

    routing = result["pilot_surface_routing"]
    assert routing["partition_unit"] == "frozen island code"
    assert routing["block"] == "v0.75 spatial block ID for that island"
    assert routing["heldout_specific_species_universe_forbidden"] is True
    assert routing["response_file_id"] == "beetles_speciesmatrix_presenceabsence.csv"
    assert routing["response_file_sha256"] == "d" * 64
    assert set(routing["pilot_island_to_block"]) == set(spatial["pilot_islands"])
    assert set(routing["confirmatory_island_to_block"]) == set(
        spatial["confirmatory_islands"]
    )

    assert result["pilot_response_authorized"] is False
    assert result["confirmatory_response_authorized"] is False
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["predictive_denominator_contribution"] == 0
    assert result["counts_as_empirical_evidence"] is False


def test_generated_v031_is_compatible_with_v032_island_unit_spatial_block_surface(
    tmp_path: Path,
):
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = make_inputs()
    result = module.build(
        intake,
        intake_receipt,
        spatial,
        contract=contract,
        spatial_receipt_sha256=spatial_sha,
    )

    protocol_path = tmp_path / "v031.json"
    protocol_path.write_text(
        json.dumps(result["v0_31_protocol"]),
        encoding="utf-8",
    )
    pilot_csv = tmp_path / "pilot.csv"
    rows = ["partition_unit,block,target"]
    for idx, island in enumerate(spatial["pilot_islands"]):
        block = spatial["island_to_block"][island]
        # Three targets per island. Alternating patterns guarantee both classes
        # remain in every leave-one-spatial-block-out training complement.
        targets = (1, 0, 1) if idx % 2 == 0 else (0, 1, 0)
        for target in targets:
            rows.append(f"{island},{block},{target}")
    pilot_csv.write_text("\n".join(rows) + "\n", encoding="utf-8")

    code, receipt = run_v032(protocol_path, pilot_csv)

    assert code == 0
    assert receipt["status"] == "qualified_for_new_confirmatory_protocol"
    assert receipt["total_blocks"] == 3
    assert receipt["estimable_blocks"] == 3
    assert {row["block"] for row in receipt["block_audits"]} == set(
        spatial["pilot_block_ids"]
    )
    assert receipt["confirmatory_response_row_count_seen"] == 0
    assert receipt["effect_size"] is None
    assert receipt["prediction_score"] is None


def test_v032_rejects_confirmatory_island_even_with_pilot_block_label(tmp_path: Path):
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = make_inputs()
    result = module.build(
        intake,
        intake_receipt,
        spatial,
        contract=contract,
        spatial_receipt_sha256=spatial_sha,
    )
    protocol_path = tmp_path / "v031.json"
    protocol_path.write_text(json.dumps(result["v0_31_protocol"]), encoding="utf-8")
    pilot_csv = tmp_path / "pilot.csv"
    confirmatory_island = spatial["confirmatory_islands"][0]
    pilot_block = spatial["pilot_block_ids"][0]
    pilot_csv.write_text(
        "partition_unit,block,target\n"
        f"{confirmatory_island},{pilot_block},1\n",
        encoding="utf-8",
    )

    code, receipt = run_v032(protocol_path, pilot_csv)
    assert code == 2
    assert receipt["status"] == "STOP_confirmatory_partition_exposed"
    assert receipt["confirmatory_unit"] == confirmatory_island


def test_spatial_receipt_sha_must_bind_v012_intake():
    module = load_script()
    contract, intake, intake_receipt, spatial, _ = make_inputs()
    with pytest.raises(
        module.BorealPrepilotBuilderError,
        match="does not bind v0.12 intake",
    ):
        module.build(
            intake,
            intake_receipt,
            spatial,
            contract=contract,
            spatial_receipt_sha256="0" * 64,
        )


def test_wrong_island_to_block_role_is_rejected():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = make_inputs()
    island = spatial["pilot_islands"][0]
    spatial["island_to_block"][island] = spatial["confirmatory_block_ids"][0]
    with pytest.raises(
        module.BorealPrepilotBuilderError,
        match="pilot island mapped outside pilot blocks",
    ):
        module.build(
            intake,
            intake_receipt,
            spatial,
            contract=contract,
            spatial_receipt_sha256=spatial_sha,
        )


def test_intake_receipt_does_not_authorize_response():
    module = load_script()
    contract, intake, intake_receipt, spatial, spatial_sha = make_inputs()
    intake_receipt["pilot_response_authorized"] = True
    with pytest.raises(
        module.BorealPrepilotBuilderError,
        match="ceiling violated",
    ):
        module.build(
            intake,
            intake_receipt,
            spatial,
            contract=contract,
            spatial_receipt_sha256=spatial_sha,
        )


def test_v080_status_keeps_fresh_denominator_zero():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
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
