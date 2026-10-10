import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("rare254",R/"scripts/camtrapasia_study_rarefaction_v1_254.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_hypergeometric_exact_finite_sample_formula():
    assert m.found_prob(4,0,2)==0
    assert m.found_prob(4,4,2)==1
    assert abs(m.found_prob(4,1,2)-.5)<1e-12
    assert abs(m.found_prob(4,2,2)-5/6)<1e-12
def test_original_provenance_and_no_causal_claims():
    c=json.loads((R/"development/camtrapasia_study_rarefaction_contract_v1_254.json").read_text())
    assert c["measure"]["primary_k_studies"]==18
    assert c["measure"]["secondary_k_studies_all_eras"]==25
    assert c["measure"]["quantiles_are_confidence_intervals"] is False
    assert c["measure"]["no_island_effect_p_value"] is True
    assert c["study_design"]["same_original_geographic_block"] is True
    assert all(x is False for x in c["guards"].values())
