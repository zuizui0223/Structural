from pathlib import Path
import importlib.util,json,math
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/audit_global_mammals_isolation_empty_support_v1_87.py"
    spec=importlib.util.spec_from_file_location("audit",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_partial_formula_matches_standard_identity():
    m=load_module()
    got=m.partial(0.3,0.1,0.2)
    exp=(0.3-0.1*0.2)/math.sqrt((1-0.1**2)*(1-0.2**2))
    assert abs(got-exp)<1e-15

def test_contract_asks_one_specific_confound_question():
    x=json.loads((ROOT/"development/global_mammals_isolation_empty_support_audit_contract_v1_87.json").read_text())
    assert "merely a restatement" in x["question"]
    assert x["variables"]["x"]=="block mean z_Current_isolation"
    assert x["variables"]["z"]=="block graph_empty_fraction"
    assert len(x["anti_fishing"])==5
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["new_response_access_authorized"] is False

def test_workflow_uses_only_frozen_block_summaries():
    s=(ROOT/".github/workflows/global-mammals-isolation-empty-support-v1_87.yml").read_text()
    assert "11130602935" in s
    assert "11139081593" in s
    assert "block_context.csv" in s
    assert "block_prediction_behavior.csv" in s
    assert "Appendix_1" not in s
    assert "DRYAD_TOKEN" not in s
    assert "confirmatory_matrix" not in s

def test_audit_cannot_change_primary():
    x=json.loads((ROOT/"development/global_mammals_isolation_empty_support_audit_request_v1_87.json").read_text())
    assert x["new_response_access_authorized"] is False
    assert x["confirmatory_status_change_authorized"] is False
    assert x["one_shot"] is True
