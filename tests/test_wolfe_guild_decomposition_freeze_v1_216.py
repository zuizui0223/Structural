from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
F=ROOT/"development/wolfe_guild_decomposition_freeze_v1_216.json"
def test_frozen_1024_outcome_bounds_do_not_justify_interaction_mechanism():
    z=json.loads(F.read_text())
    a=z["numerical"]["missingness_extreme_ranges"]
    assert z["source_counts"]["exhaustive_completions"]==1024
    assert a["overall_joint"][0]>0
    assert a["overall_independence_product"][0]>0
    assert a["overall_covariance_remainder"][0]>0
    assert a["six_minus_four_independence_product"][0]>0
    assert a["six_minus_four_covariance_remainder"][0]<0<a["six_minus_four_covariance_remainder"][1]
    assert z["interpretation"]["six_minus_four_covariance_component_sign_robust"] is False
    assert z["interpretation"]["GEB_submission_authorized"] is False

def test_evidence_was_exploratory_and_does_not_reopen_old_systems():
    z=json.loads(F.read_text())
    assert z["provenance"]["synthetic_tests"]=="2 passed"
    assert z["provenance"]["workflow_result"]=="success"
    assert "POSTHOC" in z["provenance"]["scientific_evidence_class"]
    assert all(x is False for x in z["policy"].values())
    assert z["interpretation"]["independent_original_mammal_validation"] is False
