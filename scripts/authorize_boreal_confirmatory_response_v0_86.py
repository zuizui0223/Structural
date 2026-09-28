#!/usr/bin/env python3
"""Authorize one-shot boreal confirmatory response after exact v0.85 replay."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from scripts.freeze_boreal_preconfirmatory_model_v0_85 import (
    DEFAULT_EXTERNAL,
    freeze as freeze_v085,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_confirmatory_response_authorization_contract_v0_86.json"
)
DEFAULT_V085_CONTRACT = (
    ROOT / "development/boreal_preconfirmatory_model_contract_v0_85.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)


class BorealConfirmatoryAuthorizationError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealConfirmatoryAuthorizationError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def authorize(
    *,
    pilot_execution: Mapping,
    pilot_snapshot: Mapping,
    geometry_csv: Path,
    projection_receipt: Mapping,
    habitat_reference_csv: Path,
    habitat_receipt: Mapping,
    spatial_receipt: Mapping,
    operator: Mapping,
    operator_receipt: Mapping,
    model_receipt: Mapping,
    predictions_text: str,
    external: Mapping,
    contract: Mapping,
    v085_contract: Mapping,
    metadata: Mapping,
    model_receipt_sha256: str,
) -> dict:
    candidate = contract["candidate_id"]
    required = contract["required_model_freeze"]

    if model_receipt.get("schema") != required["schema"]:
        raise BorealConfirmatoryAuthorizationError(
            "unexpected v0.85 model receipt schema"
        )
    if model_receipt.get("status") != required["status"]:
        raise BorealConfirmatoryAuthorizationError(
            "v0.85 model freeze did not qualify"
        )
    if model_receipt.get("candidate_id") != candidate:
        raise BorealConfirmatoryAuthorizationError(
            "v0.85 candidate identity mismatch"
        )
    for key, expected in (
        ("confirmatory_target_values_opened", 0),
        ("confirmatory_response_authorized", False),
        ("effect_size", None),
        ("prediction_score", None),
        ("counts_as_empirical_evidence", False),
    ):
        if model_receipt.get(key) != expected:
            raise BorealConfirmatoryAuthorizationError(
                f"v0.85 boundary mismatch: {key}"
            )

    replay_receipt, replay_predictions = freeze_v085(
        pilot_execution=pilot_execution,
        pilot_snapshot=pilot_snapshot,
        geometry_csv=geometry_csv,
        projection_receipt=projection_receipt,
        habitat_reference_csv=habitat_reference_csv,
        habitat_receipt=habitat_receipt,
        spatial_receipt=spatial_receipt,
        operator=operator,
        operator_receipt=operator_receipt,
        external=external,
        contract=v085_contract,
    )
    if replay_receipt != dict(model_receipt):
        raise BorealConfirmatoryAuthorizationError(
            "v0.85 model receipt does not exact-replay"
        )
    if replay_predictions != predictions_text:
        raise BorealConfirmatoryAuthorizationError(
            "v0.85 prediction surface does not exact-replay"
        )
    prediction_sha = hashlib.sha256(
        predictions_text.encode("utf-8")
    ).hexdigest()
    if prediction_sha != model_receipt.get(
        "prediction_surface_sha256"
    ):
        raise BorealConfirmatoryAuthorizationError(
            "prediction surface SHA mismatch"
        )

    if metadata.get("schema") != (
        "structural.boreal_lake_islands_dryad_metadata_result.v0_65"
    ):
        raise BorealConfirmatoryAuthorizationError(
            "unexpected v0.65 metadata schema"
        )
    if metadata.get("response_values_opened") is not False:
        raise BorealConfirmatoryAuthorizationError(
            "v0.65 response boundary violated"
        )
    response = contract["response_file"]
    frozen = metadata.get("focal_files", {}).get(response["name"])
    if not isinstance(frozen, dict):
        raise BorealConfirmatoryAuthorizationError(
            "frozen response metadata missing"
        )
    if (
        frozen.get("file_id") != response["dryad_file_id"]
        or frozen.get("size") != response["expected_size_bytes"]
        or frozen.get("sha256") != response["expected_sha256"]
        or frozen.get("role") != "primary_response"
    ):
        raise BorealConfirmatoryAuthorizationError(
            "confirmatory response identity drift"
        )

    return {
        "schema": "structural.boreal_confirmatory_response_authorization.v0_86",
        "status": "AUTHORIZED_ONE_SHOT_CONFIRMATORY_RESPONSE",
        "candidate_id": candidate,
        "source_model_receipt_sha256": model_receipt_sha256,
        "prediction_surface_sha256": prediction_sha,
        "prediction_row_count": model_receipt["prediction_row_count"],
        "species_count": model_receipt["species_count"],
        "confirmatory_island_count": model_receipt[
            "confirmatory_island_count"
        ],
        "confirmatory_block_count": model_receipt[
            "confirmatory_block_count"
        ],
        "response_file": {
            "name": response["name"],
            "dryad_file_id": response["dryad_file_id"],
            "size_bytes": response["expected_size_bytes"],
            "sha256": response["expected_sha256"],
        },
        "allowed_semantic_access": dict(
            contract["allowed_semantic_access_after_authorization"]
        ),
        "router": {
            "implementation": contract["router"]["implementation"],
            "pilot_target_values_parsed_must_equal": 0,
            "nonfocal_confirmatory_target_values_parsed_must_equal": 0,
        },
        "confirmatory_response_authorized": True,
        "authorization_consumed": False,
        "effect_size": None,
        "prediction_score": None,
        "counts_as_empirical_evidence": False,
        "eligible_action": "execute_one_shot_confirmatory_scoring",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot_execution", type=Path)
    parser.add_argument("pilot_snapshot", type=Path)
    parser.add_argument("geometry_csv", type=Path)
    parser.add_argument("projection_receipt", type=Path)
    parser.add_argument("habitat_reference_csv", type=Path)
    parser.add_argument("habitat_receipt", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("operator_json", type=Path)
    parser.add_argument("operator_receipt", type=Path)
    parser.add_argument("model_receipt", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--external", type=Path, default=DEFAULT_EXTERNAL)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--v085-contract",
        type=Path,
        default=DEFAULT_V085_CONTRACT,
    )
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_confirmatory_response_authorization_contract.v0_86"
        ):
            raise BorealConfirmatoryAuthorizationError(
                "unexpected v0.86 contract schema"
            )
        predictions_text = args.predictions.read_text(encoding="utf-8")
        result = authorize(
            pilot_execution=_load(args.pilot_execution),
            pilot_snapshot=_load(args.pilot_snapshot),
            geometry_csv=args.geometry_csv,
            projection_receipt=_load(args.projection_receipt),
            habitat_reference_csv=args.habitat_reference_csv,
            habitat_receipt=_load(args.habitat_receipt),
            spatial_receipt=_load(args.spatial_receipt),
            operator=_load(args.operator_json),
            operator_receipt=_load(args.operator_receipt),
            model_receipt=_load(args.model_receipt),
            predictions_text=predictions_text,
            external=_load(args.external),
            contract=contract,
            v085_contract=_load(args.v085_contract),
            metadata=_load(args.metadata),
            model_receipt_sha256=sha256_file(args.model_receipt),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealConfirmatoryAuthorizationError,
    ) as exc:
        result = {
            "schema": "structural.boreal_confirmatory_response_authorization.v0_86",
            "status": "STOP",
            "reason": str(exc),
            "confirmatory_response_authorized": False,
            "authorization_consumed": False,
            "effect_size": None,
            "prediction_score": None,
            "counts_as_empirical_evidence": False,
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
