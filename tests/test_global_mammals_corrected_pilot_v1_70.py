from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/run_global_mammals_corrected_macro_pilot_v1_70.py"
    spec=importlib.util.spec_from_file_location("mcpilot",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_corrected_parser_treats_header_as_species_only():
    m=load_module()
    raw=b'sp1;sp2\n1;0;1\n'
    rec=list(m.iter_records(raw))
    assert m.parse_record(rec[0])==["sp1","sp2"]
    assert m.canon_id(m.first_field(rec[1],59))=="1"
    assert m.parse_record(rec[1])==["1","0","1"]

def test_new_lineage_keeps_science_fixed():
    x=json.loads((ROOT/"development/global_mammals_corrected_macro_pilot_contract_v1_70.json").read_text())
    assert x["analysis_route"]=="separate_nonconfirmatory_exploratory_macro_lineage"
    assert x["response_identity"]["header_fields"]==5394
    assert x["response_identity"]["data_record_fields"]==5395
    assert x["species_universe"]["minimum_presence"]==13
    assert x["species_universe"]["minimum_absence"]==13
    assert x["scientific_method_lock"]["population_changed_from_v167"] is False
    assert x["scientific_method_lock"]["R0_R3_C_method_changed_from_v167"] is False
    assert x["evidence_boundary"]["fresh_status_restored"] is False

def test_confirmatory_occurrence_remains_closed():
    s=(ROOT/".github/workflows/global-mammals-corrected-pilot-v1_71.yml").read_text()
    assert "confirmatory_occurrence_values_decoded" in s
    assert "confirmatory_response_authorized" in s
