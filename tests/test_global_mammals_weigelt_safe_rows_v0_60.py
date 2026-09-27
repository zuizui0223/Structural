from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"development/global_mammals_weigelt_safe_rows_result_v0_60.json"
STATUS=ROOT/"development/current_status_v0_60.json"
PRIORITY=ROOT/"development/structural_active_priority_v0_60.json"

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def test_v060_safe_table_identity_and_response_ceiling():
    x=load(RESULT)
    assert x["status"]=="safe_islanddata_rows_extracted"
    assert x["output"]["row_count"]==17883
    assert x["output"]["distinct_id_count"]==17883
    assert x["output"]["safe_column_count"]==23
    assert x["output"]["csv_sha256"]=="ebb4b54cc9b056a1ea61fcae3a53bf578c0e47488e4a496d40fceaeca4f4b8af"
    assert x["evidence_boundary"]["forbidden_columns_opened"]==0
    assert x["evidence_boundary"]["geometry_values_opened"]==0
    assert x["evidence_boundary"]["mammal_response_requests"]==0
    assert x["evidence_boundary"]["mammal_response_values_opened"] is False

def test_core_external_isolation_fields_are_complete():
    x=load(RESULT)
    null=x["null_counts"]
    for field in [
        "id","countryiso","country","area","dist","slmp","gmmc","elev",
        "temp","vart","ccvt","prec","varp"
    ]:
        assert null[field]==0
    assert null["archip"]==6587
    assert null["name_long"]==6337
    assert null["name_lat"]==6337

def test_v060_status_keeps_response_sealed_and_denominator_zero():
    x=load(STATUS)
    hold=x["pristine_global_mammal_hold"]
    assert x["fresh_empirical_state"]["active_candidates"]==[]
    assert x["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    assert hold["raw_presence_absence_response_opened"] is False
    assert hold["response_occurrence_values_opened"]==0
    assert hold["core_external_reference_complete"] is True
    assert hold["archipelago_complete"] is False
    assert hold["coordinates_complete"] is False

def test_v060_priority_allows_only_ID_crosswalk_next():
    p=load(PRIORITY)
    assert p["status"]=="pristine_global_mammal_safe_geography_ready_ID_crosswalk_next"
    assert p["pristine_hold"]["response_opened"] is False
    assert p["pristine_hold"]["next_gate"]=="ID-only crosswalk"
    prohibited="\n".join(p["prohibited"])
    assert "species occurrence value" in prohibited
    assert "fuzzy/name/coordinate matching" in prohibited
