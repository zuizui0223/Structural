#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from structural.mechanism_transition_estimability import (  # noqa: E402
    M1,
    M2,
    MechanismTransitionObservation,
    audit_mechanism_transition_pilot,
)
from scripts.validate_mechanism_protocol_v0_1 import (  # noqa: E402
    MechanismProtocolError,
    validate_future_protocol,
)


SCHEMA = "structural.mechanism_transition_pilot_result.v0_2"


def parse_state(value: str) -> int | None:
    text = value.strip()
    if text in {"", "NA", "NaN", "nan", "None"}:
        return None
    if text == "0":
        return 0
    if text == "1":
        return 1
    raise ValueError(f"state must be 0/1/blank/NA, got {value!r}")


def fingerprint_protocol(data: dict) -> str:
    payload = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _zero_evidence_payload(**extra) -> dict:
    return {
        "schema": SCHEMA,
        **extra,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "confirmatory_response_authorized": False,
    }


def _validate_pilot_extension(data: dict) -> dict:
    validate_future_protocol(data)

    required = (
        "mechanism_pilot_partition",
        "mechanism_confirmatory_partition",
        "dynamic_estimability",
        "mechanism_pilot_response_accessed",
        "mechanism_confirmatory_response_accessed",
        "mechanism_pilot_used_for_effect_estimation",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(
            "mechanism pilot protocol missing keys: " + ", ".join(missing)
        )

    for key in ("mechanism_pilot_partition", "mechanism_confirmatory_partition"):
        value = data[key]
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) and item.strip() for item in value)
        ):
            raise ValueError(f"{key} must be a non-empty list of non-empty strings")
        if len(value) != len(set(value)):
            raise ValueError(f"{key} contains duplicates")

    if set(data["mechanism_pilot_partition"]) & set(
        data["mechanism_confirmatory_partition"]
    ):
        raise ValueError(
            "mechanism pilot and confirmatory partitions must be disjoint"
        )

    for key in (
        "mechanism_pilot_response_accessed",
        "mechanism_confirmatory_response_accessed",
        "mechanism_pilot_used_for_effect_estimation",
    ):
        if not isinstance(data[key], bool):
            raise ValueError(f"{key} must be boolean")

    if data["mechanism_pilot_response_accessed"]:
        raise ValueError("mechanism pilot response already accessed before freeze")
    if data["mechanism_confirmatory_response_accessed"]:
        raise ValueError("mechanism confirmatory response already accessed")
    if data["mechanism_pilot_used_for_effect_estimation"]:
        raise ValueError("mechanism burned pilot may not be effect evidence")

    dynamic = [
        lane
        for lane in data["mechanism_lanes_authorized"]
        if lane in {M1, M2}
    ]
    if not dynamic:
        raise ValueError("mechanism transition pilot requires M1 and/or M2")

    est = data["dynamic_estimability"]
    if not isinstance(est, dict):
        raise ValueError("dynamic_estimability must be a JSON object")
    try:
        minimum_test_rows = est["minimum_test_rows"]
        minimum_train = est["minimum_train_transition_counts"]
        minimum_blocks = est["minimum_estimable_blocks"]
    except KeyError as exc:
        raise ValueError(
            f"dynamic_estimability missing block: {exc.args[0]}"
        ) from exc

    if not all(isinstance(x, dict) for x in (
        minimum_test_rows,
        minimum_train,
        minimum_blocks,
    )):
        raise ValueError("dynamic_estimability minima blocks must be JSON objects")

    required_values = {
        "minimum_test_rows_m1": minimum_test_rows.get(M1),
        "minimum_test_rows_m2": minimum_test_rows.get(M2),
        "minimum_train_0_to_0": minimum_train.get("0_to_0"),
        "minimum_train_0_to_1": minimum_train.get("0_to_1"),
        "minimum_train_1_to_0": minimum_train.get("1_to_0"),
        "minimum_train_1_to_1": minimum_train.get("1_to_1"),
        "minimum_estimable_blocks_m1": minimum_blocks.get(M1),
        "minimum_estimable_blocks_m2": minimum_blocks.get(M2),
    }
    for label, value in required_values.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{label} must be an integer >=1")

    return {
        "requested_lanes": dynamic,
        **required_values,
    }


def run(protocol_path: Path, pilot_csv: Path) -> tuple[int, dict]:
    data = json.loads(protocol_path.read_text(encoding="utf-8"))
    try:
        settings = _validate_pilot_extension(data)
    except (ValueError, MechanismProtocolError) as exc:
        return 1, _zero_evidence_payload(
            status="invalid_or_unqualified_protocol",
            reason=str(exc),
            protocol_fingerprint=fingerprint_protocol(data)
            if isinstance(data, dict)
            else None,
        )

    protocol_fp = fingerprint_protocol(data)
    pilot_units = set(data["mechanism_pilot_partition"])
    confirmatory_units = set(data["mechanism_confirmatory_partition"])
    seen_units: set[str] = set()
    observations: list[MechanismTransitionObservation] = []

    with pilot_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("mechanism pilot CSV has no header")
        required_header = ["partition_unit", "block", "z_t", "z_t1"]
        if reader.fieldnames != required_header:
            raise ValueError(
                "mechanism pilot CSV header must be exactly: "
                + ", ".join(required_header)
            )

        for row in reader:
            unit = (row.get("partition_unit") or "").strip()
            block = (row.get("block") or "").strip()
            if unit in confirmatory_units:
                return 2, _zero_evidence_payload(
                    status="STOP_confirmatory_partition_exposed",
                    protocol_fingerprint=protocol_fp,
                    confirmatory_unit=unit,
                    pilot_consumed=True,
                )
            if unit not in pilot_units:
                return 2, _zero_evidence_payload(
                    status="STOP_unfrozen_partition_unit",
                    protocol_fingerprint=protocol_fp,
                    unfrozen_unit=unit,
                    pilot_consumed=True,
                )
            seen_units.add(unit)
            observations.append(
                MechanismTransitionObservation(
                    block=block,
                    z_t=parse_state(row.get("z_t", "")),
                    z_t1=parse_state(row.get("z_t1", "")),
                )
            )

    missing_units = sorted(pilot_units - seen_units)
    if missing_units:
        return 2, _zero_evidence_payload(
            status="STOP_missing_frozen_pilot_partition_units",
            protocol_fingerprint=protocol_fp,
            missing_pilot_units=missing_units,
            pilot_consumed=True,
        )

    audit = audit_mechanism_transition_pilot(
        observations,
        requested_lanes=settings["requested_lanes"],
        minimum_test_rows_m1=settings["minimum_test_rows_m1"],
        minimum_test_rows_m2=settings["minimum_test_rows_m2"],
        minimum_train_0_to_0=settings["minimum_train_0_to_0"],
        minimum_train_0_to_1=settings["minimum_train_0_to_1"],
        minimum_train_1_to_0=settings["minimum_train_1_to_0"],
        minimum_train_1_to_1=settings["minimum_train_1_to_1"],
        minimum_estimable_blocks_m1=settings["minimum_estimable_blocks_m1"],
        minimum_estimable_blocks_m2=settings["minimum_estimable_blocks_m2"],
    )

    requested_audits = [
        lane for lane in audit.lane_audits if lane.requested
    ]
    qualified_count = sum(lane.qualified for lane in requested_audits)
    if qualified_count == len(requested_audits):
        status = "qualified_to_freeze_confirmatory_mechanism_protocol"
        code = 0
    elif qualified_count:
        status = "partial_mechanism_estimability_only"
        code = 2
    else:
        status = "stop_mechanism_transition_estimability"
        code = 2

    payload = _zero_evidence_payload(
        status=status,
        protocol_fingerprint=protocol_fp,
        pilot_partition=list(data["mechanism_pilot_partition"]),
        confirmatory_partition_opened=False,
        confirmatory_response_row_count_seen=0,
        pilot_consumed=True,
        total_rows=audit.total_rows,
        applicable_rows=audit.applicable_rows,
        non_estimable_rows=audit.non_estimable_rows,
        transition_counts=audit.transition_counts,
        lane_audits=[
            {
                "lane": lane.lane,
                "requested": lane.requested,
                "estimable_blocks": lane.estimable_blocks,
                "minimum_estimable_blocks": lane.minimum_estimable_blocks,
                "qualified": lane.qualified,
            }
            for lane in audit.lane_audits
        ],
        block_audits=[
            {
                "block": block.block,
                "test_rows_m1": block.test_rows_m1,
                "test_rows_m2": block.test_rows_m2,
                "train_0_to_0": block.train_0_to_0,
                "train_0_to_1": block.train_0_to_1,
                "train_1_to_0": block.train_1_to_0,
                "train_1_to_1": block.train_1_to_1,
                "m1_estimable": block.m1_estimable,
                "m2_estimable": block.m2_estimable,
                "m1_reasons": list(block.m1_reasons),
                "m2_reasons": list(block.m2_reasons),
            }
            for block in audit.block_audits
        ],
        next_action=(
            "freeze_separate_confirmatory_mechanism_protocol_only"
            if code == 0
            else "do_not_open_confirmatory_mechanism_response"
        ),
    )
    return code, payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol", type=Path)
    parser.add_argument("pilot_csv", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        code, payload = run(args.protocol, args.pilot_csv)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        code, payload = 1, _zero_evidence_payload(
            status="invalid_input",
            reason=str(exc),
        )

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
