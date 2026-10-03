from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_106"

def test_abstract_limits_claim_to_tested_occupancy_regimes():
    s=(GEB/"blinded_main_text.md").read_text()
    abstract=s.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    assert "not uniformly informative across the occupancy regimes tested" in abstract
    assert "not a general mammalian isolation axis" not in abstract

def test_discussion_does_not_generalize_original_layer_across_all_mammals():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "cannot be generalized across mammal occupancy regimes" in s
    assert "cannot be generalized as a universal mammalian source-topology effect" not in s

def test_nonreplication_and_figure_order_are_unchanged():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "−0.000442" in s
    assert "−0.001098 to +0.000204" in s
    assert "+0.000430" in s
    assert "−0.27744" in s
    first={k:s.index(k) for k in ("Figure 1","Figure 2","Figure 3","Figure 4")}
    assert first["Figure 1"] < first["Figure 2"] < first["Figure 3"] < first["Figure 4"]

def test_manifest_records_wording_only_finalization():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    assert x["status"]=="GEB_SUBMISSION_PACKAGE_WORDING_FINALIZED"
    assert "occupancy regimes tested" in x["wording_guardrail"]
    assert x["new_scientific_analysis_authorized"] is False
    assert x["same_data_rescue_authorized"] is False
