from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/sw-finland-topology-freeze-v1_172.yml"
C=ROOT/"development/sw_finland_topology_freeze_contract_v1_172.json"

def test_v172_workflow_binds_exact_v171_files_before_execution():
    s=WF.read_text()
    assert "sw_finland_topology_freeze_request_v1_172.json" in s
    for name in (
      "sw_finland_exact_source_reconstruction_v1_171.json",
      "sw_finland_t0_island_geometry_v1_171.csv",
      "sw_finland_exact_source_species_v1_171.csv",
      "sw_finland_exact_source_membership_v1_171.csv",
    ):
        assert name in s
    assert 'req["input_sha256"][key]==sha' in s

def test_v172_workflow_never_references_future_outcome_file():
    s=WF.read_text().lower()
    assert "colonization_select.csv" not in s
    assert 'future_outcome_values_opened"]==0' in s
    assert 'pilot_future_outcome_authorized"] is false' in s
    assert 'confirmatory_future_outcome_authorized"] is false' in s

def test_v172_contract_request_is_t0_only():
    c=json.loads(C.read_text())
    r=c["execution_request"]
    assert r["future_outcome_access_requested"] is False
    assert r["effect_estimate_requested"] is False
    assert r["eBird_used"] is False
    assert c["matched_nulls"]["target_swap_multiplier"]==2
    assert c["matched_nulls"]["maximum_attempt_multiplier"]==400
