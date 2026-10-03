from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_sealed_species_result_is_primary_nonreplication():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_result_freeze_v1_97.json").read_text())
    assert x["P1_primary"]["supported"] is False
    assert x["P1_primary"]["bootstrap_ci95_high"]>0
    assert x["P2_constraint_signature"]["supported"] is False
    assert x["P4_topology_specificity"]["supported"] is False
    assert x["interpretation"]["P1_primary_species_layer_replication_supported"] is False
    assert x["evidence_status"]["prospective_preregistered_species_layer_evidence"] is True
    assert x["evidence_status"]["counts_as_independent_system_confirmation"] is False

def test_prediction_asymmetry_reverses_in_sealed_layer():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_result_freeze_v1_97.json").read_text())
    assert x["P2_constraint_signature"]["absence_point"]>0
    assert x["P2_constraint_signature"]["presence_point"]<0
    assert "reversed" in x["P2_constraint_signature"]["direction_relative_to_original_79_species"]

def test_actual_topology_is_not_special_in_sealed_layer():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_result_freeze_v1_97.json").read_text())
    p=x["P4_topology_specificity"]
    assert p["actual_C_better_than_n_of_20_nulls"]==11
    assert p["bootstrap_ci95_low"]<0<p["bootstrap_ci95_high"]

def test_geb_v197_leads_with_nonreplication():
    s=(ROOT/"manuscript/submission/GEB_v1_97/blinded_main_text.md").read_text()
    assert "does not replicate the exploratory source-network signal" in s
    assert "did not replicate the overall gain" in s
    assert "actual graph was indistinguishable" in s
    assert "geographically independent replication" in s

def test_figure4_is_frozen_output_only():
    r=json.loads((ROOT/"development/sealed_species_figure_request_v1_97.json").read_text())
    assert r["result_artifact_id"]==11269176943
    assert r["new_response_access_authorized"] is False
    s=(ROOT/".github/workflows/sealed-species-figure-v1_97.yml").read_text()
    assert "prepare_dryad_token" not in s
    assert "second_layer_null_scores.csv" in s
