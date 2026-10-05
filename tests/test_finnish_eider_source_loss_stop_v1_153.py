from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def load(p): return json.loads((ROOT/p).read_text())

def test_header_freeze_keeps_rows_unopened():
    x=load("development/finnish_eider_mixed_header_freeze_v1_153.json")
    assert x["header"]["columns"]==["Eider_pairs","lnSize","Year","Lon","Lat","Land","WTE","Forcov","Island_ID","Year_f","pos2"]
    assert x["header"]["group_or_reconstruction_flag_headers"]==[]
    assert x["response_boundary"]["data_row_semantic_values_opened"]==0
    assert x["response_boundary"]["Eider_pairs_values_opened"]==0

def test_eider_stop_is_due_to_reconstruction_traceability():
    x=load("development/finnish_eider_source_loss_stop_v1_153.json")
    b=x["stop_basis"]
    assert b["published_grouped_island_redistribution_exists"] is True
    assert b["row_level_group_or_reconstruction_flag_present"] is False
    assert b["response_independent_rule_can_identify_redistributed_rows"] is False
    assert x["ecological_result"]=="NOT_SCORED"
    assert x["source_loss_effect_computed"] is False

def test_stop_cannot_be_repaired_by_response_mining():
    x=load("development/finnish_eider_source_loss_stop_v1_153.json")
    s="\n".join(x["forbidden_repairs"])
    assert "fractional or unusual Eider_pairs" in s
    assert "known decline" in s
    assert "missing island-year as zero" in s

def test_priority_leaves_only_ebird_confirmatory_hold():
    x=load("development/structural_active_priority_v1_153.json")
    assert x["confirmatory_lane"]["candidate_id"]=="ebird_global_islands_2002_2019"
    assert x["confirmatory_lane"]["status"]=="HOLD_OFFICIAL_SAMPLING_EVENT_DATA_NOT_PRESENT"
    assert x["retrospective_lane"]["status"]=="STOP_RECONSTRUCTED_ROWS_NOT_IDENTIFIABLE_FROM_PUBLIC_ARCHIVE"
    assert "source-leverage ranking is not validated" in x["next_scientific_event"] or "conservation hypothesis remains unconfirmed" in x["next_scientific_event"]
