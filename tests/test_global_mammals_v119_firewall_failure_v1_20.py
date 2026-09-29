from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "development/global_mammals_v119_firewall_failure_freeze_v1_20.json"
REQUEST = ROOT / "development/global_mammals_v119_cleanup_request_v1_20.json"
WORKFLOW = ROOT / ".github/workflows/global-mammals-v119-cleanup-v1_20.yml"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v119_failure_is_recorded_as_real_response_firewall_violation():
    x = load(FREEZE)
    assert x["status"] == "TERMINAL_RESPONSE_FIREWALL_VIOLATION_V119"
    exposure = x["actual_semantic_exposure"]
    assert exposure["v1_19_receipt_semantic_flags_are_superseded"] is True
    assert exposure["header_record_utf8_decoded_as_one_wrongly_delimited_field"] is True
    assert exposure["species_header_record_semantics_opened_in_runner_memory"] is True
    assert exposure["data_rows_utf8_decoded_before_failure"] == 1
    assert exposure["exposed_source_local_row_id"] == "1"
    assert exposure["exposed_data_record_field_count"] == 5395
    assert exposure["exposed_occurrence_value_count"] == 5394
    assert exposure["exposed_occurrence_values_all_binary_0_1"] is True
    assert exposure["second_or_later_data_row_semantically_decoded"] is False
    assert exposure["biological_response_values_opened"] is True


def test_original_global_mammal_fresh_chain_is_closed_not_rescued():
    x = load(FREEZE)
    f = x["freshness_consequence"]
    assert f["original_global_mammal_chain_remains_pristine"] is False
    assert f["fresh_confirmation_authorized_under_v0_1_through_v1_19"] is False
    assert f["fresh_system_denominator_contribution"] == 0
    assert f["rerun_v1_19_authorized"] is False
    assert f["quarantine_based_fresh_reentry_authorized_now"] is False
    assert f["contaminated_macro_analysis_may_be_designed_separately"] is True


def test_safe_next_route_uses_appendix2_local_id_not_weigelt_id():
    x = load(FREEZE)
    cause = x["failure_cause"]
    assert cause["predeclared_routing_namespace"] == "Weigelt islanddata id"
    assert cause["correct_source_documented_routing_namespace"] == (
        "Appendix 2 ID matched to Appendix 1 row names"
    )
    assert cause["direct_Weigelt_id_join_is_valid"] is False
    route = x["safe_next_route"]
    assert route["response_file_may_be_reopened_now"] is False
    assert route["appendix2_dryad_file_id"] == 3242157
    assert route["appendix2_expected_size_bytes"] == 1066391
    assert route["appendix2_expected_sha256"] == (
        "fdcfc92bfa67e1ccf4d468fe2c7222bcb5919a1bce56d272b19d42525c234960"
    )
    assert route["routing_key"] == "Appendix 2 ID"


def test_cleanup_request_and_workflow_target_only_sensitive_outputs():
    req = load(REQUEST)
    assert req["workflow_run_id"] == 36522032421
    assert req["artifact_id"] == 11013611460
    assert req["preserve_run_metadata"] is True
    assert req["response_reaccess_authorized"] is False
    assert req["v1_19_rerun_authorized"] is False

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "/actions/runs/36522032421/logs" in text
    assert "/actions/artifacts/11013611460" in text
    assert 'method="DELETE"' in text
    assert "DELETE run metadata" not in text
