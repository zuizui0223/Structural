from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def load(p):
    return json.loads((ROOT/p).read_text())

def test_gift_metadata_freeze_records_pristine_1460_whole_islands():
    x=load("development/gift_metadata_freeze_commit_v1_34.json")
    assert x["query_result"]["metadata_rows"]==1930
    assert x["query_result"]["entity_class_counts"]=={
        "Island":1876,"Island Group":45,"Island Part":9
    }
    assert x["query_result"]["whole_island_unique_entity_count"]==1460
    assert x["query_result"]["whole_island_entities_with_multiple_lists"]==305
    assert x["semantic_boundary"]["species_composition_rows_returned"]==0
    assert x["canonical_run_rule"]["this_success_is_canonical"] is True

def test_mammal_quarantine_freeze_records_full_block_exclusion():
    x=load("development/global_mammals_contamination_quarantine_freeze_v1_34.json")
    q=x["quarantine_result"]
    assert q["quarantined_block_id"]=="GB_e41324eb2918"
    assert q["quarantined_island_count"]==15
    assert q["retained_island_count"]==5577
    assert q["retained_confirmatory_islands"]==4270
    assert x["response_boundary"]["Appendix1_reopened"] is False
    assert x["response_boundary"]["fresh_status_restored"] is False
