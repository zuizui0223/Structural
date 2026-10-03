from pathlib import Path
import importlib.util,json
import pytest
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    pytest.importorskip("numpy")
    p=ROOT/"scripts/freeze_global_mammals_sealed_species_predictions_v1_94.py"
    spec=importlib.util.spec_from_file_location("second",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_predictions_are_fixed_before_new_heldout_access():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_replication_contract_v1_94.json").read_text())
    assert x["population"]["second_layer_species"]==96
    assert x["population"]["heldout_target_cells"]==396096
    assert x["preconfirmatory_freeze"]["heldout_response_authorized_during_prediction_freeze"] is False
    assert x["response_boundary"]["second_layer_96_heldout_response_opened"] is False

def test_four_predictions_are_explicit_and_directional():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_replication_contract_v1_94.json").read_text())
    p=x["predictions"]
    assert p["P1_primary_overall_increment"]["favourable_direction"]=="negative"
    assert p["P2_constraint_signature"]["prediction_presence"]=="presence C-minus-R3 >= 0"
    assert "graph_nonempty" in p["P3_source_support_signature"]["estimand"]
    assert p["P4_topology_specificity"]["prediction"].startswith("actual-minus-rewired < 0")

def test_rewired_null_preserves_degree_and_distance_bins():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_replication_contract_v1_94.json").read_text())["rewired_graph_null"]
    assert x["null_graphs"]==20
    assert x["degree_sequence"].startswith("exactly preserved")
    assert x["distance_bins"]==5
    assert "same original distance bin" in x["distance_bin_constraint"]
    assert x["final_graph_connected_required"] is True
    assert x["null_selection_from_response_forbidden"] is True

def test_rewire_helper_preserves_degree_signature_on_noop_input_helpers():
    m=load_module()
    nodes=[0,1,2,3]
    edges=[(0,1,1.0,0),(1,2,1.0,0),(2,3,1.0,0),(0,3,1.0,0)]
    assert m.degree_signature(nodes,edges)==(2,2,2,2)
    assert m.bin_counts(edges)==(4,0,0,0,0)
    assert m.connected(nodes,edges) is True

def test_preconfirm_workflow_has_no_response_transport():
    s=(ROOT/".github/workflows/global-mammals-sealed-species-preconfirm-v1_94.yml").read_text()
    assert "prepare_dryad_token" not in s
    assert "fetch_global_mammal_response" not in s
    assert "second_layer_predictions.f64le" in s
    assert "heldout_second_layer_response_opened" in s

def test_prediction_script_has_no_response_access():
    s=(ROOT/"scripts/freeze_global_mammals_sealed_species_predictions_v1_94.py").read_text()
    assert "DRYAD_TOKEN" not in s
    assert "transport_v117" not in s
    assert "heldout_second_layer_target_values_used" in s
    assert "null_graphs" in s
