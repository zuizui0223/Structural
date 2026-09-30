from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_species_metadata_audit_is_response_blind():
    x=json.loads((ROOT/"development/global_mammals_species_metadata_audit_contract_v1_69.json").read_text())
    assert x["source"]["dryad_file_id"]==3242160
    assert x["allowed_semantics"]["entire_species_metadata_file_may_be_parsed"] is True
    assert x["allowed_semantics"]["species_occurrence_matrix_access"] is False
    assert x["allowed_semantics"]["species_column_selection_in_this_revision"] is False
    assert x["response_boundary"]["Appendix1_access_authorized"] is False

def test_species_metadata_workflow_never_accesses_appendix1():
    s=(ROOT/".github/workflows/global-mammals-species-metadata-audit-v1_69.yml").read_text()
    assert "3242160" in s
    assert "Appendix_1_presence_absence" not in s
    assert "run_global_mammals_macro_pilot_response" not in s
