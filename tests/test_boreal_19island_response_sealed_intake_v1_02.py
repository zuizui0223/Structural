from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_boreal_19island_response_sealed_intake_v1_02.py"
CONTRACT = ROOT / "development/boreal_19island_response_sealed_intake_contract_v1_02.json"
SPATIAL = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
STATE = ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
OPERATOR = ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
METADATA = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
PREINTAKE = ROOT / "development/boreal_lake_islands_preintake_v0_65.json"


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_intake_v102", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_real():
    module = load_module()
    return module.build(
        load(SPATIAL),
        load(STATE),
        load(OPERATOR),
        load(METADATA),
        load(PREINTAKE),
        contract=load(CONTRACT),
        parent_sha256={
            "spatial_freeze": sha(SPATIAL),
            "state_freeze": sha(STATE),
            "source_operator_freeze": sha(OPERATOR),
        },
    )


def test_real_frozen_parents_build_exact_19island_response_sealed_intake():
    intake, receipt = build_real()

    assert intake["schema"] == (
        "structural.boreal_19island_response_sealed_intake.v1_02"
    )
    assert intake["status"] == "RESPONSE_SEALED_READY_FOR_PREPILOT_CONSTRUCTION"
    assert intake["population"]["island_count"] == 19
    assert len(intake["population"]["pilot_islands"]) == 6
    assert len(intake["population"]["confirmatory_islands"]) == 13
    assert len(intake["population"]["pilot_block_ids"]) == 3
    assert len(intake["population"]["confirmatory_block_ids"]) == 7
    assert set(intake["population"]["pilot_islands"]).isdisjoint(
        intake["population"]["confirmatory_islands"]
    )
    assert intake["response_file"]["opened"] is False
    assert intake["response_values_accessed"] is False
    assert intake["response_firewall_state"] == "response_sealed"
    assert intake["response_file"]["sha256"] == (
        "01eef34863bfd49fdc68dfae0aec58766a6fcdd1234751a9c75824df9f038be0"
    )
    assert intake["source_operator"]["fingerprint"] == (
        "82e1afbd728bd677d4d7b0af65ece16be12a0dc8ae39505bbbac3d5ae151b621"
    )
    assert intake["state_reference"]["R0_columns"] == [
        "PC1", "PC2", "PC3", "TSF_Z"
    ]
    assert intake["state_reference"]["R1_add_columns"] == [
        "LOG_AREA_Z", "LOG_MAINLAND_DISTANCE_Z"
    ]

    assert receipt["status"] == "ELIGIBLE_TO_BUILD_V031_V042_RESPONSE_SEALED"
    assert receipt["island_count"] == 19
    assert receipt["pilot_block_count"] == 3
    assert receipt["confirmatory_block_count"] == 7
    assert receipt["v0_31_protocol_construction_authorized"] is True
    assert receipt["v0_42_quality_contract_construction_authorized"] is True
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["predictive_denominator_contribution"] == 0
    assert receipt["counts_as_empirical_evidence"] is False


def test_intake_is_bound_to_exact_committed_parent_files():
    intake, receipt = build_real()
    assert intake["parent_freeze_sha256"] == {
        "spatial_freeze": sha(SPATIAL),
        "state_freeze": sha(STATE),
        "source_operator_freeze": sha(OPERATOR),
    }
    assert receipt["parent_freeze_sha256"] == intake["parent_freeze_sha256"]


def test_operator_parent_tamper_fails_closed():
    module = load_module()
    operator = load(OPERATOR)
    operator["parents"]["spatial_freeze_sha256"] = "0" * 64

    with pytest.raises(module.Boreal19IntakeError, match="exact spatial freeze"):
        module.build(
            load(SPATIAL),
            load(STATE),
            operator,
            load(METADATA),
            load(PREINTAKE),
            contract=load(CONTRACT),
            parent_sha256={
                "spatial_freeze": sha(SPATIAL),
                "state_freeze": sha(STATE),
                "source_operator_freeze": sha(OPERATOR),
            },
        )


def test_response_identity_tamper_fails_closed():
    module = load_module()
    metadata = load(METADATA)
    metadata["focal_files"]["beetles_speciesmatrix_presenceabsence.csv"][
        "sha256"
    ] = "0" * 64

    with pytest.raises(module.Boreal19IntakeError, match="response identity drift"):
        module.build(
            load(SPATIAL),
            load(STATE),
            load(OPERATOR),
            metadata,
            load(PREINTAKE),
            contract=load(CONTRACT),
            parent_sha256={
                "spatial_freeze": sha(SPATIAL),
                "state_freeze": sha(STATE),
                "source_operator_freeze": sha(OPERATOR),
            },
        )
