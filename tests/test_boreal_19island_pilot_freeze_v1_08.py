from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "development/boreal_19island_pilot_freeze_request_v1_08.json"
WORKFLOW = ROOT / ".github/workflows/boreal-19island-pilot-freeze-v1_08.yml"


def test_v108_request_freezes_exact_successful_pilot_artifact():
    x = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert x["source_execution"] == {
        "workflow_run_id": 36446410357,
        "workflow_head_sha": "3123b481ca294be184a3a3e0991e8021baef1b3c",
        "artifact_id": 10980668029,
        "artifact_name": (
            "boreal-v107-burned-pilot-"
            "3123b481ca294be184a3a3e0991e8021baef1b3c-36446410357"
        ),
        "artifact_digest": (
            "sha256:5c7b09cd16151a1d481d3e7fbfb7aff8b47889d46f1713a7298bf6c806b5e57e"
        ),
    }
    assert x["file_sha256"]["execution_receipt.json"] == (
        "b332e65258a5c54fa9f49ab352f4c2822aff1d7fb17a90f9d5796aed4429951d"
    )
    assert x["file_sha256"]["training_snapshot.json"] == (
        "30ef15112fddf0c10cd159f484bf98293083932ba6343d65bcbd060881a91cef"
    )
    p = x["expected_pilot_result"]
    assert p["pilot_species_universe_count"] == 99
    assert p["applicable_rows"] == 594
    assert p["positive"] == 373
    assert p["negative"] == 221
    assert p["estimable_blocks"] == 3
    assert p["response_qualified_blocks"] == 3
    assert p["quality_retention_fraction"] == 1.0
    assert p["confirmatory_target_values_parsed"] == 0
    assert p["excluded_target_values_parsed"] == 0
    assert x["response_boundary"]["raw_response_may_be_persisted"] is False
    assert x["response_boundary"]["counts_as_empirical_evidence"] is False
    assert x["response_boundary"]["predictive_denominator_contribution"] == 0


def test_v108_workflow_persists_only_snapshot_and_audit_json():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "artifact-ids: 10980668029" in text
    assert "run-id: 36446410357" in text
    assert "merge-multiple: true" in text
    assert (
        "- .github/workflows/boreal-19island-pilot-freeze-v1_08.yml"
        in text
    )
    assert "assert not any(root.rglob(\"*.csv\"))" in text
    assert "boreal_19island_pilot_execution_v1_08.json" in text
    assert "boreal_19island_pilot_training_snapshot_v1_08.json" in text
    assert "boreal_19island_pilot_freeze_v1_08.json" in text
    assert "raw_response_may_be_persisted" not in text.split(
        "Commit exact pilot freeze to main", 1
    )[1]
    assert "permissions:\n  actions: read\n  contents: write" in text
