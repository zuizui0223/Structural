from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

from structural.boreal_confirmatory_scoring import (
    deterministic_block_bootstrap,
    score_primary,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_boreal_confirmatory_scoring_v0_87.py"
CONTRACT = ROOT / "development/boreal_confirmatory_scoring_contract_v0_87.json"
STATUS = ROOT / "development/current_status_v0_87.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_87.json"


def load_script():
    spec = importlib.util.spec_from_file_location(
        "boreal_confirmatory_scoring_v087",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prediction_text(rows):
    header = (
        "island,block,species,p_R0_hex,p_R1_hex,p_R2_hex,p_R3_hex,p_C_hex\n"
    )
    return header + "".join(
        f"{island},{block},{species},"
        f"{float(0.5).hex()},{float(0.5).hex()},{float(0.5).hex()},"
        f"{float(r3).hex()},{float(c).hex()}\n"
        for island, block, species, r3, c in rows
    )


def target_text(rows):
    return "island,block,species,target\n" + "".join(
        f"{island},{block},{species},{target}\n"
        for island, block, species, target in rows
    )


def test_primary_uses_equal_block_weights_not_raw_row_weights():
    predictions = prediction_text([
        ("A1", "B1", "sp1", 0.5, 0.8),
        ("A1", "B1", "sp2", 0.5, 0.8),
        ("A2", "B1", "sp1", 0.5, 0.8),
        ("Z1", "B2", "sp1", 0.9, 0.5),
    ])
    targets = target_text([
        ("A1", "B1", "sp1", 1),
        ("A1", "B1", "sp2", 1),
        ("A2", "B1", "sp1", 1),
        ("Z1", "B2", "sp1", 1),
    ])

    result = score_primary(
        predictions,
        targets,
        expected_blocks=("B1", "B2"),
        bootstrap_replicates=1000,
        bootstrap_seed=7,
    )

    d1 = math.log(0.5 / 0.8)
    d2 = math.log(0.9 / 0.5)
    expected_equal = (d1 + d2) / 2.0
    row_weighted = (3.0 * d1 + d2) / 4.0

    observed = float.fromhex(result["point_estimate_hex"])
    assert math.isclose(observed, expected_equal, rel_tol=1e-14)
    assert not math.isclose(observed, row_weighted, rel_tol=1e-8)
    assert observed > 0
    assert result["primary_supported"] is False


def test_uniform_favourable_blocks_support_primary():
    predictions = prediction_text([
        ("I1", "B1", "sp1", 0.5, 0.8),
        ("I2", "B2", "sp1", 0.5, 0.8),
        ("I3", "B3", "sp1", 0.5, 0.8),
        ("I4", "B4", "sp1", 0.5, 0.8),
        ("I5", "B5", "sp1", 0.5, 0.8),
        ("I6", "B6", "sp1", 0.5, 0.8),
    ])
    targets = target_text([
        ("I1", "B1", "sp1", 1),
        ("I2", "B2", "sp1", 1),
        ("I3", "B3", "sp1", 1),
        ("I4", "B4", "sp1", 1),
        ("I5", "B5", "sp1", 1),
        ("I6", "B6", "sp1", 1),
    ])
    result = score_primary(
        predictions,
        targets,
        expected_blocks=("B1", "B2", "B3", "B4", "B5", "B6"),
        bootstrap_replicates=1000,
        bootstrap_seed=20260928,
    )
    assert float.fromhex(result["point_estimate_hex"]) < 0
    assert float.fromhex(result["ci95_upper_hex"]) < 0
    assert result["primary_supported"] is True


def test_sha_bootstrap_is_exactly_reproducible():
    values = {"B1": -0.2, "B2": 0.1, "B3": -0.4}
    a = deterministic_block_bootstrap(values, replicates=50, seed=123)
    b = deterministic_block_bootstrap(
        dict(reversed(list(values.items()))),
        replicates=50,
        seed=123,
    )
    assert a == b
    assert len(a) == 50


def synthetic_execution_world(*, bad_focal=False):
    module = load_script()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract = json.loads(json.dumps(contract))
    contract["primary"]["bootstrap_replicates"] = 500

    fixed = ("sp1", "sp3")
    all_species = ["sp1", "sp2", "sp3"] + [
        f"nf{i:03d}" for i in range(463)
    ]
    assert len(all_species) == 466

    def row(island, focal1, focal3, fill):
        values = []
        for species in all_species:
            if species == "sp1":
                values.append(focal1)
            elif species == "sp3":
                values.append(focal3)
            else:
                values.append(fill)
        return island + "," + ",".join(values) + "\n"

    confirmatory_islands = tuple(f"CONF{i}" for i in range(1, 7))
    response_text = "Island," + ",".join(all_species) + "\n"
    for i in range(1, 4):
        response_text += row(f"PILOT{i}", "X", "X", "X")
    for i, island in enumerate(confirmatory_islands, start=1):
        focal1 = "X" if bad_focal and i == 1 else "1"
        response_text += row(island, focal1, "1", "X")
    response = response_text.encode("utf-8")

    contract["response_file"] = {
        "name": "beetles_speciesmatrix_presenceabsence.csv",
        "dryad_file_id": 1,
        "expected_size_bytes": len(response),
        "expected_sha256": hashlib.sha256(response).hexdigest(),
    }

    prediction_rows = []
    for i, island in enumerate(confirmatory_islands, start=1):
        block = f"C{i}"
        prediction_rows.extend([
            (island, block, "sp1", 0.5, 0.8),
            (island, block, "sp3", 0.5, 0.8),
        ])
    predictions = prediction_text(prediction_rows)
    prediction_sha = hashlib.sha256(predictions.encode("utf-8")).hexdigest()
    model_sha = "a" * 64

    model = {
        "schema": "structural.boreal_preconfirmatory_model_freeze.v0_85",
        "status": "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE",
        "candidate_id": contract["candidate_id"],
        "prediction_surface_sha256": prediction_sha,
        "prediction_row_count": 12,
        "species_count": 2,
        "confirmatory_island_count": 6,
        "confirmatory_block_count": 6,
        "primary_scoring": dict(contract["primary"]),
        "confirmatory_target_values_opened": 0,
        "confirmatory_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "counts_as_empirical_evidence": False,
    }
    auth = {
        "schema": "structural.boreal_confirmatory_response_authorization.v0_86",
        "status": "AUTHORIZED_ONE_SHOT_CONFIRMATORY_RESPONSE",
        "candidate_id": contract["candidate_id"],
        "source_model_receipt_sha256": model_sha,
        "prediction_surface_sha256": prediction_sha,
        "prediction_row_count": 12,
        "species_count": 2,
        "confirmatory_island_count": 6,
        "confirmatory_block_count": 6,
        "response_file": {
            "name": contract["response_file"]["name"],
            "dryad_file_id": 1,
            "size_bytes": len(response),
            "sha256": contract["response_file"]["expected_sha256"],
        },
        "allowed_semantic_access": {
            "species_header_names": True,
            "routing_island_field_all_rows": True,
            "confirmatory_fixed_species_occurrence_cells": True,
            "confirmatory_nonfocal_species_occurrence_cells": False,
            "pilot_island_occurrence_cells": False,
        },
        "router": {
            "pilot_target_values_parsed_must_equal": 0,
            "nonfocal_confirmatory_target_values_parsed_must_equal": 0,
        },
        "confirmatory_response_authorized": True,
        "authorization_consumed": False,
        "effect_size": None,
        "prediction_score": None,
        "counts_as_empirical_evidence": False,
        "eligible_action": "execute_one_shot_confirmatory_scoring",
    }
    snapshot = {
        "schema": "structural.boreal_beetle_pilot_training_snapshot.v0_84",
        "status": "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN",
        "pilot_species_universe": list(fixed),
    }
    island_to_block = {
        "PILOT1": "P1",
        "PILOT2": "P2",
        "PILOT3": "P3",
    }
    island_to_block.update({
        island: f"C{i}"
        for i, island in enumerate(confirmatory_islands, start=1)
    })
    spatial = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": contract["candidate_id"],
        "island_to_block": island_to_block,
        "pilot_block_ids": ["P1", "P2", "P3"],
        "confirmatory_block_ids": [f"C{i}" for i in range(1, 7)],
    }
    expected_islands = (
        "PILOT1",
        "PILOT2",
        "PILOT3",
        *confirmatory_islands,
    )
    return (
        module,
        contract,
        auth,
        model,
        model_sha,
        predictions,
        snapshot,
        spatial,
        response,
        expected_islands,
    )


def test_one_shot_execution_opens_only_focal_confirmatory_cells():
    (
        module,
        contract,
        auth,
        model,
        model_sha,
        predictions,
        snapshot,
        spatial,
        response,
        expected_islands,
    ) = synthetic_execution_world()

    result = module.execute(
        authorization=auth,
        model_receipt=model,
        predictions_text=predictions,
        pilot_snapshot=snapshot,
        spatial_receipt=spatial,
        response_bytes=response,
        contract=contract,
        expected_islands=expected_islands,
        model_receipt_sha256=model_sha,
    )
    assert result["authorization_consumed"] is True
    assert result["confirmatory_response_opened"] is True
    assert result["confirmatory_target_values_parsed"] == 12
    assert result["pilot_target_values_parsed"] == 0
    assert result["nonfocal_confirmatory_target_values_parsed"] == 0
    assert result["fresh_system_denominator_contribution"] == 1
    assert result["counts_as_fresh_confirmatory_evidence"] is True
    assert result["counts_as_primary_confirmatory_evidence"] is True
    assert result["primary_supported"] is True
    assert result["mechanism_claim_authorized"] is False
    assert result["rerun_authorized"] is False


def test_post_access_bad_focal_value_is_terminal_and_consumes_authorization():
    (
        module,
        contract,
        auth,
        model,
        model_sha,
        predictions,
        snapshot,
        spatial,
        response,
        expected_islands,
    ) = synthetic_execution_world(bad_focal=True)

    result = module.execute(
        authorization=auth,
        model_receipt=model,
        predictions_text=predictions,
        pilot_snapshot=snapshot,
        spatial_receipt=spatial,
        response_bytes=response,
        contract=contract,
        expected_islands=expected_islands,
        model_receipt_sha256=model_sha,
    )
    assert result["status"] == "TERMINAL_CONFIRMATORY_ROUTER_STOP"
    assert result["authorization_consumed"] is True
    assert result["confirmatory_response_opened"] is True
    assert result["counts_as_fresh_confirmatory_evidence"] is False
    assert result["fresh_system_denominator_contribution"] == 0
    assert result["rerun_authorized"] is False


def test_pre_access_response_sha_failure_does_not_consume_authorization():
    (
        module,
        contract,
        auth,
        model,
        model_sha,
        predictions,
        snapshot,
        spatial,
        response,
        expected_islands,
    ) = synthetic_execution_world()

    bad = response + b"x"
    with pytest.raises(
        module.BorealConfirmatoryExecutionError,
        match="response byte size mismatch",
    ):
        module.execute(
            authorization=auth,
            model_receipt=model,
            predictions_text=predictions,
            pilot_snapshot=snapshot,
            spatial_receipt=spatial,
            response_bytes=bad,
            contract=contract,
            expected_islands=expected_islands,
            model_receipt_sha256=model_sha,
        )


def test_model_receipt_sha_drift_stops_before_access():
    (
        module,
        contract,
        auth,
        model,
        _,
        predictions,
        snapshot,
        spatial,
        response,
        expected_islands,
    ) = synthetic_execution_world()

    with pytest.raises(
        module.BorealConfirmatoryExecutionError,
        match="model receipt SHA mismatch",
    ):
        module.execute(
            authorization=auth,
            model_receipt=model,
            predictions_text=predictions,
            pilot_snapshot=snapshot,
            spatial_receipt=spatial,
            response_bytes=response,
            contract=contract,
            expected_islands=expected_islands,
            model_receipt_sha256="b" * 64,
        )


def test_real_v087_contract_freezes_v055_primary_without_tail_rescue():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    primary = contract["primary"]
    assert "C-minus-R3" in primary["estimand"]
    assert primary["favourable_direction"] == "negative"
    assert primary["bootstrap_unit"] == "confirmatory v0.75 spatial block"
    assert primary["bootstrap_replicates"] == 10000
    assert primary["bootstrap_seed"] == 20260928
    assert primary["external_isolation_interaction_required"] is False
    assert primary["secondary_moderator_may_rescue_failed_primary"] is False
    assert contract["valid_completion"]["fresh_system_denominator_contribution"] == 1
    assert contract["interpretation"]["secondary_analysis_may_change_status"] is False


def test_v087_status_keeps_fresh_denominator_zero_before_execution():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["confirmatory_scoring_executed"] is False
    assert boreal["fresh_primary_result_exists"] is False
    assert boreal["confirmatory_response_values_opened"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
