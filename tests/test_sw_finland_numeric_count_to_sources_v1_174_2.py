from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/sw_finland_numeric_count_to_sources_contract_v1_174_2.json"
def test_v1742_keeps_only_frozen_numeric_authority():
    c=json.loads(C.read_text())
    assert c["required_v1_173_4"]["numeric_species"]==312
    assert c["required_v1_173_4"]["excluded_nonnumeric_species"]==275
    assert c["exact_source_rule"]["authority_species"]=="312 frozen numeric species only"
    assert c["exact_source_rule"]["nonnumeric_species"]=="exclude permanently from this route"
def test_v1742_requires_internal_complete_absence_support():
    c=json.loads(C.read_text())
    assert "archived_absent_count + recovered_historical_source_count == 471" in c["exact_source_rule"]["eligible_if"]
    assert c["exact_source_rule"]["exact_species_count_must_equal_v1_173_4_receipt"] is True
    assert c["exact_source_rule"]["minimum_exact_species"]==30
def test_v1742_future_outcome_stays_sealed():
    c=json.loads(C.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["pilot_future_outcome_authorized"] is False
    assert c["response_boundary"]["confirmatory_future_outcome_authorized"] is False
    assert c["response_boundary"]["eBird_enabled"] is False
