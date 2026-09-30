from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/run_global_mammals_macro_pilot_response_v1_65.py"
    spec=importlib.util.spec_from_file_location("mm_pilot",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_record_scanner_keeps_nonpilot_remainder_opaque():
    m=load_module()
    raw=b'id;a;b\n1;0;1\n2;1;0\n'
    rec=list(m.iter_records(raw))
    assert len(rec)==3
    assert m.canon_id_bytes(m.first_field_bytes(rec[1],59))=="1"
    assert m.canon_id_bytes(m.first_field_bytes(rec[2],59))=="2"

def test_mammal_macro_pilot_contract_is_contaminated_not_fresh():
    x=json.loads((ROOT/"development/global_mammals_macro_pilot_response_contract_v1_65.json").read_text())
    assert x["analysis_route"]=="contaminated_macro_analysis_only"
    assert x["routing"]["pilot_islands"]==1275
    assert x["routing"]["confirmatory_islands"]==4126
    assert x["species_universe"]["minimum_presence"]==13
    assert x["species_universe"]["minimum_absence"]==13
    assert x["semantic_firewall"]["confirmatory_occurrence_rows_may_open"] is False
    assert x["evidence_boundary"]["fresh_status_restored"] is False

def test_one_shot_request_is_exact_and_confirmatory_sealed():
    s=(ROOT/".github/workflows/global-mammals-macro-pilot-response-v1_66.yml").read_text()
    assert "run_global_mammals_macro_pilot_response_v1_65.py" in s
    assert "confirmatory_occurrence_values_decoded" in s
    r=json.loads((ROOT/"development/global_mammals_macro_pilot_response_request_v1_66.json").read_text())
    assert r["status"]=="REQUEST_ONE_SHOT_CONTAMINATED_MACRO_MAMMAL_PILOT"
    assert r["routing_artifact_id"]==11060106528
    assert r["pilot_islands"]==1275
    assert r["confirmatory_islands"]==4126
    assert r["species_threshold_m"]==13
    assert r["macro_pilot_response_authorized"] is True
    assert r["confirmatory_response_authorized"] is False
    assert r["fresh_status_restored"] is False
    assert r["one_shot"] is True
