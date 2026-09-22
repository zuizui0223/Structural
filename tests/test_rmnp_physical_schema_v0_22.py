from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"development/rmnp_physical_schema_receipt_v0_22.json"
M=ROOT/"development/rmnp_file_role_manifest_v0_22.json"

def test_rmnp_response_is_still_sealed():
    x=json.loads(R.read_text())
    assert x["status"]=="advance_to_protocol_freeze"
    assert x["evidence_class"]=="pristine_fresh_pre_response"
    assert x["response_firewall"]["protected_response_values_opened"] is False
    assert x["physical_schema_gates"]["response_values_read"] is False

def test_transition_is_selected_response_independently():
    x=json.loads(R.read_text())
    assert x["transition_selection_rule"]["selected_transition"]=="2021->2022"
    qualified=[p for p in x["transition_selection_rule"]["audited_pairs"] if p["qualifies"]]
    assert [p["transition"] for p in qualified]==["2021->2022"]

def test_geometry_is_source_year_only_and_reproducible():
    x=json.loads(R.read_text())
    g=x["geometry"]
    assert g["source_year"]==2021
    assert g["evaluation_sites_with_source_geometry"]==92
    assert g["excluded_shared_sites"]==["Timber Lake #3"]
    assert g["canonical_crs"].startswith("EPSG:26913")
    assert g["geometry_repair_using_2022_forbidden"] is True

def test_amma_is_excluded_before_response_access():
    x=json.loads(R.read_text())
    assert x["metadata_semantics"]["amma_taxon_identity_conflict"] is True
    assert "reintroduce AMMA" in " ".join(x["prohibited"])

def test_file_roles_keep_csv_mixed():
    x=json.loads(M.read_text())
    roles={r["relative_path"]:r["role"] for r in x["assignments"]}
    assert roles["ROMO_data_release.csv"]=="mixed"
    assert roles["romo_datarelease.xml"]=="metadata"
