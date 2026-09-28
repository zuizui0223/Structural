from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from structural.response_quality_attrition import (
    ResponseQualityContractStatus,
    contract_from_mapping,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    evaluate_transition_pilot_protocol,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_boreal_19island_prepilot_contracts_v1_03.py"
CONTRACT = ROOT / "development/boreal_19island_prepilot_contract_builder_v1_03.json"
INTAKE = ROOT / "development/boreal_19island_response_sealed_intake_v1_02.json"
RECEIPT = (
    ROOT / "development/boreal_19island_response_sealed_intake_receipt_v1_02.json"
)


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


def test_real_v102_parent_builds_generic_v031_and_v042():
    protocol_map, quality_map, receipt = build_real()

    protocol = protocol_from_mapping(protocol_map)
    pdecision = evaluate_transition_pilot_protocol(protocol)
    assert pdecision.status is PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT

    quality = contract_from_mapping(quality_map)
    qdecision = evaluate_response_quality_contract(
        protocol=protocol,
        contract=quality,
    )
    assert qdecision.status is ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT

    intake = load(INTAKE)
    assert protocol.system_id == "lac_la_ronge_boreal_19island_beetles_2026"
    assert list(protocol.pilot_partition) == intake["population"]["pilot_block_ids"]
    assert list(protocol.confirmatory_partition) == (
        intake["population"]["confirmatory_block_ids"]
    )
    assert protocol.minimum_test_rows == 3
    assert protocol.minimum_train_positive == 5
    assert protocol.minimum_train_negative == 5
    assert protocol.minimum_estimable_blocks == 3
    assert protocol.pilot_response_accessed is False
    assert protocol.confirmatory_response_accessed is False
    assert protocol.pilot_used_for_effect_estimation is False

    assert quality.minimum_response_qualified_blocks == 3
    assert quality.parent_protocol_fingerprint == pdecision.protocol_fingerprint
    assert quality.pilot_response_accessed is False
    assert quality.confirmatory_response_accessed is False

    assert receipt["status"] == "V031_AND_V042_FROZEN_RESPONSE_REMAINS_SEALED"
    assert receipt["parent_intake_fingerprint"] == (
        "87df95481c96d710190174175254b4437459714f637f1d0a99aa37c078fa8cb2"
    )
    assert receipt["source_intake_file_sha256"] == (
        "b2257ec7f06c6f8d6583c40f00eef5e4c917dc343fe8aa62800819c68226cd67"
    )
    assert receipt["source_intake_receipt_file_sha256"] == (
        "35b956b211217d2232057d151b48a9cf0076e552cc6bcbdf4c8d9c1faf5f72aa"
    )
    assert receipt["source_operator_fingerprint"] == (
        "82e1afbd728bd677d4d7b0af65ece16be12a0dc8ae39505bbbac3d5ae151b621"
    )
    assert receipt["pilot_block_count"] == 3
    assert receipt["confirmatory_block_count"] == 7
    assert receipt["pilot_island_count"] == 6
    assert receipt["confirmatory_island_count"] == 13
    assert receipt["generic_v0_31_status"] == "qualified_to_open_pilot"
    assert receipt["generic_v0_42_status"] == "qualified_to_open_pilot"
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["mechanism_response_authorized"] is False
    assert receipt["effect_size"] is None
    assert receipt["prediction_score"] is None
    assert receipt["predictive_denominator_contribution"] == 0
    assert receipt["counts_as_empirical_evidence"] is False


def test_exact_parent_identity_is_predeclared():
    contract = load(CONTRACT)
    x = contract["required_parent_identity"]
    assert x == {
        "intake_fingerprint": (
            "87df95481c96d710190174175254b4437459714f637f1d0a99aa37c078fa8cb2"
        ),
        "intake_file_sha256": (
            "b2257ec7f06c6f8d6583c40f00eef5e4c917dc343fe8aa62800819c68226cd67"
        ),
        "intake_receipt_file_sha256": (
            "35b956b211217d2232057d151b48a9cf0076e552cc6bcbdf4c8d9c1faf5f72aa"
        ),
        "source_operator_fingerprint": (
            "82e1afbd728bd677d4d7b0af65ece16be12a0dc8ae39505bbbac3d5ae151b621"
        ),
    }
    assert sha(INTAKE) == x["intake_file_sha256"]
    assert sha(RECEIPT) == x["intake_receipt_file_sha256"]


def test_parent_file_sha_tamper_fails_closed():
    module = load_module()
    with pytest.raises(module.Boreal19PrepilotError, match="intake file SHA drift"):
        module.build(
            load(INTAKE),
            load(RECEIPT),
            contract=load(CONTRACT),
            intake_file_sha256="0" * 64,
            intake_receipt_file_sha256=sha(RECEIPT),
        )


def test_intake_fingerprint_tamper_fails_closed():
    module = load_module()
    intake = load(INTAKE)
    intake["population"]["pilot_block_ids"] = list(
        reversed(intake["population"]["pilot_block_ids"])
    )
    with pytest.raises(module.Boreal19PrepilotError, match="intake fingerprint"):
        module.build(
            intake,
            load(RECEIPT),
            contract=load(CONTRACT),
            intake_file_sha256=sha(INTAKE),
            intake_receipt_file_sha256=sha(RECEIPT),
        )


def test_response_opening_tamper_fails_closed():
    module = load_module()
    intake = load(INTAKE)
    intake["response_values_accessed"] = True
    with pytest.raises(module.Boreal19PrepilotError, match="firewall already opened"):
        module.build(
            intake,
            load(RECEIPT),
            contract=load(CONTRACT),
            intake_file_sha256=sha(INTAKE),
            intake_receipt_file_sha256=sha(RECEIPT),
        )
