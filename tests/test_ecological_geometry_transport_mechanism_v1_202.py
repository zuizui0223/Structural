import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/ecological_geometry_transport_mechanism_preintake_v1_202.json"

def test_published_outcome_exposure_and_nonadmission():
    x=json.loads(P.read_text())
    assert x["status"]=="METADATA_AND_PUBLISHED_LITERATURE_ONLY_NONCONFIRMATORY"
    for c in x["published_comparators"]:
        assert "RETROSPECTIVE" in c["category"]
    k=[v for v in x["published_comparators"] if v["id"]=="southern_california_giant_kelp_lter"][0]
    assert k["version_provenance"]["exact_reproducible_version_not_yet_resolved"] is True
    assert k["observed_movement_links"] is False
    assert k["admission_now"] is False
    assert x["mechanism_comparison"]["may_create_confirmatory_protocol_now"] is False

def test_separate_true_transition_endpoints_and_lagged_sources():
    x=json.loads(P.read_text())
    o=x["mechanism_comparison"]["outcome_separation"]
    assert o["colonization"] != o["local_extinction"]
    assert "t+1" in o["colonization"] and "t+1" in o["local_extinction"]
    a=x["mechanism_comparison"]["pre_outcome_reference_ladder"]
    assert any("physical transport" in z for z in a)
    assert any("fecundity" in z for z in a)
    assert any("joint interaction" in z for z in a)

def test_no_outcome_or_old_lineage_reopening():
    x=json.loads(P.read_text())
    g=x["safeguards"]
    for key in ("no_response_cells_opened","no_prediction_binary_opened",
                "no_new_test_statistic","original_mammal_results_unchanged",
                "no_mammal_map_refit","no_ala_replay","no_hebert_transport_retries",
                "no_bala_rescue","no_sw_finland_rescue","no_ebird","submission_hold"):
        assert g[key] is True
    assert g["active_confirmatory_systems"]==0
    assert x["mechanism_comparison"]["selection_decision"].endswith("_ONLY")
