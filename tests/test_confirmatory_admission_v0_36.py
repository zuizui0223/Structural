from __future__ import annotations

from structural.confirmatory_admission import (
    ConfirmatoryAdmissionStatus,
    admission_receipt_mapping,
    evaluate_confirmatory_admission,
)
from structural.transition_pilot_protocol import (
    evaluate_transition_pilot_protocol,
    protocol_from_mapping,
)


def protocol_mapping(**changes):
    data = {
        "protocol_id": "future-v1",
        "system_id": "system-x",
        "partition_axis": "time_window",
        "pilot_partition": ["2010-2011"],
        "confirmatory_partition": ["2014-2015"],
        "endpoint_id": "annual_site_use",
        "endpoint_semantics": "1=detected; 0=surveyed non-detection; else non-estimable",
        "heldout_design_id": "leave-one-spatial-block-out",
        "minimum_test_rows": 3,
        "minimum_train_positive": 5,
        "minimum_train_negative": 5,
        "minimum_estimable_blocks": 3,
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
        "pilot_used_for_effect_estimation": False,
    }
    data.update(changes)
    return data


def clean_result(protocol):
    pre = evaluate_transition_pilot_protocol(protocol)
    audits = [
        {"block": "a", "estimable": True},
        {"block": "b", "estimable": True},
        {"block": "c", "estimable": True},
    ]
    return {
        "schema": "structural.transition_pilot_result.v0_32",
        "status": "qualified_for_new_confirmatory_protocol",
        "protocol_fingerprint": pre.protocol_fingerprint,
        "pilot_partition": list(protocol.pilot_partition),
        "confirmatory_partition_opened": False,
        "confirmatory_response_row_count_seen": 0,
        "pilot_consumed": True,
        "total_blocks": 3,
        "estimable_blocks": 3,
        "minimum_estimable_blocks": 3,
        "block_audits": audits,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
    }


def test_clean_chain_enters_queue_but_never_authorizes_response():
    protocol = protocol_from_mapping(protocol_mapping())
    decision = evaluate_confirmatory_admission(
        protocol=protocol,
        pilot_result=clean_result(protocol),
    )
    assert decision.status is ConfirmatoryAdmissionStatus.ADMITTED
    assert decision.reasons == ()
    assert decision.eligible_action == "freeze_confirmatory_protocol_only"
    assert decision.confirmatory_response_authorized is False
    receipt = admission_receipt_mapping(decision)
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["predictive_denominator_contribution"] == 0
    assert receipt["ttf_handoff_authorized"] is False


def test_v0_31_failure_cannot_be_rescued_by_clean_looking_pilot():
    protocol = protocol_from_mapping(
        protocol_mapping(confirmatory_response_accessed=True)
    )
    decision = evaluate_confirmatory_admission(
        protocol=protocol,
        pilot_result=clean_result(protocol),
    )
    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert any(reason.startswith("v0_31:") for reason in decision.reasons)


def test_fingerprint_mismatch_stops():
    protocol = protocol_from_mapping(protocol_mapping())
    result = clean_result(protocol)
    result["protocol_fingerprint"] = "b" * 64
    decision = evaluate_confirmatory_admission(protocol=protocol, pilot_result=result)
    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert "v0_33:pilot_protocol_fingerprint_mismatch" in decision.reasons


def test_predictive_denominator_must_be_exactly_zero():
    protocol = protocol_from_mapping(protocol_mapping())
    result = clean_result(protocol)
    result["predictive_denominator_contribution"] = None
    decision = evaluate_confirmatory_admission(protocol=protocol, pilot_result=result)
    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert "v0_32:pilot_predictive_denominator_not_exactly_zero" in decision.reasons


def test_block_accounting_is_recomputed():
    protocol = protocol_from_mapping(protocol_mapping())
    result = clean_result(protocol)
    result["estimable_blocks"] = 3
    result["block_audits"][2]["estimable"] = False
    decision = evaluate_confirmatory_admission(protocol=protocol, pilot_result=result)
    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert "v0_32:estimable_block_count_inconsistent" in decision.reasons


def test_confirmatory_exposure_stops_even_after_pilot_pass():
    protocol = protocol_from_mapping(protocol_mapping())
    result = clean_result(protocol)
    result["confirmatory_response_row_count_seen"] = 1
    decision = evaluate_confirmatory_admission(protocol=protocol, pilot_result=result)
    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert any("confirmatory_response" in reason for reason in decision.reasons)
