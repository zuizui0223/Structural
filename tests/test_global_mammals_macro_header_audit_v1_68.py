from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/audit_global_mammals_macro_header_v1_68.py"
    spec=importlib.util.spec_from_file_location("mh",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_header_logical_record_stops_before_data():
    m=load_module()
    raw=b'"id";"sp;1";sp2\n1;0;1\n'
    h=m.first_logical_record(raw)
    assert h==b'"id";"sp;1";sp2'

def test_contract_does_not_reopen_occurrences():
    x=json.loads((ROOT/"development/global_mammals_macro_header_audit_contract_v1_68.json").read_text())
    assert x["failure_parent"]["v1_65_rerun_authorized"] is False
    assert x["allowed_semantics"]["decode_header_record_only"] is True
    assert x["allowed_semantics"]["data_record_occurrence_values_decoded"]==0
    assert x["scientific_constraints"]["may_not_change_m13_species_selection_rule"] is True
    assert x["evidence_boundary"]["fresh_status_restored"] is False

def test_workflow_has_no_pilot_or_confirmatory_parser():
    s=(ROOT/".github/workflows/global-mammals-macro-header-audit-v1_68.yml").read_text()
    assert "run_global_mammals_macro_pilot_response_v1_65.py" not in s
    assert "audit_global_mammals_macro_header_v1_68.py" in s
    assert "data_record_occurrence_values_decoded" in s
