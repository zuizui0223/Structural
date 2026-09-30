from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_numeric_replay_tolerance_is_inherited_not_response_selected():
    x=json.loads((ROOT/"development/gift_replay_numeric_equivalence_contract_v1_63.json").read_text())
    assert x["tolerance_basis"]["absolute_tolerance"]==1e-12
    assert "v1.60" in x["tolerance_basis"]["source"]
    assert x["tolerance_basis"]["not_selected_from_confirmatory_targets"] is True
    assert x["scoring_policy_if_pass"]["score_original_frozen_predictions_only"] is True
    assert x["failure_policy"]["confirmatory_response_authorized_by_this_audit"] is False

def test_failed_exact_replay_consumed_no_confirmatory_response():
    x=json.loads((ROOT/"development/gift_replay_numeric_equivalence_contract_v1_63.json").read_text())
    assert x["failed_exact_replay"]["workflow_run_id"]==36738553501
    assert x["failed_exact_replay"]["confirmatory_api_requested"] is False
    assert x["failed_exact_replay"]["confirmatory_response_consumed"] is False

def test_audit_workflow_has_no_GIFT_response_access():
    s=(ROOT/".github/workflows/gift-replay-numeric-audit-v1_63.yml").read_text()
    assert "run_gift_confirmatory_response" not in s
    assert "GIFT_checklists_raw" not in s
    assert "audit_gift_replay_numeric_equivalence_v1_63.py" in s
    assert "--tolerance 1e-12" in s
