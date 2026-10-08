import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/full_original_island_neighbour_geometry_freeze_v1_223.json"
def test_frozen_full_original_node_summary():
    x=json.loads(P.read_text())
    assert x["execution"]["unit_tests_passed"]==2
    assert x["results"]["focal_matched_islands"]==3878
    assert x["fixed_method"]["entire_original_Barreto_selected_centroids"]==5401
    assert abs(x["results"]["fraction_of_nearest_other_Weigelt_named_points_with_no_compatible_selected_other_centroid"]-0.21325425477050025)<1e-12
    assert abs(x["results"]["fraction_of_nearest_other_Weigelt_named_point_at_least_5km_nearer_than_original_selected_nearest"]-0.1371841155234657)<1e-12
def test_not_claiming_mammal_zero_or_discrete_graph_missingness():
    x=json.loads(P.read_text())
    assert x["scientific_interpretation"]["actual_original_kNN_graph_node_missing_fraction_identified"] is False
    assert x["scientific_interpretation"]["biologically_mammal_empty_island_fraction_identified"] is False
    assert x["scientific_interpretation"]["no_new_test_of_original_529_mammal_species_labels"] is True
    assert all(v is False for v in x["guard"].values())
    old=json.loads((ROOT/"manuscript/submission/GEB_CURRENT.json").read_text())
    assert old["submission_authorized"] is False
