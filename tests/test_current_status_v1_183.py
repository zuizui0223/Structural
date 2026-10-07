from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"development/current_status_v1_183.json"
P=ROOT/"development/structural_active_priority_v1_183.json"

def test_topology_specificity_and_irreplaceability_are_separated():
    x=json.loads(S.read_text())
    assert x["central_empirical_evidence"]["ultrarare_occurrence"]["actual_better_than_nulls"]=="20/20"
    t=x["response_free_source_structure"]["target_space_turnover_v1_181"]
    assert t["mean_actual_minus_null_beta"] < 0
    assert t["ci95"][1] < 0
    assert x["claim_boundary"]["node_level_irreplaceability_supported"] is False

def test_semantic_correction_preserves_numeric_v122_result():
    x=json.loads(S.read_text())
    a=x["response_free_source_structure"]["aggregate_balance_v1_122"]
    assert a["mean_actual_minus_null_effective_count"] > 0
    assert "not by itself spatial complementarity" in a["corrected_interpretation"]

def test_priority_forbids_rescue_and_management_translation():
    x=json.loads(P.read_text())
    assert any("do not rescue distributed irreplaceability" in s for s in x["do_not"])
    assert any("individual-source conservation priority" in s for s in x["do_not"])
