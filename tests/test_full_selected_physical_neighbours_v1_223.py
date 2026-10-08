import pytest
pytest.importorskip("numpy")
pytest.importorskip("scipy")
from pathlib import Path
import json,importlib.util
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v223",R/"scripts/nearest_fully_selected_v1_223.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_contract_keeps_all_selected_nodes():
    d=json.loads((R/"development/full_original_selected_neighbour_contract_v1_223.json").read_text())
    assert d["true_original_selected_world"].startswith("All 5401")
    assert d["fixed_rules"]["threshold_km_for_material_distance_difference"]==5
    assert d["fixed_rules"]["no_graph_edges_reconstructed"] is True
    assert d["limits"]["geographic_nodes_not_mammal_zero_labels"] is True
    assert all(v is False for v in d["policy"].values())
def test_safe_coordinate_statistics():
    a=m.summaries([1,2,3,4])
    assert a["median"]==2.5
    assert a["q25"]==1.75
