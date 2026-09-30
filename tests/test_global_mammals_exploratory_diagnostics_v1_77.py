from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/run_global_mammals_exploratory_diagnostics_v1_77.py"
    spec=importlib.util.spec_from_file_location("diag",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_rank_and_spearman_are_deterministic():
    m=load_module()
    assert m.average_ranks([1,1,3])==[1.5,1.5,3.0]
    assert abs(m.spearman([1,2,3],[3,2,1])+1.0)<1e-15

def test_contract_is_posthoc_and_nonrescuing():
    x=json.loads((ROOT/"development/global_mammals_exploratory_diagnostics_contract_v1_77.json").read_text())
    assert x["status"]=="POSTHOC_NONRESCUING_DIAGNOSTICS_DECLARED_AFTER_EXPLORATORY_PRIMARY"
    assert x["inputs"]["block_scores"]["blocks"]==168
    assert x["cross_system_context"]["pooled_inference_authorized"] is False
    assert x["counts_as_confirmatory_evidence"] is False
    assert "no p-value threshold" in x["anti_rescue"][3]

def test_diagnostics_are_block_weighted_and_use_frozen_context():
    x=json.loads((ROOT/"development/global_mammals_exploratory_diagnostics_contract_v1_77.json").read_text())
    g=x["diagnostics"]["geographic_breadth"]
    e=x["diagnostics"]["external_isolation_context"]
    assert g["block_unit"]=="frozen confirmatory bioregion-by-10-degree block"
    assert "z_Current_isolation" in e["variables"]
    assert "within-bioregion-centered Spearman rho for the same three covariates" in e["report"]

def test_workflow_reads_only_frozen_outputs():
    s=(ROOT/".github/workflows/global-mammals-exploratory-diagnostics-v1_77.yml").read_text()
    assert "11113225988" in s
    assert "11059506168" in s
    assert "run_global_mammals_exploratory_diagnostics_v1_77.py" in s
    assert "Appendix_1" not in s
    assert "DRYAD_TOKEN" not in s
