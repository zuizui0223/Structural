import pytest
pytest.importorskip("numpy")
pytest.importorskip("scipy")
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v240",ROOT/"scripts/camtrapasia_nearest_heldout_centroid_v1_240.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_nearest_centroid_radius_is_geography_not_island_identity():
 x=json.loads((ROOT/"development/camtrapasia_nearest_centroid_contract_v1_240.json").read_text())
 assert x["comparison"]["fixed_distances_km"]==[5,25,100]
 assert x["gate_limits"]["even_under_5km_is_not_island_identity"] is True
 assert x["gate_limits"]["field_detection_data_untouched"] is True
 assert all(a is False for a in x["safeguards"].values())
def test_positive_geographic_distances_and_quantiles():
 assert m.quantile([1,2,3,4],.5)==2.5
 assert m.quantile([1,2,3,4],.25)==1.75
