from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/boreal_stage_b_orchestrator_contract_v0_88.json"
WORKFLOW = ROOT / ".github/workflows/boreal-lake-islands-stage-b-v0_88.yml"
STATUS = ROOT / "development/current_status_v0_88.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_88.json"


def test_v088_contract_is_response_independent_and_main_bound():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert x["workflow_requirements"]["trigger"] == "workflow_dispatch_only"
    assert x["workflow_requirements"]["ref"] == "refs/heads/main"
    assert x["workflow_requirements"]["repository"] == "zuizui0223/Structural"
    assert x["workflow_requirements"]["canonical_manifest_must_be_git_tracked"] is True
    assert x["workflow_requirements"]["stage_a_head_must_be_ancestor_of_current_main"] is True
    ceiling = x["evidence_ceiling"]
    assert ceiling["biological_response_values_opened"] is False
    assert ceiling["pilot_response_authorized"] is False
    assert ceiling["confirmatory_response_authorized"] is False
    assert ceiling["counts_as_empirical_evidence"] is False
    assert ceiling["fresh_system_denominator_contribution"] == 0
    assert x["artifact_policy"]["raw_mixed_csv_upload_forbidden"] is True
    assert x["artifact_policy"]["biological_response_upload_forbidden"] is True


def test_workflow_runs_only_manually_on_main_and_binds_manifest_lineage():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "\n  pull_request:" not in text
    assert "\n  schedule:" not in text
    assert 'test "$GITHUB_REF" = "refs/heads/main"' in text
    assert "persist-credentials: false" in text
    assert "fetch-depth: 0" in text
    assert (
        'git ls-files --error-unmatch "$MANIFEST" >/dev/null'
        in text
    )
    assert "git", "merge-base", "--is-ancestor"" in text
    assert (
        "development/boreal_lake_islands_header_manifest_freeze_result.json"
        in text
    )


def test_workflow_chain_is_exactly_response_independent_and_ordered():
    text = WORKFLOW.read_text(encoding="utf-8")
    commands = [
        "fetch_boreal_mixed_files_v0_72.py",
        "project_boreal_safe_rows_v0_74.py",
        "freeze_boreal_spatial_partition_v0_75.py",
        "freeze_boreal_habitat_reference_v0_76.py",
        "freeze_boreal_dual_isolation_operator_v0_83.py",
        "build_boreal_v012_intake_v0_79.py",
        "build_boreal_prepilot_contracts_v0_80.py",
    ]
    positions = [text.index(command) for command in commands]
    assert positions == sorted(positions)

    forbidden = [
        "fetch_boreal_beetle_response_v0_82.py",
        "run_boreal_beetle_pilot_v0_82.py",
        "run_boreal_beetle_pilot_v0_84.py",
        "authorize_boreal_beetle_pilot_response_v0_81.py",
        "authorize_boreal_confirmatory_response_v0_86.py",
        "run_boreal_confirmatory_scoring_v0_87.py",
    ]
    for command in forbidden:
        assert command not in text


def test_workflow_deletes_raw_before_upload_and_uploads_allowlist_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    delete_pos = text.index("rm -rf build/boreal_v088/raw")
    upload_pos = text.index("Upload response-independent Stage-B bundle")
    assert delete_pos < upload_pos

    upload = text[upload_pos:]
    assert "build/boreal_v088/raw" not in upload
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    for filename in contract["artifact_policy"]["allowed_outputs"]:
        assert f"build/boreal_v088/{filename}" in upload
    assert "retention-days: 14" in upload


def test_stage_b_artifact_surface_contains_design_needed_afterward():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    outputs = set(x["artifact_policy"]["allowed_outputs"])
    assert {
        "safe_geometry.csv",
        "projection_receipt.json",
        "spatial_receipt.json",
        "habitat_reference.csv",
        "habitat_receipt.json",
        "source_operator.json",
        "source_operator_receipt.json",
        "v012_intake.json",
        "v012_intake_receipt.json",
        "v031_protocol.json",
        "v042_quality_contract.json",
        "prepilot_receipt.json",
    } <= outputs
    assert not any("beetle" in name and "response" in name for name in outputs)


def test_v088_status_keeps_fresh_denominator_zero_before_execution():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["canonical_header_manifest_committed"] is False
    assert boreal["stage_B_workflow_executed"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["pilot_response_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
