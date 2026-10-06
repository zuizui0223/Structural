from pathlib import Path
import importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/project_sw_finland_potential_islands_v1_170.py"
CONTRACT=ROOT/"development/sw_finland_potential_lookup_execution_contract_v1_170.json"

def load():
    spec=importlib.util.spec_from_file_location("swf170",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def fake_contract(n=3):
    c=json.loads(CONTRACT.read_text())
    c["allowed_projection"]["expected_unique_species"]=n
    c["anchor_checks"]={}
    return c

def test_layout_projection_discards_future_tail_before_parsing():
    m=load()
    text=(
      "species                         Potential_islands Num_colonized Prop_colonized Random_effect\n"
      "Acer platanoides                464               BAD FUTURE TOKENS\n"
      "Allium schoenoprasum             56               STILL FORBIDDEN\n"
      "Anchusa arvensis                471               0 0 NA\n"
      "Island_name Euref_X Euref_Y Potential_spp Num_colonizing Prop_colonizing Random_effect\n"
    )
    rows,r=m.project_text(text,fake_contract())
    assert dict(rows)=={"Acer platanoides":464,"Allium schoenoprasum":56,"Anchusa arvensis":471}
    assert r["future_summary_values_parsed"]==0
    assert r["future_summary_values_persisted"]==0

def test_wrapped_species_label_is_joined_only_from_safe_prefix():
    m=load()
    text=(
      "species                                      Potential_islands Num_colonized Prop_colonized Random_effect\n"
      "Alchemilla filicaulis ssp.\n"
      "filicaulis                                   455               0 0 NA\n"
      "Aster tripolium                              362               233 .64 X\n"
      "Agrostis stolonifera                          11               4 .36 X\n"
      "Island_name Euref_X Euref_Y Potential_spp Num_colonizing Prop_colonizing Random_effect\n"
    )
    rows,_=m.project_text(text,fake_contract())
    assert dict(rows)["Alchemilla filicaulis ssp. filicaulis"]==455

def test_execution_contract_forbids_future_summary_use():
    c=json.loads(CONTRACT.read_text())
    assert c["forbidden_semantics"]["values_may_be_persisted"] is False
    assert c["forbidden_semantics"]["values_may_define_eligibility"] is False
    assert c["response_boundary"]["row_level_recent_outcome_access_authorized"] is False
    assert c["response_boundary"]["eBird_enabled"] is False
