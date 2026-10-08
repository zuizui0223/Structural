import json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v231",ROOT/"scripts/compare_zhoushan_taxa_v1_231.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def test_existing_canonical_taxon_normalization_and_no_fuzzy():
    assert mod.norm("  Canis.lupus ")=="canis lupus"
    assert mod.norm(" Canis_lupus ")=="canis lupus"
    assert mod.norm("Canis lupus")=="canis lupus"
    assert mod.norm("Canis lupus familiaris")!="canis lupus"
def test_same_named_roster_preexisting_rule_and_no_outcomes():
    x=json.loads((ROOT/"development/zhoushan_taxon_encoding_repair_v1_231.json").read_text())
    assert "v1_188" in x["predetermined_preexisting_rule_source"]
    assert x["audit_all_529_species_names"] is True
    assert x["no_field_incidence_read"] is True
    assert x["no_original_mammal_heldout_read"] is True
    assert x["GEB_submission_authorized"] is False
