import importlib.util,json
from pathlib import Path
S=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v220",S/"scripts/compare_unpaired_island_area_v1_220.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_quantiles_and_geographic_only_contract():
    assert m.stats([1,2,3,4])["median_km2"]==2.5
    assert m.stats([1,2,3,4])["q25_km2"]==1.75
    c=json.loads((S/"development/unpaired_island_area_contract_v1_220.json").read_text())
    assert c["no_mammal_outcomes_or_predictions"] is True
    assert c["no_mammal_zero_identification"] is True
    assert c["comparison"].startswith("UNPAIRED")
    assert c["no_inference_about_causal_selection_bias"] is True
def test_v219_terminal_id_gate():
    x=json.loads((S/"development/mammal_geography_id_stop_v1_219.json").read_text())
    assert x["identical_numeric_ids_across_sources"]==796
    assert x["numeric_ID_equality_establishes_same_geographic_island"] is False
    assert x["focal_mammal_response_values_read"]==0
    assert x["geographic_selection_effect_computed"] is False
