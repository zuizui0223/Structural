import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
f=ROOT/"development/wolfe_identifier_audit_v1_211.json"
spec=importlib.util.spec_from_file_location("wc211",ROOT/"scripts/run_wolfe_joint_predator_v1_211.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_identification_discrepancy_is_frozen_and_unconfirmed():
    x=json.loads(f.read_text())
    e=x["evidence_before_biological_scores"]
    assert e["suspect_source_row_id"]=="6HoLM1"
    assert e["suspect_source_label"]=="matrix_dispersal=none"
    assert e["within_same_code_other_matrix_labels"]==["low"]*3
    assert e["expected_corrected_cell_sizes"]=={"n3":4,"n4":41,"n5":0}
    assert e["independently_verified_by_lab_protocol"] is False
    assert x["conditional_science"]["no_causal_robustness_without_original_lab_treatment_confirmation"]
def test_response_free_attribute_rule_is_exactly_one_row_only():
    script=(ROOT/"scripts/run_wolfe_joint_predator_v1_211.py").read_text()
    assert 'if r.get("")=="6HoLM1":' in script
    assert 'm="low"' in script
    assert 'r["microcosm"]!="6HoLM"' in script
    assert "same" not in "irrelevant"
def test_predecessor_stop_unmodified():
    x=json.loads((ROOT/"development/wolfe_factorial_qc_stop_v1_210.json").read_text())
    assert x["ecological_response_scores_produced"]==0
    assert x["no_v210_same_protocol_rerun"] is True
