from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

from scripts.build_boreal_prepilot_contracts_v0_80 import build as build_v080
from scripts.build_boreal_v012_intake_v0_79 import build_intake as build_v079
from scripts.freeze_boreal_dual_isolation_operator_v0_83 import freeze as freeze_v083
from scripts.freeze_boreal_habitat_reference_v0_76 import (
    run as run_v076,
)
from scripts.freeze_boreal_spatial_partition_v0_75 import (
    run as run_v075,
)
from scripts.validate_independent_system_intake_v0_12 import (
    canonical_fingerprint,
    validate_intake_v0_12,
)
from scripts.verify_boreal_stage_b_bundle_v0_89 import (
    BorealStageBBundleError,
    sha256_file,
    verify_bundle,
)
from structural.boreal_habitat_reference import population_mean_sd


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/boreal_stage_b_bundle_verifier_contract_v0_89.json"
WORKFLOW = ROOT / ".github/workflows/boreal-lake-islands-stage-b-v0_89.yml"
STATUS = ROOT / "development/current_status_v0_89.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_89.json"

V072 = ROOT / "development/boreal_lake_islands_exact_transport_contract_v0_72.json"
V075 = ROOT / "development/boreal_lake_islands_spatial_partition_contract_v0_75.json"
V076 = ROOT / "development/boreal_lake_islands_habitat_reference_contract_v0_76.json"
V083 = ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"
V079 = ROOT / "development/boreal_lake_islands_v012_intake_builder_contract_v0_79.json"
V080 = ROOT / "development/boreal_lake_islands_prepilot_contract_builder_v0_80.json"
PREINTAKE = ROOT / "development/boreal_lake_islands_preintake_v0_65.json"
METADATA = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
UNIVERSE = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def geometry_fixture(universe: tuple[str, ...]) -> str:
    assert len(universe) == 42
    lines = ["Island,Lat,Long"]
    for i in range(21):
        lat = -40.0 + i * 4.0
        for j, island in enumerate(universe[2 * i : 2 * i + 2]):
            lon = 0.005 * j
            lines.append(
                f"{island},{float(lat).hex()},{float(lon).hex()}"
            )
    return "\n".join(lines) + "\n"


def habitat_fixture(universe: tuple[str, ...]) -> tuple[str, dict]:
    values = [float(i + 1) for i in range(len(universe))]
    mean, sd = population_mean_sd(values)
    lines = ["Island,Basal.area"]
    for island, value in zip(universe, values):
        lines.append(f"{island},{value.hex()}")
    text = "\n".join(lines) + "\n"
    constants = {
        "Basal.area": {
            "mean_hex": float(mean).hex(),
            "population_sd_hex": float(sd).hex(),
            "n": len(universe),
        }
    }
    return text, constants


def make_bundle(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    contract = load(CONTRACT)
    v072 = load(V072)
    v075 = load(V075)
    v076 = load(V076)
    v083 = load(V083)
    v079 = load(V079)
    v080 = load(V080)
    preintake = load(PREINTAKE)
    metadata = load(METADATA)
    universe = tuple(load(UNIVERSE)["current_study_island_universe"]["codes"])
    candidate = contract["candidate_id"]

    geometry_text = geometry_fixture(universe)
    habitat_text, constants = habitat_fixture(universe)
    (root / "safe_geometry.csv").write_text(geometry_text, encoding="utf-8")
    (root / "safe_habitat.csv").write_text(habitat_text, encoding="utf-8")

    projection = {
        "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
        "status": "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED",
        "candidate_id": candidate,
        "geometry": {
            "row_count": 42,
            "unique_island_count": 42,
            "sha256": sha_text(geometry_text),
            "coordinate_encoding": "python_float_hex",
        },
        "habitat": {
            "row_count": 42,
            "eligible_columns": ["Basal.area"],
            "incomplete_columns": [],
            "zero_variance_columns": [],
            "standardization_constants": constants,
            "reference_mode": "single_population_z_variable",
            "pca_required": False,
            "sha256": sha_text(habitat_text),
            "value_encoding": "python_float_hex",
        },
        "protected_response_values_opened": False,
        "unclassified_values_returned": False,
        "counts_as_empirical_evidence": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": "synthetic-test",
    }
    write_json(root / "projection_receipt.json", projection)

    spatial = run_v075(
        root / "safe_geometry.csv",
        projection,
        contract=v075,
        universe=universe,
    )
    assert spatial["spatial_block_count"] >= 9
    assert spatial["pilot_block_count"] >= 3
    assert spatial["confirmatory_block_count"] >= 6
    write_json(root / "spatial_receipt.json", spatial)

    habitat_full = run_v076(
        root / "safe_habitat.csv",
        projection,
        contract=v076,
        universe=universe,
    )
    reference_text = habitat_full.pop("reference_csv")
    (root / "habitat_reference.csv").write_text(
        reference_text,
        encoding="utf-8",
    )
    write_json(root / "habitat_receipt.json", habitat_full)

    operator, operator_receipt = freeze_v083(
        root / "safe_geometry.csv",
        projection,
        spatial,
        spatial_receipt_sha256=sha256_file(root / "spatial_receipt.json"),
        contract=v083,
    )
    assert operator_receipt["cross_v075_block_edge_count"] >= 1
    write_json(root / "source_operator.json", operator)
    write_json(root / "source_operator_receipt.json", operator_receipt)

    receipt_paths = {
        "safe_projection_v0_74": root / "projection_receipt.json",
        "spatial_partition_v0_75": root / "spatial_receipt.json",
        "habitat_reference_v0_76": root / "habitat_receipt.json",
    }
    intake = build_v079(
        projection,
        spatial,
        habitat_full,
        contract=v079,
        preintake=preintake,
        metadata=metadata,
        receipt_sha256={
            key: sha256_file(path)
            for key, path in receipt_paths.items()
        },
    )
    write_json(root / "v012_intake.json", intake)
    code, intake_receipt = validate_intake_v0_12(intake)
    assert code == 0
    intake_receipt["builder_schema"] = (
        "structural.boreal_v012_intake_builder_result.v0_79"
    )
    intake_receipt["generated_intake_fingerprint"] = canonical_fingerprint(
        intake
    )
    intake_receipt["counts_as_empirical_evidence"] = False
    write_json(root / "v012_intake_receipt.json", intake_receipt)

    protocol, quality, prepilot = build_v080(
        intake,
        intake_receipt,
        spatial,
        spatial_receipt_sha256=sha256_file(root / "spatial_receipt.json"),
        contract=v080,
    )
    write_json(root / "v031_protocol.json", protocol)
    write_json(root / "v042_quality_contract.json", quality)
    write_json(root / "prepilot_receipt.json", prepilot)

    stage_a_sha = "a" * 40
    header_manifest = {
        "schema": "structural.boreal_lake_islands_header_manifest_freeze.v0_74",
        "status": "header_manifests_frozen_before_row_projection",
        "stage_a_execution": {
            "head_sha": stage_a_sha,
        },
        "safe_row_projection_authorized": True,
        "row_values_opened_by_freezer": 0,
        "biological_response_values_opened_by_freezer": False,
        "counts_as_empirical_evidence": False,
        "v0_12_intake_authorized": False,
    }
    header_manifest_sha = "f" * 64
    context_req = contract["execution_context"]
    context = {
        "schema": context_req["schema"],
        "status": context_req["status"],
        "repository": context_req["repository"],
        "head_sha": "b" * 40,
        "ref": context_req["ref"],
        "run_id": 123,
        "run_attempt": 1,
        "workflow": "Boreal lake islands Stage B v0.89",
        "workflow_ref": context_req["workflow_ref"],
        "stage_a_head_sha": stage_a_sha,
        "header_manifest_sha256": header_manifest_sha,
        "biological_response_values_opened": False,
        "counts_as_empirical_evidence": False,
    }
    write_json(root / "execution_context.json", context)

    token = {
        "schema": "structural.dryad_token_prepare_result.v0_73",
        "status": "token_installed_in_runner_environment",
        "mode": "client_credentials_minted_token",
        "expires_in_seconds": 36000,
        "token_persisted_in_receipt": False,
        "client_credentials_persisted_in_receipt": False,
        "counts_as_empirical_evidence": False,
    }
    write_json(root / "token_receipt.json", token)

    transport_files = {}
    for name, target in v072["targets"].items():
        transport_files[name] = {
            "file_id": target["dryad_file_id"],
            "size_bytes": target["expected_size_bytes"],
            "sha256": target["expected_sha256"],
            "transport": "downloaded_and_verified",
        }
    transport = {
        "schema": "structural.boreal_lake_islands_exact_transport_result.v0_72",
        "status": "exact_mixed_file_bytes_verified",
        "candidate_id": candidate,
        "files": transport_files,
        "header_decoded": False,
        "data_rows_semantically_opened": 0,
        "safe_row_values_opened": False,
        "biological_response_values_opened": False,
        "model_fit_count": 0,
        "counts_as_empirical_evidence": False,
        "safe_row_projection_authorized": False,
        "v0_11_intake_authorized": False,
        "next_action": "synthetic-test",
    }
    write_json(root / "transport_receipt.json", transport)

    return {
        "root": root,
        "contract": contract,
        "header_manifest": header_manifest,
        "header_manifest_sha": header_manifest_sha,
        "v072": v072,
        "v075": v075,
        "v076": v076,
        "v083": v083,
        "v079": v079,
        "v080": v080,
        "preintake": preintake,
        "metadata": metadata,
    }


def verify(world):
    return verify_bundle(
        world["root"],
        contract=world["contract"],
        header_manifest=world["header_manifest"],
        header_manifest_sha256=world["header_manifest_sha"],
        v072=world["v072"],
        v075=world["v075"],
        v076=world["v076"],
        v083=world["v083"],
        v079=world["v079"],
        v080=world["v080"],
        preintake=world["preintake"],
        metadata=world["metadata"],
    )


def test_complete_stage_b_bundle_exact_replays(tmp_path: Path):
    world = make_bundle(tmp_path)
    result = verify(world)

    assert result["status"] == "VERIFIED_RESPONSE_INDEPENDENT_PREPILOT_BUNDLE"
    assert result[
        "eligible_to_commit_response_independent_prepilot_bundle"
    ] is True
    assert result["biological_response_values_opened"] is False
    assert result["pilot_response_authorized"] is False
    assert result["confirmatory_response_authorized"] is False
    assert result["counts_as_empirical_evidence"] is False
    assert result["fresh_system_denominator_contribution"] == 0
    assert all(result["exact_replay"].values())
    assert len(result["artifact_sha256"]) == 16
    assert len(result["bundle_fingerprint"]) == 64


def test_tampered_spatial_receipt_is_rejected(tmp_path: Path):
    world = make_bundle(tmp_path)
    path = world["root"] / "spatial_receipt.json"
    x = load(path)
    x["selected_radius_km"] = float(x["selected_radius_km"]) + 0.1
    write_json(path, x)

    with pytest.raises(
        BorealStageBBundleError,
        match="spatial receipt does not exact-replay",
    ):
        verify(world)


def test_tampered_prepilot_contract_is_rejected(tmp_path: Path):
    world = make_bundle(tmp_path)
    path = world["root"] / "v042_quality_contract.json"
    x = load(path)
    x["minimum_response_qualified_blocks"] += 1
    write_json(path, x)

    with pytest.raises(
        BorealStageBBundleError,
        match="v0.42 quality contract does not exact-replay",
    ):
        verify(world)


def test_extra_artifact_file_is_rejected(tmp_path: Path):
    world = make_bundle(tmp_path)
    (world["root"] / "unexpected.txt").write_text(
        "nope",
        encoding="utf-8",
    )
    with pytest.raises(
        BorealStageBBundleError,
        match="file surface mismatch",
    ):
        verify(world)


def test_v089_workflow_runs_verifier_before_upload_and_has_no_response_access():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "\n  pull_request:" not in text
    assert 'test "$GITHUB_REF" = "refs/heads/main"' in text
    assert "persist-credentials: false" in text
    assert "fetch-depth: 0" in text
    assert "workflow_ref" in text
    verify_pos = text.index("verify_boreal_stage_b_bundle_v0_89.py")
    upload_pos = text.index("Upload exact-replay verified Stage-B bundle")
    assert verify_pos < upload_pos
    assert "bundle_receipt.json" in text[upload_pos:]

    for forbidden in (
        "fetch_boreal_beetle_response_v0_82.py",
        "run_boreal_beetle_pilot_v0_84.py",
        "authorize_boreal_beetle_pilot_response_v0_81.py",
        "authorize_boreal_confirmatory_response_v0_86.py",
        "run_boreal_confirmatory_scoring_v0_87.py",
    ):
        assert forbidden not in text


def test_v089_contract_and_status_keep_zero_fresh_evidence():
    contract = load(CONTRACT)
    out = contract["output"]
    assert out["pilot_response_authorized"] is False
    assert out["confirmatory_response_authorized"] is False
    assert out["counts_as_empirical_evidence"] is False
    assert out["fresh_system_denominator_contribution"] == 0

    status = load(STATUS)
    priority = load(PRIORITY)
    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["stage_B_workflow_executed"] is False
    assert boreal["stage_B_bundle_verified"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["pilot_response_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
