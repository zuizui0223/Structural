from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"manuscript/submission/GEB_v1_184"

def words(s):
    return len(re.sub(r"[#*_>\x60\[\]{}()]"," ",s).split())

def test_geb_v184_format():
    text=(DIR/"blinded_main_text.md").read_text()
    abstract=text[text.index("## Abstract"):text.index("## 1. Introduction")]
    main=text[text.index("## 1. Introduction"):text.index("## References")]
    assert words(abstract)<=300
    assert words(main)<=5000
    for h in ("Aim","Location","Time period","Major taxa studied","Methods","Results","Main conclusions"):
        assert f"**{h}:**" in abstract
    assert len(re.search(r"\*\*Running title:\*\* (.+)",text).group(1))<40

def test_topology_and_node_irreplaceability_are_separate_claims():
    q=json.loads((DIR/"submission_qa_v1_184.json").read_text())
    assert "supported prospectively" in q["evidence_separation"]["network_level_topology_specificity"]
    assert "not supported" in q["evidence_separation"]["source_node_spatial_irreplaceability"]
    assert q["claim_boundary"]["source_node_management_ranking"] is False
    assert q["claim_boundary"]["demographic_redundancy"] is False

def test_old_complementarity_overclaim_removed():
    text=(DIR/"blinded_main_text.md").read_text()
    assert "Observed source configurations were also more complementary than matched random placements" not in text
    assert "Aggregate balance is not spatial complementarity" in text
    assert "actual−null beta = **−0.2620**" in text

def test_source_turnover_is_response_free_mechanism_not_confirmatory_endpoint():
    text=(DIR/"blinded_main_text.md").read_text()
    assert "No held-out occurrence value was read" in text
    assert "post-hoc response-free mechanism" in text
