#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.freeze_mechanism_confirmatory_protocol_v0_5 import (  # noqa: E402
    freeze as freeze_confirmatory_protocol,
)
from scripts.freeze_mechanism_scoring_input_v0_8 import (  # noqa: E402
    freeze_scoring_input,
)

SCHEMA = "structural.mechanism_response_authorization.v0_6"


class MechanismResponseAuthorizationError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MechanismResponseAuthorizationError(
            f"cannot read JSON {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MechanismResponseAuthorizationError(
            f"{path} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_git_tracked(path: Path, *, label: str) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise MechanismResponseAuthorizationError(
            f"{label} must live inside repository"
        ) from exc
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", str(relative)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise MechanismResponseAuthorizationError(
            f"{label} must be git-tracked before response authorization"
        )
    return str(relative)


def authorization_id(
    *,
    freeze_receipt_sha256: str,
    scoring_receipt_sha256: str,
    scoring_input_sha256: str,
    protocol_fingerprint: str,
    response_partition: list[str],
) -> str:
    payload = json.dumps(
        {
            "freeze_receipt_sha256": freeze_receipt_sha256,
            "scoring_receipt_sha256": scoring_receipt_sha256,
            "scoring_input_sha256": scoring_input_sha256,
            "protocol_fingerprint": protocol_fingerprint,
            "response_partition": response_partition,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def authorize(
    lane_protocol_path: Path,
    freeze_receipt_path: Path,
    scoring_receipt_path: Path,
    scoring_input_csv: Path,
    mechanism_protocol_path: Path,
    structural_queue_path: Path,
    *,
    transition_pilot_csv: Path | None = None,
    genetic_populations_csv: Path | None = None,
    genetic_pairs_csv: Path | None = None,
    environment_csv: Path | None = None,
    allow_synthetic_structural_queue: bool = False,
    require_tracked_receipt: bool = True,
    require_tracked_scoring_receipt: bool = True,
) -> tuple[int, dict]:
    tracked_freeze: str | None = None
    if require_tracked_receipt:
        try:
            tracked_freeze = require_git_tracked(
                freeze_receipt_path,
                label="v0.5 freeze receipt",
            )
        except MechanismResponseAuthorizationError as exc:
            return 2, {
                "schema": SCHEMA,
                "status": "STOP_freeze_receipt_not_committed",
                "reason": str(exc),
                "confirmatory_response_authorized": False,
                "mechanism_claim_authorized": False,
                "effect_size": None,
                "prediction_score": None,
            }

    tracked_scoring: str | None = None
    if require_tracked_scoring_receipt:
        try:
            tracked_scoring = require_git_tracked(
                scoring_receipt_path,
                label="v0.8 scoring-input receipt",
            )
        except MechanismResponseAuthorizationError as exc:
            return 2, {
                "schema": SCHEMA,
                "status": "STOP_scoring_receipt_not_committed",
                "reason": str(exc),
                "confirmatory_response_authorized": False,
                "mechanism_claim_authorized": False,
                "effect_size": None,
                "prediction_score": None,
            }

    stored_freeze = load_json(freeze_receipt_path)
    freeze_code, recomputed_freeze = freeze_confirmatory_protocol(
        lane_protocol_path,
        mechanism_protocol_path,
        structural_queue_path,
        transition_pilot_csv=transition_pilot_csv,
        genetic_populations_csv=genetic_populations_csv,
        genetic_pairs_csv=genetic_pairs_csv,
        environment_csv=environment_csv,
        allow_synthetic_structural_queue=allow_synthetic_structural_queue,
    )
    if freeze_code != 0:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_confirmatory_freeze_no_longer_replays",
            "freeze_status": recomputed_freeze.get("status"),
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
        }
    if stored_freeze != recomputed_freeze:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_committed_freeze_receipt_not_exact_replay",
            "stored_receipt_sha256": sha256_file(freeze_receipt_path),
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
        }

    stored_scoring = load_json(scoring_receipt_path)
    scoring_code, recomputed_scoring = freeze_scoring_input(
        lane_protocol_path,
        freeze_receipt_path,
        scoring_input_csv,
        mechanism_protocol_path,
        structural_queue_path,
        transition_pilot_csv=transition_pilot_csv,
        genetic_populations_csv=genetic_populations_csv,
        genetic_pairs_csv=genetic_pairs_csv,
        environment_csv=environment_csv,
        allow_synthetic_structural_queue=allow_synthetic_structural_queue,
        require_tracked_freeze_receipt=require_tracked_receipt,
    )
    if scoring_code != 0:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_scoring_input_freeze_no_longer_replays",
            "scoring_status": recomputed_scoring.get("status"),
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
        }
    if stored_scoring != recomputed_scoring:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_committed_scoring_receipt_not_exact_replay",
            "stored_scoring_receipt_sha256": sha256_file(scoring_receipt_path),
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
        }

    if stored_freeze.get("schema") != (
        "structural.mechanism_confirmatory_freeze_receipt.v0_5"
    ):
        raise MechanismResponseAuthorizationError(
            "unexpected freeze receipt schema"
        )
    if stored_scoring.get("schema") != (
        "structural.mechanism_scoring_input_freeze_receipt.v0_8"
    ):
        raise MechanismResponseAuthorizationError(
            "unexpected scoring receipt schema"
        )
    if stored_scoring.get("status") != (
        "mechanism_scoring_inputs_frozen_before_response"
    ):
        raise MechanismResponseAuthorizationError(
            "scoring inputs are not frozen before response"
        )
    if stored_scoring.get("scoring_input_frozen") is not True:
        raise MechanismResponseAuthorizationError(
            "scoring input receipt does not prove frozen inputs"
        )
    if stored_scoring.get("confirmatory_response_authorized") is not False:
        raise MechanismResponseAuthorizationError(
            "scoring inputs must have frozen before response authorization"
        )
    if stored_scoring.get("protocol_fingerprint") != stored_freeze.get(
        "protocol_fingerprint"
    ):
        raise MechanismResponseAuthorizationError(
            "scoring receipt protocol fingerprint mismatch"
        )
    if stored_scoring.get("response_partition") != stored_freeze.get(
        "response_partition"
    ):
        raise MechanismResponseAuthorizationError(
            "scoring receipt response partition mismatch"
        )
    if stored_scoring.get("next_action") != "run_v0_6_response_authorization_only":
        raise MechanismResponseAuthorizationError(
            "scoring receipt next-action drift"
        )

    response_partition = stored_freeze.get("response_partition")
    if (
        not isinstance(response_partition, list)
        or not response_partition
        or not all(isinstance(unit, str) and unit.strip() for unit in response_partition)
    ):
        raise MechanismResponseAuthorizationError(
            "freeze receipt response partition invalid"
        )

    freeze_sha = sha256_file(freeze_receipt_path)
    scoring_receipt_sha = sha256_file(scoring_receipt_path)
    scoring_input_sha = sha256_file(scoring_input_csv)
    if scoring_input_sha != stored_scoring.get("scoring_input_file_sha256"):
        raise MechanismResponseAuthorizationError(
            "raw scoring input SHA does not match v0.8 receipt"
        )

    auth_id = authorization_id(
        freeze_receipt_sha256=freeze_sha,
        scoring_receipt_sha256=scoring_receipt_sha,
        scoring_input_sha256=scoring_input_sha,
        protocol_fingerprint=stored_freeze["protocol_fingerprint"],
        response_partition=response_partition,
    )

    synthetic = bool(allow_synthetic_structural_queue)
    return 0, {
        "schema": SCHEMA,
        "status": "confirmatory_mechanism_response_access_authorized_once",
        "authorization_id": auth_id,
        "system_id": stored_freeze["system_id"],
        "mechanism_lane": stored_freeze["mechanism_lane"],
        "protocol_id": stored_freeze["protocol_id"],
        "protocol_fingerprint": stored_freeze["protocol_fingerprint"],
        "freeze_receipt_path": tracked_freeze,
        "freeze_receipt_sha256": freeze_sha,
        "scoring_receipt_path": tracked_scoring,
        "scoring_receipt_sha256": scoring_receipt_sha,
        "scoring_input_file_sha256": scoring_input_sha,
        "scoring_input_key_set_sha256": stored_scoring[
            "scoring_input_audit"
        ]["key_set_sha256"],
        "response_partition": response_partition,
        "authorization_scope":
            "read_exact_frozen_response_partition_for_this_lane_protocol_only",
        "single_use": True,
        "response_access_consumed": False,
        "confirmatory_response_authorized": True,
        "mechanism_claim_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "ttf_handoff_authorized": False,
        "synthetic_ci_authorization": synthetic,
        "counts_as_empirical_evidence": False if synthetic else None,
        "next_action":
            "open_exact_response_partition_once_then_record_access_before_scoring",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_protocol", type=Path)
    parser.add_argument("freeze_receipt", type=Path)
    parser.add_argument("scoring_receipt", type=Path)
    parser.add_argument("scoring_input_csv", type=Path)
    parser.add_argument("mechanism_protocol", type=Path)
    parser.add_argument("structural_queue", type=Path)
    parser.add_argument("--transition-pilot", type=Path)
    parser.add_argument("--genetic-populations", type=Path)
    parser.add_argument("--genetic-pairs", type=Path)
    parser.add_argument("--environment", type=Path)
    parser.add_argument("--allow-synthetic-structural-queue", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        code, payload = authorize(
            args.lane_protocol,
            args.freeze_receipt,
            args.scoring_receipt,
            args.scoring_input_csv,
            args.mechanism_protocol,
            args.structural_queue,
            transition_pilot_csv=args.transition_pilot,
            genetic_populations_csv=args.genetic_populations,
            genetic_pairs_csv=args.genetic_pairs,
            environment_csv=args.environment,
            allow_synthetic_structural_queue=args.allow_synthetic_structural_queue,
            require_tracked_receipt=True,
            require_tracked_scoring_receipt=True,
        )
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        MechanismResponseAuthorizationError,
    ) as exc:
        code, payload = 1, {
            "schema": SCHEMA,
            "status": "invalid_input",
            "reason": str(exc),
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
        }

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
