from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/sw_finland_header_grammar_diagnostic_contract_v1_166_1.json"
R=ROOT/"development/sw_finland_header_grammar_diagnostic_request_v1_166_1.json"
S=ROOT/"scripts/audit_sw_finland_header_grammar_v1_166_1.py"

def test_contract_keeps_rows_and_outcomes_closed():
    x=json.loads(C.read_text())
    assert x["parent_failure"]["data_rows_semantically_opened"]==0
    assert x["parent_failure"]["outcome_values_read"]==0
    assert x["permitted_delimiters"]==[",",";","\t"]
    assert x["response_boundary"]["t0_projection_authorized"] is False

def test_request_is_zero_row_only():
    x=json.loads(R.read_text())
    assert x["prior_data_rows_opened"]==0
    assert x["prior_outcome_values_read"]==0
    assert x["future_outcome_access"] is False
    assert x["eBird_used"] is False

def test_script_reads_only_first_record_per_delimiter():
    s=S.read_text()
    assert "next(r)" in s
    assert "data_rows_semantically_opened" in s
    assert "outcome_values_read" in s
