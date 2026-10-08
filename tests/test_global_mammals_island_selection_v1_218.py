import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/"development/global_mammals_island_universe_selection_v1_218.json"

def test_mammal_selected_nodes_vs_geom_edges_and_heldout_firewall():
    x=json.loads(P.read_text())
    assert x["original_source_islands"]-x["post_source_quarantined_islands"]-x["post_source_prior_overlap_excluded_islands"]==x["structural_retained_islands"]==5401
    assert x["node_inclusion_based_on_mammal_map_labels"] is True
    assert x["kNN_edges_selected_from_coordinates_given_nodes"] is True
    assert x["original_mammal_focal_heldout_access_firewall_remains_intact"] is True
    assert x["edges_are_observed_mammal_dispersal"] is False
    assert x["impact_direction_or_magnitude_from_existing_frozen_results_known"] is False

def test_working_manuscript_discloses_conditioned_node_universe():
    s=(R/"manuscript/working/GEB_v1_217/blinded_main_text.md").read_text()
    assert "zero mammals mapped by IUCN" in s
    assert "5,401 selected mammal-database islands" in s
    assert "potential geographic intermediate nodes" in s
    assert "Barreto, E., Rangel" in s
    assert "10.1098/rspb.2021.1879" in s
    c=json.loads((R/"manuscript/submission/GEB_CURRENT.json").read_text())
    assert c["version"]=="v1.185"
    assert c["submission_authorized"] is False
