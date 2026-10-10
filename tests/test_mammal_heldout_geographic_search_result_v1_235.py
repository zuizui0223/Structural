import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/mammal_heldout_geographic_search_index_freeze_v1_235.json"
def test_geography_index_actual_global_denominators():
    x=json.loads(P.read_text())
    assert x["counts"]["heldout_islands"]==4126
    assert x["counts"]["distinct_original_heldout_blocks"]==168
    assert x["counts"]["primary_nonempty_10deg_tiles"]==154
    assert x["counts"]["shifted_nonempty_10deg_tiles"]==173
    assert x["primary_grid_top_geographic_cells"][0]["heldout"]==322
    assert x["primary_grid_top_geographic_cells"][0]["blocks"]==2
    assert x["five_degree_shift_grid_top_geographic_cells"][0]["blocks"]==6
    assert x["scientific_interpretation"]["original_mammal_heldout_values_read"]==0
    assert all(z is False for z in x["safeguards"].values())
