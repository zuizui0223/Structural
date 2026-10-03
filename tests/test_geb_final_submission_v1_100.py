from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_97"

def test_final_manifest_records_nonreplication_and_assets():
    x=json.loads((GEB/"submission_manifest_v1_100.json").read_text())
    s=x["scientific_result"]["sealed_species_layer"]
    assert s["species"]==96
    assert s["P1_supported"] is False
    assert s["actual_graph_better_than_nulls"]=="11/20"
    assert x["anonymous_review_SI"]["artifact_id"]==11269048949
    assert x["anonymous_review_SI"]["inner_zip_sha256"]=="dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d"
    assert x["anonymous_review_SI"]["direct_identifier_hits"]==0
    assert x["figures"]["figure_4"]["artifact_id"]==11269267611
    assert x["new_scientific_analysis_authorized"] is False
    assert x["same_data_rescue_authorized"] is False

def test_final_checklist_marks_generated_assets_done():
    s=(GEB/"submission_checklist.md").read_text()
    assert "[x] Figure 4" in s
    assert "Anonymous review SI updated with sealed-species result" in s
    assert "dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d" in s
    assert "Final neutralized SI bundle passed identifier scan" in s

def test_readiness_says_no_more_same_data_science():
    s=(GEB/"final_readiness_v1_100.md").read_text()
    assert "No additional same-data rescue analysis is authorized." in s
    assert "396,096 held-out values were still unread" in s
    assert "No scientific analysis is needed before submission." in s

def test_anonymity_test_is_behavior_based_not_regex_literal_brittle():
    s=(ROOT/"tests/test_geb_anonymous_bundle_v1_99.py").read_text()
    assert "from review_dependencies import" in s
    assert "import review_dependencies" in s
    assert "r\"from scripts\\\\.[A-Za-z0-9_]+ import\"" not in s
