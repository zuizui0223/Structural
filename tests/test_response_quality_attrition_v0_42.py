from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_transition_pilot_v0_32 import run as run_v0_32
from structural.future_admission_v0_42 import (
    FutureAdmissionStatus,
    evaluate_future_admission_v0_42,
)
from structural.response_quality_attrition import (
    ResponseQualityAttritionContract,
    ResponseQualityAuditStatus,
    ResponseQualityContractStatus,
    audit_response_quality_attrition,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (
    protocol_fingerprint,
    protocol_from_mapping,
)


def protocol_mapping(**changes):
    data = {
        "protocol_id": "future-v42",
        "system_id": "system-v42",
        "partition_axis": "time_window",
        "pilot_partition": ["pilot-A"],
        "confirmatory_partition": ["confirm-B"],
        "endpoint_id": "future-state",
        "endpoint_semantics": "binary; response-quality failures are non-estimable",
        "heldout_design_id": "leave-one-block-out",
        "minimum_test_rows": 2,
        "minimum_train_positive": 1,
        "minimum_train_negative": 1,
        "minimum_estimable_blocks": 2,
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
        "pilot_used_for_effect_estimation": False,
    }
    data.update(changes)
    return data


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data), encoding="utf-8")


def write_rows(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["partition_unit", "block", "target"])
        writer.writerows(rows)


def make_contract(protocol, **changes):
    data = dict(
        contract_id="quality-v42",
        system_id=protocol.system_id,
        parent_protocol_fingerprint=protocol_fingerprint(protocol),
        minimum_response_qualified_blocks=3,
        response_quality_semantics=(
            "rows failing predeclared survey/completeness/effort gates are encoded "
            "as missing targets before pilot audit"
        ),
        pilot_response_accessed=False,
        confirmatory_response_accessed=False,
    )
    data.update(changes)
    return ResponseQualityAttritionContract(**data)


def run_pilot(tmp_path: Path, mapping: dict, rows):
    protocol_path = tmp_path / "protocol.json"
    pilot_path = tmp_path / "pilot.csv"
    write_json(protocol_path, mapping)
    write_rows(pilot_path, rows)
    code, result = run_v0_32(protocol_path, pilot_path)
    return code, result, protocol_from_mapping(mapping)


def test_v042_catches_quality_attrition_that_old_v032_would_admit(tmp_path: Path):
    code, pilot, protocol = run_pilot(
        tmp_path,
        protocol_mapping(),
        [
            ["pilot-A", "A", 1],
            ["pilot-A", "A", 0],
            ["pilot-A", "B", 1],
            ["pilot-A", "B", 0],
            ["pilot-A", "C", 1],
            ["pilot-A", "C", ""],
        ],
    )

    assert code == 0
    assert pilot["status"] == "qualified_for_new_confirmatory_protocol"
    assert pilot["estimable_blocks"] == 2

    quality = audit_response_quality_attrition(
        protocol=protocol,
        contract=make_contract(protocol),
        pilot_result=pilot,
    )
    assert quality.status is ResponseQualityAuditStatus.STOP_ATTRITION
    assert quality.response_qualified_blocks == 2
    assert quality.minimum_response_qualified_blocks == 3
    assert quality.attrited_block_ids == ("C",)

    final = evaluate_future_admission_v0_42(
        protocol=protocol,
        pilot_result=pilot,
        quality_contract=make_contract(protocol),
    )
    assert final.status is FutureAdmissionStatus.STOP
    assert "v0_42:stop_response_quality_attrition" in final.reasons
    assert final.confirmatory_response_authorized is False


def test_endpoint_collapse_remains_distinct_from_response_attrition(tmp_path: Path):
    mapping = protocol_mapping(minimum_train_negative=2)
    code, pilot, protocol = run_pilot(
        tmp_path,
        mapping,
        [
            ["pilot-A", "A", 1],
            ["pilot-A", "A", 1],
            ["pilot-A", "B", 1],
            ["pilot-A", "B", 1],
            ["pilot-A", "C", 1],
            ["pilot-A", "C", 0],
        ],
    )

    assert code == 2
    assert pilot["status"] == "stop_endpoint_variation"

    quality = audit_response_quality_attrition(
        protocol=protocol,
        contract=make_contract(protocol),
        pilot_result=pilot,
    )
    assert quality.status is ResponseQualityAuditStatus.QUALIFIED
    assert quality.response_qualified_blocks == 3
    assert quality.attrited_block_ids == ()

    final = evaluate_future_admission_v0_42(
        protocol=protocol,
        pilot_result=pilot,
        quality_contract=make_contract(protocol),
    )
    assert final.status is FutureAdmissionStatus.STOP
    assert any(reason.startswith("v0_32:") for reason in final.reasons)
    assert not any("stop_response_quality_attrition" in reason for reason in final.reasons)


def test_clean_pilot_must_pass_both_existing_chain_and_quality_gate(tmp_path: Path):
    code, pilot, protocol = run_pilot(
        tmp_path,
        protocol_mapping(),
        [
            ["pilot-A", "A", 1],
            ["pilot-A", "A", 0],
            ["pilot-A", "B", 1],
            ["pilot-A", "B", 0],
            ["pilot-A", "C", 1],
            ["pilot-A", "C", 0],
        ],
    )

    assert code == 0
    final = evaluate_future_admission_v0_42(
        protocol=protocol,
        pilot_result=pilot,
        quality_contract=make_contract(protocol),
    )
    assert final.status is FutureAdmissionStatus.ADMITTED
    assert final.reasons == ()
    assert final.response_qualified_blocks == 3
    assert final.quality_retention_fraction == 1.0
    assert final.eligible_action == "freeze_confirmatory_protocol_only"
    assert final.confirmatory_response_authorized is False


def test_quality_contract_itself_must_be_frozen_before_pilot_access():
    protocol = protocol_from_mapping(protocol_mapping())
    contract = make_contract(protocol, pilot_response_accessed=True)
    decision = evaluate_response_quality_contract(protocol=protocol, contract=contract)

    assert decision.status is ResponseQualityContractStatus.STOP
    assert "pilot_response_already_accessed_before_quality_freeze" in decision.reasons


def test_quality_minimum_cannot_be_weaker_than_estimability_minimum():
    protocol = protocol_from_mapping(protocol_mapping(minimum_estimable_blocks=3))
    contract = make_contract(protocol, minimum_response_qualified_blocks=2)
    decision = evaluate_response_quality_contract(protocol=protocol, contract=contract)

    assert decision.status is ResponseQualityContractStatus.STOP
    assert "quality_block_minimum_below_estimable_block_minimum" in decision.reasons
