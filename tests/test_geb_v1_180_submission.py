from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"manuscript/submission/GEB_v1_180"

def words(s):
    return len(re.sub(r"[#*_>\x60\[\]{}()]"," ",s).split())

def test_format_and_role_inversion_sequence():
    text=(DIR/"blinded_main_text.md").read_text()
    abstract=text[text.index("## Abstract"):text.index("## 1. Introduction")]
    main=text[text.index("## 1. Introduction"):text.index("## References")]
    assert words(abstract)<=300
    assert words(main)<=5000
    for h in ("Aim","Location","Time period","Major taxa studied","Methods","Results","Main conclusions"):
        assert f"**{h}:**" in abstract
    assert "failed that constraint-signature prediction in the opposite direction" in abstract
    assert "Connectivity changes role, not only strength" in text
    assert "Scarcity explains topology exposure, but not the role inversion" in text

def test_claim_boundaries():
    q=json.loads((DIR/"submission_qa_v1_180.json").read_text())
    b=q["claim_boundary"]
    assert b["formal_monotonic_gradient"] is False
    assert b["cross_layer_trend_pvalue"] is False
    assert b["causal_role_switch"] is False
    assert b["coefficient_magnitudes_as_effect_sizes"] is False
    assert b["realized_dispersal"] is False
    assert b["rescue"] is False

def test_sw_finland_not_smuggled_into_biological_story():
    text=(DIR/"blinded_main_text.md").read_text().lower()
    assert "sw finland" not in text
    q=json.loads((DIR/"submission_qa_v1_180.json").read_text())
    assert q["provenance"]["sw_finland_in_manuscript"] is False
