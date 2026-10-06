from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"development/sw_finland_header_acquisition_contract_v1_166.json"
WORKFLOW=ROOT/".github/workflows/sw-finland-header-audit-v1_166.yml"

def test_header_acquisition_is_manual_main_only_and_response_free():
    x=json.loads(CONTRACT.read_text())
    assert x["workflow"]["trigger"]=="workflow_dispatch_only"
    assert x["workflow"]["required_ref"]=="refs/heads/main"
    assert x["source"]["expected_md5"]=="ff648878946ba430fb86c4ab2aa02baa"
    assert x["response_boundary"]["outcome_values_read"]==0
    assert x["success_ceiling"].startswith("HEADER_ONLY")

def test_workflow_deletes_raw_before_upload_and_never_runs_t0_projection():
    s=WORKFLOW.read_text()
    assert "workflow_dispatch" in s
    assert 'test "$GITHUB_REF" = "refs/heads/main"' in s
    assert "audit_sw_finland_colonization_header_v1_163.py" in s
    assert "project_sw_finland_t0_state_v1_164.py" not in s
    assert "rm -rf build/swf_v1166/raw" in s
    assert "build/swf_v1166/audit/*.json" in s
    tail=s.split("Upload response-free header receipts only",1)[-1]
    assert "colonization_select.csv" not in tail
