from pathlib import Path
import ast,json

ROOT=Path(__file__).resolve().parents[1]

def test_contract_forbids_occurrence_semantics():
    x=json.loads((ROOT/"development/bala_event_core_audit_contract_v1_128.json").read_text())
    assert x["source"]["dataset_doi"]=="10.15468/rpdkx9"
    assert x["source"]["expected_event_records_reported"]==10379
    assert x["source"]["expected_occurrence_records_reported"]==63904
    assert "decode Occurrence extension text" in x["forbidden_before_occurrence_access"]
    assert x["response_boundary"]["occurrence_extension_semantically_opened"] is False
    assert x["response_boundary"]["taxon_occurrence_values_opened"]==0

def test_phase_fallback_is_frozen_from_event_dates_not_prose():
    x=json.loads((ROOT/"development/bala_event_core_audit_contract_v1_128.json").read_text())
    p=x["phase_audit"]["date_cluster_fallback"]
    assert p["allowed_only_if_explicit_labels_do_not_cover_all_core_rows"] is True
    assert p["cluster_rule"].startswith("sort distinct observed years")
    assert p["no_prose_calendar_boundary_use"] is True

def test_site_key_is_not_selected_before_audit():
    x=json.loads((ROOT/"development/bala_event_core_audit_contract_v1_128.json").read_text())
    assert x["site_key_audit"]["do_not_select_final_site_key_in_v1_128"] is True
    assert x["core_panel_gate_for_next_version"]["minimum_three_phase_sites"]==20
    assert x["core_panel_gate_for_next_version"]["minimum_three_phase_islands"]==5

def test_script_never_decodes_occurrence_member():
    s=(ROOT/"scripts/audit_bala_event_core_v1_128.py").read_text()
    tree=ast.parse(s)
    # Only Event core is passed to parse_event_core.
    assert "parse_event_core(event_bytes,core)" in s
    assert "occurrence_extension_semantically_opened" in s
    assert '"taxon_occurrence_values_opened":0' in s
    assert "occurrence_location" in s

def test_workflow_uploads_only_safe_audit_outputs():
    s=(ROOT/".github/workflows/bala-event-core-audit-v1_128.yml").read_text()
    assert "event_core_audit.json" in s
    assert "site_key_candidates.csv" in s
    assert "occurrence.txt" not in s
    assert "event_by_taxon_rows_parsed" in s
    assert "taxon_occurrence_values_opened" in s
