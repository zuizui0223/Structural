from __future__ import annotations

import hashlib
import json
from pathlib import Path

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
FREEZE = ROOT / "development/boreal_19island_prepilot_freeze_v1_04.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v104_freeze_matches_exact_committed_artifact_files():
    freeze = load(FREEZE)
    assert freeze["status"] == "PREPILOT_CONTRACTS_COMMITTED_RESPONSE_SEALED"

    for key in ("protocol", "quality_contract", "prepilot_receipt"):
        item = freeze["files"][key]
        path = ROOT / item["path"]
        assert path.is_file()
        assert sha(path) == item["sha256"]

    assert freeze["files"]["protocol"]["sha256"] == (
        "1b742e92d95e026b2d276746360a96e0562d4aeb88e3d12b20314d72e862c725"
    )
    assert freeze["files"]["quality_contract"]["sha256"] == (
        "249be60bd133b89c1b5a37015d105719abb04b720e7d6fc427a3590dce773a35"
    )
    assert freeze["files"]["prepilot_receipt"]["sha256"] == (
        "61b4c4bbd1f3ea7d662594ecd58dc09ba38db450fc884a0fabdfd619ffe3961b"
    )


def test_v104_committed_protocol_and_quality_exact_replay_generic_evaluators():
    freeze = load(FREEZE)
    protocol = protocol_from_mapping(load(ROOT / freeze["files"]["protocol"]["path"]))
    quality = contract_from_mapping(
        load(ROOT / freeze["files"]["quality_contract"]["path"])
    )

    pdecision = evaluate_transition_pilot_protocol(protocol)
    qdecision = evaluate_response_quality_contract(
        protocol=protocol,
        contract=quality,
    )

    assert pdecision.status is PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT
    assert qdecision.status is ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT
    assert pdecision.protocol_fingerprint == freeze["protocol_fingerprint"]
    assert qdecision.contract_fingerprint == freeze["quality_contract_fingerprint"]
    assert quality.parent_protocol_fingerprint == freeze["protocol_fingerprint"]


def test_v104_receipt_preserves_zero_evidence_and_response_seal():
    freeze = load(FREEZE)
    receipt = load(ROOT / freeze["files"]["prepilot_receipt"]["path"])

    assert receipt["parent_intake_fingerprint"] == freeze[
        "parent_intake_fingerprint"
    ]
    assert receipt["source_operator_fingerprint"] == freeze[
        "source_operator_fingerprint"
    ]
    assert receipt["protocol_fingerprint"] == freeze["protocol_fingerprint"]
    assert receipt["quality_contract_fingerprint"] == freeze[
        "quality_contract_fingerprint"
    ]
    assert receipt["pilot_block_count"] == 3
    assert receipt["confirmatory_block_count"] == 7
    assert receipt["pilot_island_count"] == 6
    assert receipt["confirmatory_island_count"] == 13
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["predictive_denominator_contribution"] == 0
    assert receipt["counts_as_empirical_evidence"] is False

    assert freeze["response_boundary"] == {
        "pilot_response_opened": False,
        "confirmatory_response_opened": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "counts_as_empirical_evidence": False,
        "predictive_denominator_contribution": 0,
    }
    assert freeze["pilot_authorization_may_be_built"] is True
