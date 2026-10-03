from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_audit_is_posthoc_nonrescuing():
    x=json.loads((ROOT/"development/global_mammals_original79_topology_audit_contract_v1_116.json").read_text())
    assert x["evidence_class"].startswith("posthoc")
    assert x["interpretation"]["may_change_original_exploratory_status"] is False
    assert x["interpretation"]["counts_as_confirmatory_evidence"] is False
    assert x["new_response_access_authorized"] is False

def test_same_twenty_nulls_are_reused():
    x=json.loads((ROOT/"development/global_mammals_original79_topology_audit_contract_v1_116.json").read_text())
    assert x["null_ensemble"]["null_graphs"]==20
    assert x["null_ensemble"]["exact_same_graph_fingerprints_required"] is True
    assert x["null_ensemble"]["response_based_selection_forbidden"] is True

def test_audit_reports_all_presence_absence_topology_contrasts():
    s=(ROOT/"scripts/run_global_mammals_original79_topology_audit_v1_116.py").read_text()
    assert '"all_cells"' in s
    assert '"presence_cells"' in s
    assert '"absence_cells"' in s
    assert "actual_better_than_n_of_20_nulls" in s
    assert "new_response_accessed" in s

def test_workflow_uses_only_frozen_response_artifact():
    s=(ROOT/".github/workflows/global-mammals-original79-topology-audit-v1_116.yml").read_text()
    assert "11113225988" not in s  # bound by exact artifact name/run, not public response access
    assert "exploratory_confirmatory_matrix.csv" in s
    assert "prepare_dryad_token" not in s
    assert "Appendix_1_presence_absence.csv" not in s
