from pathlib import Path
import json
import importlib.util

ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/audit_bala_protocol_grammar_v1_132.py"
    spec=importlib.util.spec_from_file_location("bala132",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_protocol_contract_comes_from_publication_not_outcome_count_search():
    x=json.loads((ROOT/"development/bala_protocol_grammar_audit_contract_v1_132.json").read_text())
    assert x["publication_basis"]["pitfall_protocol"]["traps_per_site_phase"]==30
    assert x["publication_basis"]["pitfall_protocol"]["traps_per_preservative_class"]==15
    assert x["publication_basis"]["beating_protocol"]["tree_species_per_site_phase_max"]==3
    assert x["publication_basis"]["beating_protocol"]["samples_per_tree_species_max"]==10
    assert "do not drop a syntactically valid slot merely because dropping it moves the count toward 4929" in x["anti_selection"]

def test_field_number_parser_is_protocol_only():
    m=load_module()
    assert m.parse_field("ETHY-S01")==("ETHY",1)
    assert m.parse_field("TURQ-S15")==("TURQ",15)
    assert m.parse_field("JUNI-S10")==("JUNI",10)
    assert m.parse_field("NA-NA") is None

def test_audit_does_not_resolve_aliases_or_choose_final_core():
    x=json.loads((ROOT/"development/bala_protocol_grammar_audit_contract_v1_132.json").read_text())
    assert x["field_number_grammar"]["prefix_aliases_are_not_resolved_in_this_audit"] is True
    assert "do not resolve TUR/TURQ or plant-prefix aliases in this audit" in x["anti_selection"]
    assert x["response_boundary"]["confirmatory_eligible_after_this_audit"] is False

def test_workflow_never_parses_occurrence_semantics():
    s=(ROOT/".github/workflows/bala-protocol-grammar-v1_132.yml").read_text()
    assert "occurrence_extension_semantically_opened" in s
    assert "event_by_taxon_rows_parsed" in s
    assert "source_loss_effects_computed" in s
    assert "Occurrence" not in s or "response firewall" in s
