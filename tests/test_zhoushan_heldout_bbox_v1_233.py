import json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("geo233",ROOT/"scripts/zhoushan_original_heldout_bbox_v1_233.py")
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def test_region_source_box_is_fixed_by_paper():
 x=json.loads((ROOT/"development/zhoushan_heldout_region_geography_contract_v1_233.json").read_text())
 b=x["basis"]
 assert abs(m.LAT_MIN-b["latitude_south"])<1e-12
 assert abs(m.LAT_MAX-b["latitude_north"])<1e-12
 assert abs(m.LON_MIN-b["longitude_west"])<1e-12
 assert abs(m.LON_MAX-b["longitude_east"])<1e-12
 assert x["input_artifacts"]["original_confirmatory_4126"]["n"]==4126
 assert x["definition"]["no_species_presence_cell_access"] is True
 assert x["definition"]["no_predictions_read"] is True
 assert all(z is False for z in x["guards"].values())
def test_safe_ids_and_percentiles():
 assert m.canonical("00001")=="1"
 assert m.quant([1,2,3,4],.5)==2.5
 assert m.quant([1,2,3,4],.25)==1.75
