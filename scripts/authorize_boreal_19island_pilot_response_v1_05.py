#!/usr/bin/env python3
"""Authorize one future burned-pilot opening for the frozen 19-island system.

This gate opens no response bytes. It exact-checks the committed response-sealed
pre-pilot chain and emits a one-shot authorization that permits a later executor
to decode occurrence values only for the six frozen pilot islands.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from structural.response_quality_attrition import (
    contract_fingerprint,
    contract_from_mapping,
)
from structural.transition_pilot_protocol import (
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_pilot_response_authorization_contract_v1_05.json"
)
DEFAULT_INTAKE = (
    ROOT / "development/boreal_19island_response_sealed_intake_v1_02.json"
)
DEFAULT_INTAKE_RECEIPT = (
    ROOT / "development/boreal_19island_response_sealed_intake_receipt_v1_02.json"
)
DEFAULT_FREEZE = (
    ROOT / "development/boreal_19island_prepilot_freeze_v1_04.json"
)
DEFAULT_PROTOCOL = (
    ROOT / "development/boreal_19island_v031_protocol_v1_03.json"
)
DEFAULT_QUALITY = (
    ROOT / "development/boreal_19island_v042_quality_contract_v1_03.json"
)
DEFAULT_PREPILOT_RECEIPT = (
    ROOT / "development/boreal_19island_prepilot_receipt_v1_03.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
DEFAULT_FULL_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class Boreal19PilotAuthorizationError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19PilotAuthorizationError(
            f"{path.name} must contain a JSON object"
        )
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
        raise Boreal19PilotAuthorizationError(f"invalid SHA-256: {label}")
    return value


def authorize(
    intake: Mapping,
    intake_receipt: Mapping,
    prepilot_freeze: Mapping,
    protocol_mapping: Mapping,
    quality_mapping: Mapping,
    prepilot_receipt: Mapping,
    metadata: Mapping,
    full_universe: Mapping,
    *,
    contract: Mapping,
    observed_file_sha256: Mapping[str, str],
) -> dict:
    candidate = contract["candidate_id"]
    required = contract["required_parent_identity"]

    if intake.get("schema") != (
        "structural.boreal_19island_response_sealed_intake.v1_02"
    ):
        raise Boreal19PilotAuthorizationError("unexpected v1.02 intake schema")
    if intake.get("status") != (
        "RESPONSE_SEALED_READY_FOR_PREPILOT_CONSTRUCTION"
    ):
        raise Boreal19PilotAuthorizationError("v1.02 intake did not qualify")
    if intake.get("system_id") != candidate:
        raise Boreal19PilotAuthorizationError("v1.02 candidate mismatch")
    if intake.get("response_firewall_state") != "response_sealed":
        raise Boreal19PilotAuthorizationError("response firewall is not sealed")
    if intake.get("response_values_accessed") is not False:
        raise Boreal19PilotAuthorizationError("response already accessed")

    intake_fp = canonical_sha256(dict(intake))
    if intake_fp != required["parent_intake_fingerprint"]:
        raise Boreal19PilotAuthorizationError(
            "v1.02 intake fingerprint drift from frozen parent"
        )
    if intake_receipt.get("schema") != (
        "structural.boreal_19island_response_sealed_intake_receipt.v1_02"
    ):
        raise Boreal19PilotAuthorizationError(
            "unexpected v1.02 intake receipt schema"
        )
    if intake_receipt.get("status") != (
        "ELIGIBLE_TO_BUILD_V031_V042_RESPONSE_SEALED"
    ):
        raise Boreal19PilotAuthorizationError("v1.02 intake receipt did not qualify")
    if intake_receipt.get("intake_fingerprint") != intake_fp:
        raise Boreal19PilotAuthorizationError("v1.02 intake receipt fingerprint drift")
    for key, expected in (
        ("pilot_response_authorized", False),
        ("confirmatory_response_authorized", False),
        ("counts_as_empirical_evidence", False),
        ("predictive_denominator_contribution", 0),
    ):
        if intake_receipt.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"v1.02 intake receipt ceiling mismatch: {key}"
            )

    if prepilot_freeze.get("schema") != (
        "structural.boreal_19island_prepilot_freeze.v1_04"
    ):
        raise Boreal19PilotAuthorizationError("unexpected v1.04 freeze schema")
    if prepilot_freeze.get("status") != (
        "PREPILOT_CONTRACTS_COMMITTED_RESPONSE_SEALED"
    ):
        raise Boreal19PilotAuthorizationError("v1.04 freeze did not qualify")
    if prepilot_freeze.get("candidate_id") != candidate:
        raise Boreal19PilotAuthorizationError("v1.04 candidate mismatch")
    if prepilot_freeze.get("pilot_authorization_may_be_built") is not True:
        raise Boreal19PilotAuthorizationError(
            "v1.04 does not authorize construction of pilot authorization"
        )

    execution = prepilot_freeze.get("source_execution")
    if not isinstance(execution, dict):
        raise Boreal19PilotAuthorizationError("v1.04 source execution missing")
    for key, expected in (
        ("run_id", required["source_workflow_run_id"]),
        ("head_sha", required["source_workflow_head_sha"]),
        ("artifact_id", required["source_artifact_id"]),
        ("artifact_digest", required["source_artifact_digest"]),
    ):
        if execution.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"v1.04 source execution drift: {key}"
            )

    freeze_files = prepilot_freeze.get("files")
    if not isinstance(freeze_files, dict):
        raise Boreal19PilotAuthorizationError("v1.04 file identities missing")
    file_rules = (
        ("protocol", "protocol_file_sha256"),
        ("quality_contract", "quality_contract_file_sha256"),
        ("prepilot_receipt", "prepilot_receipt_file_sha256"),
    )
    for label, expected_key in file_rules:
        row = freeze_files.get(label)
        if not isinstance(row, dict):
            raise Boreal19PilotAuthorizationError(
                f"v1.04 file identity missing: {label}"
            )
        frozen_sha = _sha(row.get("sha256"), f"v1.04 {label}")
        expected_sha = _sha(required[expected_key], expected_key)
        observed_sha = _sha(observed_file_sha256.get(label), f"observed {label}")
        if frozen_sha != expected_sha or observed_sha != expected_sha:
            raise Boreal19PilotAuthorizationError(
                f"exact pre-pilot file SHA mismatch: {label}"
            )

    if prepilot_freeze.get("parent_intake_fingerprint") != intake_fp:
        raise Boreal19PilotAuthorizationError(
            "v1.04 parent intake fingerprint mismatch"
        )
    if prepilot_freeze.get("source_operator_fingerprint") != (
        required["source_operator_fingerprint"]
    ):
        raise Boreal19PilotAuthorizationError(
            "v1.04 source operator fingerprint mismatch"
        )

    protocol = protocol_from_mapping(dict(protocol_mapping))
    quality = contract_from_mapping(dict(quality_mapping))
    pfp = protocol_fingerprint(protocol)
    qfp = contract_fingerprint(quality)
    if pfp != required["protocol_fingerprint"]:
        raise Boreal19PilotAuthorizationError("v0.31 protocol fingerprint drift")
    if qfp != required["quality_contract_fingerprint"]:
        raise Boreal19PilotAuthorizationError("v0.42 quality fingerprint drift")
    if quality.parent_protocol_fingerprint != pfp:
        raise Boreal19PilotAuthorizationError(
            "v0.42 is not bound to exact v0.31 protocol"
        )
    if prepilot_freeze.get("protocol_fingerprint") != pfp:
        raise Boreal19PilotAuthorizationError(
            "v1.04 protocol fingerprint mismatch"
        )
    if prepilot_freeze.get("quality_contract_fingerprint") != qfp:
        raise Boreal19PilotAuthorizationError(
            "v1.04 quality fingerprint mismatch"
        )

    if prepilot_receipt.get("schema") != (
        "structural.boreal_19island_prepilot_contract_result.v1_03"
    ):
        raise Boreal19PilotAuthorizationError("unexpected v1.03 receipt schema")
    if prepilot_receipt.get("status") != (
        "V031_AND_V042_FROZEN_RESPONSE_REMAINS_SEALED"
    ):
        raise Boreal19PilotAuthorizationError("v1.03 receipt did not qualify")
    if prepilot_receipt.get("parent_intake_fingerprint") != intake_fp:
        raise Boreal19PilotAuthorizationError("v1.03 intake fingerprint mismatch")
    if prepilot_receipt.get("protocol_fingerprint") != pfp:
        raise Boreal19PilotAuthorizationError("v1.03 protocol fingerprint mismatch")
    if prepilot_receipt.get("quality_contract_fingerprint") != qfp:
        raise Boreal19PilotAuthorizationError("v1.03 quality fingerprint mismatch")
    for key, expected in (
        ("pilot_response_authorized", False),
        ("confirmatory_response_authorized", False),
        ("mechanism_response_authorized", False),
        ("effect_size", None),
        ("prediction_score", None),
        ("predictive_denominator_contribution", 0),
        ("counts_as_empirical_evidence", False),
    ):
        if prepilot_receipt.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"v1.03 receipt ceiling mismatch: {key}"
            )

    population = intake.get("population")
    if not isinstance(population, dict):
        raise Boreal19PilotAuthorizationError("v1.02 population missing")
    analysis_order = population.get("island_order")
    pilot_islands = population.get("pilot_islands")
    confirmatory_islands = population.get("confirmatory_islands")
    island_to_block = population.get("island_to_block")
    if not isinstance(analysis_order, list) or len(analysis_order) != 19:
        raise Boreal19PilotAuthorizationError("analysis population is not 19 islands")
    if not isinstance(pilot_islands, list) or len(pilot_islands) != 6:
        raise Boreal19PilotAuthorizationError("pilot population is not 6 islands")
    if (
        not isinstance(confirmatory_islands, list)
        or len(confirmatory_islands) != 13
    ):
        raise Boreal19PilotAuthorizationError(
            "confirmatory population is not 13 islands"
        )
    if set(pilot_islands) & set(confirmatory_islands):
        raise Boreal19PilotAuthorizationError(
            "pilot and confirmatory islands overlap"
        )
    if set(pilot_islands) | set(confirmatory_islands) != set(analysis_order):
        raise Boreal19PilotAuthorizationError(
            "pilot/confirmatory islands do not cover analysis population"
        )
    if not isinstance(island_to_block, dict) or set(island_to_block) != set(
        analysis_order
    ):
        raise Boreal19PilotAuthorizationError("analysis island-to-block map drift")
    if tuple(protocol.pilot_partition) != tuple(
        population.get("pilot_block_ids") or ()
    ):
        raise Boreal19PilotAuthorizationError("v0.31 pilot block order drift")
    if tuple(protocol.confirmatory_partition) != tuple(
        population.get("confirmatory_block_ids") or ()
    ):
        raise Boreal19PilotAuthorizationError("v0.31 confirmatory block order drift")

    if full_universe.get("row_count") != 42:
        raise Boreal19PilotAuthorizationError("full source universe is not 42 islands")
    full = full_universe.get("current_study_island_universe", {}).get("codes")
    if not isinstance(full, list) or len(full) != 42 or len(set(full)) != 42:
        raise Boreal19PilotAuthorizationError("full source island codes invalid")
    if not set(analysis_order) < set(full):
        raise Boreal19PilotAuthorizationError(
            "analysis population is not a strict subset of 42-island source universe"
        )
    excluded = [island for island in full if island not in set(analysis_order)]
    if len(excluded) != 23:
        raise Boreal19PilotAuthorizationError("excluded island count is not 23")

    response_rule = contract["response_file"]
    response = intake.get("response_file")
    if not isinstance(response, dict) or response.get("opened") is not False:
        raise Boreal19PilotAuthorizationError("v1.02 response file is not sealed")
    for key, expected in (
        ("name", response_rule["name"]),
        ("dryad_file_id", response_rule["dryad_file_id"]),
        ("size_bytes", response_rule["expected_size_bytes"]),
        ("sha256", response_rule["expected_sha256"]),
    ):
        if response.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"v1.02 response identity drift: {key}"
            )

    if metadata.get("schema") != (
        "structural.boreal_lake_islands_dryad_metadata_result.v0_65"
    ):
        raise Boreal19PilotAuthorizationError("unexpected Dryad metadata schema")
    if metadata.get("response_values_opened") is not False:
        raise Boreal19PilotAuthorizationError(
            "Dryad metadata response boundary violated"
        )
    meta = metadata.get("focal_files", {}).get(response_rule["name"])
    if not isinstance(meta, dict):
        raise Boreal19PilotAuthorizationError("frozen response metadata missing")
    for key, expected in (
        ("file_id", response_rule["dryad_file_id"]),
        ("size", response_rule["expected_size_bytes"]),
        ("sha256", response_rule["expected_sha256"]),
        ("role", "primary_response"),
    ):
        if meta.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"frozen response metadata drift: {key}"
            )

    freeze_boundary = prepilot_freeze.get("response_boundary")
    if not isinstance(freeze_boundary, dict):
        raise Boreal19PilotAuthorizationError("v1.04 response boundary missing")
    for key, expected in (
        ("pilot_response_opened", False),
        ("confirmatory_response_opened", False),
        ("pilot_response_authorized", False),
        ("confirmatory_response_authorized", False),
        ("counts_as_empirical_evidence", False),
        ("predictive_denominator_contribution", 0),
    ):
        if freeze_boundary.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"v1.04 response boundary violated: {key}"
            )

    core = {
        "schema": "structural.boreal_19island_pilot_response_authorization.v1_05",
        "status": contract["authorization_ceiling"]["status"],
        "candidate_id": candidate,
        "parent_intake_fingerprint": intake_fp,
        "source_operator_fingerprint": required["source_operator_fingerprint"],
        "protocol_fingerprint": pfp,
        "quality_contract_fingerprint": qfp,
        "response_file": {
            "name": response_rule["name"],
            "dryad_file_id": response_rule["dryad_file_id"],
            "size_bytes": response_rule["expected_size_bytes"],
            "sha256": response_rule["expected_sha256"],
            "expected_species_columns": response_rule["expected_species_columns"],
        },
        "full_source_island_order": list(full),
        "analysis_island_order": list(analysis_order),
        "pilot_islands": list(pilot_islands),
        "confirmatory_islands": list(confirmatory_islands),
        "excluded_islands": excluded,
        "island_to_block": dict(island_to_block),
        "pilot_block_ids": list(protocol.pilot_partition),
        "confirmatory_block_ids": list(protocol.confirmatory_partition),
        "allowed_semantic_access": dict(
            contract["allowed_semantic_access_after_authorization"]
        ),
        "router": dict(contract["router"]),
        "pilot_response_authorized": True,
        "confirmatory_response_authorized": False,
        "authorization_consumed": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "response_values_opened_by_authorization": False,
        "next_action": contract["authorization_ceiling"]["next_action"],
    }
    return {
        **core,
        "authorization_fingerprint": canonical_sha256(core),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--intake", type=Path, default=DEFAULT_INTAKE)
    parser.add_argument(
        "--intake-receipt",
        type=Path,
        default=DEFAULT_INTAKE_RECEIPT,
    )
    parser.add_argument("--prepilot-freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--quality", type=Path, default=DEFAULT_QUALITY)
    parser.add_argument(
        "--prepilot-receipt",
        type=Path,
        default=DEFAULT_PREPILOT_RECEIPT,
    )
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument(
        "--full-universe",
        type=Path,
        default=DEFAULT_FULL_UNIVERSE,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    file_paths = {
        "protocol": args.protocol,
        "quality_contract": args.quality,
        "prepilot_receipt": args.prepilot_receipt,
    }
    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_19island_pilot_response_authorization_contract.v1_05"
        ):
            raise Boreal19PilotAuthorizationError(
                "unexpected v1.05 authorization contract schema"
            )
        result = authorize(
            _load(args.intake),
            _load(args.intake_receipt),
            _load(args.prepilot_freeze),
            _load(args.protocol),
            _load(args.quality),
            _load(args.prepilot_receipt),
            _load(args.metadata),
            _load(args.full_universe),
            contract=contract,
            observed_file_sha256={
                name: sha256_file(path)
                for name, path in file_paths.items()
            },
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19PilotAuthorizationError,
    ) as exc:
        result = {
            "schema": "structural.boreal_19island_pilot_response_authorization.v1_05",
            "status": "STOP",
            "reason": str(exc),
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "authorization_consumed": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "response_values_opened_by_authorization": False,
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
