#!/usr/bin/env python3
"""Build the response-sealed 19-island boreal beetle intake.

This stage combines only already-committed response-independent freezes plus the
previously frozen Dryad response-file identity. It never opens the beetle matrix.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_response_sealed_intake_contract_v1_02.json"
)
DEFAULT_SPATIAL = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)
DEFAULT_STATE = (
    ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
)
DEFAULT_OPERATOR = (
    ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
DEFAULT_PREINTAKE = (
    ROOT / "development/boreal_lake_islands_preintake_v0_65.json"
)
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class Boreal19IntakeError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19IntakeError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA64.fullmatch(value):
        raise Boreal19IntakeError(f"invalid SHA-256: {label}")
    return value


def build(
    spatial: Mapping,
    state: Mapping,
    operator: Mapping,
    metadata: Mapping,
    preintake: Mapping,
    *,
    contract: Mapping,
    parent_sha256: Mapping[str, str],
) -> tuple[dict, dict]:
    candidate = contract["candidate_id"]
    required = contract["required_parent_status"]

    if spatial.get("schema") != "structural.boreal_19island_spatial_partition_freeze.v1_00":
        raise Boreal19IntakeError("unexpected spatial-freeze schema")
    if spatial.get("status") != required["spatial_freeze"]:
        raise Boreal19IntakeError("spatial freeze did not qualify")
    if spatial.get("candidate_id") != candidate:
        raise Boreal19IntakeError("spatial candidate mismatch")

    if state.get("schema") != "structural.boreal_19island_state_reference_freeze.v0_99":
        raise Boreal19IntakeError("unexpected state-freeze schema")
    if state.get("status") != required["state_freeze"]:
        raise Boreal19IntakeError("state freeze did not qualify")
    if state.get("candidate_id") != candidate:
        raise Boreal19IntakeError("state candidate mismatch")

    if operator.get("schema") != "structural.boreal_19island_source_operator_freeze.v1_01":
        raise Boreal19IntakeError("unexpected source-operator-freeze schema")
    if operator.get("status") != required["source_operator_freeze"]:
        raise Boreal19IntakeError("source operator freeze did not qualify")
    if operator.get("candidate_id") != candidate:
        raise Boreal19IntakeError("source operator candidate mismatch")
    if operator.get("prepilot_intake_may_be_built") is not True:
        raise Boreal19IntakeError("source operator does not authorize pre-pilot intake")

    population = contract["population"]
    state_order = state.get("island_order")
    pilot_islands = spatial.get("pilot_islands")
    confirmatory_islands = spatial.get("confirmatory_islands")
    pilot_blocks = spatial.get("pilot_block_ids")
    confirmatory_blocks = spatial.get("confirmatory_block_ids")
    island_to_block = spatial.get("island_to_block")
    if not isinstance(state_order, list) or len(state_order) != population["island_count"]:
        raise Boreal19IntakeError("state island population is not exact 19-island support")
    if len(set(state_order)) != len(state_order):
        raise Boreal19IntakeError("state island order contains duplicates")
    if not isinstance(pilot_islands, list) or not isinstance(confirmatory_islands, list):
        raise Boreal19IntakeError("spatial island partitions missing")
    if set(pilot_islands) & set(confirmatory_islands):
        raise Boreal19IntakeError("pilot and confirmatory islands overlap")
    if set(pilot_islands) | set(confirmatory_islands) != set(state_order):
        raise Boreal19IntakeError("spatial partition does not cover exact state population")
    if len(pilot_islands) != population["pilot_island_count"]:
        raise Boreal19IntakeError("pilot island count drift")
    if len(confirmatory_islands) != population["confirmatory_island_count"]:
        raise Boreal19IntakeError("confirmatory island count drift")
    if not isinstance(pilot_blocks, list) or len(pilot_blocks) != population["pilot_block_count"]:
        raise Boreal19IntakeError("pilot block count drift")
    if not isinstance(confirmatory_blocks, list) or len(confirmatory_blocks) != population["confirmatory_block_count"]:
        raise Boreal19IntakeError("confirmatory block count drift")
    if set(pilot_blocks) & set(confirmatory_blocks):
        raise Boreal19IntakeError("pilot and confirmatory blocks overlap")
    if not isinstance(island_to_block, dict) or set(island_to_block) != set(state_order):
        raise Boreal19IntakeError("island-to-block map drift")

    for mapping, label in ((spatial, "spatial"), (state, "state")):
        for key in (
            "counts_as_empirical_evidence",
            "pilot_response_authorized",
            "confirmatory_response_authorized",
        ):
            if mapping.get(key) is not False and (
                not isinstance(mapping.get("response_boundary"), dict)
                or mapping["response_boundary"].get(key) is not False
            ):
                raise Boreal19IntakeError(f"{label} response boundary violated: {key}")
    op_boundary = operator.get("response_boundary")
    if not isinstance(op_boundary, dict):
        raise Boreal19IntakeError("source operator response boundary missing")
    for key in (
        "species_occurrence_used_to_build_operator",
        "pilot_response_used_to_build_operator",
        "confirmatory_response_used_to_build_operator",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if op_boundary.get(key) is not False:
            raise Boreal19IntakeError(f"source operator boundary violated: {key}")

    state_sha = _sha(parent_sha256.get("state_freeze"), "state freeze")
    spatial_sha = _sha(parent_sha256.get("spatial_freeze"), "spatial freeze")
    operator_sha = _sha(parent_sha256.get("source_operator_freeze"), "source operator freeze")
    if operator.get("parents", {}).get("spatial_freeze_sha256") != spatial_sha:
        raise Boreal19IntakeError("operator is not bound to exact spatial freeze")
    if operator.get("parents", {}).get("state_freeze_sha256") != state_sha:
        raise Boreal19IntakeError("operator is not bound to exact state freeze")
    operator_fingerprint = _sha(operator.get("operator_fingerprint"), "operator fingerprint")
    state_reference_sha = _sha(state.get("state_reference_sha256"), "state reference")

    if metadata.get("schema") != "structural.boreal_lake_islands_dryad_metadata_result.v0_65":
        raise Boreal19IntakeError("unexpected Dryad metadata schema")
    if metadata.get("response_values_opened") is not False:
        raise Boreal19IntakeError("Dryad metadata response boundary violated")
    response = metadata.get("focal_files", {}).get(contract["response_file"]["name"])
    if not isinstance(response, dict):
        raise Boreal19IntakeError("frozen beetle response identity missing")
    for key, expected in (
        ("file_id", contract["response_file"]["dryad_file_id"]),
        ("size", contract["response_file"]["expected_size_bytes"]),
        ("sha256", contract["response_file"]["expected_sha256"]),
        ("role", "primary_response"),
    ):
        if response.get(key) != expected:
            raise Boreal19IntakeError(f"beetle response identity drift: {key}")

    source_identity = preintake.get("source_identity")
    if not isinstance(source_identity, dict):
        raise Boreal19IntakeError("preintake source identity missing")
    if source_identity.get("response_values_opened_by_structural") is not False:
        raise Boreal19IntakeError("preintake response boundary violated")
    if source_identity.get("dryad_version_id") != metadata.get("selected_version_id"):
        raise Boreal19IntakeError("Dryad version id drift")
    if source_identity.get("dryad_version_number") != metadata.get("selected_version_number"):
        raise Boreal19IntakeError("Dryad version number drift")

    model_roles = state.get("model_roles")
    if model_roles != {
        "R0_columns": contract["model_binding"]["R0"],
        "R1_add_columns": contract["model_binding"]["R1_add"],
    }:
        raise Boreal19IntakeError("state model roles drift from predeclared intake")

    source_fingerprint = canonical_sha256({
        "dryad_identifier": metadata["dryad_identifier"],
        "dryad_version_id": metadata["selected_version_id"],
        "dryad_version_number": metadata["selected_version_number"],
        "source_article_doi": source_identity["source_article_doi"],
        "response_file_id": response["file_id"],
        "response_file_sha256": response["sha256"],
        "population_islands": state_order,
    })

    intake = {
        "schema": "structural.boreal_19island_response_sealed_intake.v1_02",
        "status": "RESPONSE_SEALED_READY_FOR_PREPILOT_CONSTRUCTION",
        "system_id": candidate,
        "source_id": metadata["dryad_identifier"],
        "source_version": (
            f"dryad-v{metadata['selected_version_number']}-version-id-"
            f"{metadata['selected_version_id']}"
        ),
        "source_fingerprint": source_fingerprint,
        "response_firewall_state": "response_sealed",
        "response_values_accessed": False,
        "population": {
            "island_count": len(state_order),
            "island_order": list(state_order),
            "pilot_islands": list(pilot_islands),
            "confirmatory_islands": list(confirmatory_islands),
            "pilot_block_ids": list(pilot_blocks),
            "confirmatory_block_ids": list(confirmatory_blocks),
            "island_to_block": dict(island_to_block),
        },
        "response_file": {
            "name": contract["response_file"]["name"],
            "dryad_file_id": response["file_id"],
            "size_bytes": response["size"],
            "sha256": response["sha256"],
            "opened": False,
            "full_file_island_count_reported": (
                contract["response_file"]["expected_full_file_island_count_reported"]
            ),
            "analysis_population_island_count": len(state_order),
        },
        "state_reference": {
            "path": state["state_reference_path"],
            "sha256": state_reference_sha,
            "R0_columns": list(model_roles["R0_columns"]),
            "R1_add_columns": list(model_roles["R1_add_columns"]),
        },
        "source_operator": {
            "fingerprint": operator_fingerprint,
            "operator_file_sha256": _sha(
                operator["source_execution"]["operator_file_sha256"],
                "operator file",
            ),
            "selected_k": operator["selected_k"],
            "kernel_scale_km_hex": operator["kernel_scale_km_hex"],
            "edge_count": operator["edge_count"],
            "cross_validation_block_edge_count": operator[
                "cross_validation_block_edge_count"
            ],
        },
        "parent_freeze_sha256": {
            "spatial_freeze": spatial_sha,
            "state_freeze": state_sha,
            "source_operator_freeze": operator_sha,
        },
        "endpoint_design": dict(contract["endpoint_design"]),
        "prepilot_design": dict(contract["prepilot_design"]),
        "mechanism_claim_requested": False,
        "response_boundary": dict(contract["response_boundary"]),
    }
    intake_fingerprint = canonical_sha256(intake)
    receipt = {
        "schema": "structural.boreal_19island_response_sealed_intake_receipt.v1_02",
        "status": "ELIGIBLE_TO_BUILD_V031_V042_RESPONSE_SEALED",
        "system_id": candidate,
        "source_fingerprint": source_fingerprint,
        "intake_fingerprint": intake_fingerprint,
        "parent_freeze_sha256": dict(intake["parent_freeze_sha256"]),
        "operator_fingerprint": operator_fingerprint,
        "island_count": len(state_order),
        "pilot_block_count": len(pilot_blocks),
        "confirmatory_block_count": len(confirmatory_blocks),
        "v0_31_protocol_construction_authorized": True,
        "v0_42_quality_contract_construction_authorized": True,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "mechanism_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return intake, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--spatial", type=Path, default=DEFAULT_SPATIAL)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--operator", type=Path, default=DEFAULT_OPERATOR)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--preintake", type=Path, default=DEFAULT_PREINTAKE)
    parser.add_argument("--output-intake", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    parent_paths = {
        "spatial_freeze": args.spatial,
        "state_freeze": args.state,
        "source_operator_freeze": args.operator,
    }
    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_19island_response_sealed_intake_contract.v1_02"
        ):
            raise Boreal19IntakeError("unexpected v1.02 contract schema")
        intake, receipt = build(
            _load(args.spatial),
            _load(args.state),
            _load(args.operator),
            _load(args.metadata),
            _load(args.preintake),
            contract=contract,
            parent_sha256={
                name: sha256_file(path) for name, path in parent_paths.items()
            },
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19IntakeError,
    ) as exc:
        intake = None
        receipt = {
            "schema": "structural.boreal_19island_response_sealed_intake_receipt.v1_02",
            "status": "STOP",
            "reason": str(exc),
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "mechanism_response_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
        }
        code = 2
    else:
        code = 0

    if intake is not None and args.output_intake is not None:
        args.output_intake.parent.mkdir(parents=True, exist_ok=True)
        args.output_intake.write_text(
            json.dumps(intake, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
