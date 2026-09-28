#!/usr/bin/env python3
"""Verify and cryptographically freeze a response-independent boreal Stage-B bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from scripts.build_boreal_prepilot_contracts_v0_80 import (
    build as build_v080,
)
from scripts.build_boreal_v012_intake_v0_79 import (
    build_intake as build_v079,
)
from scripts.freeze_boreal_dual_isolation_operator_v0_83 import (
    freeze as freeze_v083,
)
from scripts.freeze_boreal_habitat_reference_v0_76 import (
    load_universe as load_universe_v076,
    run as run_v076,
)
from scripts.freeze_boreal_spatial_partition_v0_75 import (
    load_universe as load_universe_v075,
    run as run_v075,
)
from scripts.validate_independent_system_intake_v0_12 import (
    canonical_fingerprint,
    validate_intake_v0_12,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_stage_b_bundle_verifier_contract_v0_89.json"
)
DEFAULT_HEADER_MANIFEST = (
    ROOT / "development/boreal_lake_islands_header_manifest_freeze_result.json"
)
DEFAULT_V072 = (
    ROOT / "development/boreal_lake_islands_exact_transport_contract_v0_72.json"
)
DEFAULT_V075 = (
    ROOT / "development/boreal_lake_islands_spatial_partition_contract_v0_75.json"
)
DEFAULT_V076 = (
    ROOT / "development/boreal_lake_islands_habitat_reference_contract_v0_76.json"
)
DEFAULT_V083 = (
    ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"
)
DEFAULT_V079 = (
    ROOT / "development/boreal_lake_islands_v012_intake_builder_contract_v0_79.json"
)
DEFAULT_V080 = (
    ROOT / "development/boreal_lake_islands_prepilot_contract_builder_v0_80.json"
)
DEFAULT_PREINTAKE = (
    ROOT / "development/boreal_lake_islands_preintake_v0_65.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class BorealStageBBundleError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealStageBBundleError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _require_false(mapping: Mapping, keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if mapping.get(key) is not False:
            raise BorealStageBBundleError(
                f"{label} boundary mismatch: {key}"
            )


def _verify_execution_context(
    context: Mapping,
    *,
    contract: Mapping,
    header_manifest: Mapping,
    header_manifest_sha256: str,
) -> None:
    req = contract["execution_context"]
    if context.get("schema") != req["schema"]:
        raise BorealStageBBundleError(
            "unexpected Stage-B execution-context schema"
        )
    if context.get("status") != req["status"]:
        raise BorealStageBBundleError(
            "Stage-B execution context did not qualify"
        )
    if context.get("repository") != req["repository"]:
        raise BorealStageBBundleError(
            "Stage-B repository identity mismatch"
        )
    if context.get("ref") != req["ref"]:
        raise BorealStageBBundleError(
            "Stage-B was not run from main"
        )
    if context.get("workflow_ref") != req["workflow_ref"]:
        raise BorealStageBBundleError(
            "Stage-B workflow identity mismatch"
        )
    head = context.get("head_sha")
    if not isinstance(head, str) or not SHA40.fullmatch(head):
        raise BorealStageBBundleError(
            "invalid Stage-B head SHA"
        )
    if not isinstance(context.get("run_id"), int) or context["run_id"] < 1:
        raise BorealStageBBundleError(
            "invalid Stage-B run ID"
        )
    if not isinstance(context.get("run_attempt"), int) or context["run_attempt"] < 1:
        raise BorealStageBBundleError(
            "invalid Stage-B run attempt"
        )
    if context.get("header_manifest_sha256") != header_manifest_sha256:
        raise BorealStageBBundleError(
            "canonical header-manifest SHA mismatch"
        )
    if context.get("stage_a_head_sha") != header_manifest.get(
        "stage_a_execution", {}
    ).get("head_sha"):
        raise BorealStageBBundleError(
            "Stage-A head binding mismatch"
        )
    _require_false(
        context,
        (
            "biological_response_values_opened",
            "counts_as_empirical_evidence",
        ),
        "Stage-B execution context",
    )


def _verify_transport(
    token: Mapping,
    transport: Mapping,
    *,
    v072: Mapping,
    candidate_id: str,
) -> None:
    if token.get("schema") != "structural.dryad_token_prepare_result.v0_73":
        raise BorealStageBBundleError(
            "unexpected token receipt schema"
        )
    if token.get("status") != "token_installed_in_runner_environment":
        raise BorealStageBBundleError(
            "token preparation did not qualify"
        )
    _require_false(
        token,
        (
            "token_persisted_in_receipt",
            "client_credentials_persisted_in_receipt",
            "counts_as_empirical_evidence",
        ),
        "token receipt",
    )

    if transport.get("schema") != (
        "structural.boreal_lake_islands_exact_transport_result.v0_72"
    ):
        raise BorealStageBBundleError(
            "unexpected transport receipt schema"
        )
    if transport.get("status") != "exact_mixed_file_bytes_verified":
        raise BorealStageBBundleError(
            "exact mixed-file transport did not qualify"
        )
    if transport.get("candidate_id") != candidate_id:
        raise BorealStageBBundleError(
            "transport candidate identity mismatch"
        )
    for key, expected in (
        ("header_decoded", False),
        ("data_rows_semantically_opened", 0),
        ("safe_row_values_opened", False),
        ("biological_response_values_opened", False),
        ("counts_as_empirical_evidence", False),
        ("safe_row_projection_authorized", False),
        ("v0_11_intake_authorized", False),
    ):
        if transport.get(key) != expected:
            raise BorealStageBBundleError(
                f"transport boundary mismatch: {key}"
            )
    files = transport.get("files")
    if not isinstance(files, dict):
        raise BorealStageBBundleError(
            "transport file evidence missing"
        )
    for name, target in v072["targets"].items():
        observed = files.get(name)
        if not isinstance(observed, dict):
            raise BorealStageBBundleError(
                f"transport evidence missing: {name}"
            )
        if observed.get("file_id") != target["dryad_file_id"]:
            raise BorealStageBBundleError(
                f"transport file ID mismatch: {name}"
            )
        if observed.get("size_bytes") != target["expected_size_bytes"]:
            raise BorealStageBBundleError(
                f"transport byte-size mismatch: {name}"
            )
        if observed.get("sha256") != target["expected_sha256"]:
            raise BorealStageBBundleError(
                f"transport SHA mismatch: {name}"
            )


def _verify_projection(
    root: Path,
    projection: Mapping,
    *,
    candidate_id: str,
) -> None:
    if projection.get("schema") != (
        "structural.boreal_lake_islands_safe_projection_result.v0_74"
    ):
        raise BorealStageBBundleError(
            "unexpected v0.74 projection receipt"
        )
    if projection.get("status") != (
        "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED"
    ):
        raise BorealStageBBundleError(
            "v0.74 safe projection did not qualify"
        )
    if projection.get("candidate_id") != candidate_id:
        raise BorealStageBBundleError(
            "v0.74 candidate identity mismatch"
        )
    _require_false(
        projection,
        (
            "protected_response_values_opened",
            "unclassified_values_returned",
            "counts_as_empirical_evidence",
            "v0_11_intake_authorized",
            "pilot_response_authorized",
            "confirmatory_response_authorized",
        ),
        "v0.74 projection",
    )

    geometry_text = (root / "safe_geometry.csv").read_text(encoding="utf-8")
    habitat_text = (root / "safe_habitat.csv").read_text(encoding="utf-8")
    geometry = projection.get("geometry")
    habitat = projection.get("habitat")
    if not isinstance(geometry, dict) or not isinstance(habitat, dict):
        raise BorealStageBBundleError(
            "v0.74 geometry/habitat metadata missing"
        )
    if geometry.get("row_count") != 42 or geometry.get(
        "unique_island_count"
    ) != 42:
        raise BorealStageBBundleError(
            "v0.74 geometry is not exact 42-island support"
        )
    if habitat.get("row_count") != 42:
        raise BorealStageBBundleError(
            "v0.74 habitat is not exact 42-island support"
        )
    if sha256_text(geometry_text) != geometry.get("sha256"):
        raise BorealStageBBundleError(
            "safe geometry SHA differs from v0.74 receipt"
        )
    if sha256_text(habitat_text) != habitat.get("sha256"):
        raise BorealStageBBundleError(
            "safe habitat SHA differs from v0.74 receipt"
        )


def verify_bundle(
    root: Path,
    *,
    contract: Mapping,
    header_manifest: Mapping,
    header_manifest_sha256: str,
    v072: Mapping,
    v075: Mapping,
    v076: Mapping,
    v083: Mapping,
    v079: Mapping,
    v080: Mapping,
    preintake: Mapping,
    metadata: Mapping,
) -> dict:
    expected = tuple(contract["required_input_files"])
    observed = tuple(sorted(
        p.name for p in root.iterdir()
        if p.is_file() and p.name != "bundle_receipt.json"
    ))
    if observed != tuple(sorted(expected)):
        raise BorealStageBBundleError(
            f"Stage-B file surface mismatch: {list(observed)}"
        )
    if (root / "raw").exists():
        raise BorealStageBBundleError(
            "raw mixed directory survived Stage B"
        )

    context = _load(root / "execution_context.json")
    token = _load(root / "token_receipt.json")
    transport = _load(root / "transport_receipt.json")
    projection = _load(root / "projection_receipt.json")
    spatial = _load(root / "spatial_receipt.json")
    habitat_receipt = _load(root / "habitat_receipt.json")
    operator = _load(root / "source_operator.json")
    operator_receipt = _load(root / "source_operator_receipt.json")
    intake = _load(root / "v012_intake.json")
    intake_receipt = _load(root / "v012_intake_receipt.json")
    protocol = _load(root / "v031_protocol.json")
    quality = _load(root / "v042_quality_contract.json")
    prepilot = _load(root / "prepilot_receipt.json")

    candidate = contract["candidate_id"]
    _verify_execution_context(
        context,
        contract=contract,
        header_manifest=header_manifest,
        header_manifest_sha256=header_manifest_sha256,
    )
    _verify_transport(
        token,
        transport,
        v072=v072,
        candidate_id=candidate,
    )
    _verify_projection(
        root,
        projection,
        candidate_id=candidate,
    )

    universe75 = load_universe_v075()
    replay_spatial = run_v075(
        root / "safe_geometry.csv",
        dict(projection),
        contract=dict(v075),
        universe=universe75,
    )
    if replay_spatial != dict(spatial):
        raise BorealStageBBundleError(
            "v0.75 spatial receipt does not exact-replay"
        )

    universe76 = load_universe_v076()
    replay_habitat_full = run_v076(
        root / "safe_habitat.csv",
        dict(projection),
        contract=dict(v076),
        universe=universe76,
    )
    replay_reference = replay_habitat_full.pop("reference_csv")
    actual_reference = (
        root / "habitat_reference.csv"
    ).read_text(encoding="utf-8")
    if replay_reference != actual_reference:
        raise BorealStageBBundleError(
            "v0.76 habitat reference does not exact-replay"
        )
    if replay_habitat_full != dict(habitat_receipt):
        raise BorealStageBBundleError(
            "v0.76 habitat receipt does not exact-replay"
        )

    spatial_sha = sha256_file(root / "spatial_receipt.json")
    replay_operator, replay_operator_receipt = freeze_v083(
        root / "safe_geometry.csv",
        dict(projection),
        dict(spatial),
        spatial_receipt_sha256=spatial_sha,
        contract=dict(v083),
    )
    if replay_operator != dict(operator):
        raise BorealStageBBundleError(
            "v0.83 source operator does not exact-replay"
        )
    if replay_operator_receipt != dict(operator_receipt):
        raise BorealStageBBundleError(
            "v0.83 operator receipt does not exact-replay"
        )

    receipt_paths = {
        "safe_projection_v0_74": root / "projection_receipt.json",
        "spatial_partition_v0_75": root / "spatial_receipt.json",
        "habitat_reference_v0_76": root / "habitat_receipt.json",
    }
    replay_intake = build_v079(
        dict(projection),
        dict(spatial),
        dict(habitat_receipt),
        contract=dict(v079),
        preintake=dict(preintake),
        metadata=dict(metadata),
        receipt_sha256={
            key: sha256_file(path)
            for key, path in receipt_paths.items()
        },
    )
    if replay_intake != dict(intake):
        raise BorealStageBBundleError(
            "v0.79 v0.12 intake does not exact-replay"
        )
    code, replay_intake_receipt = validate_intake_v0_12(
        dict(replay_intake)
    )
    if code != 0:
        raise BorealStageBBundleError(
            "replayed v0.12 intake failed generic validator"
        )
    replay_intake_receipt["builder_schema"] = (
        "structural.boreal_v012_intake_builder_result.v0_79"
    )
    replay_intake_receipt["generated_intake_fingerprint"] = (
        canonical_fingerprint(replay_intake)
    )
    replay_intake_receipt["counts_as_empirical_evidence"] = False
    if replay_intake_receipt != dict(intake_receipt):
        raise BorealStageBBundleError(
            "v0.79 intake validation receipt does not exact-replay"
        )

    replay_protocol, replay_quality, replay_prepilot = build_v080(
        dict(intake),
        dict(intake_receipt),
        dict(spatial),
        spatial_receipt_sha256=spatial_sha,
        contract=dict(v080),
    )
    if replay_protocol != dict(protocol):
        raise BorealStageBBundleError(
            "v0.80 v0.31 protocol does not exact-replay"
        )
    if replay_quality != dict(quality):
        raise BorealStageBBundleError(
            "v0.80 v0.42 quality contract does not exact-replay"
        )
    if replay_prepilot != dict(prepilot):
        raise BorealStageBBundleError(
            "v0.80 prepilot receipt does not exact-replay"
        )

    artifact_sha = {
        name: sha256_file(root / name)
        for name in expected
    }
    bundle_core = {
        "candidate_id": candidate,
        "stage_b_head_sha": context["head_sha"],
        "stage_b_run_id": context["run_id"],
        "stage_a_head_sha": context["stage_a_head_sha"],
        "header_manifest_sha256": header_manifest_sha256,
        "artifact_sha256": artifact_sha,
        "protocol_fingerprint": prepilot["protocol_fingerprint"],
        "quality_contract_fingerprint": prepilot[
            "quality_contract_fingerprint"
        ],
        "intake_fingerprint": prepilot["parent_intake_fingerprint"],
        "source_operator_fingerprint": operator_receipt[
            "operator_fingerprint"
        ],
    }
    return {
        "schema": "structural.boreal_stage_b_bundle_freeze.v0_89",
        "status": "VERIFIED_RESPONSE_INDEPENDENT_PREPILOT_BUNDLE",
        **bundle_core,
        "bundle_fingerprint": canonical_sha256(bundle_core),
        "exact_replay": {
            "v0_75_spatial_partition": True,
            "v0_76_habitat_reference": True,
            "v0_83_source_operator": True,
            "v0_79_intake_and_validator": True,
            "v0_80_v031_v042_prepilot": True,
        },
        "biological_response_values_opened": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "counts_as_empirical_evidence": False,
        "fresh_system_denominator_contribution": 0,
        "eligible_to_commit_response_independent_prepilot_bundle": True,
        "next_action": (
            "commit this exact verified Stage-B bundle and its receipt; "
            "only then may the separate v0.81 pilot authorization be considered"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--header-manifest",
        type=Path,
        default=DEFAULT_HEADER_MANIFEST,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_stage_b_bundle_verifier_contract.v0_89"
        ):
            raise BorealStageBBundleError(
                "unexpected v0.89 verifier contract schema"
            )
        result = verify_bundle(
            args.bundle_dir,
            contract=contract,
            header_manifest=_load(args.header_manifest),
            header_manifest_sha256=sha256_file(args.header_manifest),
            v072=_load(DEFAULT_V072),
            v075=_load(DEFAULT_V075),
            v076=_load(DEFAULT_V076),
            v083=_load(DEFAULT_V083),
            v079=_load(DEFAULT_V079),
            v080=_load(DEFAULT_V080),
            preintake=_load(DEFAULT_PREINTAKE),
            metadata=_load(DEFAULT_METADATA),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealStageBBundleError,
    ) as exc:
        result = {
            "schema": "structural.boreal_stage_b_bundle_freeze.v0_89",
            "status": "STOP",
            "reason": str(exc),
            "biological_response_values_opened": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "counts_as_empirical_evidence": False,
            "fresh_system_denominator_contribution": 0,
            "eligible_to_commit_response_independent_prepilot_bundle": False,
        }
        code = 2
    else:
        code = 0

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
