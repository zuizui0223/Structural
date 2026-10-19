#!/usr/bin/env python3
"""Construct the complete response-sealed pre-pilot bundle for the boreal 19-island system."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.freeze_boreal_19island_dual_isolation_operator_v1_00 import (  # noqa: E402
    freeze as freeze_operator_v100,
)
from scripts.validate_independent_system_intake_v0_12 import (  # noqa: E402
    canonical_fingerprint,
    validate_intake_v0_12,
)
from structural.response_quality_attrition import (  # noqa: E402
    ResponseQualityContractStatus,
    canonical_contract_mapping,
    contract_from_mapping,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (  # noqa: E402
    PilotProtocolStatus,
    canonical_protocol_mapping,
    evaluate_transition_pilot_protocol,
    protocol_from_mapping,
)


DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_prepilot_builder_contract_v1_02.json"
)
DEFAULT_HEADER_FREEZE = (
    ROOT / "development/boreal_19island_header_projection_freeze_v0_95.json"
)
DEFAULT_GEOMETRY_FREEZE = (
    ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
)
DEFAULT_GEOMETRY = (
    ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
)
DEFAULT_SPATIAL_FREEZE = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)
DEFAULT_STATE_FREEZE = (
    ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
)
DEFAULT_STATE = (
    ROOT / "development/boreal_19island_state_reference_v0_99.csv"
)
DEFAULT_OPERATOR_FREEZE = (
    ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
)
DEFAULT_OPERATOR_CONTRACT = (
    ROOT / "development/boreal_19island_dual_isolation_operator_contract_v1_00.json"
)
DEFAULT_LEGACY_OPERATOR = (
    ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
DEFAULT_PREINTAKE = (
    ROOT / "development/boreal_lake_islands_preintake_v0_65.json"
)


class Boreal19PrepilotError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19PrepilotError(f"{path.name} must contain a JSON object")
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


def _require_boundary(mapping: Mapping, keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if mapping.get(key) is not False:
            raise Boreal19PrepilotError(f"{label} boundary violated: {key}")


def _validate_population(
    contract: Mapping,
    header_freeze: Mapping,
    geometry_freeze: Mapping,
    spatial_freeze: Mapping,
    state_freeze: Mapping,
) -> tuple[str, ...]:
    candidate = contract["candidate_id"]
    if header_freeze.get("schema") != (
        "structural.boreal_19island_header_projection_freeze.v0_95"
    ):
        raise Boreal19PrepilotError("unexpected v0.95 header freeze schema")
    if header_freeze.get("candidate_id") != candidate:
        raise Boreal19PrepilotError("v0.95 candidate identity drift")
    scope = header_freeze.get("scope")
    if not isinstance(scope, dict):
        raise Boreal19PrepilotError("v0.95 population scope missing")
    expected = contract["analysis_population"]
    if scope.get("island_count_expected") != expected["island_count"]:
        raise Boreal19PrepilotError("19-island population count drift")
    if scope.get("source_defined_selection_rule") != expected["selection_rule"]:
        raise Boreal19PrepilotError("analysis-population selection rule drift")
    if scope.get("selection_basis") != expected["selection_basis"]:
        raise Boreal19PrepilotError("analysis-population selection basis drift")
    if expected.get("outcome_selected") is not False:
        raise Boreal19PrepilotError("contract must forbid outcome-selected population")
    if header_freeze.get("row_values_opened_by_freezer") != 0:
        raise Boreal19PrepilotError("v0.95 opened data rows before population freeze")
    if header_freeze.get("biological_response_values_opened_by_freezer") is not False:
        raise Boreal19PrepilotError("v0.95 biological-response boundary violated")

    if geometry_freeze.get("schema") != (
        "structural.boreal_19island_safe_geometry_freeze.v0_97"
    ):
        raise Boreal19PrepilotError("unexpected v0.97 geometry freeze schema")
    if geometry_freeze.get("candidate_id") != candidate:
        raise Boreal19PrepilotError("v0.97 geometry candidate drift")
    if geometry_freeze.get("row_count") != 19:
        raise Boreal19PrepilotError("v0.97 geometry does not have 19 islands")
    islands = tuple(geometry_freeze.get("island_order") or ())
    if len(islands) != 19 or len(set(islands)) != 19:
        raise Boreal19PrepilotError("invalid frozen 19-island order")
    _require_boundary(
        geometry_freeze,
        (
            "protected_response_values_exposed",
            "biological_response_values_opened",
            "counts_as_empirical_evidence",
            "pilot_response_authorized",
            "confirmatory_response_authorized",
        ),
        "v0.97 geometry",
    )

    if spatial_freeze.get("schema") != (
        "structural.boreal_19island_spatial_partition_freeze.v1_00"
    ):
        raise Boreal19PrepilotError("unexpected v1.00 spatial freeze schema")
    if spatial_freeze.get("candidate_id") != candidate:
        raise Boreal19PrepilotError("v1.00 spatial candidate drift")
    pilot = tuple(spatial_freeze.get("pilot_islands") or ())
    confirm = tuple(spatial_freeze.get("confirmatory_islands") or ())
    if set(pilot) & set(confirm):
        raise Boreal19PrepilotError("pilot/confirmatory island overlap")
    if set(pilot) | set(confirm) != set(islands):
        raise Boreal19PrepilotError("spatial split does not cover exact 19-island population")
    if len(spatial_freeze.get("pilot_block_ids") or ()) != 3:
        raise Boreal19PrepilotError("expected exactly three frozen pilot blocks")
    if len(spatial_freeze.get("confirmatory_block_ids") or ()) != 7:
        raise Boreal19PrepilotError("expected exactly seven confirmatory blocks")
    _require_boundary(
        spatial_freeze,
        (
            "species_occurrence_used",
            "richness_used",
            "habitat_values_used",
            "counts_as_empirical_evidence",
            "pilot_response_authorized",
            "confirmatory_response_authorized",
        ),
        "v1.00 spatial",
    )

    if state_freeze.get("schema") != (
        "structural.boreal_19island_state_reference_freeze.v0_99"
    ):
        raise Boreal19PrepilotError("unexpected v0.99 state freeze schema")
    if tuple(state_freeze.get("island_order") or ()) != islands:
        raise Boreal19PrepilotError("state-reference island order drift")
    rb = state_freeze.get("response_boundary")
    if not isinstance(rb, dict):
        raise Boreal19PrepilotError("v0.99 response boundary missing")
    _require_boundary(
        rb,
        (
            "species_occurrence_used",
            "richness_values_returned",
            "protected_response_values_exposed",
            "counts_as_empirical_evidence",
            "pilot_response_authorized",
            "confirmatory_response_authorized",
        ),
        "v0.99 state",
    )
    return islands


def _verify_operator(
    *,
    contract: Mapping,
    geometry_freeze: Mapping,
    spatial_freeze: Mapping,
    state_freeze: Mapping,
    operator_freeze: Mapping,
    operator_contract: Mapping,
    legacy_operator: Mapping,
    geometry_path: Path,
    spatial_freeze_path: Path,
    state_freeze_path: Path,
) -> str:
    if operator_freeze.get("schema") != (
        "structural.boreal_19island_source_operator_freeze.v1_01"
    ):
        raise Boreal19PrepilotError("unexpected v1.01 source-operator freeze schema")
    if operator_freeze.get("candidate_id") != contract["candidate_id"]:
        raise Boreal19PrepilotError("v1.01 operator candidate drift")
    if operator_freeze.get("prepilot_intake_may_be_built") is not True:
        raise Boreal19PrepilotError("v1.01 does not authorize pre-pilot construction")
    rb = operator_freeze.get("response_boundary")
    if not isinstance(rb, dict):
        raise Boreal19PrepilotError("v1.01 response boundary missing")
    _require_boundary(
        rb,
        (
            "species_occurrence_used_to_build_operator",
            "pilot_response_used_to_build_operator",
            "confirmatory_response_used_to_build_operator",
            "counts_as_empirical_evidence",
            "pilot_response_authorized",
            "confirmatory_response_authorized",
        ),
        "v1.01 operator",
    )

    operator, receipt = freeze_operator_v100(
        geometry_path,
        geometry_freeze=geometry_freeze,
        spatial_freeze=spatial_freeze,
        state_freeze=state_freeze,
        contract=operator_contract,
        legacy=legacy_operator,
        spatial_freeze_sha256=sha256_file(spatial_freeze_path),
        state_freeze_sha256=sha256_file(state_freeze_path),
    )
    observed = canonical_sha256(operator)
    frozen = operator_freeze.get("operator_fingerprint")
    if observed != frozen or receipt.get("operator_fingerprint") != frozen:
        raise Boreal19PrepilotError("v1.01 source operator did not exact-replay")
    for key in ("selected_k", "kernel_scale_km_hex", "edge_count"):
        if receipt.get(key) != operator_freeze.get(key):
            raise Boreal19PrepilotError(f"v1.01 operator replay drift: {key}")
    if receipt.get("cross_validation_block_edge_count") != operator_freeze.get(
        "cross_validation_block_edge_count"
    ):
        raise Boreal19PrepilotError("v1.01 cross-block edge count drift")
    return str(frozen)


def _build_intake(
    *,
    contract: Mapping,
    islands: tuple[str, ...],
    header_freeze: Mapping,
    geometry_freeze: Mapping,
    spatial_freeze: Mapping,
    state_freeze: Mapping,
    operator_freeze: Mapping,
    metadata: Mapping,
    preintake: Mapping,
    geometry_freeze_sha: str,
    spatial_freeze_sha: str,
    state_freeze_sha: str,
    operator_freeze_sha: str,
    operator_fingerprint: str,
) -> dict:
    if metadata.get("schema") != (
        "structural.boreal_lake_islands_dryad_metadata_result.v0_65"
    ):
        raise Boreal19PrepilotError("unexpected Dryad metadata schema")
    if metadata.get("response_values_opened") is not False:
        raise Boreal19PrepilotError("Dryad metadata response boundary violated")
    response = metadata.get("focal_files", {}).get(
        contract["response_file"]["name"]
    )
    if not isinstance(response, dict):
        raise Boreal19PrepilotError("frozen beetle response metadata missing")
    response_spec = contract["response_file"]
    for key, observed, expected in (
        ("file_id", response.get("file_id"), response_spec["dryad_file_id"]),
        ("size", response.get("size"), response_spec["expected_size_bytes"]),
        ("sha256", response.get("sha256"), response_spec["expected_sha256"]),
        ("role", response.get("role"), "primary_response"),
    ):
        if observed != expected:
            raise Boreal19PrepilotError(f"response metadata drift: {key}")

    source_identity = preintake.get("source_identity")
    if not isinstance(source_identity, dict):
        raise Boreal19PrepilotError("source article identity missing")
    population_identity = {
        "island_order": list(islands),
        "selection_rule": contract["analysis_population"]["selection_rule"],
        "selection_basis": contract["analysis_population"]["selection_basis"],
        "outcome_selected": False,
    }
    population_fingerprint = canonical_sha256(population_identity)
    source_fingerprint = canonical_sha256({
        "dryad_identifier": metadata["dryad_identifier"],
        "dryad_version_id": metadata["selected_version_id"],
        "dryad_version_number": metadata["selected_version_number"],
        "source_article_doi": source_identity["source_article_doi"],
        "primary_response_file_id": response["file_id"],
        "primary_response_file_sha256": response["sha256"],
        "analysis_population_fingerprint": population_fingerprint,
        "analysis_population_selection_rule": population_identity["selection_rule"],
    })

    identity = contract["intake_identity"]
    endpoint = dict(contract["endpoint_design"])
    intake = {
        "schema": identity["schema"],
        "status": identity["status"],
        "system_id": contract["candidate_id"],
        "source_id": identity["source_id"],
        "source_version": identity["source_version"],
        "source_fingerprint": source_fingerprint,
        "origin": identity["origin"],
        "is_prior_closed_system": False,
        "response_firewall_state": "response_sealed",
        "response_values_accessed": False,
        "source_files": [
            {
                "file_id": "boreal_19island_safe_geometry_v0_97.csv",
                "sha256": geometry_freeze["geometry_sha256"],
                "role": "geometry",
                "opened": True,
            },
            {
                "file_id": "boreal_19island_state_reference_v0_99.csv",
                "sha256": state_freeze["state_reference_sha256"],
                "role": "safe_metadata",
                "opened": True,
            },
            {
                "file_id": "boreal_19island_source_operator_canonical_v1_01.json",
                "sha256": operator_fingerprint,
                "role": "safe_metadata",
                "opened": True,
            },
            {
                "file_id": response_spec["name"],
                "sha256": response_spec["expected_sha256"],
                "role": "response",
                "opened": False,
            },
        ],
        "freshness_metadata": dict(contract["freshness_semantics"]),
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
        "endpoint_design": endpoint,
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
            "preintake_receipt_sha256": {
                "safe_projection_v0_74": geometry_freeze_sha,
                "spatial_partition_v0_75": spatial_freeze_sha,
                "habitat_reference_v0_76": state_freeze_sha,
            },
        },
        "analysis_population": {
            **population_identity,
            "analysis_population_fingerprint": population_fingerprint,
            "count": 19,
            "parent_matrix_island_rows": response_spec["parent_matrix_island_rows"],
            "response_file_semantic_scope": (
                "later response routers may semantically expose only these 19 rows; "
                "the other 23 parent-matrix rows remain out of the analysis population"
            ),
        },
        "response_blind_parent_bindings": {
            "header_projection_freeze_v0_95_sha256": canonical_sha256(
                dict(header_freeze)
            ),
            "geometry_freeze_v0_97_sha256": geometry_freeze_sha,
            "spatial_freeze_v1_00_sha256": spatial_freeze_sha,
            "state_freeze_v0_99_sha256": state_freeze_sha,
            "source_operator_freeze_v1_01_sha256": operator_freeze_sha,
            "source_operator_fingerprint": operator_fingerprint,
        },
        "response_contract": {
            "parent_matrix_island_rows": response_spec["parent_matrix_island_rows"],
            "species_columns": response_spec["species_columns"],
            "required_response_domain": list(response_spec["required_response_domain"]),
            "domain_verified_now": False,
            "domain_violation_after_future_authorized_open": "terminal STOP",
            "pilot_semantic_scope": (
                "six frozen pilot island rows only; 13 frozen confirmatory rows "
                "and 23 out-of-population rows remain semantically opaque"
            ),
        },
    }
    return intake


def _build_protocol_and_quality(
    intake: Mapping,
    intake_receipt: Mapping,
    spatial_freeze: Mapping,
    *,
    contract: Mapping,
) -> tuple[dict, dict, dict]:
    if intake_receipt.get("status") != (
        "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts"
    ):
        raise Boreal19PrepilotError("v0.12 intake validator did not qualify")
    intake_fingerprint = canonical_fingerprint(dict(intake))
    if intake_receipt.get("intake_fingerprint") != intake_fingerprint:
        raise Boreal19PrepilotError("v0.12 intake fingerprint drift")
    if intake_receipt.get("v0_31_protocol_construction_authorized") is not True:
        raise Boreal19PrepilotError("v0.31 construction not authorized")
    if intake_receipt.get("v0_42_quality_contract_construction_authorized") is not True:
        raise Boreal19PrepilotError("v0.42 construction not authorized")
    for key in (
        "pilot_response_authorized",
        "confirmatory_response_authorized",
        "mechanism_response_authorized",
        "mechanism_claim_authorized",
    ):
        if intake_receipt.get(key) is not False:
            raise Boreal19PrepilotError(f"intake ceiling violated: {key}")

    pilot_blocks = list(spatial_freeze["pilot_block_ids"])
    confirmatory_blocks = list(spatial_freeze["confirmatory_block_ids"])
    v31 = contract["v0_31"]
    endpoint_semantics = (
        "One common burned-pilot-supported beetle species universe is defined "
        "after the future one-shot pilot opens only: include exactly beetle "
        "species detected on at least two distinct frozen pilot islands among "
        "DN, FD, HU, IL, IS and PP. Apply that identical species universe to "
        "every held-out pilot spatial block. Emit one exact binary target per "
        "pilot island x fixed-universe species. Values outside the prospectively "
        "frozen domain {0,1}, missing frozen pilot islands, or an empty supported "
        "species universe are terminal non-estimability stops. The other 13 "
        "analysis-population islands and all 23 out-of-population parent-matrix "
        "rows remain semantically opaque. The pilot is feasibility evidence only."
    )
    protocol_mapping = {
        "protocol_id": "boreal-19island-beetles-v0.31-" + intake_fingerprint[:12],
        "system_id": contract["candidate_id"],
        "partition_axis": v31["partition_axis"],
        "pilot_partition": pilot_blocks,
        "confirmatory_partition": confirmatory_blocks,
        "endpoint_id": v31["endpoint_id"],
        "endpoint_semantics": endpoint_semantics,
        "heldout_design_id": v31["heldout_design_id"],
        "minimum_test_rows": v31["minimum_test_rows"],
        "minimum_train_positive": v31["minimum_train_positive"],
        "minimum_train_negative": v31["minimum_train_negative"],
        "minimum_estimable_blocks": v31["minimum_estimable_blocks"],
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
        "pilot_used_for_effect_estimation": False,
    }
    protocol = protocol_from_mapping(protocol_mapping)
    pdec = evaluate_transition_pilot_protocol(protocol)
    if pdec.status is not PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT:
        raise Boreal19PrepilotError("constructed v0.31 protocol failed evaluator")

    v42 = contract["v0_42"]
    quality_mapping = {
        "contract_id": "boreal-19island-beetles-quality-v0.42-" + pdec.protocol_fingerprint[:12],
        "system_id": contract["candidate_id"],
        "parent_protocol_fingerprint": pdec.protocol_fingerprint,
        "minimum_response_qualified_blocks": v42[
            "minimum_response_qualified_blocks"
        ],
        "response_quality_semantics": (
            "A frozen pilot block is response-qualified only when the single "
            "common pilot-supported species universe yields at least the frozen "
            "minimum_test_rows exact binary island-by-species targets. The "
            "common universe is defined once from only the six frozen pilot "
            "islands as species detected on at least two distinct pilot islands. "
            "Unexpected nonbinary values, a missing pilot island, inability to "
            "construct the common universe, or any attempted semantic access to "
            "the 13 confirmatory or 23 out-of-population rows is a terminal STOP. "
            "No blocks, islands, species, thresholds, or partitions may be "
            "rescued, substituted, merged, imputed, or relaxed after opening."
        ),
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
    }
    quality = contract_from_mapping(quality_mapping)
    qdec = evaluate_response_quality_contract(protocol=protocol, contract=quality)
    if qdec.status is not ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT:
        raise Boreal19PrepilotError("constructed v0.42 quality contract failed evaluator")

    receipt = {
        "schema": "structural.boreal_19island_prepilot_contract_result.v1_02",
        "status": "V012_V031_V042_FROZEN_RESPONSE_REMAINS_SEALED",
        "candidate_id": contract["candidate_id"],
        "parent_intake_fingerprint": intake_fingerprint,
        "analysis_population_fingerprint": intake["analysis_population"][
            "analysis_population_fingerprint"
        ],
        "source_operator_fingerprint": intake["response_blind_parent_bindings"][
            "source_operator_fingerprint"
        ],
        "protocol_fingerprint": pdec.protocol_fingerprint,
        "quality_contract_fingerprint": qdec.contract_fingerprint,
        "pilot_block_count": len(pilot_blocks),
        "confirmatory_block_count": len(confirmatory_blocks),
        "pilot_island_count": len(spatial_freeze["pilot_islands"]),
        "confirmatory_island_count": len(spatial_freeze["confirmatory_islands"]),
        "parent_matrix_island_rows": contract["response_file"][
            "parent_matrix_island_rows"
        ],
        "out_of_population_rows_must_remain_opaque": 23,
        "generic_v0_31_status": pdec.status.value,
        "generic_v0_42_status": qdec.status.value,
        "response_domain_frozen": list(
            contract["response_file"]["required_response_domain"]
        ),
        "response_domain_verified_now": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "mechanism_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return (
        canonical_protocol_mapping(protocol),
        canonical_contract_mapping(quality),
        receipt,
    )


def build(
    *,
    contract: Mapping,
    header_freeze: Mapping,
    geometry_freeze: Mapping,
    spatial_freeze: Mapping,
    state_freeze: Mapping,
    operator_freeze: Mapping,
    operator_contract: Mapping,
    legacy_operator: Mapping,
    metadata: Mapping,
    preintake: Mapping,
    geometry_path: Path,
    state_path: Path,
    geometry_freeze_path: Path,
    spatial_freeze_path: Path,
    state_freeze_path: Path,
    operator_freeze_path: Path,
) -> tuple[dict, dict, dict, dict, dict]:
    if contract.get("schema") != (
        "structural.boreal_19island_prepilot_builder_contract.v1_02"
    ):
        raise Boreal19PrepilotError("unexpected v1.02 contract schema")

    islands = _validate_population(
        contract,
        header_freeze,
        geometry_freeze,
        spatial_freeze,
        state_freeze,
    )
    if sha256_file(geometry_path) != geometry_freeze["geometry_sha256"]:
        raise Boreal19PrepilotError("committed geometry byte identity drift")
    if sha256_file(state_path) != state_freeze["state_reference_sha256"]:
        raise Boreal19PrepilotError("committed state-reference byte identity drift")

    operator_fingerprint = _verify_operator(
        contract=contract,
        geometry_freeze=geometry_freeze,
        spatial_freeze=spatial_freeze,
        state_freeze=state_freeze,
        operator_freeze=operator_freeze,
        operator_contract=operator_contract,
        legacy_operator=legacy_operator,
        geometry_path=geometry_path,
        spatial_freeze_path=spatial_freeze_path,
        state_freeze_path=state_freeze_path,
    )

    intake = _build_intake(
        contract=contract,
        islands=islands,
        header_freeze=header_freeze,
        geometry_freeze=geometry_freeze,
        spatial_freeze=spatial_freeze,
        state_freeze=state_freeze,
        operator_freeze=operator_freeze,
        metadata=metadata,
        preintake=preintake,
        geometry_freeze_sha=sha256_file(geometry_freeze_path),
        spatial_freeze_sha=sha256_file(spatial_freeze_path),
        state_freeze_sha=sha256_file(state_freeze_path),
        operator_freeze_sha=sha256_file(operator_freeze_path),
        operator_fingerprint=operator_fingerprint,
    )
    code, intake_receipt = validate_intake_v0_12(intake)
    if code != 0:
        raise Boreal19PrepilotError(
            "generated v0.12 intake failed validator: "
            + str(intake_receipt.get("status"))
            + " / "
            + str(intake_receipt.get("reason", ""))
        )
    intake_receipt["builder_schema"] = (
        "structural.boreal_19island_prepilot_builder_result.v1_02"
    )
    intake_receipt["counts_as_empirical_evidence"] = False

    protocol, quality, prepilot_receipt = _build_protocol_and_quality(
        intake,
        intake_receipt,
        spatial_freeze,
        contract=contract,
    )
    return intake, intake_receipt, protocol, quality, prepilot_receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--header-freeze", type=Path, default=DEFAULT_HEADER_FREEZE)
    parser.add_argument("--geometry-freeze", type=Path, default=DEFAULT_GEOMETRY_FREEZE)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--spatial-freeze", type=Path, default=DEFAULT_SPATIAL_FREEZE)
    parser.add_argument("--state-freeze", type=Path, default=DEFAULT_STATE_FREEZE)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--operator-freeze", type=Path, default=DEFAULT_OPERATOR_FREEZE)
    parser.add_argument("--operator-contract", type=Path, default=DEFAULT_OPERATOR_CONTRACT)
    parser.add_argument("--legacy-operator", type=Path, default=DEFAULT_LEGACY_OPERATOR)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--preintake", type=Path, default=DEFAULT_PREINTAKE)
    parser.add_argument("--output-intake", type=Path)
    parser.add_argument("--output-intake-receipt", type=Path)
    parser.add_argument("--output-protocol", type=Path)
    parser.add_argument("--output-quality", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        values = build(
            contract=_load(args.contract),
            header_freeze=_load(args.header_freeze),
            geometry_freeze=_load(args.geometry_freeze),
            spatial_freeze=_load(args.spatial_freeze),
            state_freeze=_load(args.state_freeze),
            operator_freeze=_load(args.operator_freeze),
            operator_contract=_load(args.operator_contract),
            legacy_operator=_load(args.legacy_operator),
            metadata=_load(args.metadata),
            preintake=_load(args.preintake),
            geometry_path=args.geometry,
            state_path=args.state,
            geometry_freeze_path=args.geometry_freeze,
            spatial_freeze_path=args.spatial_freeze,
            state_freeze_path=args.state_freeze,
            operator_freeze_path=args.operator_freeze,
        )
        intake, intake_receipt, protocol, quality, receipt = values
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19PrepilotError,
    ) as exc:
        intake = intake_receipt = protocol = quality = None
        receipt = {
            "schema": "structural.boreal_19island_prepilot_contract_result.v1_02",
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

    outputs = (
        (args.output_intake, intake),
        (args.output_intake_receipt, intake_receipt),
        (args.output_protocol, protocol),
        (args.output_quality, quality),
        (args.receipt, receipt),
    )
    for path, value in outputs:
        if path is not None and value is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(value, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
