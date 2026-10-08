from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"scripts/audit_external_mammal_checklist_headers_v1_188.py"
CON=ROOT/"development/global_mammals_independent_checklist_preintake_v1_188.json"
def load():
    spec=importlib.util.spec_from_file_location("mcheck188",SRC)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def test_body_row_binary_suffix_remains_opaque():
    m=load()
    assert m.first_field_only(b'"Island, North",1,0,1\n')=="Island, North"
    assert m.first_field_only(b'"I ""alpha""",0,1\n')=='I "alpha"'
    assert m.first_field_only(b'South,0,1,0\r\n')=="South"

def test_schema_only_extracts_names_and_headers_not_binary():
    m=load()
    names,taxa=m.schema_only(b',Mammalia spec A,Mammalia spec B\nIsland 1,1,0\nIsland 2,0,1\n',"x.csv")
    assert names==["Island 1","Island 2"]
    assert taxa==["Mammalia spec A","Mammalia spec B"]

def test_predeclared_island_taxon_and_source_gate():
    c=json.loads(CON.read_text())
    assert len(c["files"])==9
    assert c["preoutcome_thresholds"]["min_exact_focal_species_header_overlap"]==20
    assert c["preoutcome_thresholds"]["min_archipelagos_with_focal_species_headers"]==3
    assert c["allowed_preoutcome_access"]["source_island_species_binary_labels"] is False
    assert c["future_endpoint"]["label_access_now_authorized"] is False
    assert c["policy"]["eBird_used"] is False
