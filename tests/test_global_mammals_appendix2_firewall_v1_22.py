from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIREWALL = (
    ROOT / "development/global_mammals_appendix2_column_firewall_v1_22.json"
)


def load():
    return json.loads(FIREWALL.read_text(encoding="utf-8"))


def test_all_25_observed_headers_are_classified_exactly_once():
    x = load()
    observed = x["observed_headers_in_order"]
    safe = x["safe_columns_in_source_order"]
    closed = x["closed_unneeded_columns_in_source_order"]
    protected = x["protected_response_derived_columns_in_source_order"]

    assert len(observed) == 25
    assert len(safe) == 13
    assert len(closed) == 2
    assert len(protected) == 10
    assert len(set(observed)) == 25
    assert set(safe).isdisjoint(closed)
    assert set(safe).isdisjoint(protected)
    assert set(closed).isdisjoint(protected)
    assert set(safe) | set(closed) | set(protected) == set(observed)
    assert [v for v in observed if v in set(safe)] == safe
    assert [v for v in observed if v in set(closed)] == closed
    assert [v for v in observed if v in set(protected)] == protected


def test_coordinate_names_follow_observed_appendix2_headers_not_preaudit_guess():
    x = load()
    safe = x["safe_columns_in_source_order"]
    assert "Longitude_centroid" in safe
    assert "Latitude_centroid" in safe
    assert "Long_centroid" not in safe
    assert "Lat_centroid" not in safe
    assert x["model_reference_intent"]["geometry"] == [
        "Longitude_centroid",
        "Latitude_centroid",
    ]


def test_response_derived_and_sie_associated_headers_are_all_forbidden():
    x = load()
    protected = set(x["protected_response_derived_columns_in_source_order"])
    expected = {
        "Richness_mammal",
        "Richness_bat",
        "Richness_nonVol",
        "SIE_mammal",
        "SIE_bats",
        "SIE_nonVol",
        "pSIE_mammal",
        "pSIE_bats",
        "pSIE_nonVol",
        "bioregion_SIE",
    }
    assert protected == expected
    assert set(x["protected_response_derived_reasons"]) == expected


def test_safe_reference_preserves_area_isolation_climate_and_realm():
    x = load()
    roles = x["safe_roles"]
    for key in (
        "ID",
        "Longitude_centroid",
        "Latitude_centroid",
        "Area",
        "Current_isolation",
        "Past_isolation",
        "Climate_velocity",
        "Temperature_mean",
        "Temperature_sd",
        "Precipitation_mean",
        "Precipitation_sd",
        "Elevation_sd",
        "bioregion",
    ):
        assert key in roles

    intent = x["model_reference_intent"]
    assert intent["routing"] == "ID"
    assert intent["R1_add"] == [
        "Area",
        "Current_isolation",
        "Past_isolation",
        "Climate_velocity",
    ]




def test_postheader_firewall_does_not_expand_preaudit_safe_intent():
    x = load()
    safe = set(x["safe_columns_in_source_order"])
    assert "Island_name" not in safe
    assert "CountryISO" not in safe
    assert x["closed_unneeded_columns_in_source_order"] == [
        "Island_name",
        "CountryISO",
    ]
    assert set(x["closed_unneeded_reasons"]) == {
        "Island_name",
        "CountryISO",
    }
    assert x["exact_partition_rule"][
        "post_header_safe_set_expansion_beyond_preaudit_intent_forbidden"
    ] is True
    assert x["exact_partition_rule"]["coordinate_alias_resolution_allowed"] == (
        "Lat_centroid and Long_centroid preaudit intents map only to the observed "
        "exact headers Latitude_centroid and Longitude_centroid"
    )


def test_firewall_is_bound_to_successful_header_audit_provenance():
    x = load()
    source = x["source_header_audit"]
    assert source["workflow_run_id"] == 36523712323
    assert source["workflow_head_sha"] == (
        "94eb91ea5dc33e3ff50538ae52b3916b49cb9176"
    )
    assert source["artifact_id"] == 11013841173
    assert source["artifact_digest"] == (
        "sha256:38a5db3dc16ed9a225409fe3746fd8a5f1f77f73944b96f7c767fc8cf7c7f2ea"
    )
    assert source["header_audit_json_sha256"] == (
        "7e763886ed41ad7a148f2ac995d1017a14123719bf8fb5ec216ec03831dc18fc"
    )
    assert source["sheet_name"] == "table_s1"
    assert source["header_sha256"] == (
        "cc1803dfde02370aea850b588b99944de7ac34d1b0311c4d60a6826ed8bfaa65"
    )
    assert source["appendix2_data_rows_semantically_opened"] == 0
    assert source["appendix2_data_cell_values_decoded"] == 0


def test_safe_projection_is_authorized_only_after_firewall_commit_and_not_fresh():
    x = load()
    boundary = x["row_access_boundary"]
    assert boundary[
        "safe_row_projection_authorized_after_this_firewall_is_committed"
    ] is True
    assert boundary["closed_unneeded_row_values_authorized"] is False
    assert boundary["protected_response_derived_row_values_authorized"] is False
    assert boundary["response_file_access_authorized"] is False
    assert boundary["appendix2_data_rows_semantically_opened_in_v1_22"] == 0
    assert boundary["biological_response_values_opened_in_v1_22"] is False

    fresh = x["freshness_boundary"]
    assert fresh["original_global_mammal_fresh_chain_closed_by_v1_20"] is True
    assert fresh["v1_22_does_not_restore_freshness"] is True
    assert fresh["counts_as_fresh_confirmation"] is False
    assert fresh["fresh_system_denominator_contribution"] == 0
    assert fresh["quarantine_reentry_authorized"] is False
