from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"development/boreal_19island_bird_pilot_preaccess_retry_contract_v1_164_1.json"
REQUEST=ROOT/"development/boreal_19island_bird_pilot_execution_request_v1_164_1.json"
WORKFLOW=ROOT/".github/workflows/boreal-19island-bird-pilot-v1_164_1.yml"

def test_retry_is_strictly_preaccess_and_science_unchanged():
    c=json.loads(CONTRACT.read_text())
    assert c["prior_failure"]["workflow_run_id"]==37394192161
    assert c["prior_failure"]["bird_response_transport_started"] is False
    assert c["prior_failure"]["bird_pilot_occurrence_values_decoded"]==0
    assert c["prior_failure"]["authorization_consumed"] is False
    assert c["retry_change"]["scientific_protocol_changed"] is False
    assert c["retry_change"]["topology_nulls_changed"] is False
    assert c["retry_change"]["pilot_gate_changed"] is False

def test_retry_request_keeps_response_closed():
    r=json.loads(REQUEST.read_text())
    assert r["one_shot"] is True
    assert r["prior_failure_before_response_transport"] is True
    assert r["bird_pilot_values_opened_before_retry"] is False
    assert r["bird_confirmatory_values_opened_before_retry"] is False
    assert r["effect_estimate_requested"] is False
    assert r["eBird_used"] is False

def test_workflow_repairs_only_pythonpath_and_preserves_firewall():
    s=WORKFLOW.read_text()
    assert 'PYTHONPATH: ${{ github.workspace }}:${{ github.workspace }}/src' in s
    assert "boreal_19island_bird_pilot_execution_request_v1_164_1.json" in s
    assert "fetch_boreal_19island_bird_response_v1_164.py" in s
    assert "run_boreal_19island_bird_pilot_v1_164.py" in s
    assert 'assert e["confirmatory_target_values_parsed"]==0' in s
    assert 'assert e["excluded_target_values_parsed"]==0' in s
    assert "preaccess_retry_of_run_id" in s
