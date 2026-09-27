from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/"development/global_mammals_reference_gpkg_schema_result_v0_58.json"
FIREWALL=ROOT/"development/global_mammals_weigelt_safe_column_firewall_v0_59.json"
STATUS=ROOT/"development/current_status_v0_59.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v058_schema_result_keeps_mammal_response_sealed():
    x=load(SCHEMA)
    assert x["status"]=="reference_gpkg_schema_only_complete"
    assert x["islanddata"]["row_count"]==17883
    assert x["islanddata"]["geometry_type"]=="POINT"
    assert x["islanddata"]["srs_id"]==4326
    assert x["schema_only_ceiling"]["row_values_semantically_opened"]==0
    assert x["schema_only_ceiling"]["geometry_values_opened"]==0
    assert x["schema_only_ceiling"]["mammal_response_requests"]==0
    assert x["schema_only_ceiling"]["mammal_response_values_opened"] is False


def test_v059_safe_columns_exist_and_forbidden_columns_are_disjoint():
    schema=load(SCHEMA)
    fw=load(FIREWALL)
    cols=set(schema["islanddata"]["columns"])
    safe=set(fw["safe_columns"])
    forbidden=set(fw["forbidden_columns"])

    assert safe <= cols
    assert forbidden <= cols
    assert safe.isdisjoint(forbidden)
    for required in [
        "id","archip","island","name_long","name_lat","area","dist",
        "slmp","gmmc","elev","temp","vart","ccvt","prec","varp"
    ]:
        assert required in safe


def test_biotic_and_ordination_columns_are_prospectively_forbidden():
    fw=load(FIREWALL)
    forbidden=set(fw["forbidden_columns"])

    for prefix in ("sr","pam","upgma","pca"):
        assert any(x.startswith(prefix) for x in forbidden)
    assert "geom" in forbidden
    assert "buffer" in forbidden
    assert "modeled_t" in forbidden
    assert fw["row_values_opened_so_far"]==0
    assert fw["mammal_response_opened"] is False


def test_v059_status_keeps_fresh_denominator_zero():
    x=load(STATUS)
    assert x["fresh_empirical_state"]["active_candidates"]==[]
    assert x["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    hold=x["pristine_global_mammal_hold"]
    assert hold["raw_presence_absence_response_opened"] is False
    assert hold["response_requests"]==0
    assert hold["islanddata_rows"]==17883
    assert hold["safe_island_id_column"]=="id"
