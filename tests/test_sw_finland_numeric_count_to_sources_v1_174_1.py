from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/sw_finland_numeric_count_to_sources_contract_v1_174_1.json"

def test_v1741_permanently_excludes_nonnumeric_species():
    c=json.loads(C.read_text())
    assert c["required_v1_173_3"]["numeric_species"]==312
    assert c["required_v1_173_3"]["excluded_nonnumeric_species"]==275
    assert c["reconstruction"]["excluded_nonnumeric_species_may_reenter"] is False

def test_v1741_does_not_loosen_exact_source_gate():
    c=json.loads(C.read_text())
    assert c["required_v1_173_3"]["minimum_exact_source_species"]==30
    assert c["required_v1_173_3"]["impossible_species_required"]==0
    assert c["reconstruction"]["minimum_exact_species"]==30
    assert c["reconstruction"]["exact_species_count_must_equal_v1_173_3_receipt"] is True

def test_future_outcome_remains_sealed():
    c=json.loads(C.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["protected_outcome_values_decoded"]==0
    assert c["response_boundary"]["pilot_future_outcome_authorized"] is False
    assert c["response_boundary"]["confirmatory_future_outcome_authorized"] is False
    assert c["response_boundary"]["eBird_enabled"] is False
