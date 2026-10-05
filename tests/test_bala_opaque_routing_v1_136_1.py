from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_failed_v136_opened_no_taxon_or_response_semantics():
    x=json.loads((ROOT/"development/bala_opaque_taxon_routing_stop_v1_136_1.json").read_text())
    b=x["response_boundary_at_stop"]
    assert b["mf_tokens_decoded"]==0
    assert b["organismQuantity_values_decoded"]==0
    assert b["eventID_values_decoded"]==0
    assert b["taxonomy_values_decoded"]==0
    assert b["pilot_semantic_response_opened"] is False
    assert b["confirmatory_semantic_response_opened"] is False

def test_physical_column_correction_is_schema_derived():
    x=json.loads((ROOT/"development/bala_opaque_taxon_routing_contract_v1_136_1.json").read_text())
    assert x["source"]["mapped_extension_field_definitions"]==31
    assert x["source"]["coreid_physical_column"] is True
    assert x["source"]["physical_field_count_rule"]=="max(coreid_index and all Occurrence field indices)+1"
    assert x["source"]["expected_physical_field_count"]==32
    assert x["scientific_invariants_from_v1_136"]["partition_rule_changed"] is False

def test_corrected_router_uses_meta_manifest_to_derive_count():
    s=(ROOT/"scripts/route_bala_occurrence_opaque_v1_136_1.py").read_text()
    assert "physical_field_count(meta)" in s
    assert "max(idx)+1" in s
    assert "fields[idx]" in s
    assert "fields[17]" not in s
    assert "fields[12]" not in s

def test_retry_workflow_is_operational_and_response_unopened():
    s=(ROOT/".github/workflows/bala-opaque-routing-v1_136_1.yml").read_text()
    assert "37187589920" in s
    assert "37211623631" in s
    assert "route_bala_occurrence_opaque_v1_136_1.py" in s
    assert "organismQuantity_values_decoded" in s
    assert "confirmatory_occurrence_semantic_access_authorized" in s
    assert "source_loss_effects_computed" in s
