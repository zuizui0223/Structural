#!/usr/bin/env python3
"""Build the boreal v0.12 response-sealed intake from frozen preintake receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from scripts.validate_independent_system_intake_v0_12 import (
    canonical_fingerprint,
    validate_intake_v0_12,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_v012_intake_builder_contract_v0_79.json"
)
DEFAULT_PREINTAKE = (
    ROOT / "development/boreal_lake_islands_preintake_v0_65.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class BorealIntakeBuilderError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealIntakeBuilderError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Mapping) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA64.fullmatch(value):
        raise BorealIntakeBuilderError(f"invalid SHA-256: {label}")
    return value


def _validate_projection(receipt: Mapping, candidate_id: str) -> tuple[str, str]:
    if receipt.get("schema") != (
        "structural.boreal_lake_islands_safe_projection_result.v0_74"
    ):
        raise BorealIntakeBuilderError("unexpected v0.74 receipt schema")
    if receipt.get("status") != "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED":
        raise BorealIntakeBuilderError("v0.74 safe projection did not qualify")
    if receipt.get("candidate_id") != candidate_id:
        raise BorealIntakeBuilderError("v0.74 candidate identity mismatch")
    if receipt.get("protected_response_values_opened") is not False:
        raise BorealIntakeBuilderError("v0.74 protected response boundary violated")
    if receipt.get("counts_as_empirical_evidence") is not False:
        raise BorealIntakeBuilderError("v0.74 evidence boundary violated")
    if receipt.get("pilot_response_authorized") is not False:
        raise BorealIntakeBuilderError("v0.74 pilot ceiling violated")
    if receipt.get("confirmatory_response_authorized") is not False:
        raise BorealIntakeBuilderError("v0.74 confirmatory ceiling violated")

    geometry = receipt.get("geometry")
    habitat = receipt.get("habitat")
    if not isinstance(geometry, dict) or not isinstance(habitat, dict):
        raise BorealIntakeBuilderError("v0.74 geometry/habitat receipt missing")
    if geometry.get("row_count") != 42 or geometry.get("unique_island_count") != 42:
        raise BorealIntakeBuilderError("v0.74 geometry is not exact 42-island support")
    if habitat.get("row_count") != 42:
        raise BorealIntakeBuilderError("v0.74 habitat is not exact 42-island support")
    eligible = habitat.get("eligible_columns")
    if not isinstance(eligible, list) or not eligible:
        raise BorealIntakeBuilderError("v0.74 has no eligible habitat columns")
    return (
        _require_sha(geometry.get("sha256"), "v0.74 geometry"),
        _require_sha(habitat.get("sha256"), "v0.74 habitat"),
    )


def _validate_spatial(
    receipt: Mapping,
    *,
    candidate_id: str,
    geometry_sha: str,
) -> None:
    if receipt.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealIntakeBuilderError("unexpected v0.75 receipt schema")
    if receipt.get("status") != "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY":
        raise BorealIntakeBuilderError("v0.75 spatial partition did not qualify")
    if receipt.get("candidate_id") != candidate_id:
        raise BorealIntakeBuilderError("v0.75 candidate identity mismatch")
    if receipt.get("source_geometry_sha256") != geometry_sha:
        raise BorealIntakeBuilderError("v0.75 geometry SHA does not bind v0.74")
    if receipt.get("spatial_block_count", 0) < 9:
        raise BorealIntakeBuilderError("v0.75 has fewer than nine spatial blocks")
    if receipt.get("pilot_block_count", 0) < 3:
        raise BorealIntakeBuilderError("v0.75 has fewer than three pilot blocks")
    if receipt.get("confirmatory_block_count", 0) < 6:
        raise BorealIntakeBuilderError(
            "v0.75 has fewer than six confirmatory blocks"
        )
    pilot = receipt.get("pilot_islands")
    confirmatory = receipt.get("confirmatory_islands")
    if not isinstance(pilot, list) or not isinstance(confirmatory, list):
        raise BorealIntakeBuilderError("v0.75 island partitions missing")
    if set(pilot) & set(confirmatory):
        raise BorealIntakeBuilderError("v0.75 pilot/confirmatory islands overlap")
    if len(set(pilot) | set(confirmatory)) != 42:
        raise BorealIntakeBuilderError("v0.75 partition does not cover 42 islands")
    for key in (
        "species_occurrence_used",
        "richness_used",
        "habitat_values_used",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if receipt.get(key) is not False:
            raise BorealIntakeBuilderError(f"v0.75 boundary violated: {key}")


def _validate_habitat(
    receipt: Mapping,
    *,
    candidate_id: str,
    habitat_sha: str,
    projection_receipt: Mapping,
) -> str:
    if receipt.get("schema") != (
        "structural.boreal_lake_islands_habitat_reference_result.v0_76"
    ):
        raise BorealIntakeBuilderError("unexpected v0.76 receipt schema")
    if receipt.get("status") != "HABITAT_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY":
        raise BorealIntakeBuilderError("v0.76 habitat reference did not qualify")
    if receipt.get("candidate_id") != candidate_id:
        raise BorealIntakeBuilderError("v0.76 candidate identity mismatch")
    if receipt.get("source_habitat_sha256") != habitat_sha:
        raise BorealIntakeBuilderError("v0.76 habitat SHA does not bind v0.74")
    if receipt.get("eligible_columns") != projection_receipt["habitat"]["eligible_columns"]:
        raise BorealIntakeBuilderError("v0.76 eligible habitat columns drift")
    reference_sha = _require_sha(
        receipt.get("reference_sha256"),
        "v0.76 habitat reference",
    )
    for key in (
        "species_occurrence_used",
        "richness_used",
        "protected_response_values_opened",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if receipt.get(key) is not False:
            raise BorealIntakeBuilderError(f"v0.76 boundary violated: {key}")
    return reference_sha


def build_intake(
    projection_receipt: Mapping,
    spatial_receipt: Mapping,
    habitat_receipt: Mapping,
    *,
    contract: Mapping,
    preintake: Mapping,
    metadata: Mapping,
    receipt_sha256: Mapping[str, str],
) -> dict:
    candidate_id = contract["candidate_id"]
    if preintake.get("candidate_id") != candidate_id:
        raise BorealIntakeBuilderError("v0.65 preintake candidate drift")
    if metadata.get("schema") != (
        "structural.boreal_lake_islands_dryad_metadata_result.v0_65"
    ):
        raise BorealIntakeBuilderError("unexpected v0.65 Dryad metadata schema")
    if metadata.get("response_values_opened") is not False:
        raise BorealIntakeBuilderError("v0.65 response boundary violated")

    geometry_sha, habitat_sha = _validate_projection(
        projection_receipt,
        candidate_id,
    )
    _validate_spatial(
        spatial_receipt,
        candidate_id=candidate_id,
        geometry_sha=geometry_sha,
    )
    reference_sha = _validate_habitat(
        habitat_receipt,
        candidate_id=candidate_id,
        habitat_sha=habitat_sha,
        projection_receipt=projection_receipt,
    )

    required_hash_keys = {
        "safe_projection_v0_74",
        "spatial_partition_v0_75",
        "habitat_reference_v0_76",
    }
    if set(receipt_sha256) != required_hash_keys:
        raise BorealIntakeBuilderError("preintake receipt hash keys drift")
    for key, value in receipt_sha256.items():
        _require_sha(value, key)

    identity = contract["intake_identity"]
    if identity["system_id"] != candidate_id:
        raise BorealIntakeBuilderError("contract system identity drift")

    source_identity = preintake["source_identity"]
    response_meta = metadata["focal_files"][
        "beetles_speciesmatrix_presenceabsence.csv"
    ]
    if response_meta.get("role") != "primary_response":
        raise BorealIntakeBuilderError("primary response metadata role drift")
    response_sha = _require_sha(
        response_meta.get("sha256"),
        "frozen beetle response file",
    )
    source_fingerprint_input = {
        "dryad_identifier": metadata["dryad_identifier"],
        "dryad_version_id": metadata["selected_version_id"],
        "dryad_version_number": metadata["selected_version_number"],
        "source_article_doi": source_identity["source_article_doi"],
        "primary_response_file_id": response_meta["file_id"],
        "primary_response_file_sha256": response_sha,
    }
    source_fingerprint = canonical_sha256(source_fingerprint_input)

    intake = {
        "schema": identity["schema"],
        "status": identity["status"],
        "system_id": candidate_id,
        "source_id": identity["source_id"],
        "source_version": identity["source_version"],
        "source_fingerprint": source_fingerprint,
        "origin": identity["origin"],
        "is_prior_closed_system": False,
        "response_firewall_state": "response_sealed",
        "response_values_accessed": False,
        "source_files": [
            {
                "file_id": "safe_geometry.csv",
                "sha256": geometry_sha,
                "role": "geometry",
                "opened": True,
            },
            {
                "file_id": "habitat_reference.csv",
                "sha256": reference_sha,
                "role": "safe_metadata",
                "opened": True,
            },
            {
                "file_id": "beetles_speciesmatrix_presenceabsence.csv",
                "sha256": response_sha,
                "role": "response",
                "opened": False,
            },
        ],
        "freshness_metadata": {
            key: contract["freshness_semantics"][key]
            for key in (
                "temporal_replication",
                "immutable_source_identity",
                "spatial_unit_id_documented",
                "coordinates_or_geometry_documented",
                "outcome_file_separable",
                "operator_semantics_declarable",
                "connectivity_question_already_published",
                "response_result_seen_by_project",
            )
        },
        "selection_firewall": {
            "candidate_hunt_active": False,
            "system_selected_using_response_direction": False,
            "system_selected_using_connectivity_result": False,
            "mechanism_lanes_selected_using_response_direction": False,
            "graph_scale_selected_using_response_direction": False,
            "endpoint_selected_using_response_direction": False,
            "published_effect_direction_used_for_selection": False,
        },
        "analysis_bindings": {
            "structural_partition_contract":
                "development/transition_pilot_protocol_contract_v0_31.json",
            "response_quality_gate":
                "development/response_quality_attrition_gate_v0_42.json",
            "ecological_hypothesis":
                "development/prospective_dual_isolation_source_pool_hypothesis_v0_55.json",
        },
        "endpoint_design": dict(contract["endpoint_design"]),
        "mechanism_claim_requested": False,
        "requested_mechanism_lanes": [],
        "response_blind_data_support": {
            "environment_predictor_metadata_available": True,
            "safe_geometry_available": True,
            "spatial_partition_frozen": True,
            "habitat_reference_frozen": True,
            "temporal_transition_metadata_available": False,
            "genetic_sampling_metadata_available": False,
            "biological_response_values_accessed": False,
            "preintake_receipt_sha256": dict(receipt_sha256),
        },
    }
    return intake


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projection_receipt", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("habitat_receipt", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--preintake", type=Path, default=DEFAULT_PREINTAKE)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output-intake", type=Path)
    parser.add_argument("--validation-receipt", type=Path)
    args = parser.parse_args()

    receipt_paths = {
        "safe_projection_v0_74": args.projection_receipt,
        "spatial_partition_v0_75": args.spatial_receipt,
        "habitat_reference_v0_76": args.habitat_receipt,
    }
    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_lake_islands_v012_intake_builder_contract.v0_79"
        ):
            raise BorealIntakeBuilderError("unexpected v0.79 contract schema")
        intake = build_intake(
            _load(args.projection_receipt),
            _load(args.spatial_receipt),
            _load(args.habitat_receipt),
            contract=contract,
            preintake=_load(args.preintake),
            metadata=_load(args.metadata),
            receipt_sha256={
                key: sha256_file(path)
                for key, path in receipt_paths.items()
            },
        )
        code, validation = validate_intake_v0_12(intake)
        if code != 0:
            raise BorealIntakeBuilderError(
                "generated v0.12 intake failed validator: "
                + str(validation.get("status"))
            )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealIntakeBuilderError,
    ) as exc:
        intake = None
        validation = {
            "schema": "structural.boreal_v012_intake_builder_result.v0_79",
            "status": "STOP",
            "reason": str(exc),
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "counts_as_empirical_evidence": False,
        }
        code = 2
    else:
        validation["builder_schema"] = (
            "structural.boreal_v012_intake_builder_result.v0_79"
        )
        validation["generated_intake_fingerprint"] = canonical_fingerprint(intake)
        validation["counts_as_empirical_evidence"] = False

    if intake is not None and args.output_intake is not None:
        args.output_intake.parent.mkdir(parents=True, exist_ok=True)
        args.output_intake.write_text(
            json.dumps(intake, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    text = json.dumps(validation, indent=2, sort_keys=True) + "\n"
    if args.validation_receipt is not None:
        args.validation_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.validation_receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
