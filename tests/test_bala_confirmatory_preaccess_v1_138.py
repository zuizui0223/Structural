from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_preaccess_contract_freezes_training_and_reference():
    x=json.loads((ROOT/"development/bala_confirmatory_preaccess_contract_v1_138.json").read_text())
    assert x["transition_population"]["primary_loss_count"]=="exactly one t0 occupied island absent at t1"
    assert x["transition_population"]["minimum_confirmatory_taxon_clusters_before_t2"]==10
    assert x["reference_R2"]["island_state"].startswith("six target-island dummy variables")
    assert x["model"]["training_rows"]=="22 frozen exactly-one-loss pilot target rows"
    assert x["model"]["ridge_lambda"]==1.0
    assert x["response_boundary"]["confirmatory_t2_semantic_access_authorized"] is False

def test_phase_router_only_decodes_coreid():
    s=(ROOT/"scripts/route_bala_confirmatory_phase_v1_138.py").read_text()
    assert '"decoded_fields":["coreid"]' in s.replace(" ","")
    assert '"MF_tokens_decoded":0' in s.replace(" ","")
    assert "identificationRemarks" not in s
    assert "organismQuantity" not in s

def test_prediction_runner_has_no_t2_input():
    s=(ROOT/"scripts/freeze_bala_confirmatory_predictions_v1_138.py").read_text()
    assert "confirmatory_t0t1_surface" in s
    assert "confirmatory_t2" not in s
    assert "BALA3" in s  # pilot training only
    assert '"t2_values_used":False' in s.replace(" ","")

def test_workflow_never_passes_t2_to_prediction_runner():
    s=(ROOT/".github/workflows/bala-confirmatory-preaccess-v1_138.yml").read_text()
    step=s.split("Freeze all confirmatory predictions without t2",1)[1].split("Enforce t2 seal",1)[0]
    assert "confirmatory_t2_occurrence_rows.sealed.tsv" not in step
    assert "confirmatory_t0_t1_occurrence_rows.tsv" in step

def test_future_scoring_is_frozen_before_t2():
    x=json.loads((ROOT/"development/bala_confirmatory_preaccess_contract_v1_138.json").read_text())
    s=x["future_scoring"]
    assert s["primary_estimand"].startswith("equal-weight mean across confirmatory taxon clusters")
    assert s["bootstrap_replicates"]==10000
    assert s["minimum_estimable_taxon_clusters"]==10
    assert x["confirmatory_prediction_freeze"]["t2_values_used"] is False
