from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
TABLE=ROOT/"development/boreal_lake_islands_thesis_safe_table_v0_69.json"
STATUS=ROOT/"development/current_status_v0_69.json"
PRIORITY=ROOT/"development/structural_active_priority_v0_69.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_thesis_safe_table_is_42_rows_and_unique():
    x=load(TABLE)
    assert x["status"]=="complete_independent_response_free_core_external_table_42_of_42"
    assert x["row_count"]==42
    assert x["unique_island_count"]==42
    codes=[r["island"] for r in x["rows"]]
    assert len(codes)==len(set(codes))==42


def test_full_current_island_universe_is_exactly_42():
    x=load(TABLE)
    u=x["current_study_island_universe"]

    assert u["status"]=="response_independent_42_of_42_island_codes_and_core_external_attributes_resolved"
    assert u["count"]==42
    assert len(u["codes"])==len(set(u["codes"]))==42
    assert u["provenance"]["additional_current_codes_not_in_thesis_table"]==[]
    rows={r["island"]:r for r in x["rows"]}
    assert rows["SR"]=={
        "island":"SR","area_ha":1.9,"distance_to_mainland_km":0.54,
        "tsf_2020_years":83,"fire_history_source":"Dendro"
    }
    assert rows["TB"]=={
        "island":"TB","area_ha":19.5,"distance_to_mainland_km":6.63,
        "tsf_2020_years":82,"fire_history_source":"Dendro"
    }
    assert rows["WD"]=={
        "island":"WD","area_ha":52.7,"distance_to_mainland_km":0.08,
        "tsf_2020_years":5,"fire_history_source":"Landsat"
    }
    assert rows["WF"]=={
        "island":"WF","area_ha":49.8,"distance_to_mainland_km":0.64,
        "tsf_2020_years":5,"fire_history_source":"Landsat"
    }


def test_richness_values_are_not_persisted():
    x=load(TABLE)
    persisted=set(x["rows"][0])
    assert persisted=={
        "island","area_ha","distance_to_mainland_km",
        "tsf_2020_years","fire_history_source"
    }
    forbidden=x["source"]["response_derived_fields_present_in_source_but_not_persisted"]
    assert forbidden==["S beetles","S plants","S birds"]


def test_core_external_attributes_are_complete_but_coordinates_remain_unresolved():
    x=load(TABLE)
    c=x["completeness"]

    assert c["island_identity"]=={"resolved":42,"total":42}
    assert c["area_ha"]=={"resolved":42,"total":42}
    assert c["distance_to_mainland_km"]=={"resolved":42,"total":42}
    assert c["tsf_2020_years"]=={"resolved":42,"total":42}
    assert c["latitude"]=={"resolved":0,"total":42}
    assert c["longitude"]=={"resolved":0,"total":42}
    assert x["source_article_population"]["additional_safe_attribute_rows_unresolved"]==[]


def test_no_coordinates_are_inferred_from_map():
    x=load(TABLE)
    text="\n".join(x["reconciliation_notes"])
    assert "must not be estimated by eyeballing" in text
    assert x["completeness"]["latitude"]=={"resolved":0,"total":42}
    assert x["completeness"]["longitude"]=={"resolved":0,"total":42}


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
    assert boreal["safe_area_distance_tsf_resolved"]==42
    assert boreal["core_external_reference_complete"] is True
    assert boreal["latlong_resolved"]==0
    assert boreal["biological_response_opened"] is False
    assert boreal["v0_11_intake_authorized"] is False
    assert p["fresh_active_empirical_candidate"] is None
    assert p["fresh_confirmatory_eligible_count"]==0


def test_core_external_reference_uses_direct_mainland_distance():
    x=load(TABLE)
    ref=x["prospective_core_external_reference"]

    assert ref["status"]=="frozen_before_any_biological_response_access"
    assert ref["raw_fields"]==[
        "area_ha","distance_to_mainland_km","tsf_2020_years"
    ]
    assert ref["transformations"]["log_area"]=="log10(area_ha + 1)"
    assert ref["transformations"]["log_mainland_distance"]==(
        "log1p(distance_to_mainland_km)"
    )
    assert ref["replaces_unavailable_buffer5000_as_required_external_isolation"] is True
    assert ref["biological_response_used"] is False


def test_full_safe_ranges_include_all_42_islands():
    x=load(TABLE)

    assert x["observed_safe_ranges_42"]=={
        "area_ha":[1,350.4],
        "distance_to_mainland_km":[0.02,7.9],
        "tsf_2020_years":[1,231],
    }
