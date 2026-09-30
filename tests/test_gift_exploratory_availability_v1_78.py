from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_availability_rule_is_global_not_list180_rescue():
    x=json.loads((ROOT/"development/gift_exploratory_availability_contract_v1_78.json").read_text())
    r=x["endpoint_availability_rule"]
    assert r["query"].startswith("one GIFT_checklists_raw call")
    assert r["replacement_lists_allowed"] is False
    assert r["replacement_entities_allowed"] is False
    assert r["manual_exception_for_list_180_or_any_other_list"] is False

def test_fresh_terminal_status_cannot_be_restored():
    x=json.loads((ROOT/"development/gift_exploratory_availability_contract_v1_78.json").read_text())
    assert "fresh GIFT terminal v1.76 status is unchanged" in x["anti_rescue"]
    assert x["counts_as_fresh_confirmation"] is False
    assert x["counts_as_primary_confirmatory_evidence"] is False

def test_response_script_uses_all_frozen_lists_once_and_persists_no_raw_rows():
    s=(ROOT/"scripts/run_gift_exploratory_availability_v1_78.R").read_text()
    assert "list_ID=as.numeric(confirm$list_ID)" in s
    assert "unavailable <- setdiff(confirm$list_ID,returned_lists)" in s
    assert "raw_species_rows_persisted=FALSE" in s
    assert "replacement" not in s.lower()

def test_scorer_uses_original_predictions_without_refit():
    s=(ROOT/"scripts/score_gift_exploratory_availability_v1_78.py").read_text()
    assert "3c87379be8081edd05ad42e56a8b58a39b2ff75e15ba75993147fb21a0992db4" in s
    assert "refit" not in s.lower()
    assert "fresh_status_restored" in s

def test_workflow_is_nonconfirmatory_and_exact_parent_bound():
    s=(ROOT/".github/workflows/gift-exploratory-availability-v1_78.yml").read_text()
    assert "11060636113" in s and "11060478567" in s and "11060858946" in s
    assert "Score original frozen prediction surface" in s
    assert "counts_as_primary_confirmatory_evidence" in s
