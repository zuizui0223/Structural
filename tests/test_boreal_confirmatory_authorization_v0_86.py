from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from structural.boreal_confirmatory_router import (
    BorealConfirmatoryRouterError,
    build_boreal_confirmatory_surface,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/authorize_boreal_confirmatory_response_v0_86.py"
CONTRACT = ROOT / "development/boreal_confirmatory_response_authorization_contract_v0_86.json"
METADATA = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
STATUS = ROOT / "development/current_status_v0_86.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_86.json"


def load_auth():
    spec = importlib.util.spec_from_file_location(
        "boreal_confirmatory_auth_v086",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_router_inputs():
    pilot = ("P1", "P2", "P3")
    confirmatory = ("C1", "C2", "C3")
    islands = (
        "I1", "I2", "I3",
        "J1", "J2", "J3",
    )
    mapping = {
        "I1": "P1",
        "I2": "P2",
        "I3": "P3",
        "J1": "C1",
        "J2": "C2",
        "J3": "C3",
    }
    # Fixed species are sp1 and sp3. Pilot occurrence bytes are invalid and
    # confirmatory non-focal sp2/sp4 bytes are also invalid.
    raw = (
        b"Island,sp1,sp2,sp3,sp4\n"
        b"I1,\xff,\xfe,\xff,\xfe\n"
        b"I2,\xfe,\xff,\xfe,\xff\n"
        b"I3,\xff,\xff,\xfe,\xfe\n"
        b"J1,1,\xff,0,\xfe\n"
        b"J2,0,\xfe,1,\xff\n"
        b"J3,1,\xff,1,\xfe\n"
    )
    return raw, mapping, pilot, confirmatory, islands


def test_confirmatory_router_opens_only_fixed_species_on_confirmatory_islands():
    raw, mapping, pilot, confirmatory, islands = synthetic_router_inputs()
    routed = build_boreal_confirmatory_surface(
        response_csv_bytes=raw,
        island_to_block=mapping,
        pilot_partition=pilot,
        confirmatory_partition=confirmatory,
        expected_islands=islands,
        fixed_species=("sp1", "sp3"),
        expected_species_count=4,
    )

    assert routed.source_response_rows_seen == 6
    assert routed.routing_island_fields_decoded == 6
    assert routed.confirmatory_island_rows_semantically_parsed == 3
    assert routed.confirmatory_target_values_parsed == 6
    assert routed.pilot_target_values_parsed == 0
    assert routed.nonfocal_confirmatory_target_values_parsed == 0
    assert routed.fixed_species_count == 2
    assert routed.confirmatory_island_count == 3
    assert routed.confirmatory_block_count == 3

    lines = routed.csv_text.splitlines()
    assert lines[0] == "island,block,species,target"
    assert lines[1:] == [
        "J1,C1,sp1,1",
        "J1,C1,sp3,0",
        "J2,C2,sp1,0",
        "J2,C2,sp3,1",
        "J3,C3,sp1,1",
        "J3,C3,sp3,1",
    ]
    assert "\ufffd" not in routed.csv_text


def test_confirmatory_router_stops_on_bad_focal_confirmatory_value():
    raw, mapping, pilot, confirmatory, islands = synthetic_router_inputs()
    raw = raw.replace(b"J1,1,\xff,0,\xfe", b"J1,X,\xff,0,\xfe")
    with pytest.raises(
        BorealConfirmatoryRouterError,
        match="unexpected confirmatory focal occurrence",
    ):
        build_boreal_confirmatory_surface(
            response_csv_bytes=raw,
            island_to_block=mapping,
            pilot_partition=pilot,
            confirmatory_partition=confirmatory,
            expected_islands=islands,
            fixed_species=("sp1", "sp3"),
            expected_species_count=4,
        )


def test_v086_authorization_requires_exact_v085_replay(monkeypatch):
    module = load_auth()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    candidate = contract["candidate_id"]

    predictions = (
        "island,block,species,p_R0_hex,p_R1_hex,p_R2_hex,p_R3_hex,p_C_hex\n"
        "A,C1,sp1,0x1p-1,0x1p-1,0x1p-1,0x1p-1,0x1p-1\n"
    )
    prediction_sha = hashlib.sha256(
        predictions.encode("utf-8")
    ).hexdigest()
    receipt = {
        "schema": "structural.boreal_preconfirmatory_model_freeze.v0_85",
        "status": "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE",
        "candidate_id": candidate,
        "prediction_surface_sha256": prediction_sha,
        "prediction_row_count": 1,
        "species_count": 1,
        "confirmatory_island_count": 1,
        "confirmatory_block_count": 1,
        "confirmatory_target_values_opened": 0,
        "confirmatory_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "counts_as_empirical_evidence": False,
    }

    monkeypatch.setattr(
        module,
        "freeze_v085",
        lambda **kwargs: (dict(receipt), predictions),
    )

    result = module.authorize(
        pilot_execution={},
        pilot_snapshot={},
        geometry_csv=Path("unused-geometry.csv"),
        projection_receipt={},
        habitat_reference_csv=Path("unused-habitat.csv"),
        habitat_receipt={},
        spatial_receipt={},
        operator={},
        operator_receipt={},
        model_receipt=receipt,
        predictions_text=predictions,
        external={},
        contract=contract,
        v085_contract={},
        metadata=metadata,
        model_receipt_sha256="a" * 64,
    )

    assert result["status"] == "AUTHORIZED_ONE_SHOT_CONFIRMATORY_RESPONSE"
    assert result["confirmatory_response_authorized"] is True
    assert result["authorization_consumed"] is False
    assert result["prediction_surface_sha256"] == prediction_sha
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["counts_as_empirical_evidence"] is False
    allowed = result["allowed_semantic_access"]
    assert allowed["confirmatory_fixed_species_occurrence_cells"] is True
    assert allowed["confirmatory_nonfocal_species_occurrence_cells"] is False
    assert allowed["pilot_island_occurrence_cells"] is False


def test_v086_authorization_rejects_prediction_surface_drift(monkeypatch):
    module = load_auth()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    candidate = contract["candidate_id"]
    frozen = "header\nA\n"
    receipt = {
        "schema": "structural.boreal_preconfirmatory_model_freeze.v0_85",
        "status": "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE",
        "candidate_id": candidate,
        "prediction_surface_sha256": hashlib.sha256(
            frozen.encode("utf-8")
        ).hexdigest(),
        "prediction_row_count": 1,
        "species_count": 1,
        "confirmatory_island_count": 1,
        "confirmatory_block_count": 1,
        "confirmatory_target_values_opened": 0,
        "confirmatory_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "counts_as_empirical_evidence": False,
    }
    monkeypatch.setattr(
        module,
        "freeze_v085",
        lambda **kwargs: (dict(receipt), frozen),
    )

    with pytest.raises(
        module.BorealConfirmatoryAuthorizationError,
        match="prediction surface does not exact-replay",
    ):
        module.authorize(
            pilot_execution={},
            pilot_snapshot={},
            geometry_csv=Path("unused"),
            projection_receipt={},
            habitat_reference_csv=Path("unused"),
            habitat_receipt={},
            spatial_receipt={},
            operator={},
            operator_receipt={},
            model_receipt=receipt,
            predictions_text=frozen + "tampered",
            external={},
            contract=contract,
            v085_contract={},
            metadata=metadata,
            model_receipt_sha256="b" * 64,
        )


def test_real_v086_response_identity_matches_v065():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    target = contract["response_file"]
    frozen = metadata["focal_files"][target["name"]]

    assert frozen["file_id"] == target["dryad_file_id"]
    assert frozen["size"] == target["expected_size_bytes"]
    assert frozen["sha256"] == target["expected_sha256"]
    assert frozen["role"] == "primary_response"
    assert contract["exact_replay"]["required"] is True
    assert contract["execution_authorized_now"] is False


def test_v086_status_keeps_confirmatory_response_unopened():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["confirmatory_predictions_frozen"] is False
    assert boreal["confirmatory_response_authorization_issued"] is False
    assert boreal["confirmatory_response_values_opened"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
