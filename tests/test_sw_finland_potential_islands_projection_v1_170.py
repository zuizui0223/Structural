from pathlib import Path
import importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/project_sw_finland_potential_islands_v1_170.py"
CONTRACT=ROOT/"development/sw_finland_potential_islands_projection_contract_v1_170.json"

def load():
    spec=importlib.util.spec_from_file_location("swf170",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def contract(n=4):
    c=json.loads(CONTRACT.read_text());c=dict(c)
    c["validation"]=dict(c["validation"])
    c["validation"]["expected_unique_species"]=n
    c["validation"]["sentinels"]={}
    return c

def test_extract_retains_only_t0_species_and_potential_islands():
    m=load()
    txt="""species Potential_islands Num_colonized Prop_colonized Random_effect
Acer platanoides                         464  17  0.036637931 NA
Alchemilla filicaulis ssp. filicaulis  455   0  0 NA
Allium schoenoprasum                      56  35  0.625 1.245173729
Anchusa arvensis                         471   0  0 NA
Island_name Euref_X Euref_Y Potential_spp Num_colonizing Prop_colonizing Random_effect
"""
    rows=m.extract(txt,contract())
    assert [(r["species"],r["Potential_islands"]) for r in rows]==[
      ("Acer platanoides",464),
      ("Alchemilla filicaulis ssp. filicaulis",455),
      ("Allium schoenoprasum",56),
      ("Anchusa arvensis",471),
    ]
    assert rows[0]["historical_source_count"]==7
    assert rows[-1]["historical_source_count"]==0
    assert all(set(r)=={"species","Potential_islands","historical_source_count"} for r in rows)

def test_future_summary_values_are_not_returned_or_persistable():
    x=json.loads(CONTRACT.read_text())
    f=x["forbidden_future_summary_semantics"]
    assert f["may_be_persisted"] is False
    assert f["may_define_eligibility"] is False
    assert f["may_be_returned_in_receipt"] is False

def test_wrong_species_count_stops():
    m=load()
    txt="""species Potential_islands Num_colonized Prop_colonized Random_effect
A 470 1 0.1 NA
Island_name Euref_X Euref_Y Potential_spp Num_colonizing Prop_colonizing Random_effect
"""
    try:m.extract(txt,contract(2))
    except m.Stop:pass
    else:raise AssertionError("incomplete supplement extraction must stop")
