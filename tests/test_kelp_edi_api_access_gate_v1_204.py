from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
G=ROOT/"development/kelp_edi_api_access_gate_v1_204.json"
def test_edi_gate_keeps_auth_and_metadata_separate():
    x=json.loads(G.read_text(encoding="utf-8"))
    a=x["access_classification"]
    assert "AUTH" in x["status"]
    assert "2026-07-30" in x["official_policy"]
    assert len(x["target_packages"])==4
    assert a["authenticated_access_verified"] is False
    assert a["user_credential_or_secret_recorded"] is False
    assert a["allow_anonymous_API_bypass"] is False
    for key in ("metadata_resource_map_decoded","external_entity_names_opened",
                "original_source_header_decoded","original_source_data_values_decoded",
                "transport_edge_values_decoded","original_mammal_response_opened"):
        assert a[key] is False
    assert a["this_result_is_an_access_policy_gate_not_404_or_missing_data"] is True
    assert x["scientific_hold"] is True
    assert x["active_confirmatory_systems"]==0
    assert x["eBird_used"] is False
