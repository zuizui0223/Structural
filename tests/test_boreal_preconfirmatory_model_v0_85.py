from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

from structural.boreal_beetle_pilot_router import encode_binary_vector_hex
from structural.boreal_confirmatory_model import (
    fit_ridge_logistic,
    predict_probability,
)
from structural.boreal_dual_isolation_operator import (
    freeze_connected_knn_operator,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_preconfirmatory_model_v0_85.py"
CONTRACT = ROOT / "development/boreal_preconfirmatory_model_contract_v0_85.json"
EXTERNAL = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
STATUS = ROOT / "development/current_status_v0_85.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_85.json"


def load_script():
    spec = importlib.util.spec_from_file_location(
        "boreal_preconfirmatory_v085",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_pure_python_ridge_logistic_is_deterministic_and_directional():
    rows = [
        (1.0, -2.0),
        (1.0, -1.0),
        (1.0, 1.0),
        (1.0, 2.0),
    ]
    targets = [0, 0, 1, 1]

    fit1 = fit_ridge_logistic(
        rows,
        targets,
        columns=("intercept", "x"),
    )
    fit2 = fit_ridge_logistic(
        list(reversed(rows)),
        list(reversed(targets)),
        columns=("intercept", "x"),
    )

    assert [value.hex() for value in fit1.coefficients] == [
        value.hex() for value in fit2.coefficients
    ]
    assert fit1.coefficients[1] > 0
    assert predict_probability((1.0, 2.0), fit1) > 0.5
    assert predict_probability((1.0, -2.0), fit1) < 0.5


def synthetic_freeze_inputs(tmp_path: Path):
    module = load_script()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    external = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    candidate = contract["candidate_id"]
    islands = tuple(
        external["current_study_island_universe"]["codes"]
    )
    assert len(islands) == 42

    geometry_path = tmp_path / "safe_geometry.csv"
    geometry_rows = []
    with geometry_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["Island", "Lat", "Long"])
        for index, island in enumerate(islands):
            lat = 50.0 + index * 0.01
            lon = -105.0 + (index % 3) * 0.002
            geometry_rows.append((island, lat, lon))
            writer.writerow([island, float(lat).hex(), float(lon).hex()])
    geometry_text = geometry_path.read_text(encoding="utf-8")
    geometry_sha = sha256_text(geometry_text)
    coordinates = {
        island: (lat, lon)
        for island, lat, lon in geometry_rows
    }

    projection = {
        "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
        "status": "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED",
        "candidate_id": candidate,
        "geometry": {
            "row_count": 42,
            "unique_island_count": 42,
            "sha256": geometry_sha,
        },
        "protected_response_values_opened": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }

    habitat_path = tmp_path / "habitat_reference.csv"
    with habitat_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["Island", "HAB1", "HAB2"])
        for index, island in enumerate(islands):
            writer.writerow([
                island,
                float((index - 20.5) / 10.0).hex(),
                float(((index % 7) - 3.0) / 2.0).hex(),
            ])
    habitat_text = habitat_path.read_text(encoding="utf-8")
    habitat_sha = sha256_text(habitat_text)
    habitat_receipt = {
        "schema": "structural.boreal_lake_islands_habitat_reference_result.v0_76",
        "status": "HABITAT_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "reference_sha256": habitat_sha,
        "species_occurrence_used": False,
        "richness_used": False,
        "protected_response_values_opened": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }

    blocks = (
        "P1", "P2", "P3",
        "C1", "C2", "C3", "C4", "C5", "C6",
    )
    island_to_block = {
        island: blocks[index % len(blocks)]
        for index, island in enumerate(islands)
    }
    pilot_islands = [
        island for island in islands
        if island_to_block[island] in {"P1", "P2", "P3"}
    ]
    confirmatory_islands = [
        island for island in islands
        if island_to_block[island].startswith("C")
    ]
    spatial = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "island_to_block": island_to_block,
        "pilot_block_ids": ["P1", "P2", "P3"],
        "confirmatory_block_ids": ["C1", "C2", "C3", "C4", "C5", "C6"],
        "pilot_islands": sorted(pilot_islands),
        "confirmatory_islands": sorted(confirmatory_islands),
        "species_occurrence_used": False,
        "richness_used": False,
        "habitat_values_used": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }

    operator = freeze_connected_knn_operator(coordinates)
    operator_fingerprint = module.canonical_sha256(operator)
    cross_edges = [
        row for row in operator["edges"]
        if island_to_block[row["left"]] != island_to_block[row["right"]]
    ]
    assert cross_edges
    operator_receipt = {
        "schema": "structural.boreal_dual_isolation_operator_result.v0_83",
        "status": "DUAL_ISOLATION_OPERATOR_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "operator_fingerprint": operator_fingerprint,
        "cross_v075_block_edge_count": len(cross_edges),
        "confirmatory_response_used_to_build_operator": False,
    }

    species = ("sp1", "sp2", "sp3")
    snapshot_order = []
    for block in ("P1", "P2", "P3"):
        snapshot_order.extend(sorted(
            island for island in pilot_islands
            if island_to_block[island] == block
        ))

    targets = {}
    for index, island in enumerate(snapshot_order):
        values = (
            1 if index % 2 == 0 else 0,
            1 if index % 3 in (0, 1) else 0,
            1 if index % 4 in (1, 2, 3) else 0,
        )
        targets[island] = encode_binary_vector_hex(values)

    snapshot = {
        "schema": "structural.boreal_beetle_pilot_training_snapshot.v0_84",
        "status": "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN",
        "candidate_id": candidate,
        "response_file_sha256": "a" * 64,
        "raw_pilot_surface_sha256": "b" * 64,
        "pilot_species_universe": list(species),
        "pilot_species_universe_count": len(species),
        "pilot_species_universe_sha256": "c" * 64,
        "pilot_island_order": snapshot_order,
        "pilot_island_to_block": {
            island: island_to_block[island]
            for island in snapshot_order
        },
        "target_bit_count": len(species),
        "targets_hex_by_island": targets,
        "pilot_island_count": len(snapshot_order),
        "pilot_block_count": 3,
        "confirmatory_target_values_parsed": 0,
        "confirmatory_occurrence_values_stored": False,
        "single_semantic_router_pass": True,
        "qualified_for_confirmatory_model_freeze": True,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
    }
    snapshot["snapshot_fingerprint"] = module.canonical_sha256(snapshot)

    execution = {
        "schema": "structural.boreal_beetle_burned_pilot_execution.v0_84",
        "status": "QUALIFIED_TO_FREEZE_CONFIRMATORY_PROTOCOL_WITH_MODEL_SNAPSHOT",
        "authorization_consumed": True,
        "confirmatory_target_values_parsed": 0,
        "confirmatory_response_authorized": False,
        "model_snapshot_frozen": True,
        "model_snapshot_fingerprint": snapshot["snapshot_fingerprint"],
    }

    return (
        module,
        contract,
        external,
        execution,
        snapshot,
        geometry_path,
        projection,
        habitat_path,
        habitat_receipt,
        spatial,
        operator,
        operator_receipt,
        species,
        confirmatory_islands,
    )


def test_full_v085_freeze_builds_predictions_without_confirmatory_targets(
    tmp_path: Path,
):
    (
        module,
        contract,
        external,
        execution,
        snapshot,
        geometry_path,
        projection,
        habitat_path,
        habitat_receipt,
        spatial,
        operator,
        operator_receipt,
        species,
        confirmatory_islands,
    ) = synthetic_freeze_inputs(tmp_path)

    receipt, predictions = module.freeze(
        pilot_execution=execution,
        pilot_snapshot=snapshot,
        geometry_csv=geometry_path,
        projection_receipt=projection,
        habitat_reference_csv=habitat_path,
        habitat_receipt=habitat_receipt,
        spatial_receipt=spatial,
        operator=operator,
        operator_receipt=operator_receipt,
        external=external,
        contract=contract,
    )

    assert receipt["status"] == (
        "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE"
    )
    assert receipt["confirmatory_target_values_opened"] == 0
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["effect_size"] is None
    assert receipt["prediction_score"] is None
    assert receipt["counts_as_empirical_evidence"] is False
    assert receipt["species_count"] == len(species)
    assert receipt["confirmatory_island_count"] == len(confirmatory_islands)
    assert receipt["prediction_row_count"] == (
        len(confirmatory_islands) * len(species)
    )
    assert set(receipt["models"]) == {"R0", "R1", "R2", "R3", "C"}
    assert receipt["prediction_surface_sha256"] == sha256_text(predictions)

    lines = predictions.splitlines()
    assert lines[0] == (
        "island,block,species,p_R0_hex,p_R1_hex,p_R2_hex,p_R3_hex,p_C_hex"
    )
    assert len(lines) - 1 == receipt["prediction_row_count"]
    assert "target" not in lines[0].lower()
    assert all(
        spatial["island_to_block"][row.split(",")[0]].startswith("C")
        for row in lines[1:]
    )


def test_v085_rejects_any_confirmatory_parse_flag(tmp_path: Path):
    (
        module,
        contract,
        external,
        execution,
        snapshot,
        geometry_path,
        projection,
        habitat_path,
        habitat_receipt,
        spatial,
        operator,
        operator_receipt,
        _,
        _,
    ) = synthetic_freeze_inputs(tmp_path)
    execution = dict(execution)
    execution["confirmatory_target_values_parsed"] = 1

    try:
        module.freeze(
            pilot_execution=execution,
            pilot_snapshot=snapshot,
            geometry_csv=geometry_path,
            projection_receipt=projection,
            habitat_reference_csv=habitat_path,
            habitat_receipt=habitat_receipt,
            spatial_receipt=spatial,
            operator=operator,
            operator_receipt=operator_receipt,
            external=external,
            contract=contract,
        )
    except module.BorealPreconfirmatoryFreezeError as exc:
        assert "confirmatory parse boundary" in str(exc)
    else:
        raise AssertionError("confirmatory parse flag should STOP v0.85")


def test_v085_contract_keeps_primary_on_overall_c_minus_r3():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    scoring = contract["primary_scoring"]
    assert "C-minus-R3" in scoring["estimand"]
    assert scoring["favourable_direction"] == "negative"
    assert scoring["bootstrap_unit"] == "confirmatory v0.75 spatial block"
    assert scoring["bootstrap_replicates"] == 10000
    assert scoring["external_isolation_interaction_required"] is False
    assert scoring["secondary_moderator_may_rescue_failed_primary"] is False
    assert contract["freeze_ceiling"]["confirmatory_response_authorized"] is False


def test_v085_status_keeps_confirmatory_response_sealed():
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
    assert boreal["confirmatory_predictions_frozen"] is False
    assert boreal["confirmatory_response_values_opened"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
