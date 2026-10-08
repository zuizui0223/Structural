from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/structural_source_redundancy_synchrony_v1_202.json"
def test_synchrony_insurance_claim_is_hypothesis_only():
    x=json.loads(P.read_text())
    assert x["novelty_boundary"]["not_yet_demonstrated"] is True
    assert x["novelty_boundary"]["source_count_is_not_demographic_redundancy"] is True
    assert x["preoutcome_constraints"]["covariance_only_from_strictly_earlier_training_windows"] is True
    assert x["preoutcome_constraints"]["matched_null_preserve_geo_source_count_and_time"] is False
    assert x["safeguards"]["active_confirmatory_systems"]==0
    assert x["safeguards"]["scientific_hold"] is True
    assert x["safeguards"]["eBird"] is False
    assert not any(x["safeguards"][k] for k in ("opened_new_occurrence","opened_new_spore_production","opened_new_spore_transport","original_mammal_heldout_revisited","mammal_evidence_reclassified"))
def test_no_pseudo_replication_from_published_kelp():
    x=json.loads(P.read_text())
    assert "2024" in x["novelty_boundary"]["known"]
    assert "source" in x["novelty_boundary"]["proposed_increment"]
    assert x["preoutcome_constraints"]["forbid_target_future_source_status"] is True
    assert x["preoutcome_constraints"]["source_covariance_estimation_must_not_use_same_holdout_year"] is True
