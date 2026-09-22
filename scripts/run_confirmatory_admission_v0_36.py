#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from structural.confirmatory_admission import (  # noqa: E402
    ConfirmatoryAdmissionStatus,
    admission_receipt_mapping,
    evaluate_confirmatory_admission,
)
from structural.transition_pilot_protocol import protocol_from_mapping  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recompute v0.31-v0.33 and emit a deterministic admission receipt."
    )
    parser.add_argument("protocol", type=Path)
    parser.add_argument("pilot_result", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        protocol_data = json.loads(args.protocol.read_text(encoding="utf-8"))
        pilot_result = json.loads(args.pilot_result.read_text(encoding="utf-8"))
        protocol = protocol_from_mapping(protocol_data)
        decision = evaluate_confirmatory_admission(
            protocol=protocol,
            pilot_result=pilot_result,
            confirmatory_response_accessed=False,
        )
        payload = admission_receipt_mapping(decision)
        code = 0 if decision.status is ConfirmatoryAdmissionStatus.ADMITTED else 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "schema": "structural.confirmatory_admission_receipt.v0_36",
            "status": "invalid_input",
            "reason": str(exc),
            "confirmatory_response_authorized": False,
            "predictive_denominator_contribution": 0,
            "ttf_handoff_authorized": False,
        }
        code = 1

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
