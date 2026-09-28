from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_boreal_19island_prepilot_contracts_v1_03.py"
CONTRACT = ROOT / "development/boreal_19island_prepilot_contract_builder_v1_03.json"
INTAKE = ROOT / "development/boreal_19island_response_sealed_intake_v1_02.json"
RECEIPT = ROOT / "development/boreal_19island_response_sealed_intake_receipt_v1_02.json"


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_v103", SCRIPT)
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
        load(INTAKE),
        load(RECEIPT),
        contract=load(CONTRACT),
        intake_file_sha256=sha(INTAKE),
        intake_receipt_file_sha256=sha(RECEIPT),
    )


def test_real_v102_intake_builds_generic_v031_and_v042():
    protocol, quality, receipt = build_real()

    assert protocol["system_id"] == "lac_la_ronge_boreal_19island_beetles_2026"
    assert len(protocol["pilot_partition"]) == 3
    assert len(protocol["confirmatory_partition"]) == 7
    assert protocol["minimum_test_rows"] == 3
    assert protocol["minimum_train_positive"] == 5
    assert protocol["minimum_train_negative"] == 5
    assert protocol["minimum_estimable_blocks"] == 3
    assert protocol["pilot_response_accessed"] is False
    assert protocol["confirmatory_response_accessed"] is False
    assert protocol["pilot_used_for_effect_estimation"] is False

    assert quality["system_id"] == protocol["system_id"]
    assert quality["minimum_response_qualified_blocks"] == 3
    assert quality["pilot_response_accessed"] is False
    assert quality["confirmatory_response_accessed"] is False

    assert receipt["status"] == "V031_AND_V042_FROZEN_RESPONSE_REMAINS_SEALED"
    assert receipt["generic_v0_31_status"] == "qualified_to_open_pilot"
    assert receipt["generic_v0_42_status"] == (\n        "qualified_response_quality_contract_before_pilot"\n    )\n    assert receipt["pilot_block_count"] == 3
    assert receipt["confirmatory_block_count"] == 7
    assert receipt["pilot_island_count"] == 6
    assert receipt["confirmatory_island_count"] == 13
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["effect_size"] is None
    assert receipt["prediction_score"] is None
    assert receipt["predictive_denominator_contribution"] == 0
    assert receipt["counts_as_empirical_evidence"] is False


def test_v103_is_bound_to_exact_v102_files_and_operator():
    _, _, receipt = build_real()
    intake = load(INTAKE)
    assert receipt["source_intake_file_sha256"] == sha(INTAKE)
    assert receipt["source_intake_receipt_file_sha256"] == sha(RECEIPT)
    assert receipt["parent_intake_fingerprint"] == load(RECEIPT)[
        "intake_fingerprint"
    ]
    assert receipt["source_operator_fingerprint"] == intake["source_operator"][
        "fingerprint"
    ]
    assert quality_parent_matches_protocol()


def quality_parent_matches_protocol():
    protocol, quality, receipt = build_real()
    return (
        quality["parent_protocol_fingerprint"] == receipt["protocol_fingerprint"]
    )


def test_tampered_intake_fingerprint_fails_closed():
    module = load_module()
    receipt = load(RECEIPT)
    receipt["intake_fingerprint"] = "0" * 64
    with pytest.raises(module.Boreal19PrepilotError, match="intake fingerprint"):
        module.build(
            load(INTAKE),
            receipt,
            contract=load(CONTRACT),
            intake_file_sha256=sha(INTAKE),
            intake_receipt_file_sha256=sha(RECEIPT),
        )


def test_post_open_rescue_drift_fails_closed():
    module = load_module()
    intake = load(INTAKE)
    intake["prepilot_design"]["v0_42"]["post_open_rescue_forbidden"] = False
    receipt = load(RECEIPT)
    receipt["intake_fingerprint"] = module.canonical_sha256(intake)

    with pytest.raises(module.Boreal19PrepilotError, match="rescue prohibition"):
        module.build(
            intake,
            receipt,
            contract=load(CONTRACT),
            intake_file_sha256=sha(INTAKE),
            intake_receipt_file_sha256=sha(RECEIPT),
        )
