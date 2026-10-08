from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
P=R/"manuscript/working/GEB_v1_217/blinded_main_text.md"
L=R/"manuscript/working/GEB_v1_217/claim_audit_v1_217.json"

def test_actual_mammal_label_ontology_and_gain_fraction():
    x=P.read_text()
    assert "IUCN-2017" in x
    assert "GADM" in x
    assert "90.18%" in x and "9.82%" in x
    assert "−0.59626" in x and "−0.53773" in x and "−0.05853" in x
    assert "20/20" in x
    assert "not an independent survey" in x
    assert "not causal mechanisms" in x

def test_historical_submission_not_promoted():
    c=json.loads((R/"manuscript/submission/GEB_CURRENT.json").read_text())
    z=json.loads(L.read_text())
    assert c["version"]=="v1.185" and c["submission_authorized"] is False
    assert z["GEB_CURRENT_untouched"] is True
    assert z["submission_authorized"] is False
    assert z["mathematical_effects_unchanged"] is True
    old=(R/"manuscript/submission/GEB_v1_185/blinded_main_text.md").read_text()
    assert P.read_text()!=old

def test_working_conclusions_constrain_graph_claim():
    s=P.read_text()
    assert "The constructed geographic network was predictive" in s
    assert "not evidence that rare island mammals disperse along a unique graph" in s
    import re
    w=len(re.sub(r"[#*_>\x60\[\]{}()]"," ",s[s.index("## 1. Introduction"):s.index("## References")]).split())
    assert w <= 5000
