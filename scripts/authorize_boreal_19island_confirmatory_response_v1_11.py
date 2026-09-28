#!/usr/bin/env python3
"""Authorize one-shot 19-island confirmatory response after exact v1.09 replay."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from scripts.freeze_boreal_19island_preconfirmatory_model_v1_09 import (
    DEFAULT_CONTRACT as DEFAULT_V109_CONTRACT,
    DEFAULT_GEOMETRY,
    DEFAULT_GEOMETRY_FREEZE,
    DEFAULT_LEGACY_OPERATOR,
    DEFAULT_OPERATOR_CONTRACT,
    DEFAULT_OPERATOR_FREEZE,
    DEFAULT_PILOT_EXECUTION,
    DEFAULT_PILOT_FREEZE,
    DEFAULT_PILOT_SNAPSHOT,
    DEFAULT_SPATIAL_FREEZE,
    DEFAULT_STATE,
    DEFAULT_STATE_FREEZE,
    freeze as freeze_v109,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_confirmatory_authorization_contract_v1_11.json"
)
DEFAULT_PRECONFIRMATORY_FREEZE = (
    ROOT / "development/boreal_19island_preconfirmatory_freeze_v1_10.json"
)
DEFAULT_PREDICTIONS = (
    ROOT / "development/boreal_19island_confirmatory_predictions_v1_10.csv"
)
DEFAULT_MODEL_RECEIPT = (
    ROOT / "development/boreal_19island_preconfirmatory_model_receipt_v1_10.json"
)
DEFAULT_METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
DEFAULT_FULL_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class Boreal19ConfirmatoryAuthorizationError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19ConfirmatoryAuthorizationError(
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


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA64.fullmatch(value):
        raise Boreal19ConfirmatoryAuthorizationError(
            f"invalid SHA-256: {label}"
        )
    return value


def _exact_replay(
    *,
    committed_receipt: Mapping,
    committed_predictions: str,
) -> None:
    replay_receipt, replay_predictions = freeze_v109(
        pilot_freeze=_load(DEFAULT_PILOT_FREEZE),
        pilot_execution=_load(DEFAULT_PILOT_EXECUTION),
        pilot_snapshot=_load(DEFAULT_PILOT_SNAPSHOT),
        pilot_execution_file_sha256=sha256_file(DEFAULT_PILOT_EXECUTION),
        pilot_snapshot_file_sha256=sha256_file(DEFAULT_PILOT_SNAPSHOT),
        state_path=DEFAULT_STATE,
        state_freeze_path=DEFAULT_STATE_FREEZE,
        state_freeze=_load(DEFAULT_STATE_FREEZE),
        geometry_path=DEFAULT_GEOMETRY,
        geometry_freeze=_load(DEFAULT_GEOMETRY_FREEZE),
        spatial_freeze_path=DEFAULT_SPATIAL_FREEZE,
        spatial_freeze=_load(DEFAULT_SPATIAL_FREEZE),
        operator_freeze=_load(DEFAULT_OPERATOR_FREEZE),
        operator_contract=_load(DEFAULT_OPERATOR_CONTRACT),
        legacy_operator=_load(DEFAULT_LEGACY_OPERATOR),
        contract=_load(DEFAULT_V109_CONTRACT),
    )
    if replay_receipt != dict(committed_receipt):
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.09 model receipt does not exact-replay"
        )
    if replay_predictions != committed_predictions:
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.09 prediction surface does not exact-replay"
        )


def authorize(
    *,
    preconfirmatory_freeze: Mapping,
    model_receipt: Mapping,
    predictions_text: str,
    pilot_snapshot: Mapping,
    spatial_freeze: Mapping,
    metadata: Mapping,
    full_universe: Mapping,
    contract: Mapping,
    preconfirmatory_freeze_sha256: str,
    model_receipt_sha256: str,
    predictions_sha256: str,
) -> dict:
    candidate = contract["candidate_id"]
    required = contract["required_prediction_freeze"]

    if preconfirmatory_freeze.get("schema") != required["schema"]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "unexpected v1.10 preconfirmatory freeze schema"
        )
    if preconfirmatory_freeze.get("status") != required["status"]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 preconfirmatory freeze did not qualify"
        )
    if preconfirmatory_freeze.get("candidate_id") != candidate:
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 candidate identity mismatch"
        )
    if preconfirmatory_freeze.get("exact_replay_verified") is not True:
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 exact replay not verified"
        )
    if preconfirmatory_freeze.get(
        "confirmatory_authorization_may_be_built"
    ) is not True:
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 does not authorize confirmatory gate construction"
        )

    files = preconfirmatory_freeze.get("files")
    if not isinstance(files, dict):
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 file identities missing"
        )
    prediction_row = files.get("confirmatory_predictions")
    receipt_row = files.get("model_receipt")
    if not isinstance(prediction_row, dict) or not isinstance(
        receipt_row, dict
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 prediction/receipt identities missing"
        )
    if prediction_row.get("sha256") != required[
        "prediction_file_sha256"
    ]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 prediction file identity drift"
        )
    if receipt_row.get("sha256") != required[
        "model_receipt_file_sha256"
    ]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 model receipt identity drift"
        )
    if predictions_sha256 != required["prediction_file_sha256"]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "committed prediction file SHA drift"
        )
    if model_receipt_sha256 != required["model_receipt_file_sha256"]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "committed model receipt file SHA drift"
        )

    model_result = preconfirmatory_freeze.get("model_result")
    if not isinstance(model_result, dict):
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 model result missing"
        )
    for key, expected in (
        ("status", "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE"),
        ("models_fingerprint", required["models_fingerprint"]),
        ("prediction_surface_sha256", required["prediction_surface_sha256"]),
        ("pilot_snapshot_fingerprint", required["pilot_snapshot_fingerprint"]),
        (
            "pilot_species_universe_sha256",
            required["pilot_species_universe_sha256"],
        ),
        (
            "source_operator_fingerprint",
            required["source_operator_fingerprint"],
        ),
        ("species_count", required["species_count"]),
        ("prediction_row_count", required["prediction_row_count"]),
        (
            "confirmatory_island_count",
            required["confirmatory_island_count"],
        ),
        (
            "confirmatory_block_count",
            required["confirmatory_block_count"],
        ),
        ("confirmatory_target_values_opened", 0),
        ("excluded_target_values_opened", 0),
        ("confirmatory_response_authorized", False),
        ("predictive_denominator_contribution", 0),
        ("counts_as_empirical_evidence", False),
    ):
        if model_result.get(key) != expected:
            raise Boreal19ConfirmatoryAuthorizationError(
                f"v1.10 model result drift: {key}"
            )

    boundary = preconfirmatory_freeze.get("response_boundary")
    if not isinstance(boundary, dict):
        raise Boreal19ConfirmatoryAuthorizationError(
            "v1.10 response boundary missing"
        )
    for key, expected in (
        ("confirmatory_response_opened", False),
        ("confirmatory_target_values_opened", 0),
        ("excluded_target_values_opened", 0),
        ("confirmatory_response_authorized", False),
        ("counts_as_empirical_evidence", False),
        ("predictive_denominator_contribution", 0),
    ):
        if boundary.get(key) != expected:
            raise Boreal19ConfirmatoryAuthorizationError(
                f"v1.10 response boundary violated: {key}"
            )

    if model_receipt.get("schema") != (
        "structural.boreal_19island_preconfirmatory_model_freeze.v1_09"
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "unexpected committed model receipt schema"
        )
    if model_receipt.get("status") != (
        "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE"
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "committed model receipt did not qualify"
        )
    if model_receipt.get("candidate_id") != candidate:
        raise Boreal19ConfirmatoryAuthorizationError(
            "model receipt candidate identity mismatch"
        )
    for key, expected in (
        ("models_fingerprint", required["models_fingerprint"]),
        ("prediction_surface_sha256", required["prediction_surface_sha256"]),
        ("pilot_snapshot_fingerprint", required["pilot_snapshot_fingerprint"]),
        (
            "pilot_species_universe_sha256",
            required["pilot_species_universe_sha256"],
        ),
        (
            "source_operator_fingerprint",
            required["source_operator_fingerprint"],
        ),
        ("species_count", required["species_count"]),
        ("prediction_row_count", required["prediction_row_count"]),
        ("confirmatory_island_count", required["confirmatory_island_count"]),
        ("confirmatory_block_count", required["confirmatory_block_count"]),
        ("confirmatory_target_values_opened", 0),
        ("excluded_target_values_opened", 0),
        ("confirmatory_response_authorized", False),
        ("predictive_denominator_contribution", 0),
        ("counts_as_empirical_evidence", False),
    ):
        if model_receipt.get(key) != expected:
            raise Boreal19ConfirmatoryAuthorizationError(
                f"committed model receipt drift: {key}"
            )
    if sha256_text(predictions_text) != required[
        "prediction_surface_sha256"
    ]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "prediction surface content SHA drift"
        )

    # Refit/replay from only the committed pilot snapshot and response-independent
    # parents. No confirmatory response bytes are involved in this check.
    _exact_replay(
        committed_receipt=model_receipt,
        committed_predictions=predictions_text,
    )

    if pilot_snapshot.get("schema") != (
        "structural.boreal_19island_pilot_training_snapshot.v1_07"
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "unexpected pilot snapshot schema"
        )
    if pilot_snapshot.get("status") != (
        "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN"
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "pilot snapshot did not qualify"
        )
    species = tuple(pilot_snapshot.get("pilot_species_universe") or ())
    if len(species) != required["species_count"]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "fixed species count drift"
        )
    if pilot_snapshot.get("pilot_species_universe_sha256") != required[
        "pilot_species_universe_sha256"
    ]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "fixed species universe SHA drift"
        )
    if pilot_snapshot.get("snapshot_fingerprint") != required[
        "pilot_snapshot_fingerprint"
    ]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "pilot snapshot fingerprint drift"
        )

    if spatial_freeze.get("schema") != (
        "structural.boreal_19island_spatial_partition_freeze.v1_00"
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "unexpected spatial freeze schema"
        )
    if spatial_freeze.get("status") != (
        "SPATIAL_PARTITION_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "spatial freeze did not qualify"
        )
    analysis_order = tuple(
        spatial_freeze.get("pilot_islands", ())
    ) + tuple(spatial_freeze.get("confirmatory_islands", ()))
    # Preserve the canonical 19-island order from the v1.09 model population.
    state_order = tuple(
        _load(DEFAULT_STATE_FREEZE).get("island_order") or ()
    )
    if len(state_order) != contract["population"]["analysis_island_count"]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "analysis population is not exact 19 islands"
        )
    if set(analysis_order) != set(state_order):
        raise Boreal19ConfirmatoryAuthorizationError(
            "spatial/state analysis population mismatch"
        )
    pilot_islands = tuple(spatial_freeze.get("pilot_islands") or ())
    confirmatory_islands = tuple(
        spatial_freeze.get("confirmatory_islands") or ()
    )
    if len(pilot_islands) != contract["population"]["pilot_island_count"]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "pilot island count drift"
        )
    if len(confirmatory_islands) != contract["population"][
        "confirmatory_island_count"
    ]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "confirmatory island count drift"
        )
    mapping = spatial_freeze.get("island_to_block")
    if not isinstance(mapping, dict) or set(mapping) != set(state_order):
        raise Boreal19ConfirmatoryAuthorizationError(
            "analysis island-to-block map drift"
        )

    full = full_universe.get(
        "current_study_island_universe", {}
    ).get("codes")
    if (
        full_universe.get("row_count") != 42
        or not isinstance(full, list)
        or len(full) != 42
        or len(set(full)) != 42
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "full source universe is not exact 42 islands"
        )
    if not set(state_order) < set(full):
        raise Boreal19ConfirmatoryAuthorizationError(
            "analysis population is not strict subset of source universe"
        )
    excluded = tuple(
        island for island in full if island not in set(state_order)
    )
    if len(excluded) != contract["population"]["excluded_island_count"]:
        raise Boreal19ConfirmatoryAuthorizationError(
            "excluded island count drift"
        )

    response_rule = contract["response_file"]
    if metadata.get("schema") != (
        "structural.boreal_lake_islands_dryad_metadata_result.v0_65"
    ):
        raise Boreal19ConfirmatoryAuthorizationError(
            "unexpected Dryad metadata schema"
        )
    frozen = metadata.get("focal_files", {}).get(response_rule["name"])
    if not isinstance(frozen, dict):
        raise Boreal19ConfirmatoryAuthorizationError(
            "frozen response metadata missing"
        )
    for key, expected in (
        ("file_id", response_rule["dryad_file_id"]),
        ("size", response_rule["expected_size_bytes"]),
        ("sha256", response_rule["expected_sha256"]),
        ("role", "primary_response"),
    ):
        if frozen.get(key) != expected:
            raise Boreal19ConfirmatoryAuthorizationError(
                f"response identity drift: {key}"
            )

    core = {
        "schema": (
            "structural.boreal_19island_confirmatory_response_authorization.v1_11"
        ),
        "status": contract["authorization_ceiling"]["status"],
        "candidate_id": candidate,
        "source_preconfirmatory_freeze_sha256": _sha(
            preconfirmatory_freeze_sha256,
            "preconfirmatory freeze file",
        ),
        "source_model_receipt_sha256": model_receipt_sha256,
        "prediction_surface_sha256": predictions_sha256,
        "models_fingerprint": required["models_fingerprint"],
        "pilot_snapshot_fingerprint": required[
            "pilot_snapshot_fingerprint"
        ],
        "fixed_species_universe_sha256": required[
            "pilot_species_universe_sha256"
        ],
        "fixed_species_count": len(species),
        "prediction_row_count": required["prediction_row_count"],
        "full_source_island_order": list(full),
        "analysis_island_order": list(state_order),
        "pilot_islands": list(pilot_islands),
        "confirmatory_islands": list(confirmatory_islands),
        "excluded_islands": list(excluded),
        "island_to_block": dict(mapping),
        "pilot_block_ids": list(
            spatial_freeze.get("pilot_block_ids") or ()
        ),
        "confirmatory_block_ids": list(
            spatial_freeze.get("confirmatory_block_ids") or ()
        ),
        "response_file": {
            "name": response_rule["name"],
            "dryad_file_id": response_rule["dryad_file_id"],
            "size_bytes": response_rule["expected_size_bytes"],
            "sha256": response_rule["expected_sha256"],
            "expected_species_columns": response_rule[
                "expected_species_columns"
            ],
        },
        "allowed_semantic_access": dict(
            contract["allowed_semantic_access_after_authorization"]
        ),
        "router": dict(contract["router"]),
        "confirmatory_response_authorized": True,
        "authorization_consumed": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "response_values_opened_by_authorization": False,
        "eligible_action": contract["authorization_ceiling"][
            "eligible_action"
        ],
        "next_action": contract["authorization_ceiling"]["next_action"],
    }
    return {
        **core,
        "authorization_fingerprint": canonical_sha256(core),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--preconfirmatory-freeze",
        type=Path,
        default=DEFAULT_PRECONFIRMATORY_FREEZE,
    )
    parser.add_argument(
        "--predictions", type=Path, default=DEFAULT_PREDICTIONS
    )
    parser.add_argument(
        "--model-receipt", type=Path, default=DEFAULT_MODEL_RECEIPT
    )
    parser.add_argument(
        "--pilot-snapshot", type=Path, default=DEFAULT_PILOT_SNAPSHOT
    )
    parser.add_argument(
        "--spatial-freeze", type=Path, default=DEFAULT_SPATIAL_FREEZE
    )
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument(
        "--full-universe", type=Path, default=DEFAULT_FULL_UNIVERSE
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_19island_confirmatory_authorization_contract.v1_11"
        ):
            raise Boreal19ConfirmatoryAuthorizationError(
                "unexpected v1.11 authorization contract schema"
            )
        predictions_text = args.predictions.read_text(encoding="utf-8")
        result = authorize(
            preconfirmatory_freeze=_load(args.preconfirmatory_freeze),
            model_receipt=_load(args.model_receipt),
            predictions_text=predictions_text,
            pilot_snapshot=_load(args.pilot_snapshot),
            spatial_freeze=_load(args.spatial_freeze),
            metadata=_load(args.metadata),
            full_universe=_load(args.full_universe),
            contract=contract,
            preconfirmatory_freeze_sha256=sha256_file(
                args.preconfirmatory_freeze
            ),
            model_receipt_sha256=sha256_file(args.model_receipt),
            predictions_sha256=sha256_file(args.predictions),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19ConfirmatoryAuthorizationError,
    ) as exc:
        result = {
            "schema": (
                "structural.boreal_19island_confirmatory_response_authorization.v1_11"
            ),
            "status": "STOP",
            "reason": str(exc),
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

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
