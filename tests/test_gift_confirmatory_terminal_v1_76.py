from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_gift_confirmatory_failure_is_terminal_after_access():
    x=json.loads((ROOT/"development/gift_confirmatory_terminal_freeze_v1_76.json").read_text())
    assert x["terminal_result"]["confirmatory_response_consumed"] is True
    assert x["terminal_result"]["confirmatory_list_requests_started"] is True
    assert x["terminal_result"]["primary_scored"] is False
    assert x["terminal_result"]["rerun_authorized"] is False
    assert x["terminal_result"]["fresh_system_denominator_contribution"]==0

def test_terminal_api_failure_is_not_relabelled_ecological_null():
    x=json.loads((ROOT/"development/gift_confirmatory_terminal_freeze_v1_76.json").read_text())
    s=x["scientific_interpretation"]
    assert s["C_minus_R3_direction_observed"] is False
    assert s["counts_as_support_or_non_support_for_internal_source_continuity"] is False
    assert s["endpoint_completeness_failure_is_not_an_ecological_null_result"] is True
    assert s["same_protocol_retry_authorized"] is False

def test_program_claims_remain_conservative():
    x=json.loads((ROOT/"development/gift_confirmatory_terminal_freeze_v1_76.json").read_text())
    p=x["program_consequence"]
    assert p["global_pristine_plant_fresh_confirmation_completed"] is False
    assert p["global_pristine_plant_fresh_denominator_contribution"]==0
    assert p["macro_paper_must_not_claim_two_successful_confirmatory_taxonomic_replications"] is True
