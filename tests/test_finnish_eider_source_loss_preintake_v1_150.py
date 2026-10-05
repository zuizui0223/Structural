from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT/rel).read_text())

def test_eider_lane_is_retrospective_only():
    x=load("development/finnish_eider_source_loss_retrospective_preintake_v1_150.json")
    assert x["evidence_class"]["retrospective_only"] is True
    assert x["evidence_class"]["may_count_as_confirmation"] is False
    assert x["response_boundary"]["dataset_values_opened_for_structural_source_leverage"] is False
    assert x["response_boundary"]["source_leverage_effects_computed"]==0

def test_eider_schema_gates_block_spurious_source_loss():
    x=load("development/finnish_eider_source_loss_retrospective_preintake_v1_150.json")
    g=x["schema_audit_success_rules"]
    assert g["zero_is_surveyed_zero_documented"] is True
    assert g["missing_year_is_not_zero_documented"] is True
    assert g["response_independent_distance_object_keyed_to_island_id_available"] is True
    assert g["redistributed_grouped_island_rows_identifiable"] is True
    stops="\n".join(x["stop_rules"])
    assert "zeros cannot be distinguished" in stops
    assert "grouped-island reconstructed rows" in stops

def test_priority_keeps_ebird_confirmatory_and_eider_retrospective_separate():
    x=load("development/structural_active_priority_v1_150.json")
    assert x["confirmatory_lane"]["candidate_id"]=="ebird_global_islands_2002_2019"
    assert x["retrospective_lane"]["candidate_id"]=="finnish_common_eider_archipelago_1997_2020"
    assert x["retrospective_lane"]["may_count_as_confirmation"] is False
    assert "overturn BALA confirmatory non-support" in "\n".join(x["do_not"])
