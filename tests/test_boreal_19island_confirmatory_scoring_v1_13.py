from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_boreal_19island_confirmatory_scoring_v1_13.py"
CONTRACT = ROOT / "development/boreal_19island_confirmatory_scoring_contract_v1_13.json"


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_score_v113", SCRIPT)
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


def synthetic_world(*, bad_focal=False):
    module = load_module()
    base_contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract = json.loads(json.dumps(base_contract))
    candidate = "synthetic-19island"
    contract["candidate_id"] = candidate
    contract["primary"]["bootstrap_replicates"] = 500

    full = tuple(f"I{i:02d}" for i in range(1, 43))
    analysis = full[:19]
    pilot = analysis[:6]
    confirm = analysis[6:]
    excluded = full[19:]
    pilot_blocks = ("P1", "P2", "P3")
    confirm_blocks = tuple(f"C{i}" for i in range(1, 8))
    mapping = {}
    for i, island in enumerate(pilot):
        mapping[island] = pilot_blocks[i % 3]
    for i, island in enumerate(confirm):
        mapping[island] = confirm_blocks[i % 7]

    fixed = ("sp1", "sp3")
    fixed_sha = hashlib.sha256(
        "".join(f"{x}\n" for x in fixed).encode()
    ).hexdigest()
    all_species = ["sp1", "sp2", "sp3"] + [
        f"nf{i:03d}" for i in range(463)
    ]
    assert len(all_species) == 466

    def row(island, focal1, focal3, other):
        fields = []
        for species in all_species:
            if species == "sp1":
                fields.append(focal1)
            elif species == "sp3":
                fields.append(focal3)
            else:
                fields.append(other)
        return island.encode() + b"," + b",".join(
            value if isinstance(value, bytes) else value.encode()
            for value in fields
        ) + b"\n"

    response = ("Island," + ",".join(all_species) + "\n").encode()
    for index, island in enumerate(full):
        if island in confirm:
            focal1 = "X" if bad_focal and island == confirm[0] else "1"
            response += row(
                island,
                focal1=focal1,
                focal3="1",
                other=b"\xff",
            )
        else:
            response += row(
                island,
                focal1=b"\xff",
                focal3=b"\xfe",
                other=b"\xff",
            )
    response_sha = hashlib.sha256(response).hexdigest()

    predictions_rows = []
    for island in confirm:
        block = mapping[island]
        predictions_rows.extend([
            (island, block, "sp1", 0.5, 0.8),
            (island, block, "sp3", 0.5, 0.8),
        ])
    predictions = prediction_text(predictions_rows)
    prediction_sha = hashlib.sha256(predictions.encode()).hexdigest()
    model_sha = "a" * 64
    auth_sha = "b" * 64
    auth_fp = "c" * 64
    snapshot_fp = "d" * 64
    models_fp = "e" * 64

    contract["required_authorization"] = {
        "schema": "synthetic.auth",
        "status": "AUTHORIZED",
        "authorization_fingerprint": auth_fp,
        "authorization_json_sha256": auth_sha,
        "confirmatory_response_authorized": True,
        "authorization_consumed": False,
        "counts_as_empirical_evidence": False,
    }
    contract["required_prediction_freeze"] = {
        "prediction_surface_sha256": prediction_sha,
        "prediction_file_sha256": prediction_sha,
        "model_receipt_file_sha256": model_sha,
        "models_fingerprint": models_fp,
        "pilot_snapshot_fingerprint": snapshot_fp,
        "pilot_species_universe_sha256": fixed_sha,
        "species_count": 2,
        "prediction_row_count": len(predictions_rows),
        "confirmatory_island_count": 13,
        "confirmatory_block_count": 7,
    }
    contract["response_file"] = {
        "name": "response.csv",
        "dryad_file_id": 1,
        "download_url": "https://example.invalid/response",
        "expected_size_bytes": len(response),
        "expected_sha256": response_sha,
        "expected_species_columns": 466,
        "expected_full_source_island_rows": 42,
    }
    contract["semantic_access"] = {
        "router": "synthetic",
        "routing_island_fields_decoded_required": 42,
        "confirmatory_fixed_species_occurrence_cells": True,
        "confirmatory_target_values_parsed_required": 26,
        "pilot_target_values_parsed_required": 0,
        "excluded_target_values_parsed_required": 0,
        "nonfocal_confirmatory_target_values_parsed_required": 0,
    }

    authorization = {
        "schema": "synthetic.auth",
        "status": "AUTHORIZED",
        "candidate_id": candidate,
        "authorization_fingerprint": auth_fp,
        "confirmatory_response_authorized": True,
        "authorization_consumed": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "response_values_opened_by_authorization": False,
        "eligible_action": "execute_one_shot_19island_confirmatory_scoring",
        "source_model_receipt_sha256": model_sha,
        "prediction_surface_sha256": prediction_sha,
        "models_fingerprint": models_fp,
        "prediction_row_count": len(predictions_rows),
        "fixed_species_universe_sha256": fixed_sha,
        "full_source_island_order": list(full),
        "analysis_island_order": list(analysis),
        "pilot_islands": list(pilot),
        "confirmatory_islands": list(confirm),
        "excluded_islands": list(excluded),
        "island_to_block": mapping,
        "pilot_block_ids": list(pilot_blocks),
        "confirmatory_block_ids": list(confirm_blocks),
        "response_file": {
            "name": "response.csv",
            "dryad_file_id": 1,
            "size_bytes": len(response),
            "sha256": response_sha,
            "expected_species_columns": 466,
        },
        "allowed_semantic_access": {
            "species_header_names": True,
            "routing_island_field_all_42_rows": True,
            "confirmatory_fixed_species_occurrence_cells": True,
            "confirmatory_nonfocal_species_occurrence_cells": False,
            "pilot_island_occurrence_cells": False,
            "excluded_island_occurrence_cells": False,
        },
    }
    authorization_freeze = {
        "schema": (
            "structural.boreal_19island_confirmatory_authorization_freeze.v1_12"
        ),
        "status": (
            "CONFIRMATORY_AUTHORIZATION_COMMITTED_BY_FINGERPRINT_RESPONSE_UNOPENED"
        ),
        "candidate_id": candidate,
        "scoring_execution_may_be_built": True,
        "authorization": {
            "authorization_json_sha256": auth_sha,
            "authorization_fingerprint": auth_fp,
        },
        "response_boundary": {
            "response_values_opened": False,
            "confirmatory_response_authorized": True,
            "authorization_consumed": False,
            "counts_as_empirical_evidence": False,
            "predictive_denominator_contribution": 0,
        },
    }
    model_receipt = {
        "schema": (
            "structural.boreal_19island_preconfirmatory_model_freeze.v1_09"
        ),
        "status": "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE",
        "candidate_id": candidate,
        "models_fingerprint": models_fp,
        "prediction_surface_sha256": prediction_sha,
        "pilot_snapshot_fingerprint": snapshot_fp,
        "pilot_species_universe_sha256": fixed_sha,
        "species_count": 2,
        "prediction_row_count": len(predictions_rows),
        "confirmatory_island_count": 13,
        "confirmatory_block_count": 7,
        "confirmatory_target_values_opened": 0,
        "excluded_target_values_opened": 0,
        "confirmatory_response_authorized": False,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "primary_scoring": {
            "favourable_direction": "negative",
            "bootstrap_replicates": 500,
            "bootstrap_seed": 20260928,
            "external_isolation_interaction_required": False,
            "secondary_moderator_may_rescue_failed_primary": False,
        },
    }
    snapshot = {
        "schema": "structural.boreal_19island_pilot_training_snapshot.v1_07",
        "status": "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN",
        "snapshot_fingerprint": snapshot_fp,
        "pilot_species_universe": list(fixed),
    }
    spatial = {
        "schema": "structural.boreal_19island_spatial_partition_freeze.v1_00",
        "status": "SPATIAL_PARTITION_COMMITTED_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "pilot_block_ids": list(pilot_blocks),
        "confirmatory_block_ids": list(confirm_blocks),
        "pilot_islands": list(pilot),
        "confirmatory_islands": list(confirm),
        "island_to_block": mapping,
    }
    return {
        "module": module,
        "contract": contract,
        "authorization": authorization,
        "authorization_freeze": authorization_freeze,
        "authorization_sha": auth_sha,
        "model_receipt": model_receipt,
        "model_sha": model_sha,
        "predictions": predictions,
        "prediction_sha": prediction_sha,
        "snapshot": snapshot,
        "spatial": spatial,
        "response": response,
    }


def run_world(world):
    return world["module"].execute(
        authorization=world["authorization"],
        authorization_freeze=world["authorization_freeze"],
        authorization_file_sha256=world["authorization_sha"],
        model_receipt=world["model_receipt"],
        model_receipt_file_sha256=world["model_sha"],
        predictions_text=world["predictions"],
        predictions_file_sha256=world["prediction_sha"],
        pilot_snapshot=world["snapshot"],
        spatial_freeze=world["spatial"],
        response_bytes=world["response"],
        contract=world["contract"],
    )


def test_one_shot_execution_scores_only_fixed_confirmatory_targets():
    result = run_world(synthetic_world())
    assert result["status"] == (
        "PRIMARY_SUPPORTED_INTERNAL_SOURCE_ISOLATION_NONREDUNDANT"
    )
    assert result["authorization_consumed"] is True
    assert result["confirmatory_response_opened"] is True
    assert result["routing_island_fields_decoded"] == 42
    assert result["confirmatory_target_values_parsed"] == 26
    assert result["pilot_target_values_parsed"] == 0
    assert result["excluded_target_values_parsed"] == 0
    assert result["nonfocal_confirmatory_target_values_parsed"] == 0
    assert result["fixed_species_count"] == 2
    assert result["confirmatory_island_count"] == 13
    assert result["confirmatory_block_count"] == 7
    assert result["excluded_island_count"] == 23
    assert result["fresh_system_denominator_contribution"] == 1
    assert result["counts_as_fresh_confirmatory_evidence"] is True
    assert result["counts_as_primary_confirmatory_evidence"] is True
    assert result["primary_supported"] is True
    assert result["mechanism_claim_authorized"] is False
    assert result["rerun_authorized"] is False


def test_post_access_bad_focal_value_is_terminal_and_nonrerunnable():
    result = run_world(synthetic_world(bad_focal=True))
    assert result["status"] == "TERMINAL_CONFIRMATORY_ROUTER_STOP"
    assert result["authorization_consumed"] is True
    assert result["confirmatory_response_opened"] is True
    assert result["fresh_system_denominator_contribution"] == 0
    assert result["counts_as_fresh_confirmatory_evidence"] is False
    assert result["primary_supported"] is None
    assert result["rerun_authorized"] is False


def test_pre_access_response_sha_failure_does_not_consume_authorization():
    world = synthetic_world()
    world["response"] += b"x"
    with pytest.raises(
        world["module"].Boreal19ConfirmatoryExecutionError,
        match="response byte size mismatch",
    ):
        run_world(world)


def test_real_v113_contract_reuses_v087_primary_without_rescue():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    primary = contract["primary"]
    assert "C-minus-R3" in primary["estimand"]
    assert primary["favourable_direction"] == "negative"
    assert primary["bootstrap_replicates"] == 10000
    assert primary["bootstrap_seed"] == 20260928
    assert primary["quantile_method"] == "linear_type7"
    assert primary["external_isolation_interaction_required"] is False
    assert primary["secondary_moderator_may_rescue_failed_primary"] is False
    assert contract["valid_completion"]["fresh_system_denominator_contribution"] == 1
    assert contract["interpretation"]["secondary_analysis_may_change_status"] is False
    assert contract["interpretation"]["mechanism_claim_authorized"] is False
