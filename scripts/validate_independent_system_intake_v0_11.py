#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.validate_independent_system_intake_v0_10 import (  # noqa: E402
    load_json,
    validate_intake,
)

RECEIPT_SCHEMA = "structural.independent_system_intake_receipt.v0_11"


def validate_intake_v0_11(intake: dict) -> tuple[int, dict]:
    """Replay v0.10 intake and add the future-only v0.42 construction boundary."""

    code, prior = validate_intake(intake)
    if code != 0:
        out = dict(prior)
        out["schema"] = RECEIPT_SCHEMA
        out["parent_intake_version"] = "v0.10"
        out["v0_42_quality_contract_construction_authorized"] = False
        out["historical_systems_re_adjudicated"] = False
        return code, out

    if prior.get("status") != "eligible_to_construct_v0_31_partition_protocol":
        return 1, {
            "schema": RECEIPT_SCHEMA,
            "status": "invalid_parent_intake_receipt",
            "system_id": prior.get("system_id"),
            "parent_intake_version": "v0.10",
            "eligible_action": None,
            "v0_31_protocol_construction_authorized": False,
            "v0_42_quality_contract_construction_authorized": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "mechanism_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "mechanism_claim_contribution": 0,
            "historical_systems_re_adjudicated": False,
            "ttf_handoff_authorized": False,
        }

    out = dict(prior)
    out.update(
        {
            "schema": RECEIPT_SCHEMA,
            "status": "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts",
            "parent_intake_version": "v0.10",
            "eligible_action": (
                "construct_v0_31_protocol_then_bind_v0_42_quality_contract_only"
            ),
            "v0_31_protocol_construction_authorized": True,
            "v0_42_quality_contract_construction_authorized": True,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "mechanism_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "mechanism_claim_contribution": 0,
            "historical_systems_re_adjudicated": False,
            "ttf_handoff_authorized": False,
        }
    )
    return 0, out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("intake", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        intake = load_json(args.intake)
        code, payload = validate_intake_v0_11(intake)
    except Exception as exc:
        code = 1
        payload = {
            "schema": RECEIPT_SCHEMA,
            "status": "invalid_intake",
            "reason": str(exc),
            "eligible_action": None,
            "v0_31_protocol_construction_authorized": False,
            "v0_42_quality_contract_construction_authorized": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "mechanism_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "mechanism_claim_contribution": 0,
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
