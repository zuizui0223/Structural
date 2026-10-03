from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_reference_audit_defines_narrow_novelty():
    s=(ROOT/"manuscript/macro_dual_isolation_verified_references_v1_86.md").read_text()
    assert "training-only occupied insular source network" in s
    assert "Carter, Z. T." in s
    assert "Ortiz-Rodríguez" in s
    assert "Daniel, A." in s
    assert "10.1111/jbi.13778" in s
    assert "10.1002/ece3.5567" in s

def test_v186_manuscript_does_not_claim_graph_or_source_pool_novelty():
    s=(ROOT/"manuscript/macro_dual_isolation_mammal_v1_86.md").read_text()
    assert "The novelty of the present study is therefore not the claim that island isolation is multidimensional or that networks matter." in s
    assert "That conditional increment—not graph theory, connectivity modelling, or the species-pool concept themselves—is the intended conceptual contribution." in s
    assert "Supplementary Fig. S2" in s
    assert "fresh global confirmation" in s
    assert "two-taxon replication" in s

def test_prediction_behavior_figure_is_summary_only():
    r=json.loads((ROOT/"development/macro_prediction_behavior_figure_request_v1_86.json").read_text())
    assert r["source"]=="development/global_mammals_prediction_behavior_freeze_v1_85.json"
    assert r["source_git_blob_sha1"]=="6efcf12d88dc84f0c1da75553bc4d08f946fbf7e"
    assert r["new_response_access_authorized"] is False
    s=(ROOT/"scripts/build_prediction_behavior_figure_v1_86.py").read_text()
    assert "GIFT_checklists" not in s
    assert "DRYAD" not in s
    assert "Appendix_1" not in s
    assert "figS2_prediction_behavior" in s

def test_v186_figure_shows_required_guardrails():
    s=(ROOT/"scripts/build_prediction_behavior_figure_v1_86.py").read_text()
    assert 'oa["absence"]["C_minus_R3"]' in s
    assert 'oa["presence"]["C_minus_R3"]' in s
    assert 'ge["nonempty_cell_mean_C_minus_R3"]' in s
    assert 'rk["R3_ROC_AUC"]' in s
    assert 'rk["C_average_precision"]' in s

def test_workflow_has_no_response_connectors():
    s=(ROOT/".github/workflows/macro-prediction-behavior-figure-v1_86.yml").read_text()
    assert "new_response_access_authorized" in s
    assert "prepare_dryad_token" not in s
    assert "download-artifact" not in s
    assert "build_prediction_behavior_figure_v1_86.py" in s
