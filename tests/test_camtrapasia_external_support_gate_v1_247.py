import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v247",R/"scripts/camtrapasia_external_support_gate_v1_247.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_exact_preoutcome_response_free_stop_decision():
    t=json.loads((R/"development/camtrapasia_published_mammal_taxon_overlap_freeze_v1_238.json").read_text())
    a=json.loads((R/"development/camtrapasia_original_island_area_consistency_freeze_v1_246.json").read_text())
    x=m.evaluate(t,a)
    assert x["published_species_name_overlaps"]==38
    assert x["geographic_area_consistent_same_component_survey_studies"]==2
    assert x["distinct_source_original_heldout_island_ids"]==1
    assert x["distinct_original_heldout_spatial_blocks"]==1
    assert x["maximum_possible_species_x_distinct_island_cells"]==38
    assert x["field_camera_capture_rows_read"]==0
    assert x["independent_global_529_prediction_evaluation_admitted"] is False
def test_survey_count_does_not_become_island_replicates():
    d=json.loads((R/"development/camtrapasia_external_support_contract_v1_247.json").read_text())
    assert d["strict_inference_ceiling"]["independent_camera_studies_on_one_island_are_NOT_island_replicates"] is True
    assert d["strict_inference_ceiling"]["no_external_GEB_performance_metric_permitted"] is True
    assert all(v is False for v in d["policy"].values())
