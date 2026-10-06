from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/sw_finland_header_reaudit_contract_v1_166_2.json"
R=ROOT/"development/sw_finland_header_reaudit_request_v1_166_2.json"
S=ROOT/"scripts/audit_sw_finland_colonization_header_v1_166_2.py"

def test_reaudit_is_bound_to_committed_semicolon_grammar():
    c=json.loads(C.read_text())
    assert c["grammar"]["selected_delimiter"]==";"
    assert c["response_boundary"]["data_rows_semantically_opened"]==0
    assert c["response_boundary"]["outcome_values_read"]==0
    assert c["response_boundary"]["t0_row_projection_authorized_during_this_revision"] is False

def test_request_does_not_project_rows():
    r=json.loads(R.read_text())
    assert r["selected_delimiter"]==";"
    assert r["prior_data_rows_opened"]==0
    assert r["prior_outcome_values_read"]==0
    assert r["t0_row_projection_requested"] is False

def test_reauditor_reads_only_one_header_record():
    s=S.read_text()
    assert "next(rd)" in s
    assert 'delimiter=delim' in s
    assert '"schema":"structural.sw_finland_plant_colonization_header_audit.v1_163"' in s
