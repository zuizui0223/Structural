from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/run_global_mammals_schema_corrected_pilot_v1_69.py"
    spec=importlib.util.spec_from_file_location("m",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_corrected_header_has_no_routing_field():
    x=json.loads((ROOT/"development/global_mammals_header_schema_correction_v1_69.json").read_text())
    assert x["corrected_physical_schema"]["header_fields"]==5394
    assert x["corrected_physical_schema"]["header_semantics"].startswith("all 5394")
    assert x["corrected_physical_schema"]["data_record_fields"]==5395
    assert x["corrected_physical_schema"]["first_species"]=="Cephalophus.adersi"
    assert x["what_does_not_change"]["species_count"]==5394
    assert x["what_does_not_change"]["species_threshold_m"]==13

def test_parser_semantics_match_irregular_csv():
    m=load_module()
    raw=b'sp1;sp2\n1;1;0\n2;0;1\n'
    rec=list(m.iter_records(raw))
    assert m.parse_full_record(rec[0])==["sp1","sp2"]
    assert m.canon_id_bytes(m.first_field_bytes(rec[1],59))=="1"
    assert m.parse_full_record(rec[1])==["1","1","0"]

def test_new_lineage_remains_nonfresh_and_same_science():
    c=json.loads((ROOT/"development/global_mammals_schema_corrected_pilot_contract_v1_69.json").read_text())
    assert c["analysis_route"]=="header_exposed_contaminated_macro_only"
    assert c["species_universe"]["minimum_presence"]==13
    assert c["scientific_method"]["model_or_feature_change_after_header_failure"] is False
    assert c["semantic_firewall"]["confirmatory_occurrence_rows_may_open"] is False
    assert c["evidence_boundary"]["fresh_status_restored"] is False

def test_request_is_one_shot():
    r=json.loads((ROOT/"development/global_mammals_schema_corrected_pilot_request_v1_70.json").read_text())
    assert r["header_audit_artifact_id"]==11111510286
    assert r["pilot_islands"]==1275
    assert r["confirmatory_islands"]==4126
    assert r["species_threshold_m"]==13
    assert r["pilot_occurrence_access_authorized"] is True
    assert r["confirmatory_occurrence_access_authorized"] is False
    assert r["one_shot"] is True
