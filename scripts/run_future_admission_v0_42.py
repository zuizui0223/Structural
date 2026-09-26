#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from structural.future_admission_v0_42 import (
    evaluate_future_admission_v0_42,
    future_admission_receipt_mapping,
)
from structural.response_quality_attrition import contract_from_mapping
from structural.transition_pilot_protocol import protocol_from_mapping


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol", type=Path)
    parser.add_argument("pilot_result", type=Path)
    parser.add_argument("quality_contract", type=Path)
    parser.add_argument("--confirmatory-response-accessed", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        protocol = protocol_from_mapping(
            json.loads(args.protocol.read_text(encoding="utf-8"))
        )
        pilot_result = json.loads(args.pilot_result.read_text(encoding="utf-8"))
        quality_contract = contract_from_mapping(
            json.loads(args.quality_contract.read_text(encoding="utf-8"))
        )
        decision = evaluate_future_admission_v0_42(
            protocol=protocol,
            pilot_result=pilot_result,
            quality_contract=quality_contract,
            confirmatory_response_accessed=args.confirmatory_response_accessed,
        )
        payload = future_admission_receipt_mapping(decision)
        code = 0 if decision.status.value.startswith("admitted") else 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        code = 1
        payload = {
            "schema": "structural.future_confirmatory_admission_receipt.v0_42",
            "status": "invalid_input",
            "reason": str(exc),
            "confirmatory_response_authorized": False,
            "predictive_denominator_contribution": 0,
            "historical_systems_re_adjudicated": False,
            "ttf_handoff_authorized": False,
        }

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
