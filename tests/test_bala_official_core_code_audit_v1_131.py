from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_publication_core_codes_are_31_but_30_lineages():
    x=json.loads((ROOT/"development/bala_official_core_code_audit_contract_v1_131.json").read_text())
    codes=set(x["official_core_codes"]["unchanged_29"])
    codes.add(x["official_core_codes"]["BALA1_replaced_site_code"])
    codes.add(x["official_core_codes"]["BALA2_BALA3_replacement_site_code"])
    assert len(codes)==31
    assert x["official_core_codes"]["BALA1_replaced_site_code"]=="FAI-NFCF-T-11"
    assert x["official_core_codes"]["BALA2_BALA3_replacement_site_code"]=="FAI-NFCF-TB26"

def test_alias_codes_are_explicitly_noncore():
    x=json.loads((ROOT/"development/bala_official_core_code_audit_contract_v1_131.json").read_text())
    aliases=x["official_core_codes"]["explicitly_not_publication_core_codes"]
    assert "FAI-NFCF-TB11" in aliases
    assert "TER-NFBF-TY01" in aliases
    assert "TER-NFTB-TY18" in aliases

def test_sample_slot_is_audit_only_not_posthoc_dedup_rule():
    x=json.loads((ROOT/"development/bala_official_core_code_audit_contract_v1_131.json").read_text())
    assert x["sample_slot_definition"]["final_deduplication_rule_selected"] is False
    assert "do not deduplicate Event rows" in x["anti_selection"][3]

def test_script_keeps_occurrence_opaque():
    s=(ROOT/"scripts/audit_bala_official_core_codes_v1_131.py").read_text()
    assert "del occ_bytes" in s
    assert "parse_event_core(event_bytes,core)" in s
    assert '"taxon_occurrence_values_opened":0' in s
    assert '"final_core_rule_selected":False' in s

def test_workflow_never_opens_occurrence_semantics():
    s=(ROOT/".github/workflows/bala-official-core-code-audit-v1_131.yml").read_text()
    assert "occurrence_extension_semantically_opened" in s
    assert "taxon_occurrence_values_opened" in s
    assert "occurrence.txt" not in s
