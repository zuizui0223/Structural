import importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
m=importlib.util.spec_from_file_location("idx235",P/"scripts/index_original_mammal_heldout_geography_v1_235.py")
v=importlib.util.module_from_spec(m);m.loader.exec_module(v)
def test_precommitted_geogrid_half_open_boundaries():
 assert v.tile(0,0,0)==((0,10),(0,10))
 assert v.tile(-0.01,-0.01,0)==((-10,0),(-10,0))
 assert v.tile(30.1,121.6,0)==((30,40),(120,130))
 assert v.tile(29.9,121.6,0)==((20,30),(120,130))
 assert v.tile(29.9,121.6,5)==((25,35),(115,125))
def test_heldout_plus_selected_counts_and_scientific_limits():
 ledger=json.loads((P/"development/mammal_heldout_geographic_search_index_v1_235.json").read_text())
 assert ledger["provenance"]["Barreto_safe"]["rows"]==5592
 assert ledger["provenance"]["heldout_routing"]["rows"]==4126
 assert ledger["provenance"]["selected_nodes"]["rows"]==5401
 assert ledger["grid"]["cell_width_degrees"]==10
 assert ledger["limits"]["geographic_grid_cell_not_biological_archipelago"] is True
 assert all(x is False for x in ledger["safeguards"].values())
