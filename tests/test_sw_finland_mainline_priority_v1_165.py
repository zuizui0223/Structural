from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
PRIORITY=ROOT/"development/structural_active_priority_v1_165.json"
REQUEST=ROOT/"development/sw_finland_header_audit_dispatch_request_v1_166.json"
DISPATCH=ROOT/".github/workflows/sw-finland-header-audit-dispatcher-v1_166.yml"

def test_priority_moves_to_non_ebird_independent_temporal_candidate():
    x=json.loads(PRIORITY.read_text())
    assert x["project_policy"]["ebird_enabled"] is False
    assert x["active_temporal_candidate"]["candidate_id"]=="sw_finland_archipelago_plants_1930s_1996_2017"
    assert "header audit" in x["next_scientific_event"].lower()
    assert any("do not reopen the boreal bird pilot" in v for v in x["do_not"])

def test_dispatch_request_is_header_only():
    x=json.loads(REQUEST.read_text())
    assert x["one_shot"] is True
    assert x["data_rows_semantically_opened_before_request"]==0
    assert x["outcome_values_read_before_request"]==0
    assert x["t0_projection_requested"] is False
    assert x["future_outcome_requested"] is False
    assert x["eBird_used"] is False

def test_dispatcher_targets_manual_header_workflow_only():
    s=DISPATCH.read_text()
    assert "sw-finland-header-audit-v1_166.yml/dispatches" in s
    assert '"ref":"main"' in s
    assert "actions: write" in s
