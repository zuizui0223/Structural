from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/run_global_mammals_prediction_behavior_v1_84.py"
    spec=importlib.util.spec_from_file_location("pb",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_metric_helpers_are_deterministic():
    m=load_module()
    assert m.average_ranks([1,1,3])==[1.5,1.5,3.0]
    assert abs(m.roc_auc([0,1],[0.1,0.9])-1.0)<1e-15
    assert abs(m.average_precision([0,1],[0.1,0.9])-1.0)<1e-15

def test_contract_keeps_primary_and_balanced_metric_separate():
    x=json.loads((ROOT/"development/global_mammals_prediction_behavior_contract_v1_84.json").read_text())
    assert x["interpretation_guardrails"]["primary_v1_76_unchanged"] is True
    assert x["interpretation_guardrails"]["balanced_class_diagnostic_is_not_a_replacement_estimand"] is True
    assert x["interpretation_guardrails"]["no_species_or_block_removal"] is True
    assert x["counts_as_confirmatory_evidence"] is False

def test_graph_empty_definition_is_frozen_not_response_selected():
    x=json.loads((ROOT/"development/global_mammals_prediction_behavior_contract_v1_84.json").read_text())
    d=x["diagnostics"]["graph_empty_support"]["empty_definition"]
    assert "no occupied pilot island" in d
    assert "exactly the graph-source-empty state" in d

def test_workflow_reads_only_frozen_artifacts():
    s=(ROOT/".github/workflows/global-mammals-prediction-behavior-v1_84.yml").read_text()
    assert "11112360652" in s
    assert "11112450910" in s
    assert "11113225988" in s
    assert "DRYAD_TOKEN" not in s
    assert "Appendix_1" not in s
    assert "run_global_mammals_prediction_behavior_v1_84.py" in s
