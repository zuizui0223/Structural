#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.run_transition_pilot_v0_32 import run as run_transition_pilot  # noqa: E402
from structural.confirmatory_admission import (  # noqa: E402
    ConfirmatoryAdmissionStatus,
    admission_receipt_mapping,
    evaluate_confirmatory_admission,
)
from structural.transition_pilot_protocol import protocol_from_mapping  # noqa: E402


QUEUE_SCHEMA = "structural.confirmatory_admission_queue.v0_38"
ENTRY_KEYS = {
    "system_id",
    "protocol_id",
    "protocol_path",
    "pilot_input_path",
    "pilot_input_sha256",
    "pilot_result_path",
    "admission_receipt_path",
    "protocol_fingerprint",
}


class QueueValidationError(ValueError):
    pass


def _repo_file(path_text: object) -> Path:
    if not isinstance(path_text, str) or not path_text.strip():
        raise QueueValidationError("queue paths must be non-empty strings")
    path = (ROOT / path_text).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise QueueValidationError(f"path escapes repository: {path_text}") from exc
    if not path.is_file():
        raise QueueValidationError(f"missing referenced file: {path_text}")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_queue(queue_path: Path) -> int:
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    if not isinstance(queue, dict):
        raise QueueValidationError("queue must be a JSON object")
    if queue.get("schema") != QUEUE_SCHEMA:
        raise QueueValidationError("unexpected queue schema")
    if queue.get("confirmatory_response_authorized") is not False:
        raise QueueValidationError("queue must never authorize confirmatory response")

    entries = queue.get("entries")
    if not isinstance(entries, list):
        raise QueueValidationError("entries must be a list")
    if queue.get("entry_count") != len(entries):
        raise QueueValidationError("entry_count does not match entries")

    identities: set[tuple[str, str]] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise QueueValidationError(f"entry {index} must be an object")
        if set(entry) != ENTRY_KEYS:
            raise QueueValidationError(f"entry {index} keys do not match frozen schema")

        identity = (entry["system_id"], entry["protocol_id"])
        if not all(isinstance(v, str) and v.strip() for v in identity):
            raise QueueValidationError(f"entry {index} has invalid identity")
        if identity in identities:
            raise QueueValidationError(f"duplicate queue identity: {identity}")
        identities.add(identity)

        protocol_path = _repo_file(entry["protocol_path"])
        pilot_input_path = _repo_file(entry["pilot_input_path"])
        pilot_result_path = _repo_file(entry["pilot_result_path"])
        receipt_path = _repo_file(entry["admission_receipt_path"])

        expected_pilot_sha = entry["pilot_input_sha256"]
        if not isinstance(expected_pilot_sha, str) or len(expected_pilot_sha) != 64:
            raise QueueValidationError(f"entry {index} pilot_input_sha256 invalid")
        observed_pilot_sha = _sha256(pilot_input_path)
        if observed_pilot_sha != expected_pilot_sha:
            raise QueueValidationError(f"entry {index} pilot input SHA-256 mismatch")

        stored_pilot_result = json.loads(
            pilot_result_path.read_text(encoding="utf-8")
        )
        replay_code, replay_pilot_result = run_transition_pilot(
            protocol_path,
            pilot_input_path,
        )
        if replay_code != 0:
            raise QueueValidationError(
                f"entry {index} raw burned pilot no longer qualifies on replay"
            )
        if replay_pilot_result != stored_pilot_result:
            raise QueueValidationError(
                f"entry {index} stored pilot result is not exact v0.32 replay"
            )

        protocol_data = json.loads(protocol_path.read_text(encoding="utf-8"))
        stored_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        protocol = protocol_from_mapping(protocol_data)

        decision = evaluate_confirmatory_admission(
            protocol=protocol,
            pilot_result=replay_pilot_result,
            confirmatory_response_accessed=False,
        )
        if decision.status is not ConfirmatoryAdmissionStatus.ADMITTED:
            raise QueueValidationError(
                f"entry {index} fails v0.31-v0.37: {', '.join(decision.reasons)}"
            )

        expected_receipt = admission_receipt_mapping(decision)
        if stored_receipt != expected_receipt:
            raise QueueValidationError(f"entry {index} receipt is not reproducible")
        if entry["system_id"] != decision.system_id:
            raise QueueValidationError(f"entry {index} system_id mismatch")
        if entry["protocol_id"] != decision.protocol_id:
            raise QueueValidationError(f"entry {index} protocol_id mismatch")
        if entry["protocol_fingerprint"] != decision.protocol_fingerprint:
            raise QueueValidationError(f"entry {index} fingerprint mismatch")

    return len(entries)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "queue",
        type=Path,
        nargs="?",
        default=ROOT / "development/confirmatory_admission_queue_v0_38.json",
    )
    args = parser.parse_args()
    try:
        count = validate_queue(args.queue)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"confirmatory queue replay validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"confirmatory replay queue valid: {count} admitted system(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
