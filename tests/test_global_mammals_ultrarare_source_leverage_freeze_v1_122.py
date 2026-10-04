from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_source_leverage_freeze_is_response_free_and_nonconfirmatory():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_source_leverage_freeze_v1_122.json").read_text())
    assert x["response_boundary"]["heldout_occurrence_values_used"] is False
    assert x["response_boundary"]["heldout_occurrence_values_opened"] is False
    assert x["interpretation"]["evidence_hierarchy_change"] is False
    assert x["interpretation"]["current_v1_119_heldout_result_unchanged"] is True

def test_source_leverage_exact_summary():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_source_leverage_freeze_v1_122.json").read_text())
    m=x["result"]["multi_source"]
    assert x["population"]["species"]==529
    assert x["population"]["multi_source_species"]==212
    assert m["actual_effective_count_gt_matched_null_mean"]==141
    assert m["species_where_any_removal_creates_graph_empty"]==18
    assert m["paired_mean_bootstrap_ci95"][0]>0

def test_active_priority_stops_same_dataset_mechanism_mining():
    x=json.loads((ROOT/"development/structural_active_priority_v1_122.json").read_text())
    assert x["evidence_hierarchy_changed"] is False
    assert "independent temporal or response-sealed validation" in x["next_scientific_event"]
