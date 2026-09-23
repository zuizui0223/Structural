#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from structural.transition_estimability import PilotObservation, audit_transition_pilot
from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    evaluate_transition_pilot_protocol,
    protocol_from_mapping,
)


def parse_target(value: str):
    text = value.strip()
    if text in {"", "NA", "NaN", "nan", "None"}:
        return None
    if text == "0":
        return 0
    if text == "1":
        return 1
    raise ValueError(f"target must be 0/1/blank/NA, got {value!r}")


def run(protocol_path: Path, pilot_csv: Path) -> tuple[int, dict]:
    protocol_data = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol = protocol_from_mapping(protocol_data)
    pre = evaluate_transition_pilot_protocol(protocol)
    if pre.status is not PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT:
        return 1, {
            "schema": "structural.transition_pilot_result.v0_32",
            "status": "invalid_or_unqualified_protocol",
            "reasons": list(pre.reasons),
            "protocol_fingerprint": pre.protocol_fingerprint,
        }

    pilot_units = set(protocol.pilot_partition)
    confirmatory_units = set(protocol.confirmatory_partition)
    observations: list[PilotObservation] = []
    seen_units: set[str] = set()

    with pilot_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("pilot CSV has no header")
        required = ["partition_unit", "block", "target"]
        if reader.fieldnames != required:
            raise ValueError(
                "pilot CSV header must be exactly: " + ", ".join(required)
            )

        for row in reader:
            unit = (row.get("partition_unit") or "").strip()
            block = (row.get("block") or "").strip()
            if unit in confirmatory_units:
                return 2, {
                    "schema": "structural.transition_pilot_result.v0_32",
                    "status": "STOP_confirmatory_partition_exposed",
                    "protocol_fingerprint": pre.protocol_fingerprint,
                    "confirmatory_unit": unit,
                    "pilot_consumed": True,
                    "effect_size": None,
                    "prediction_score": None,
                }
            if unit not in pilot_units:
                return 2, {
                    "schema": "structural.transition_pilot_result.v0_32",
                    "status": "STOP_unfrozen_partition_unit",
                    "protocol_fingerprint": pre.protocol_fingerprint,
                    "unfrozen_unit": unit,
                    "pilot_consumed": True,
                    "effect_size": None,
                    "prediction_score": None,
                }
            seen_units.add(unit)
            observations.append(PilotObservation(block=block, target=parse_target(row.get("target",""))))

    missing_pilot_units = sorted(pilot_units - seen_units)
    if missing_pilot_units:
        return 2, {
            "schema": "structural.transition_pilot_result.v0_32",
            "status": "STOP_missing_frozen_pilot_partition_units",
            "protocol_fingerprint": pre.protocol_fingerprint,
            "missing_pilot_units": missing_pilot_units,
            "pilot_consumed": True,
            "effect_size": None,
            "prediction_score": None,
        }

    audit = audit_transition_pilot(
        observations,
        minimum_test_rows=protocol.minimum_test_rows,
        minimum_train_positive=protocol.minimum_train_positive,
        minimum_train_negative=protocol.minimum_train_negative,
        minimum_estimable_blocks=protocol.minimum_estimable_blocks,
    )

    payload = {
        "schema": "structural.transition_pilot_result.v0_32",
        "status": audit.decision.value,
        "protocol_fingerprint": pre.protocol_fingerprint,
        "pilot_partition": list(protocol.pilot_partition),
        "confirmatory_partition_opened": False,
        "confirmatory_response_row_count_seen": 0,
        "pilot_consumed": True,
        "applicable_rows": audit.applicable_rows,
        "positive": audit.positive,
        "negative": audit.negative,
        "non_estimable": audit.non_estimable,
        "total_blocks": audit.total_blocks,
        "estimable_blocks": audit.estimable_blocks,
        "minimum_estimable_blocks": audit.minimum_estimable_blocks,
        "block_audits": [
            {
                "block": b.block,
                "test_rows": b.test_rows,
                "test_positive": b.test_positive,
                "test_negative": b.test_negative,
                "train_rows": b.train_rows,
                "train_positive": b.train_positive,
                "train_negative": b.train_negative,
                "estimable": b.estimable,
                "reasons": list(b.reasons),
            }
            for b in audit.block_audits
        ],
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
    }
    return (0 if audit.decision.value.startswith("qualified") else 2), payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol", type=Path)
    parser.add_argument("pilot_csv", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        code, payload = run(args.protocol, args.pilot_csv)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        code, payload = 1, {
            "schema": "structural.transition_pilot_result.v0_32",
            "status": "invalid_input",
            "reason": str(exc),
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
