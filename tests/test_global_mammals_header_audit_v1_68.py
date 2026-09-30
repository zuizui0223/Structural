from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v165_is_terminal_and_no_occurrence_was_opened():
    x=json.loads((ROOT/"development/global_mammals_macro_pilot_failure_freeze_v1_68.json").read_text())
    assert x["v165_consequence"]["rerun_authorized"] is False
    assert x["semantic_exposure"]["pilot_occurrence_values_decoded"]==0
    assert x["semantic_exposure"]["confirmatory_occurrence_values_decoded"]==0

def test_header_audit_is_only_permitted_next_semantic_step():
    x=json.loads((ROOT/"development/global_mammals_header_exposed_schema_contract_v1_68.json").read_text())
    assert x["semantic_ceiling"]["decode_exactly_one_logical_record"]=="header only"
    assert x["continuation_rule_if_clean"]["retain_species_threshold_m"]==13
    assert x["continuation_rule_if_clean"]["fresh_status_restored"] is False

def test_header_workflow_has_no_routing_or_occurrence_outputs():
    s=(ROOT/".github/workflows/global-mammals-header-audit-v1_68.yml").read_text()
    assert "audit_global_mammals_header_v1_68.py" in s
    assert "header_manifest.csv" in s
    assert "pilot_matrix.csv" not in s
    assert "confirmatory_matrix.csv" not in s
    assert "occurrence_data_row_access_authorized" in s

def test_header_script_does_not_iterate_data_records():
    s=(ROOT/"scripts/audit_global_mammals_header_v1_68.py").read_text()
    assert "first logical record" in s
    assert '"pilot_occurrence_values_decoded":0' in s
    assert '"confirmatory_occurrence_values_decoded":0' in s
