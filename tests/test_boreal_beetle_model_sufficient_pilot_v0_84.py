from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from structural.boreal_beetle_pilot_router import (
    build_boreal_beetle_pilot_surface,
    decode_binary_vector_hex,
)
from structural.response_quality_attrition import (
    canonical_contract_mapping,
    contract_fingerprint,
    contract_from_mapping,
)
from structural.transition_pilot_protocol import (
    canonical_protocol_mapping,
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_boreal_beetle_pilot_v0_84.py"
CONTRACT = ROOT / "development/boreal_beetle_model_sufficient_pilot_contract_v0_84.json"
STATUS = ROOT / "development/current_status_v0_84.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_84.json"


def load_script():
    spec = importlib.util.spec_from_file_location(
        "boreal_pilot_v084",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_execution_inputs():
    module = load_script()
    candidate = "synthetic-boreal"
    pilot_blocks = ("P1", "P2", "P3")
    confirmatory_blocks = ("C1", "C2", "C3", "C4", "C5", "C6")
    blocks = pilot_blocks + confirmatory_blocks
    islands = tuple(f"I{i:02d}" for i in range(1, 43))
    mapping = {
        island: blocks[index % len(blocks)]
        for index, island in enumerate(islands)
    }

    protocol = protocol_from_mapping({
        "protocol_id": "synthetic-v084",
        "system_id": candidate,
        "partition_axis": "response_independent_spatial_components_v075",
        "pilot_partition": list(pilot_blocks),
        "confirmatory_partition": list(confirmatory_blocks),
        "endpoint_id": "fixed_pilot_supported_beetle_plot_occurrence",
        "endpoint_semantics": "synthetic fixed universe",
        "heldout_design_id": (
            "leave_one_spatial_component_out_fixed_pilot_supported_species_universe"
        ),
        "minimum_test_rows": 3,
        "minimum_train_positive": 2,
        "minimum_train_negative": 2,
        "minimum_estimable_blocks": 3,
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
        "pilot_used_for_effect_estimation": False,
    })
    protocol_mapping = canonical_protocol_mapping(protocol)
    pfp = protocol_fingerprint(protocol)

    quality = contract_from_mapping({
        "contract_id": "synthetic-quality-v084",
        "system_id": candidate,
        "parent_protocol_fingerprint": pfp,
        "minimum_response_qualified_blocks": 3,
        "response_quality_semantics": "synthetic quality",
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
    })
    quality_mapping = canonical_contract_mapping(quality)
    qfp = contract_fingerprint(quality)

    lines = [b"Island,sp1,sp2,sp3,sp4\n"]
    pilot_row_index = 0
    for island in islands:
        block = mapping[island]
        if block in pilot_blocks:
            if pilot_row_index % 2 == 0:
                payload = b"1,0,1,0"
            else:
                payload = b"0,1,1,0"
            pilot_row_index += 1
        else:
            payload = b"\xff,\xfe,\xff,\xfe"
        lines.append(island.encode("utf-8") + b"," + payload + b"\n")
    response_bytes = b"".join(lines)
    response_sha = hashlib.sha256(response_bytes).hexdigest()

    spatial = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "island_to_block": mapping,
        "pilot_block_ids": list(pilot_blocks),
        "confirmatory_block_ids": list(confirmatory_blocks),
        "species_occurrence_used": False,
        "richness_used": False,
        "habitat_values_used": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }
    spatial_sha = "a" * 64

    contract = {
        "schema": "structural.boreal_beetle_model_sufficient_pilot_contract.v0_84",
        "candidate_id": candidate,
        "response_file": {
            "name": "beetles_speciesmatrix_presenceabsence.csv",
            "dryad_file_id": 1,
            "expected_size_bytes": len(response_bytes),
            "expected_sha256": response_sha,
            "expected_species_columns": 4,
        },
        "pre_access": {
            "authorization_schema": (
                "structural.boreal_beetle_pilot_response_authorization.v0_81"
            ),
            "authorization_status": "AUTHORIZED_ONE_SHOT_BURNED_PILOT_RESPONSE",
        },
        "qualified_ceiling": {
            "status": (
                "QUALIFIED_TO_FREEZE_CONFIRMATORY_PROTOCOL_WITH_MODEL_SNAPSHOT"
            )
        },
    }

    authorization = {
        "schema": "structural.boreal_beetle_pilot_response_authorization.v0_81",
        "status": "AUTHORIZED_ONE_SHOT_BURNED_PILOT_RESPONSE",
        "candidate_id": candidate,
        "pilot_response_authorized": True,
        "confirmatory_response_authorized": False,
        "authorization_consumed": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "allowed_semantic_access": {
            "header_species_names": True,
            "routing_island_field_all_rows": True,
            "pilot_island_occurrence_cells": True,
            "confirmatory_island_occurrence_cells": False,
        },
        "router": {
            "confirmatory_target_values_parsed_must_equal": 0,
        },
        "protocol_fingerprint": pfp,
        "quality_contract_fingerprint": qfp,
        "source_spatial_receipt_sha256": spatial_sha,
        "response_file": {
            "name": contract["response_file"]["name"],
            "dryad_file_id": 1,
            "size_bytes": len(response_bytes),
            "sha256": response_sha,
        },
    }

    return (
        module,
        authorization,
        protocol_mapping,
        quality_mapping,
        spatial,
        response_bytes,
        contract,
        spatial_sha,
        islands,
    )


def test_router_compact_matrix_roundtrips_fixed_species_universe():
    (
        _,
        _,
        protocol,
        _,
        spatial,
        response_bytes,
        contract,
        _,
        islands,
    ) = synthetic_execution_inputs()

    routed = build_boreal_beetle_pilot_surface(
        response_csv_bytes=response_bytes,
        island_to_block=spatial["island_to_block"],
        pilot_partition=protocol["pilot_partition"],
        confirmatory_partition=protocol["confirmatory_partition"],
        expected_islands=islands,
        expected_species_count=contract["response_file"][
            "expected_species_columns"
        ],
    )

    assert routed.confirmatory_target_values_parsed == 0
    assert routed.pilot_species_universe == ("sp1", "sp2", "sp3")
    assert len(routed.pilot_targets_hex_by_island) == (
        routed.pilot_island_count
    )
    assert tuple(
        island for island, _ in routed.pilot_targets_hex_by_island
    ) == routed.pilot_island_order

    decoded = {
        island: decode_binary_vector_hex(
            encoded,
            routed.pilot_species_universe_count,
        )
        for island, encoded in routed.pilot_targets_hex_by_island
    }
    assert set(decoded) == set(routed.pilot_island_order)
    assert all(len(values) == 3 for values in decoded.values())
    assert all(set(values) <= {0, 1} for values in decoded.values())


def test_v084_qualified_execution_freezes_model_sufficient_snapshot():
    (
        module,
        authorization,
        protocol,
        quality,
        spatial,
        response_bytes,
        contract,
        spatial_sha,
        islands,
    ) = synthetic_execution_inputs()

    result, surface, snapshot = module.execute(
        authorization,
        protocol,
        quality,
        spatial,
        response_bytes,
        contract=contract,
        spatial_receipt_sha256=spatial_sha,
        expected_islands=islands,
    )

    assert result["status"] == (
        "QUALIFIED_TO_FREEZE_CONFIRMATORY_PROTOCOL_WITH_MODEL_SNAPSHOT"
    )
    assert result["authorization_consumed"] is True
    assert result["pilot_response_opened"] is True
    assert result["confirmatory_target_values_parsed"] == 0
    assert result["model_snapshot_frozen"] is True
    assert result["confirmatory_response_authorized"] is False
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["predictive_denominator_contribution"] == 0

    assert surface is not None
    assert snapshot is not None
    assert snapshot["status"] == (
        "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN"
    )
    assert snapshot["single_semantic_router_pass"] is True
    assert snapshot["confirmatory_target_values_parsed"] == 0
    assert snapshot["confirmatory_occurrence_values_stored"] is False
    assert snapshot["qualified_for_confirmatory_model_freeze"] is True
    assert snapshot["pilot_species_universe"] == ["sp1", "sp2", "sp3"]
    assert snapshot["target_bit_count"] == 3
    assert len(snapshot["targets_hex_by_island"]) == (
        snapshot["pilot_island_count"]
    )
    assert result["model_snapshot_fingerprint"] == (
        snapshot["snapshot_fingerprint"]
    )

    reconstructed = {
        island: decode_binary_vector_hex(encoded, 3)
        for island, encoded in snapshot["targets_hex_by_island"].items()
    }
    assert all(set(values) <= {0, 1} for values in reconstructed.values())
    assert not any(
        island.startswith("I") and spatial["island_to_block"][island].startswith("C")
        for island in reconstructed
    )


def test_snapshot_fingerprint_changes_if_one_pilot_bit_changes():
    (
        module,
        authorization,
        protocol,
        quality,
        spatial,
        response_bytes,
        contract,
        spatial_sha,
        islands,
    ) = synthetic_execution_inputs()
    _, _, snapshot = module.execute(
        authorization,
        protocol,
        quality,
        spatial,
        response_bytes,
        contract=contract,
        spatial_receipt_sha256=spatial_sha,
        expected_islands=islands,
    )
    assert snapshot is not None

    tampered = json.loads(json.dumps(snapshot))
    first = tampered["pilot_island_order"][0]
    encoded = tampered["targets_hex_by_island"][first]
    tampered["targets_hex_by_island"][first] = (
        "0" * len(encoded) if set(encoded) != {"0"} else "1" * len(encoded)
    )
    tampered.pop("snapshot_fingerprint")
    assert module.canonical_sha256(tampered) != snapshot["snapshot_fingerprint"]


def test_real_v084_contract_prospectively_supersedes_unexecuted_v082():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["supersedes_before_first_real_execution"].endswith(
        "boreal_beetle_one_shot_pilot_contract_v0_82.json"
    )
    assert contract["semantic_access"][
        "confirmatory_occurrence_cells"
    ] is False
    assert contract["semantic_access"][
        "single_semantic_router_pass_required"
    ] is True
    snapshot = contract["model_snapshot"]
    assert snapshot["confirmatory_occurrence_values_in_snapshot"] is False
    assert contract["qualified_ceiling"]["confirmatory_response_authorized"] is False
    assert contract["qualified_ceiling"]["effect_size"] is None
    assert contract["qualified_ceiling"]["prediction_score"] is None


def test_v084_status_keeps_real_pilot_unconsumed():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["pilot_response_consumed"] is False
    assert boreal["model_sufficient_pilot_snapshot_exists"] is False
    assert boreal["confirmatory_response_values_opened"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
