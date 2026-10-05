from pathlib import Path
import json,hashlib,unicodedata
ROOT=Path(__file__).resolve().parents[1]

def test_mf_is_the_only_authorized_routing_field():
    x=json.loads((ROOT/"development/bala_taxon_routing_contract_v1_135.json").read_text())
    assert x["required_occurrence_fields_from_meta_xml"]["identificationRemarks"]["index"]==20
    assert x["public_builder_identity"]["semantic_mapping"]=="Occ_table identificationRemarks is copied directly from BALA_all_data$MF"
    assert x["opaque_router_semantics_for_next_gate"]["authorized_field_decode"]==["identificationRemarks"]
    assert x["opaque_router_semantics_for_next_gate"]["organismQuantity_may_be_decoded"] is False

def test_partition_is_deterministic_and_immutable():
    x=json.loads((ROOT/"development/bala_taxon_routing_contract_v1_135.json").read_text())
    p=x["deterministic_partition"]
    assert p["salt"]=="Structural-BALA-source-loss-v1.135|"
    assert p["pilot_buckets"]==[0]
    assert p["confirmatory_buckets"]==[1,2,3]
    assert p["partition_may_not_be_rebalanced_after_token_counts_are_known"] is True
    assert p["taxa_may_not_move_between_partitions"] is True

def test_schema_runner_never_opens_occurrence_rows():
    s=(ROOT/"scripts/freeze_bala_taxon_routing_schema_v1_135.py").read_text()
    assert "meta_manifest" in s
    assert "zipfile" not in s
    assert "urllib" not in s
    assert "urlopen" not in s
    assert "occurrence_data_rows_decoded" in s
    assert "taxon_tokens_opened" in s

def test_workflow_downloads_only_frozen_metadata_artifact():
    s=(ROOT/".github/workflows/bala-taxon-routing-schema-v1_135.yml").read_text()
    assert "37187589920" in s
    assert "bala-v128-event-core-audit-" in s
    assert "meta_manifest.json" in s
    assert "occurrence.txt" not in s
    assert "taxon_token_access_authorized" in s
