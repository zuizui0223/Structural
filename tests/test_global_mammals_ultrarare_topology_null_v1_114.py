from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_ultrarare_null_contract_reuses_exact_previous_ensemble():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_topology_null_contract_v1_114.json").read_text())
    n=x["null_ensemble"]
    assert n["null_graphs"]==20
    assert n["base_seed"]==2026100300
    assert len(n["expected_combined_graph_fingerprints"])==20
    assert len(set(n["expected_combined_graph_fingerprints"]))==20
    assert n["response_based_null_selection_forbidden"] is True

def test_topology_specificity_is_frozen_before_response():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_topology_null_contract_v1_114.json").read_text())
    h=x["additional_prospective_hypothesis"]
    assert h["prediction"]=="negative"
    assert "95% upper bound < 0" in h["support_rule"]
    assert h["minimum_presence_blocks"]==10
    assert h["role"].startswith("secondary prospective")
    assert x["response_boundary"]["heldout_ultrarare_response_opened"] is False

def test_null_freezer_never_reads_heldout_response():
    s=(ROOT/"scripts/freeze_global_mammals_ultrarare_topology_nulls_v1_114.py").read_text()
    assert "DRYAD" not in s
    assert "Appendix_1_presence_absence" not in s
    assert "heldout_target_values_used" in s
    assert "heldout_response_opened" in s
    assert "expected_combined_graph_fingerprints" in s

def test_workflow_binds_exact_actual_surface_and_no_response_access():
    s=(ROOT/".github/workflows/global-mammals-ultrarare-topology-null-v1_114.yml").read_text()
    assert "11284534666" in s
    assert "3307a2e058f5f8223eaf0c2d69241acd938e96b93cb02643b1b7d63b425fae04" in s
    assert "prepare_dryad_token" not in s
    assert "heldout_response_authorized" in s
