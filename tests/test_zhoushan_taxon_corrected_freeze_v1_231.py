import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_corrected_published_vs_529_species_not_old_false_zero():
    p=json.loads((R/"development/zhoushan_taxon_overlap_terminal_v1_230.json").read_text())
    x=json.loads((R/"development/zhoushan_published_taxa_corrected_freeze_v1_231.json").read_text())
    assert p["v230_zero_overlap_is_valid_eligibility_claim"] is False
    assert "SUPERSEDED" in p["current_scientific_adjudication"]
    assert x["exact_shared_species_count"]==5
    assert x["source_529_taxon_encoding"]["with_period"]==529
    assert "Rattus losea" in x["matched_species"]
    assert x["minimum_candidate_eligibility"]["valid_external_prediction_score_authorized"] is False
def test_still_no_field_incidence_or_original_heldout():
    x=json.loads((R/"development/zhoushan_published_taxa_corrected_freeze_v1_231.json").read_text())
    assert x["scientific_scope"]["source_species_incidence_values_opened"]==0
    assert x["scientific_scope"]["original_529_heldout_response_values_opened"]==0
    assert x["scientific_scope"]["new_independent_biological_result"] is False
    assert all(v is False for v in x["guards"].values())
