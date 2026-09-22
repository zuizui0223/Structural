from __future__ import annotations

from structural.confirmatory_freeze_gate import (
    ConfirmatoryFreezeStatus,
    evaluate_confirmatory_freeze_gate,
)


def clean_result():
    return {
        "status":"qualified_for_new_confirmatory_protocol",
        "protocol_fingerprint":"a"*64,
        "effect_size":None,
        "prediction_score":None,
        "predictive_denominator_contribution":0,
        "confirmatory_partition_opened":False,
        "confirmatory_response_row_count_seen":0,
    }


def test_clean_pilot_pass_allows_only_protocol_freeze_gate():
    result=evaluate_confirmatory_freeze_gate(
        expected_protocol_fingerprint="a"*64,
        pilot_result=clean_result(),
        confirmatory_response_accessed=False,
    )
    assert result.status is ConfirmatoryFreezeStatus.ELIGIBLE
    assert result.reasons == ()


def test_failed_pilot_stops():
    p=clean_result(); p["status"]="stop_endpoint_variation"
    result=evaluate_confirmatory_freeze_gate(
        expected_protocol_fingerprint="a"*64,pilot_result=p,
        confirmatory_response_accessed=False,
    )
    assert result.status is ConfirmatoryFreezeStatus.STOP
    assert "pilot_did_not_qualify" in result.reasons


def test_fingerprint_mismatch_stops():
    result=evaluate_confirmatory_freeze_gate(
        expected_protocol_fingerprint="b"*64,pilot_result=clean_result(),
        confirmatory_response_accessed=False,
    )
    assert "pilot_protocol_fingerprint_mismatch" in result.reasons


def test_predictive_pilot_output_stops():
    p=clean_result(); p["prediction_score"]=0.2
    result=evaluate_confirmatory_freeze_gate(
        expected_protocol_fingerprint="a"*64,pilot_result=p,
        confirmatory_response_accessed=False,
    )
    assert "pilot_prediction_score_present" in result.reasons


def test_confirmatory_exposure_stops():
    p=clean_result(); p["confirmatory_response_row_count_seen"]=1
    result=evaluate_confirmatory_freeze_gate(
        expected_protocol_fingerprint="a"*64,pilot_result=p,
        confirmatory_response_accessed=False,
    )
    assert result.status is ConfirmatoryFreezeStatus.STOP
    assert "confirmatory_response_rows_seen" in result.reasons
