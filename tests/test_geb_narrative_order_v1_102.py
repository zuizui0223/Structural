from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_102"

def test_prospective_validation_precedes_posthoc_diagnostics():
    s=(GEB/"blinded_main_text.md").read_text()
    assert s.index("### 2.6 Prospective sealed rare-species layer") < s.index("### 2.7 Post-hoc nonrescuing attenuation diagnostics")
    assert s.index("### 3.2 A preregistered rarer-species layer does not replicate") < s.index("### 3.3 Exploratory attenuation")
    assert s.index("### 4.1 Prospective rare-species validation sets a boundary on generality") < s.index("### 4.2 What remains of the exploratory source-network signal")

def test_scientific_numbers_are_unchanged():
    s=(GEB/"blinded_main_text.md").read_text()
    for value in (
        "−0.001814","−0.002817 to −0.000997",
        "−0.000442","−0.001098 to +0.000204",
        "+0.000430","−0.27744","−0.00603",
        "+1.56 × 10⁻⁶","11 of 20"
    ):
        assert value in s

def test_title_and_abstract_keep_boundary_framing():
    s=(GEB/"blinded_main_text.md").read_text()
    assert s.startswith("# Island isolation is not one-dimensional: source-network information differs across species occupancy regimes")
    abstract=s.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    assert len(abstract.split()) <= 300
    assert "**Aim:**" in abstract and "**Innovation:**" in abstract and "**Main conclusions:**" in abstract
    assert "did not replicate the overall gain" in abstract
    assert "not a general mammalian isolation axis" in abstract

def test_manifest_records_reordering_not_new_science():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    assert x["status"]=="GEB_SUBMISSION_PACKAGE_NARRATIVE_ORDER_FINALIZED"
    assert x["scientific_result"]["sealed_species_layer"]["P1_supported"] is False
    assert x["scientific_result"]["sealed_species_layer"]["actual_graph_better_than_nulls"]=="11/20"
    assert x["narrative_order"]["results"].startswith("prospective sealed non-replication")
    assert x["new_scientific_analysis_authorized"] is False
    assert x["same_data_rescue_authorized"] is False

def test_manuscript_stays_blinded_and_under_word_target():
    s=(GEB/"blinded_main_text.md").read_text()
    assert len(s.split()) < 5000
    assert "zuizui0223" not in s
    assert "github.com" not in s.lower()
    assert "ZHANG Ruiqi" not in s
