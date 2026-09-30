from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v181_status_keeps_fresh_and_exploratory_evidence_separate():
    x=json.loads((ROOT/"development/current_status_v1_81.json").read_text())
    assert x["fresh_empirical_state"]["completed_fresh_system_count"]==1
    assert x["fresh_empirical_state"]["fresh_primary_supported_count"]==0
    assert x["fresh_empirical_state"]["fresh_primary_not_supported_count"]==1
    assert x["fresh_empirical_state"]["fresh_terminal_unscored_attempt_count"]==1
    assert x["global_mammal_macro"]["counts_as_fresh_confirmatory_evidence"] is False
    assert x["current_ecological_synthesis"]["cross_taxon_confirmatory_generality_claim_authorized"] is False

def test_v181_priority_forbids_rescue_and_new_response():
    x=json.loads((ROOT/"development/structural_active_priority_v1_81.json").read_text())
    assert "consume no new fresh response" in x["do_now"]
    assert "retry the terminal GIFT fresh confirmatory protocol" in x["do_not"]
    assert "claim two-taxon confirmation" in x["do_not"]
