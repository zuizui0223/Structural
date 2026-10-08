import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"development/global_mammals_unpaired_geography_frame_freeze_v1_220.json"
def test_frozen_two_frame_descriptives_and_rejected_crosswalk():
    e=json.loads(E.read_text())
    a=e["two_unpaired_island_distributions"]
    assert a["Weigelt_2013"]["count"]==17883
    assert a["Structural_2026_selected"]["count"]==5401
    assert a["Weigelt_2013"]["median"]==4.08
    assert a["Structural_2026_selected"]["median"]==6.4
    assert abs(e["median_ratio"]-6.4/4.08)<1e-12
    assert e["original_join_protocol"]["verified_geographic_matches"]==0
    assert e["original_join_protocol"]["exact_numeric_ID_equalities"]==796
    assert e["scientific_claim_ceiling"]["selection_effect_on_original_529_species_C_minus_R3_identified"] is False
def test_working_manuscript_shows_nonpaired_geography_only():
    m=(ROOT/"manuscript/working/GEB_v1_217/blinded_main_text.md").read_text()
    assert "separate unpaired geography-frame comparison" in m
    assert "6.40 km²" in m and "4.08 km²" in m
    assert "Numeric IDs differed" in m
    assert "3,878 candidate island pairs" in m
    assert "do not prove mammal-zero islands" in m
    # v1.220 original numeric-ID STOP remains true; v1.221 was a separate geo-only crosswalk
    assert "10.1073/pnas.1306309110" in m
    n=len(re.sub(r"[#*_>\x60\[\]{}()]"," ",m[m.index("## 1. Introduction"):m.index("## References")]).split())
    assert n<=5000
    c=json.loads((ROOT/"manuscript/submission/GEB_CURRENT.json").read_text())
    assert c["submission_authorized"] is False and c["version"]=="v1.185"
