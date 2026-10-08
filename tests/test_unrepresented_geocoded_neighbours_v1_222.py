import json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v222",ROOT/"scripts/check_unrepresented_geocoded_neighbours_v1_222.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_contract_is_geometry_only():
    a=json.loads((ROOT/"development/unrepresented_geocoded_neighbourhood_contract_v1_222.json").read_text())
    assert a["neighbour_sets"]["no_true_mammal_zero_label"] is True
    assert a["no_reconstruction_of_original_regionwise_kNN"] is True
    assert a["no_graph_refitting_or_rescoring"] is True
    assert a["distance_endpoints"][0].startswith("fraction of focal")
    assert all(z is False for z in a["policy"].values())
def test_expected_geographic_namepoints_are_not_all_islands():
    a=json.loads((ROOT/"development/strict_spatial_island_match_result_v1_221.json").read_text())
    assert a["results"]["Weigelt_namepoint_available"]==11546
    assert a["results"]["Weigelt_namepoint_missing"]==6337
    assert a["results"]["matched_selected_Structural_islands"]==3878
def test_analytic_unit_sphere_chord_distance():
    assert abs(m.hav_from_dot(1)-0)<1e-10
    assert abs(m.hav_from_dot(-1)-3.141592653589793*m.R)<1e-7
