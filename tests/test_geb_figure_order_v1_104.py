from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_104"

def test_main_figure_citations_exist_and_are_first_cited_in_order():
    s=(GEB/"blinded_main_text.md").read_text()
    first={k:s.index(k) for k in ("Figure 1","Figure 2","Figure 3","Figure 4")}
    assert first["Figure 1"] < first["Figure 2"] < first["Figure 3"] < first["Figure 4"]
    assert "Supplementary Fig. S1" in s
    assert "Supplementary Fig. S2" in s

def test_figure_two_is_the_preregistered_sealed_validation():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "not geographically independent confirmation (Figure 2)" in s
    caps=(GEB/"figure_captions.md").read_text()
    assert "## Figure 2. A preregistered sealed rare-species layer does not replicate" in caps

def test_figure_three_and_four_match_posthoc_attenuation_order():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "external isolation increased (Figure 3)" in s
    assert "median effect near zero (−0.00014; Figure 4)" in s
    caps=(GEB/"figure_captions.md").read_text()
    assert "## Figure 3. External isolation attenuates" in caps
    assert "## Figure 4. Broadly distributed mammal species receive weaker graph-topology gains" in caps

def test_supplementary_plant_attrition_is_cited():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "endpoint attrition was severe (Supplementary Fig. S1)" in s

def test_manifest_figure_order_matches_text():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    assert x["status"]=="GEB_SUBMISSION_PACKAGE_FIGURE_ORDER_FINALIZED"
    assert x["figure_order"]["Figure 2"]=="preregistered sealed rare-species validation"
    assert x["figure_order"]["Figure 3"]=="external-isolation attenuation"
    assert x["figure_order"]["Figure 4"]=="species-breadth attenuation"
    assert x["new_scientific_analysis_authorized"] is False
    assert x["same_data_rescue_authorized"] is False
