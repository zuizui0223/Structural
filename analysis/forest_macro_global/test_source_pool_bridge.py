"""Known-truth operator-specific source network and held-out leakage checks."""
import importlib.util
from pathlib import Path
import pytest

path=Path(__file__).with_name("source_pool_bridge.py")
spec=importlib.util.spec_from_file_location("forest_island_source_bridge",path)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

nodes={"target":(0,0),"s1":(0,1),"s2":(1,0),"holdout":(0,-1),
       "link1":(1,1),"link2":(2,1)}
training={"s1":"training_A","s2":"training_B","link1":"training_A",
          "link2":"training_B","target":"validation_X","holdout":"validation_X"}

def features(graph,occupied=("s1","s2","holdout"),**kw):
    return m.source_features(target="target",target_block="validation_X",
        training_blocks=training,all_nodes=nodes,
        donor_occupied=occupied,graph_edges=graph,origin="forest_fragment",
        operator="forest_matrix_movement",decay_km=200,**kw)

def test_same_geodesic_sources_can_have_different_graph_access():
    a=features([("target","s1",1),("target","link1",1),("link1","s2",1)])
    b=features([("target","link1",3),("link1","s1",3),("link1","s2",3)])
    assert a["training_occupied_source_count"]==2
    assert b["training_occupied_source_count"]==2
    assert a["euclidean_nearest_occupied_source_km"]==b["euclidean_nearest_occupied_source_km"]
    assert a["euclidean_diffuse_occupied_source_pressure"]==b["euclidean_diffuse_occupied_source_pressure"]
    assert a["graph_nearest_occupied_source_cost"]==1
    assert b["graph_nearest_occupied_source_cost"]==6
    assert not a["unobserved_patches_assumed_absent"]
    assert not a["source_loss_or_demographic_transition_identified"]

def test_species_presence_on_heldout_nodes_never_enters_source_context():
    graph=[("target","holdout",0.01),("target","s1",1)]
    a=features(graph,occupied=("s1","holdout"))
    b=features(graph,occupied=("s1",))
    assert a==b
    assert a["training_occupied_source_count"]==1

def test_no_known_training_source_is_not_absence():
    x=features([],occupied=("holdout",))
    assert x["training_occupied_source_count"]==0
    assert x["euclidean_nearest_occupied_source_km"] is None
    assert x["graph_nearest_occupied_source_cost"] is None
    assert not x["graph_source_reachable"]
    assert x["euclidean_diffuse_occupied_source_pressure"]==0.0
    assert x["unobserved_patches_assumed_absent"] is False

def test_forest_matrix_cannot_be_interpreted_as_sea_operator():
    with pytest.raises(ValueError,match="operator_origin_mismatch"):
        m.source_features(target="target",target_block="validation_X",
            training_blocks=training,all_nodes=nodes,donor_occupied={"s1"},
            graph_edges=[],origin="oceanic_island",operator="forest_matrix_movement",decay_km=200)

def test_future_donor_exclusion_and_missing_timestamps_stop():
    graph=[("target","s1",1),("target","s2",1)]
    x=features(graph,target_sample_year=2021,donor_sample_years={"s1":2019,"s2":2022})
    assert x["training_occupied_source_count"]==1
    with pytest.raises(ValueError,match="dated_donor_missing_year"):
        features(graph,target_sample_year=2021,donor_sample_years={"s1":2019})

def test_invalid_geometry_and_graph_are_stops():
    with pytest.raises(ValueError,match="invalid_graph_node_or_self_edge"):
        features([("target","alien_patch",1)])
    with pytest.raises(ValueError,match="graph_edge_cost_must_be_positive"):
        features([("target","s1",0)])
