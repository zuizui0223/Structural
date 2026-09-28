#!/usr/bin/env python3
"""Authorize one future one-shot burned pilot for the frozen boreal 19-island system.

This stage is response-independent. It exact-replays v1.03 from the committed
v1.02 intake, verifies the committed v1.04 bundle byte identities, verifies the
frozen Dryad response identity from metadata only, and emits an authorization.
It never downloads or opens the beetle response file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.build_boreal_19island_prepilot_contracts_v1_03 import (  # noqa: E402
    build as build_v103,
)
from structural.response_quality_attrition import (  # noqa: E402
    contract_fingerprint,
    contract_from_mapping,
)
from structural.transition_pilot_protocol import (  # noqa: E402
    protocol_fingerprint,
    protocol_from_mapping,
)


DEFAULT_CONTRACT = (
    ROOT
    / "development/boreal_19island_pilot_response_authorization_contract_v1_05.json"
)
DEFAULT_INTAKE = (
    ROOT / "development/boreal_19island_response_sealed_intake_v1_02.json"
)
DEFAULT_INTAKE_RECEIPT = (
    ROOT
    / "development/boreal_19island_response_sealed_intake_receipt_v1_02.json"
)
DEFAULT_V103_CONTRACT = (
    ROOT / "development/boreal_19island_prepilot_contract_builder_v1_03.json"
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
DEFAULT_PREPILOT = (
    ROOT / "development/boreal_19island_prepilot_receipt_v1_03.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
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
    v103_contract: Mapping,
    freeze: Mapping,
    protocol_mapping: Mapping,
    quality_mapping: Mapping,
    prepilot_receipt: Mapping,
    metadata: Mapping,
    *,
    contract: Mapping,
    file_sha256: Mapping[str, str],
) -> dict:
    candidate = contract["candidate_id"]
    required = contract["required_prepilot_freeze"]

    if intake.get("schema") != "structural.boreal_19island_response_sealed_intake.v1_02":
        raise Boreal19PilotAuthorizationError("unexpected v1.02 intake schema")
    if intake.get("status") != "RESPONSE_SEALED_READY_FOR_PREPILOT_CONSTRUCTION":
        raise Boreal19PilotAuthorizationError("v1.02 intake status did not qualify")
    if intake.get("system_id") != candidate:
        raise Boreal19PilotAuthorizationError("v1.02 candidate identity mismatch")
    if intake.get("response_firewall_state") != "response_sealed":
        raise Boreal19PilotAuthorizationError("response firewall is not sealed")
    if intake.get("response_values_accessed") is not False:
        raise Boreal19PilotAuthorizationError("biological response already accessed")
    response = intake.get("response_file")
    if not isinstance(response, dict) or response.get("opened") is not False:
        raise Boreal19PilotAuthorizationError("intake response file is not sealed")

    population = intake.get("population")
    expected_population = contract["analysis_population"]
    if not isinstance(population, dict):
        raise Boreal19PilotAuthorizationError("v1.02 population missing")
    if population.get("island_count") != expected_population["island_count"]:
        raise Boreal19PilotAuthorizationError("analysis island count drift")
    if population.get("pilot_islands") != expected_population["pilot_islands"]:
        raise Boreal19PilotAuthorizationError("pilot island population drift")
    if population.get("confirmatory_islands") != expected_population["confirmatory_islands"]:
        raise Boreal19PilotAuthorizationError("confirmatory island population drift")
    if len(population.get("pilot_block_ids") or []) != expected_population["pilot_block_count"]:
        raise Boreal19PilotAuthorizationError("pilot block count drift")
    if len(population.get("confirmatory_block_ids") or []) != expected_population["confirmatory_block_count"]:
        raise Boreal19PilotAuthorizationError("confirmatory block count drift")

    if intake_receipt.get("schema") != (
        "structural.boreal_19island_response_sealed_intake_receipt.v1_02"
    ):
        raise Boreal19PilotAuthorizationError("unexpected v1.02 intake receipt schema")
    if intake_receipt.get("status") != "ELIGIBLE_TO_BUILD_V031_V042_RESPONSE_SEALED":
        raise Boreal19PilotAuthorizationError("v1.02 intake receipt did not qualify")
    if intake_receipt.get("intake_fingerprint") != required["parent_intake_fingerprint"]:
        raise Boreal19PilotAuthorizationError("v1.02 intake fingerprint drift")
    if canonical_sha256(dict(intake)) != required["parent_intake_fingerprint"]:
        raise Boreal19PilotAuthorizationError("v1.02 intake does not canonical-replay")

    if freeze.get("schema") != required["schema"]:
        raise Boreal19PilotAuthorizationError("unexpected v1.04 freeze schema")
    if freeze.get("status") != required["status"]:
        raise Boreal19PilotAuthorizationError("v1.04 pre-pilot freeze did not qualify")
    for key in (
        "parent_intake_fingerprint",
        "source_operator_fingerprint",
        "protocol_fingerprint",
        "quality_contract_fingerprint",
    ):
        if freeze.get(key) != required[key]:
            raise Boreal19PilotAuthorizationError(f"v1.04 freeze drift: {key}")
    if freeze.get("pilot_authorization_may_be_built") is not True:
        raise Boreal19PilotAuthorizationError("v1.04 does not authorize auth construction")
    boundary = freeze.get("response_boundary")
    if not isinstance(boundary, dict):
        raise Boreal19PilotAuthorizationError("v1.04 response boundary missing")
    for key, expected in (
        ("pilot_response_opened", False),
        ("confirmatory_response_opened", False),
        ("pilot_response_authorized", False),
        ("confirmatory_response_authorized", False),
        ("counts_as_empirical_evidence", False),
        ("predictive_denominator_contribution", 0),
    ):
        if boundary.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"v1.04 response ceiling violated: {key}"
            )

    required_file_keys = {
        "intake",
        "intake_receipt",
        "freeze",
        "protocol",
        "quality_contract",
        "prepilot_receipt",
    }
    if set(file_sha256) != required_file_keys:
        raise Boreal19PilotAuthorizationError("authorization file SHA keys drift")
    for key, value in file_sha256.items():
        _sha(value, key)

    freeze_files = freeze.get("files")
    if not isinstance(freeze_files, dict):
        raise Boreal19PilotAuthorizationError("v1.04 exact files missing")
    checks = (
        ("protocol", "protocol", "protocol_file_sha256"),
        ("quality_contract", "quality_contract", "quality_contract_file_sha256"),
        ("prepilot_receipt", "prepilot_receipt", "prepilot_receipt_file_sha256"),
    )
    for local_key, freeze_key, required_key in checks:
        observed = file_sha256[local_key]
        if freeze_files.get(freeze_key, {}).get("sha256") != observed:
            raise Boreal19PilotAuthorizationError(
                f"committed {local_key} bytes drift from v1.04 freeze"
            )
        if observed != required[required_key]:
            raise Boreal19PilotAuthorizationError(
                f"committed {local_key} bytes drift from authorization contract"
            )

    replay_protocol, replay_quality, replay_receipt = build_v103(
        intake,
        intake_receipt,
        contract=v103_contract,
        intake_file_sha256=file_sha256["intake"],
        intake_receipt_file_sha256=file_sha256["intake_receipt"],
    )
    if dict(protocol_mapping) != replay_protocol:
        raise Boreal19PilotAuthorizationError(
            "v0.31 protocol does not exact-replay v1.03"
        )
    if dict(quality_mapping) != replay_quality:
        raise Boreal19PilotAuthorizationError(
            "v0.42 quality contract does not exact-replay v1.03"
        )
    if dict(prepilot_receipt) != replay_receipt:
        raise Boreal19PilotAuthorizationError(
            "v1.03 pre-pilot receipt does not exact-replay"
        )

    protocol = protocol_from_mapping(dict(protocol_mapping))
    quality = contract_from_mapping(dict(quality_mapping))
    pfp = protocol_fingerprint(protocol)
    qfp = contract_fingerprint(quality)
    if pfp != required["protocol_fingerprint"]:
        raise Boreal19PilotAuthorizationError("v0.31 fingerprint drift")
    if qfp != required["quality_contract_fingerprint"]:
        raise Boreal19PilotAuthorizationError("v0.42 fingerprint drift")
    if quality.parent_protocol_fingerprint != pfp:
        raise Boreal19PilotAuthorizationError(
            "v0.42 no longer binds the exact v0.31 protocol"
        )

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
                f"pre-pilot receipt ceiling violated: {key}"
            )

    if metadata.get("schema") != "structural.boreal_lake_islands_dryad_metadata_result.v0_65":
        raise Boreal19PilotAuthorizationError("unexpected frozen Dryad metadata schema")
    if metadata.get("response_values_opened") is not False:
        raise Boreal19PilotAuthorizationError("Dryad metadata response boundary violated")
    response_meta = metadata.get("focal_files", {}).get(
        contract["response_file"]["name"]
    )
    if not isinstance(response_meta, dict):
        raise Boreal19PilotAuthorizationError("frozen beetle response metadata missing")
    for key, expected in (
        ("file_id", contract["response_file"]["dryad_file_id"]),
        ("size", contract["response_file"]["expected_size_bytes"]),
        ("sha256", contract["response_file"]["expected_sha256"]),
        ("role", "primary_response"),
    ):
        if response_meta.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"frozen beetle response identity drift: {key}"
            )
    for key, expected in (
        ("dryad_file_id", response_meta["file_id"]),
        ("size_bytes", response_meta["size"]),
        ("sha256", response_meta["sha256"]),
        ("opened", False),
    ):
        if response.get(key) != expected:
            raise Boreal19PilotAuthorizationError(
                f"v1.02 response identity drift: {key}"
            )

    payload = {
        "schema": "structural.boreal_19island_pilot_response_authorization.v1_05",
        "status": contract["authorization_ceiling"]["status"],
        "candidate_id": candidate,
        "parent_prepilot_freeze_sha256": file_sha256["freeze"],
        "parent_intake_fingerprint": required["parent_intake_fingerprint"],
        "source_operator_fingerprint": required["source_operator_fingerprint"],
        "protocol_fingerprint": pfp,
        "quality_contract_fingerprint": qfp,
        "response_file": {
            "name": contract["response_file"]["name"],
            "dryad_file_id": response_meta["file_id"],
            "size_bytes": response_meta["size"],
            "sha256": response_meta["sha256"],
            "expected_source_island_rows": contract["response_file"][
                "expected_source_island_rows"
            ],
            "expected_species_columns": contract["response_file"][
                "expected_species_columns"
            ],
        },
        "analysis_population": {
            "island_count": expected_population["island_count"],
            "pilot_islands": list(expected_population["pilot_islands"]),
            "confirmatory_islands": list(expected_population["confirmatory_islands"]),
            "excluded_source_island_count": expected_population[
                "excluded_source_island_count"
            ],
            "pilot_block_ids": list(protocol.pilot_partition),
            "confirmatory_block_ids": list(protocol.confirmatory_partition),
        },
        "allowed_semantic_access": dict(
            contract["allowed_semantic_access_after_authorization"]
        ),
        "router_requirements": dict(contract["router_requirements"]),
        "source_file_sha256": dict(file_sha256),
        "pilot_response_authorized": True,
        "confirmatory_response_authorized": False,
        "mechanism_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "authorization_consumed": False,
        "next_action": contract["authorization_ceiling"]["next_action"],
    }
    payload["authorization_fingerprint"] = canonical_sha256(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--intake", type=Path, default=DEFAULT_INTAKE)
    parser.add_argument("--intake-receipt", type=Path, default=DEFAULT_INTAKE_RECEIPT)
    parser.add_argument("--v103-contract", type=Path, default=DEFAULT_V103_CONTRACT)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--quality", type=Path, default=DEFAULT_QUALITY)
    parser.add_argument("--prepilot-receipt", type=Path, default=DEFAULT_PREPILOT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    paths = {
        "intake": args.intake,
        "intake_receipt": args.intake_receipt,
        "freeze": args.freeze,
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
            _load(args.v103_contract),
            _load(args.freeze),
            _load(args.protocol),
            _load(args.quality),
            _load(args.prepilot_receipt),
            _load(args.metadata),
            contract=contract,
            file_sha256={name: sha256_file(path) for name, path in paths.items()},
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
            "mechanism_response_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "authorization_consumed": False,
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
