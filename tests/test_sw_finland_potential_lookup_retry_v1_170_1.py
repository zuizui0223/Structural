from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/sw_finland_potential_lookup_preaccess_retry_contract_v1_170_1.json"
R=ROOT/"development/sw_finland_potential_lookup_retry_request_v1_170_1.json"
W=ROOT/".github/workflows/sw-finland-potential-lookup-v1_170_1.yml"

def test_retry_is_strictly_preaccess_transport_only():
    c=json.loads(C.read_text())
    assert c["prior_run"]["supplement_pdf_bytes_downloaded"] is False
    assert c["prior_run"]["supplement_table_rows_parsed"]==0
    assert c["prior_run"]["future_summary_values_parsed"]==0
    assert c["prior_run"]["row_level_recent_outcome_opened"] is False
    assert c["scientific_protocol"]["source_table_changed"] is False
    assert c["scientific_protocol"]["allowed_projection_changed"] is False

def test_retry_uses_current_redirect_target_and_keeps_firewall():
    c=json.loads(C.read_text());w=W.read_text()
    assert c["transport"]["current_url"].startswith("https://nso-journals.org/")
    assert c["response_boundary"]["future_summary_values_persisted_before_retry"]==0
    assert c["response_boundary"]["eBird_enabled"] is False
    assert "project_sw_finland_potential_islands_v1_170.py" in w
    assert "validate_sw_finland_potential_islands_lookup_v1_168.py" in w
    assert "rm -rf build/swf_v1701/raw build/swf_v1701/safe" in w

def test_request_is_one_shot_and_no_future_response_requested():
    r=json.loads(R.read_text())
    assert r["one_shot"] is True
    assert r["future_summary_values_requested"] is False
    assert r["row_level_recent_outcome_access_requested"] is False
    assert r["effect_estimate_requested"] is False
