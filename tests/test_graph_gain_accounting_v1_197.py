from pathlib import Path
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
freeze = ROOT / "development/global_mammals_ultrarare_result_freeze_v1_119.json"
ledger = ROOT / "development/global_mammals_graph_gain_accounting_v1_197.json"
status = ROOT / "development/current_status_v1_197.json"
priority = ROOT / "development/structural_active_priority_v1_197.json"
current = ROOT / "manuscript/submission/GEB_CURRENT.json"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def test_gain_decomposition_matches_immutable_v119_contrasts():
    f, d = read(freeze), read(ledger)
    x = d["point_estimate_accounting"]
    assert x["original_kNN_C_minus_R3"] == f["primary_presence_opportunity"]["point_C_minus_R3"]
    assert x["mean_of_20_rewired_C_minus_R3"] == f["secondary_topology_specificity"]["null_presence_C_minus_R3_mean"]
    assert x["original_kNN_C_minus_mean_rewired_C"] == f["secondary_topology_specificity"]["point_actualC_minus_mean_rewiredC"]
    assert abs(x["original_kNN_C_minus_R3"] - x["mean_of_20_rewired_C_minus_R3"] - x["original_kNN_C_minus_mean_rewired_C"]) < 1e-12
    assert math.isclose(x["mean_rewired_fraction_of_original_gain"], 0.9018459934573567, abs_tol=1e-12)
    assert math.isclose(x["kNN_specific_fraction_of_original_gain"], 0.09815400654264339, abs_tol=1e-12)
    assert math.isclose(x["mean_rewired_fraction_of_original_gain"] + x["kNN_specific_fraction_of_original_gain"], 1.0, abs_tol=1e-12)
    assert x["ratio_confidence_interval"] is None

def test_semantics_corrected_and_old_status_preserved():
    s=read(status)
    old=read(ROOT/"development/current_status_v1_195.json")
    assert "observed island adjacency" in old["central_empirical_evidence"]["ultrarare_occurrence"]["interpretation"]
    claim=s["central_empirical_evidence"]["ultrarare_occurrence"]["interpretation"]
    assert not re.search(r"observed (island )?adjacency",claim,re.I)
    assert "coordinate-derived kNN" in claim
    assert s["central_empirical_evidence"]["ultrarare_occurrence"]["presence_C_minus_R3"] == old["central_empirical_evidence"]["ultrarare_occurrence"]["presence_C_minus_R3"]
    assert s["claim_boundary"] == old["claim_boundary"]
    assert s["independent_biological_confirmation_present"] is False
    assert s["submission_status"] == "SCIENTIFIC_HOLD_PENDING_INDEPENDENT_SPECIES_ISLAND_VALIDATION"

def test_admission_and_submission_remain_on_hold():
    d,s,p,c=read(ledger),read(status),read(priority),read(current)
    assert d["evidence_boundaries"]["heldout_occurrence_reopened"] is False
    assert d["evidence_boundaries"]["external_species_island_labels_opened"] is False
    assert d["evidence_boundaries"]["original_effects_thresholds_predictions_or_nulllist_changed"] is False
    assert d["evidence_boundaries"]["ALA_v1_194_replay_authorized"] is False
    assert d["evidence_boundaries"]["eBird_used"] is False
    assert s["independent_evidence_admissibility"] == "development/independent_biological_evidence_admissibility_v1_196.json"
    assert p["canonical_status"] == "development/current_status_v1_197.json"
    assert c["scientific_status"] == p["canonical_status"]
    assert c["active_priority"] == "development/structural_active_priority_v1_197.json"
    assert c["version"] == "v1.185"
    assert c["submission_authorized"] is False
