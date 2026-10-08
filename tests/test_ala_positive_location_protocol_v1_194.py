from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/global_mammals_ala_positive_location_protocol_v1_194.json"

def test_positive_only_score_is_conditional_and_not_raw_presence_logloss():
    c=json.loads(C.read_text())
    s=c["conditional_positive_location_score"]
    assert "exactly the same 167" in s["denominator"]
    assert "-log q_model" in s["case_loss"]
    assert s["model_parameters_refit"] is False
    assert s["no_absence_discrimination_claim"] is True

def test_preoutcome_gates_are_frozen():
    c=json.loads(C.read_text())
    assert c["input_authority"]["matched_heldout_islands"]==167
    assert c["input_authority"]["provisional_taxa"]==65
    assert c["support_before_scoring"]["minimum_distinct_positive_pairs"]==50
    assert c["support_before_scoring"]["minimum_distinct_positive_taxa"]==10
    assert c["support_before_scoring"]["minimum_distinct_matched_islands_with_positive_records"]==15
    assert c["support_before_scoring"]["minimum_frozen_spatial_blocks_with_positive_records"]==5
    assert c["uncertainty"]["bootstrap_replicates"]==10000
    assert c["uncertainty"]["bootstrap_seed"]==2026100802

def test_no_implicit_absences_or_movement_claim():
    c=json.loads(C.read_text())
    assert c["eligibility_precommitted"]["no_external_zero_labels"] is True
    assert c["eligibility_precommitted"]["site_specific_native_status_still_not_verified"] is True
    assert c["response_boundary"]["external_FID_by_taxon_pairs_read_so_far"]==0
    assert c["response_boundary"]["original_heldout_labels_read"]==0
    assert c["response_boundary"]["score_request_currently_authorized"] is False
