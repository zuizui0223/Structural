from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
HOLD=ROOT/"development/global_mammals_transport_hold_v0_64.json"
STATUS=ROOT/"development/current_status_v0_64.json"
PRIORITY=ROOT/"development/structural_active_priority_v0_64.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_transport_hold_preserves_pristine_response():
    x=load(HOLD)

    assert x["status"] == (
        "HOLD_exact_response_bytes_transport_blocked_after_final_pre_response_retry"
    )
    ev=x["evidence_boundary"]
    assert ev["response_bytes_read_across_transport_attempts"]==0
    assert ev["routing_ids_decoded_across_transport_attempts"]==0
    assert ev["species_headers_decoded_across_transport_attempts"]==0
    assert ev["occurrence_values_decoded_across_transport_attempts"]==0
    assert x["response_identity"]["biological_response_values_opened"] is False


def test_all_three_transport_attempts_stopped_before_bytes():
    x=load(HOLD)
    attempts=x["transport_attempts"]

    assert [a["version"] for a in attempts]==["v0.61","v0.62","v0.63"]
    assert [a["result"] for a in attempts]==[
        "HTTP_401_before_response_bytes",
        "HTTP_403_before_response_bytes",
        "HTTP_403_before_response_bytes",
    ]
    assert all(a["response_bytes_read"]==0 for a in attempts)
    assert all(a["routing_ids_decoded"]==0 for a in attempts)


def test_crosswalk_semantics_remain_frozen_despite_transport_failure():
    x=load(HOLD)
    c=x["frozen_id_crosswalk_semantics"]

    assert c["expected_data_records"]==5592
    assert c["species_header_fields_semantically_opened"]==0
    assert c["species_occurrence_cells_semantically_opened"]==0
    assert c["join_target"]=="Weigelt safe CSV id"
    assert c["join_rule"]=="exact canonical-ID membership only"
    assert "island-name fuzzy matching" in c["forbidden_fallbacks"]


def test_resume_requires_exact_frozen_bytes_and_no_more_dryad_retries():
    x=load(HOLD)
    rule=x["final_transport_rule"]

    assert rule["further_Dryad_endpoint_retries_authorized"] is False
    assert rule["alternate_exact_byte_source_may_resume"] is True
    joined="\n".join(rule["resume_only_if"])
    assert "60486843" in joined
    assert "32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6" in joined


def test_v064_keeps_fresh_denominator_zero_and_v055_untested():
    status=load(STATUS)
    priority=load(PRIORITY)

    assert status["fresh_empirical_state"]["active_candidates"]==[]
    assert status["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    assert status["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0
    assert status["next_generation_hypothesis"]["status"]=="frozen_untested"
    assert status["pristine_global_mammal_hold"]["mammal_response_bytes_read"]==0
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"]==0
    assert priority["pristine_hold"]["further_Dryad_transport_retries_authorized"] is False


def test_safe_geography_is_complete_even_though_response_transport_is_not():
    status=load(STATUS)
    hold=status["pristine_global_mammal_hold"]

    assert hold["safe_geography_complete"] is True
    assert hold["Weigelt_safe_rows"]==17883
    assert hold["core_external_reference_complete"] is True
    assert hold["routing_ids_decoded"]==0
