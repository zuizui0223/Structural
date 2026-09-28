#!/usr/bin/env python3
"""Authorize one-shot boreal beetle burned-pilot response access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from scripts.build_boreal_prepilot_contracts_v0_80 import build as build_v080
from scripts.validate_independent_system_intake_v0_12 import canonical_fingerprint
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
    ROOT / "development/boreal_beetle_pilot_response_authorization_contract_v0_81.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
DEFAULT_V080_CONTRACT = (
    ROOT / "development/boreal_lake_islands_prepilot_contract_builder_v0_80.json"
)
SHA_HEX = set("0123456789abcdef")


class BorealPilotAuthorizationError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealPilotAuthorizationError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha(value: object, length: int = 64) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and set(value.lower()) <= SHA_HEX
    )


def authorize(
    intake: Mapping,
    intake_receipt: Mapping,
    protocol_mapping: Mapping,
    quality_mapping: Mapping,
    prepilot_receipt: Mapping,
    spatial_receipt: Mapping,
    *,
    contract: Mapping,
    v080_contract: Mapping,
    metadata: Mapping,
    spatial_receipt_sha256: str,
) -> dict:
    candidate = contract["candidate_id"]

    if intake.get("schema") != "structural.independent_system_intake.v0_12":
        raise BorealPilotAuthorizationError("unexpected v0.12 intake schema")
    if intake.get("system_id") != candidate:
        raise BorealPilotAuthorizationError("v0.12 candidate identity mismatch")
    if intake.get("response_firewall_state") != "response_sealed":
        raise BorealPilotAuthorizationError("response firewall is not sealed")
    if intake.get("response_values_accessed") is not False:
        raise BorealPilotAuthorizationError("response values already accessed")

    # Replay the complete response-sealed v0.80 constructor rather than
    # trusting a claimed prepilot receipt.
    replay_protocol, replay_quality, replay_receipt = build_v080(
        intake,
        intake_receipt,
        spatial_receipt,
        spatial_receipt_sha256=spatial_receipt_sha256,
        contract=v080_contract,
    )
    if dict(protocol_mapping) != replay_protocol:
        raise BorealPilotAuthorizationError(
            "v0.31 protocol does not exact-replay v0.80"
        )
    if dict(quality_mapping) != replay_quality:
        raise BorealPilotAuthorizationError(
            "v0.42 quality contract does not exact-replay v0.80"
        )
    if dict(prepilot_receipt) != replay_receipt:
        raise BorealPilotAuthorizationError(
            "v0.80 receipt does not exact-replay from frozen parents"
        )

    response_files = [
        row for row in intake.get("source_files", [])
        if isinstance(row, dict) and row.get("role") == "response"
    ]
    if len(response_files) != 1:
        raise BorealPilotAuthorizationError(
            "v0.12 intake must contain exactly one response file"
        )
    response = response_files[0]
    if response.get("file_id") != contract["response_file"]["name"]:
        raise BorealPilotAuthorizationError("response file identity mismatch")
    if response.get("opened") is not False:
        raise BorealPilotAuthorizationError("response file is not sealed")

    meta = metadata.get("focal_files", {}).get(
        contract["response_file"]["name"]
    )
    if not isinstance(meta, dict):
        raise BorealPilotAuthorizationError("frozen response metadata missing")
    for key, expected in (
        ("file_id", contract["response_file"]["dryad_file_id"]),
        ("size", contract["response_file"]["expected_size_bytes"]),
        ("sha256", contract["response_file"]["expected_sha256"]),
    ):
        if meta.get(key) != expected:
            raise BorealPilotAuthorizationError(
                f"frozen response metadata drift: {key}"
            )
    if meta.get("role") != "primary_response":
        raise BorealPilotAuthorizationError("frozen response metadata role drift")
    if response.get("sha256") != meta["sha256"]:
        raise BorealPilotAuthorizationError(
            "v0.12 response SHA does not match frozen Dryad metadata"
        )

    protocol = protocol_from_mapping(dict(protocol_mapping))
    quality = contract_from_mapping(dict(quality_mapping))
    pfp = protocol_fingerprint(protocol)
    qfp = contract_fingerprint(quality)

    required = contract["required_prepilot_receipt"]
    if prepilot_receipt.get("schema") != required["schema"]:
        raise BorealPilotAuthorizationError(
            "unexpected v0.80 prepilot receipt schema"
        )
    if prepilot_receipt.get("status") != required["status"]:
        raise BorealPilotAuthorizationError("v0.80 prepilot receipt did not qualify")
    if prepilot_receipt.get("candidate_id") != candidate:
        raise BorealPilotAuthorizationError("v0.80 candidate identity mismatch")
    if prepilot_receipt.get("parent_intake_fingerprint") != (
        canonical_fingerprint(dict(intake))
    ):
        raise BorealPilotAuthorizationError("v0.80 intake fingerprint mismatch")
    if prepilot_receipt.get("protocol_fingerprint") != pfp:
        raise BorealPilotAuthorizationError("v0.31 protocol fingerprint mismatch")
    if prepilot_receipt.get("quality_contract_fingerprint") != qfp:
        raise BorealPilotAuthorizationError("v0.42 quality fingerprint mismatch")
    if quality.parent_protocol_fingerprint != pfp:
        raise BorealPilotAuthorizationError(
            "v0.42 is not bound to exact v0.31 fingerprint"
        )
    for key in (
        "pilot_response_authorized",
        "confirmatory_response_authorized",
        "mechanism_response_authorized",
    ):
        if prepilot_receipt.get(key) is not False:
            raise BorealPilotAuthorizationError(
                f"v0.80 response ceiling violated: {key}"
            )
    if prepilot_receipt.get("effect_size") is not None:
        raise BorealPilotAuthorizationError("v0.80 effect_size must be null")
    if prepilot_receipt.get("prediction_score") is not None:
        raise BorealPilotAuthorizationError("v0.80 prediction_score must be null")
    if prepilot_receipt.get("predictive_denominator_contribution") != 0:
        raise BorealPilotAuthorizationError(
            "v0.80 predictive denominator must be zero"
        )

    if spatial_receipt.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealPilotAuthorizationError("unexpected v0.75 spatial schema")
    if spatial_receipt.get("status") != (
        "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY"
    ):
        raise BorealPilotAuthorizationError("v0.75 spatial receipt did not qualify")
    if spatial_receipt.get("candidate_id") != candidate:
        raise BorealPilotAuthorizationError("v0.75 candidate identity mismatch")
    if prepilot_receipt.get("source_spatial_receipt_sha256") != (
        spatial_receipt_sha256
    ):
        raise BorealPilotAuthorizationError(
            "v0.75 receipt SHA does not bind v0.80"
        )
    if protocol.pilot_partition != tuple(
        spatial_receipt.get("pilot_block_ids") or ()
    ):
        raise BorealPilotAuthorizationError(
            "v0.31 pilot blocks drift from v0.75"
        )
    if protocol.confirmatory_partition != tuple(
        spatial_receipt.get("confirmatory_block_ids") or ()
    ):
        raise BorealPilotAuthorizationError(
            "v0.31 confirmatory blocks drift from v0.75"
        )
    island_to_block = spatial_receipt.get("island_to_block")
    if not isinstance(island_to_block, dict) or len(island_to_block) != 42:
        raise BorealPilotAuthorizationError(
            "v0.75 island-to-block mapping is not exact 42-island support"
        )

    return {
        "schema": "structural.boreal_beetle_pilot_response_authorization.v0_81",
        "status": "AUTHORIZED_ONE_SHOT_BURNED_PILOT_RESPONSE",
        "candidate_id": candidate,
        "parent_intake_fingerprint": canonical_fingerprint(dict(intake)),
        "protocol_fingerprint": pfp,
        "quality_contract_fingerprint": qfp,
        "source_spatial_receipt_sha256": spatial_receipt_sha256,
        "response_file": {
            "name": contract["response_file"]["name"],
            "dryad_file_id": meta["file_id"],
            "size_bytes": meta["size"],
            "sha256": meta["sha256"],
        },
        "allowed_semantic_access": dict(
            contract["allowed_semantic_access_after_authorization"]
        ),
        "router": dict(contract["router"]),
        "pilot_response_authorized": True,
        "confirmatory_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "authorization_consumed": False,
        "next_action": contract["authorization_ceiling"]["next_action"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake", type=Path)
    parser.add_argument("intake_receipt", type=Path)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("quality", type=Path)
    parser.add_argument("prepilot_receipt", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument(
        "--v080-contract", type=Path, default=DEFAULT_V080_CONTRACT
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_beetle_pilot_response_authorization_contract.v0_81"
        ):
            raise BorealPilotAuthorizationError(
                "unexpected v0.81 authorization contract schema"
            )
        result = authorize(
            _load(args.intake),
            _load(args.intake_receipt),
            _load(args.protocol),
            _load(args.quality),
            _load(args.prepilot_receipt),
            _load(args.spatial_receipt),
            contract=contract,
            v080_contract=_load(args.v080_contract),
            metadata=_load(args.metadata),
            spatial_receipt_sha256=sha256_file(args.spatial_receipt),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealPilotAuthorizationError,
    ) as exc:
        result = {
            "schema": "structural.boreal_beetle_pilot_response_authorization.v0_81",
            "status": "STOP",
            "reason": str(exc),
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
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
