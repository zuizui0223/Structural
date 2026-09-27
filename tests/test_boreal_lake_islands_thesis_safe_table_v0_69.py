from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
TABLE=ROOT/"development/boreal_lake_islands_thesis_safe_table_v0_69.json"
STATUS=ROOT/"development/current_status_v0_69.json"
PRIORITY=ROOT/"development/structural_active_priority_v0_69.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_thesis_safe_table_is_38_rows_and_unique():
    x=load(TABLE)
    assert x["status"]=="partial_independent_response_free_safe_table_38_of_42"
    assert x["row_count"]==38
    assert x["unique_island_count"]==38
    codes=[r["island"] for r in x["rows"]]
    assert len(codes)==len(set(codes))==38


def test_full_current_island_universe_is_exactly_42():
    x=load(TABLE)
    u=x["current_study_island_universe"]

    assert u["status"]=="response_independent_42_of_42_island_codes_resolved"
    assert u["count"]==42
    assert len(u["codes"])==len(set(u["codes"]))==42
    assert u["provenance"]["additional_current_codes_not_in_thesis_table"]==[
        "SR","TB","WD","WF"
    ]
    assert set(r["island"] for r in x["rows"]).isdisjoint({"SR","TB","WD","WF"})


def test_richness_values_are_not_persisted():
    x=load(TABLE)
    persisted=set(x["rows"][0])
    assert persisted=={
        "island","area_ha","distance_to_mainland_km",
        "tsf_2020_years","fire_history_source"
    }
    forbidden=x["source"]["response_derived_fields_present_in_source_but_not_persisted"]
    assert forbidden==["S beetles","S plants","S birds"]


def test_safe_attribute_and_coordinate_gaps_are_explicit():
    x=load(TABLE)
    c=x["completeness"]

    assert c["island_identity"]=={"resolved":42,"total":42}
    assert c["area_ha"]=={"resolved":38,"total":42}
    assert c["distance_to_mainland_km"]=={"resolved":38,"total":42}
    assert c["tsf_2020_years"]=={"resolved":38,"total":42}
    assert c["latitude"]=={"resolved":0,"total":42}
    assert c["longitude"]=={"resolved":0,"total":42}
    assert x["source_article_population"]["additional_safe_attribute_rows_unresolved"]==[
        "SR","TB","WD","WF"
    ]


def test_no_value_is_inferred_for_missing_current_islands():
    x=load(TABLE)
    text="\n".join(x["reconciliation_notes"])
    assert "must not be guessed" in text
    assert "eyeballing the map" in text


def test_biological_response_remains_sealed():
    x=load(TABLE)
    fw=x["biological_response_firewall"]

    assert fw["beetle_matrix_opened"] is False
    assert fw["bird_matrix_opened"] is False
    assert fw["plant_matrix_opened"] is False
    assert fw["richness_values_from_thesis_persisted"] is False
    assert fw["v0_11_intake_authorized"] is False
    assert fw["pilot_response_authorized"] is False
    assert fw["confirmatory_response_authorized"] is False


def test_v069_status_keeps_fresh_denominator_zero():
    s=load(STATUS)
    p=load(PRIORITY)

    assert s["fresh_empirical_state"]["active_candidates"]==[]
    assert s["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    assert s["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0
    boreal=s["boreal_lake_island_preintake"]
    assert boreal["island_codes_resolved"]==42
    assert boreal["safe_area_distance_tsf_resolved"]==38
    assert boreal["latlong_resolved"]==0
    assert boreal["biological_response_opened"] is False
    assert boreal["v0_11_intake_authorized"] is False
    assert p["fresh_active_empirical_candidate"] is None
    assert p["fresh_confirmatory_eligible_count"]==0
