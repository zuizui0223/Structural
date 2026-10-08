import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/wolfe_patch_configuration_identifiability_v1_213.json"

def gini(a):
    n=len(a)
    return sum(abs(x-y) for x in a for y in a)/(2*n*sum(a))

def test_total_area_and_heterogeneity_do_not_match_between_count_levels():
    x=json.loads(P.read_text())
    c=x["experiment"]["configurations"]
    assert all(sum(v["volumes_ml"])==48 for v in c)
    h={v["patch_count"]:v for v in c if v["heterogeneous"]}
    assert len(h[4]["volumes_ml"])==4 and len(h[6]["volumes_ml"])==6
    assert h[4]["larger_to_smaller_ratio"]==2
    assert h[6]["larger_to_smaller_ratio"]==3
    assert abs(gini(h[4]["volumes_ml"])-1/6)<1e-12
    assert abs(gini(h[6]["volumes_ml"])-1/4)<1e-12
    assert h[4]["cv_population"]!=h[6]["cv_population"]
    assert x["identified_and_unidentified"]["temporal_colonization_identified"] is False

def test_experimental_mechanism_not_promoted():
    x=json.loads(P.read_text())
    assert x["future_identification_plan"]["novel_experiment_hypothesis_only"] is True
    assert x["guards"]["original_GEB_submission_authorized"] is False
    assert x["guards"]["global_mammal_heldout_reopened"] is False
    assert x["guards"]["eBird_used"] is False
