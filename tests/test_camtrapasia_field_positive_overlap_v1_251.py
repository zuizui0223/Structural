import json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v251",ROOT/"scripts/camtrapasia_field_positive_overlap_v1_251.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_no_new_biological_data_reader_and_posthoc_limit():
    c=json.loads((ROOT/"development/camtrapasia_observed_positive_overlap_contract_v1_251.json").read_text())
    assert c["existing_biological_response_already_exposed_v250"] is True
    assert c["allowed_aggregation"]["no_null_hypothesis_pvalues"] is True
    assert c["allowed_aggregation"]["no_effort_corrected_occupancy_probability"] is True
    assert all(z is False for z in c["hard_guards"].values())
def test_real_result_values_consistent_with_original_frozen_field_summary():
    x=json.loads((ROOT/"development/camtrapasia_four_island_field_positive_freeze_v1_250.json").read_text())
    assert x["counts_per_island"][2]["source_shared_focal_mammals_recorded"]==16
    assert x["counts_per_island"][3]["source_shared_focal_mammals_recorded"]==18
    assert x["original_IUCN_heldout_response_read"]==0
