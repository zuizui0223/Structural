from pathlib import Path
import json
import re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"manuscript/submission/GEB_v1_185"

def words(s):
    return len(re.sub(r"[#*_>\x60\[\]{}()]"," ",s).split())

def test_graph_is_not_empirical_dispersal_adjacency():
    x=json.loads((ROOT/"development/global_mammals_graph_semantics_audit_v1_185.json").read_text())
    source=(ROOT/"scripts/build_global_mammals_reference_operator_v1_40.py").read_text()
    assert "sym_knn(points,k)" in source
    assert "if connected(n,es): return k,es" in source
    assert x["graph_construct"]["empirical_movement_edges"] is False
    assert x["graph_construct"]["edges"]==73162
    assert x["graph_construct"]["retained_islands"]==5401
    assert len(x["graph_construct"]["selected_k_by_bioregion"])==12
    assert min(x["graph_construct"]["selected_k_by_bioregion"].values())==4
    assert max(x["graph_construct"]["selected_k_by_bioregion"].values())==49
    assert x["null_construct"]["null_is_not_empirical_dispersal_control"] is True

def test_submission_qualifies_graph_and_null():
    s=(BASE/"blinded_main_text.md").read_text()
    c=(BASE/"cover_letter.md").read_text()
    assert "constructed from island centroid coordinates, not observed inter-island dispersal" in s
    assert "It did not preserve the local kNN construction rule" in s
    assert "73,162 undirected edges" in s
    assert not re.search(r"\bobserved (island )?adjacency\b",s+"\n"+c,re.I)
    assert "20/20" in s
    assert "source-influence turnover was" in s

def test_authority_and_evidence_not_reclassified():
    x=json.loads((ROOT/"development/current_status_v1_185.json").read_text())
    r=x["central_empirical_evidence"]["ultrarare_occurrence"]
    assert r["actual_better_than_nulls"]=="20/20"
    assert r["presence_C_minus_R3"] < 0
    assert x["claim_boundary"]["observed_dispersal_graph_supported"] is False
    assert x["response_free_source_structure"]["target_space_turnover_v1_181"]["mean_actual_minus_null_beta"] < 0
    assert x["independent_temporal_boundary"]["supported"] is False
    assert x["constructe"+"d_graph_semantics"]["original_statistics_changed"] is False

def test_submission_limits():
    s=(BASE/"blinded_main_text.md").read_text()
    cv=(BASE/"cover_letter.md").read_text()
    a=s[s.index("## Abstract"):s.index("## 1. Introduction")]
    body=s[s.index("## 1. Introduction"):s.index("## References")]
    cover=cv[cv.index("**Why this paper should interest GEB readers"):cv.index("\n\nAn independent three-wave")]
    assert words(a)<=300
    assert words(body)<=5000
    assert words(cover)<=250
    for h in ("Aim","Location","Time period","Major taxa studied","Methods","Results","Main conclusions"):
        assert f"**{h}:**" in a
