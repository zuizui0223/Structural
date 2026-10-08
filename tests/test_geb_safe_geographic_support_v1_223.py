import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/"manuscript/working/GEB_v1_217/blinded_main_text.md"
def test_geographic_support_is_restricted_to_safe_candidate_matching():
    m=P.read_text()
    assert "3,878 candidate island pairs" in m
    assert "21.3%" in m
    assert "do not prove mammal-zero islands or dispersal corridors" in m
    z=json.loads((R/"development/full_original_island_neighbour_geometry_freeze_v1_223.json").read_text())
    assert z["scientific_interpretation"]["actual_original_kNN_graph_node_missing_fraction_identified"] is False
    n=len(re.sub(r"[#*_>\x60\[\]{}()]"," ",m[m.index("## 1. Introduction"):m.index("## References")]).split())
    assert n<=5000
