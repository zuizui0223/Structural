from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_geometry_operator_is_response_independent_and_parameter_free():
    x=json.loads((ROOT/"development/bala_geometry_operator_contract_v1_136.json").read_text())
    assert x["graph_operator"]["name"]=="Gabriel graph on frozen island centroids"
    assert x["graph_operator"]["lambda"]=="median original Gabriel-edge haversine length in kilometres"
    assert x["graph_operator"]["lambda_response_tuning_authorized"] is False
    assert x["expected_structure"]["islands"]==7
    assert x["response_boundary"]["occurrence_extension_semantically_opened"] is False

def test_opaque_router_authorizes_only_mf_semantics():
    x=json.loads((ROOT/"development/bala_opaque_taxon_routing_contract_v1_136.json").read_text())
    a=x["authorized_semantics"]
    assert "identificationRemarks/MF token" in a["pilot_and_confirmatory_rows"]
    assert a["confirmatory_token_identity_may_persist"] is False
    assert a["confirmatory_distinct_token_count_may_persist"] is True
    assert "decode organismQuantity" in x["forbidden_during_routing"]
    assert "summarize event-by-taxon combinations" in x["forbidden_during_routing"]

def test_router_decodes_only_routing_field():
    s=(ROOT/"scripts/route_bala_occurrence_opaque_v1_136.py").read_text()
    assert "fields[idx]" in s
    assert "fields[17]" not in s
    assert "fields[12]" not in s
    assert "fields[21]" not in s
    assert "confirmatory_token_identities_persisted" in s

def test_v136_workflow_deletes_complete_archive_and_keeps_confirmatory_sealed():
    s=(ROOT/".github/workflows/bala-opaque-routing-v1_136.yml").read_text()
    assert "37211623631" in s
    assert "11306059954" in s
    assert "rm -f build/bala_v136/input/bala.zip" in s
    assert "confirmatory_occurrence_rows.sealed.tsv" in s
    assert "organismQuantity_values_decoded" in s
    assert "source_loss_effects_computed" in s
