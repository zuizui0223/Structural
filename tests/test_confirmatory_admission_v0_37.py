from __future__ import annotations

from copy import deepcopy

from structural.confirmatory_admission import (
    ConfirmatoryAdmissionStatus,
    evaluate_confirmatory_admission,
)
from structural.transition_pilot_protocol import (
    evaluate_transition_pilot_protocol,
    protocol_from_mapping,
)


def protocol():
    return protocol_from_mapping(
        {
            "protocol_id": "future-v37",
            "system_id": "system-v37",
            "partition_axis": "time_window",
            "pilot_partition": ["pilot"],
            "confirmatory_partition": ["confirm"],
            "endpoint_id": "binary_transition",
            "endpoint_semantics": "1=event; 0=no event; else non-estimable",
            "heldout_design_id": "leave-one-block-out",
            "minimum_test_rows": 3,
            "minimum_train_positive": 5,
            "minimum_train_negative": 5,
            "minimum_estimable_blocks": 3,
            "pilot_response_accessed": False,
            "confirmatory_response_accessed": False,
            "pilot_used_for_effect_estimation": False,
        }
    )


def clean_result(p):
    fp = evaluate_transition_pilot_protocol(p).protocol_fingerprint
    block = lambda name: {
        "block": name,
        "test_rows": 6,
        "test_positive": 3,
        "test_negative": 3,
        "train_rows": 12,
        "train_positive": 6,
        "train_negative": 6,
        "estimable": True,
        "reasons": [],
    }
    return {
        "schema": "structural.transition_pilot_result.v0_32",
        "status": "qualified_for_new_confirmatory_protocol",
        "protocol_fingerprint": fp,
        "pilot_partition": ["pilot"],
        "confirmatory_partition_opened": False,
        "confirmatory_response_row_count_seen": 0,
        "pilot_consumed": True,
        "applicable_rows": 18,
        "positive": 9,
        "negative": 9,
        "non_estimable": 0,
        "total_blocks": 3,
        "estimable_blocks": 3,
        "minimum_estimable_blocks": 3,
        "block_audits": [block("A"), block("B"), block("C")],
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
    }


def test_clean_counts_recompute_to_admission():
    p = protocol()
    decision = evaluate_confirmatory_admission(protocol=p, pilot_result=clean_result(p))
    assert decision.status is ConfirmatoryAdmissionStatus.ADMITTED


def test_forged_estimable_true_cannot_override_frozen_class_gate():
    p = protocol()
    result = clean_result(p)
    forged = result["block_audits"][0]
    forged["train_positive"] = 4
    forged["train_negative"] = 8
    forged["estimable"] = True
    forged["reasons"] = []

    decision = evaluate_confirmatory_admission(protocol=p, pilot_result=result)

    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert "v0_32:block_0_estimability_inconsistent" in decision.reasons
    assert "v0_32:block_0_reasons_inconsistent" in decision.reasons


def test_reported_estimable_count_cannot_hide_recomputed_failure():
    p = protocol()
    result = clean_result(p)
    for block in result["block_audits"]:
        block["train_positive"] = 4
        block["train_negative"] = 8
        block["estimable"] = False
        block["reasons"] = ["training_positive_count_below_minimum"]
    result["estimable_blocks"] = 3

    decision = evaluate_confirmatory_admission(protocol=p, pilot_result=result)

    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert "v0_32:estimable_block_count_inconsistent" in decision.reasons
    assert "v0_32:recomputed_estimable_blocks_below_frozen_gate" in decision.reasons


def test_global_class_counts_must_match_block_partition():
    p = protocol()
    result = clean_result(p)
    result["positive"] = 10

    decision = evaluate_confirmatory_admission(protocol=p, pilot_result=result)

    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert "v0_32:applicable_class_counts_inconsistent" in decision.reasons
    assert "v0_32:test_positive_do_not_partition_positive" in decision.reasons


def test_training_counts_must_equal_heldout_complement():
    p = protocol()
    result = clean_result(p)
    result["block_audits"][1]["train_rows"] = 11

    decision = evaluate_confirmatory_admission(protocol=p, pilot_result=result)

    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert "v0_32:block_1_train_class_counts_inconsistent" in decision.reasons
    assert "v0_32:block_1_train_rows_not_heldout_complement" in decision.reasons


def test_duplicate_block_labels_stop_even_when_counts_look_valid():
    p = protocol()
    result = clean_result(p)
    result["block_audits"][2]["block"] = "A"

    decision = evaluate_confirmatory_admission(protocol=p, pilot_result=result)

    assert decision.status is ConfirmatoryAdmissionStatus.STOP
    assert "v0_32:block_2_duplicate_name" in decision.reasons
