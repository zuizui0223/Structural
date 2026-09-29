from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_gift_geography_execution_is_bound_to_canonical_metadata():
    x=json.loads((ROOT/"development/gift_whole_island_geography_request_v1_35.json").read_text())
    assert x["metadata_run_id"]==36582542511
    assert x["metadata_artifact_id"]==11039932741
    assert x["expected_whole_island_entities_before_overlap"]==1460
    assert x["species_composition_authorized"] is False

def test_mammal_reference_execution_uses_quarantined_population_only():
    x=json.loads((ROOT/"development/global_mammals_reference_operator_request_v1_36.json").read_text())
    assert x["expected_retained_islands"]==5577
    assert x["quarantine_artifact_id"]==11040646818
    assert x["Appendix1_access_authorized"] is False
