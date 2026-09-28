from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/authorize_boreal_19island_pilot_response_v1_05.py"
CONTRACT = (
    ROOT
    / "development/boreal_19island_pilot_response_authorization_contract_v1_05.json"
)
INTAKE = ROOT / "development/boreal_19island_response_sealed_intake_v1_02.json"
INTAKE_RECEIPT = (
    ROOT
    / "development/boreal_19island_response_sealed_intake_receipt_v1_02.json"
)
V103_CONTRACT = (
    ROOT / "development/boreal_19island_prepilot_contract_builder_v1_03.json"
)
FREEZE = ROOT / "development/boreal_19island_prepilot_freeze_v1_04.json"
PROTOCOL = ROOT / "development/boreal_19island_v031_protocol_v1_03.json"
QUALITY = ROOT / "development/boreal_19island_v042_quality_contract_v1_03.json"
PREPILOT = ROOT / "development/boreal_19island_prepilot_receipt_v1_03.json"
METADATA = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_auth_v105", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_hashes():
    return {
        "intake": sha(INTAKE),
        "intake_receipt": sha(INTAKE_RECEIPT),
        "freeze": sha(FREEZE),
        "protocol": sha(PROTOCOL),
        "quality_contract": sha(QUALITY),
        "prepilot_receipt": sha(PREPILOT),
    }


def authorize_real():
    module = load_module()
    return module.authorize(
        load(INTAKE),
        load(INTAKE_RECEIPT),
        load(V103_CONTRACT),
        load(FREEZE),
        load(PROTOCOL),
        load(QUALITY),
        load(PREPILOT),
        load(METADATA),
        contract=load(CONTRACT),
        file_sha256=file_hashes(),
    )


def test_real_v104_bundle_authorizes_only_one_future_19island_pilot():
    auth = authorize_real()

    assert auth["schema"] == (
        "structural.boreal_19island_pilot_response_authorization.v1_05"
    )
    assert auth["status"] == (
        "AUTHORIZED_ONE_SHOT_19ISLAND_BURNED_PILOT_RESPONSE"
    )
    assert auth["candidate_id"] == (
        "lac_la_ronge_boreal_19island_beetles_2026"
    )
    assert auth["parent_intake_fingerprint"] == (
        "87df95481c96d710190174175254b4437459714f637f1d0a99aa37c078fa8cb2"
    )
    assert auth["source_operator_fingerprint"] == (
        "82e1afbd728bd677d4d7b0af65ece16be12a0dc8ae39505bbbac3d5ae151b621"
    )
    assert auth["protocol_fingerprint"] == (
        "3a4bd6698780049918c634a5253ff1846c84e8d1c3281e26e2014d766ab90314"
    )
    assert auth["quality_contract_fingerprint"] == (
        "8ac0fe95901caae988673b3d8079b123fdac00573f749049eec3264b89906b58"
    )

    assert auth["response_file"] == {
        "name": "beetles_speciesmatrix_presenceabsence.csv",
        "dryad_file_id": 4569032,
        "size_bytes": 49005,
        "sha256": (
            "01eef34863bfd49fdc68dfae0aec58766a6fcdd1234751a9c75824df9f038be0"
        ),
        "expected_source_island_rows": 42,
        "expected_species_columns": 466,
    }
    assert auth["analysis_population"]["island_count"] == 19
    assert auth["analysis_population"]["pilot_islands"] == [
        "DN", "FD", "HU", "IL", "IS", "PP"
    ]
    assert len(auth["analysis_population"]["confirmatory_islands"]) == 13
    assert auth["analysis_population"]["excluded_source_island_count"] == 23
    assert len(auth["analysis_population"]["pilot_block_ids"]) == 3
    assert len(auth["analysis_population"]["confirmatory_block_ids"]) == 7

    semantic = auth["allowed_semantic_access"]
    assert semantic["species_header_names"] is True
    assert semantic["routing_island_field_all_42_source_rows"] is True
    assert semantic["pilot_analysis_island_occurrence_cells"] is True
    assert semantic["confirmatory_analysis_island_occurrence_cells"] is False
    assert semantic["excluded_nonanalysis_island_occurrence_cells"] is False

    assert auth["pilot_response_authorized"] is True
    assert auth["confirmatory_response_authorized"] is False
    assert auth["mechanism_response_authorized"] is False
    assert auth["authorization_consumed"] is False
    assert auth["effect_size"] is None
    assert auth["prediction_score"] is None
    assert auth["predictive_denominator_contribution"] == 0
    assert auth["counts_as_empirical_evidence"] is False
    assert len(auth["authorization_fingerprint"]) == 64


def test_authorization_exact_replays_v103_and_v104_files():
    auth = authorize_real()
    hashes = file_hashes()
    assert auth["source_file_sha256"] == hashes

    freeze = load(FREEZE)
    assert hashes["protocol"] == freeze["files"]["protocol"]["sha256"]
    assert hashes["quality_contract"] == freeze["files"]["quality_contract"]["sha256"]
    assert hashes["prepilot_receipt"] == freeze["files"]["prepilot_receipt"]["sha256"]


def test_protocol_byte_tamper_fails_closed():
    module = load_module()
    hashes = file_hashes()
    hashes["protocol"] = "0" * 64
    with pytest.raises(
        module.Boreal19PilotAuthorizationError,
        match="protocol bytes drift",
    ):
        module.authorize(
            load(INTAKE),
            load(INTAKE_RECEIPT),
            load(V103_CONTRACT),
            load(FREEZE),
            load(PROTOCOL),
            load(QUALITY),
            load(PREPILOT),
            load(METADATA),
            contract=load(CONTRACT),
            file_sha256=hashes,
        )


def test_response_identity_tamper_fails_closed():
    module = load_module()
    metadata = load(METADATA)
    metadata["focal_files"]["beetles_speciesmatrix_presenceabsence.csv"][
        "sha256"
    ] = "0" * 64
    with pytest.raises(
        module.Boreal19PilotAuthorizationError,
        match="response identity drift",
    ):
        module.authorize(
            load(INTAKE),
            load(INTAKE_RECEIPT),
            load(V103_CONTRACT),
            load(FREEZE),
            load(PROTOCOL),
            load(QUALITY),
            load(PREPILOT),
            metadata,
            contract=load(CONTRACT),
            file_sha256=file_hashes(),
        )


def test_population_tamper_fails_closed():
    module = load_module()
    intake = load(INTAKE)
    intake["population"]["pilot_islands"] = list(
        reversed(intake["population"]["pilot_islands"])
    )
    with pytest.raises(
        module.Boreal19PilotAuthorizationError,
        match="pilot island population drift",
    ):
        module.authorize(
            intake,
            load(INTAKE_RECEIPT),
            load(V103_CONTRACT),
            load(FREEZE),
            load(PROTOCOL),
            load(QUALITY),
            load(PREPILOT),
            load(METADATA),
            contract=load(CONTRACT),
            file_sha256=file_hashes(),
        )
