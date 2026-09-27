from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
FW=ROOT/"development/boreal_lake_islands_documented_column_firewall_v0_68.json"
STATUS=ROOT/"development/current_status_v0_68.json"
PRIORITY=ROOT/"development/structural_active_priority_v0_68.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v068_keeps_biological_response_sealed():
    x=load(FW)
    r=x["response_firewall"]

    assert x["status"]=="frozen_from_public_documentation_safe_row_values_unopened"
    assert r["safe_row_values_opened"] is False
    assert r["beetle_response_opened"] is False
    assert r["bird_response_opened"] is False
    assert r["plant_response_opened"] is False
    assert r["v0_11_intake_authorized"] is False
    assert r["pilot_response_authorized"] is False
    assert r["confirmatory_response_authorized"] is False


def test_required_geometry_and_external_reference_are_frozen():
    x=load(FW)
    req=x["primary_design_requirements"]

    assert req["routing_and_geometry_required"]==["Island","Lat","Long"]
    assert req["external_state_required"]==[
        "log10area","buffer5000","time.since.fire.beetles"
    ]


def test_response_derived_fields_are_forbidden():
    x=load(FW)
    alpha=x["files"]["alpha_diversity_ALL_islands.csv"]
    rda=x["files"]["RDA_environmental_variables.csv"]

    assert "beetle.richness" in alpha["forbidden_response_derived_columns"]
    assert "beetle.msom.richness" in alpha["forbidden_response_derived_columns"]
    assert "plant.richness" in rda["forbidden_response_derived_columns"]
    assert "Bird.abundance" in rda["forbidden_response_derived_columns"]
    assert "Beetle.catch.rate" in rda["forbidden_response_derived_columns"]


def test_response_selected_habitat_scales_are_not_auto_admissible():
    x=load(FW)
    alpha=x["files"]["alpha_diversity_ALL_islands.csv"]
    rule=x["primary_design_requirements"]["response_selected_habitat_scale_rule"]

    assert "buffer_1" in alpha["optional_documented_safe_columns"]
    assert "buffer_10" in alpha["optional_documented_safe_columns"]
    assert "selected those scales from species-richness slopes" in rule


def test_habitat_reference_selection_is_response_blind_and_fail_closed():
    x=load(FW)
    rule=x["primary_design_requirements"]["habitat_reference_rule"]

    assert "all 42 eligible islands" in rule["inclusion"]
    assert "no outcome-based subset selection" in rule["inclusion"]
    assert "80%" in rule["pca_rule"]
    assert rule["hard_stop"].startswith(
        "if no prospectively safe habitat-structure variable"
    )


def test_mechanical_header_verification_is_not_faked():
    x=load(FW)
    h=x["mechanical_header_verification"]

    assert h["completed"] is False
    assert h["safe_file_bytes_read"]==0
    assert h["biological_response_bytes_read"]==0
    assert "pre-response STOP" in h["rule"]


def test_v068_status_and_priority_keep_fresh_denominator_zero():
    status=load(STATUS)
    priority=load(PRIORITY)

    assert status["fresh_empirical_state"]["active_candidates"]==[]
    assert status["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    assert status["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0

    boreal=status["boreal_lake_island_preintake"]
    assert boreal["status"]=="HOLD_safe_row_values_and_coordinates_transport_unresolved"
    assert boreal["biological_response_opened"] is False
    assert boreal["v0_11_intake_authorized"] is False

    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"]==0
    assert priority["hypothesis_driven_preintake_candidate"]["response_opened"] is False


def test_no_further_blind_dryad_retry_is_authorized():
    x=load(FW)
    p=load(PRIORITY)

    assert x["transport_state"]["further_blind_Dryad_endpoint_retries_authorized"] is False
    prohibited="\n".join(p["prohibited"])
    assert "retry multiple Dryad file-content endpoints" in prohibited
    assert "open beetle, bird or plant community matrices" in prohibited
