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

from scripts.validate_confirmatory_queue_v0_38 import (  # noqa: E402
    QueueValidationError,
    validate_queue,
)
from scripts.validate_mechanism_protocol_v0_1 import (  # noqa: E402
    MechanismProtocolError,
    validate_future_protocol,
)
from scripts.run_mechanism_transition_pilot_v0_2 import (  # noqa: E402
    run as run_dynamic_pilot,
)
from scripts.run_mechanism_auxiliary_gate_v0_3 import (  # noqa: E402
    run as run_auxiliary_gate,
)

M1 = "M1_contemporary_colonization"
M2 = "M2_rescue_persistence"
M3 = "M3_historical_colonization_legacy"
M4 = "M4_environmental_proxy"
DYNAMIC = {M1, M2}
AUXILIARY = {M3, M4}
SCHEMA = "structural.mechanism_admission_receipt.v0_4"


class MechanismAdmissionError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MechanismAdmissionError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MechanismAdmissionError(f"{path} must contain a JSON object")
    return value


def protocol_fingerprint(protocol: dict) -> str:
    payload = json.dumps(
        protocol,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _zero_evidence(**extra) -> dict:
    return {
        "schema": SCHEMA,
        **extra,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "confirmatory_response_authorized": False,
        "mechanism_claim_authorized": False,
        "ttf_handoff_authorized": False,
    }


def _validate_structural_queue(
    queue_path: Path,
    *,
    protocol: dict,
    allow_synthetic_queue: bool,
) -> dict:
    try:
        validate_queue(queue_path)
    except (OSError, ValueError, json.JSONDecodeError, QueueValidationError) as exc:
        raise MechanismAdmissionError(
            f"Structural v0.38 queue replay failed: {exc}"
        ) from exc

    queue = load_json(queue_path)
    if queue.get("schema") != "structural.confirmatory_admission_queue.v0_38":
        raise MechanismAdmissionError("unexpected Structural queue schema")
    status = queue.get("status")
    if status == "synthetic_ci_fixture_nonempirical":
        if not allow_synthetic_queue:
            raise MechanismAdmissionError(
                "synthetic Structural queue requires --allow-synthetic-structural-queue"
            )
    elif status != "active_gate_first_queue_with_raw_pilot_replay":
        raise MechanismAdmissionError(
            f"unexpected Structural queue status: {status}"
        )

    system_id = protocol["system_id"]
    structural_fp = protocol["structural_admission_protocol_fingerprint"]
    matches = [
        entry
        for entry in queue.get("entries", [])
        if isinstance(entry, dict)
        and entry.get("system_id") == system_id
        and entry.get("protocol_fingerprint") == structural_fp
    ]
    if len(matches) != 1:
        raise MechanismAdmissionError(
            "mechanism protocol must match exactly one replay-validated "
            "Structural queue entry by system_id and protocol_fingerprint"
        )
    entry = matches[0]

    receipt_path = ROOT / entry["admission_receipt_path"]
    receipt = load_json(receipt_path)
    if receipt.get("schema") != "structural.confirmatory_admission_receipt.v0_36":
        raise MechanismAdmissionError("unexpected Structural admission receipt schema")
    if receipt.get("status") != "admitted_to_confirmatory_protocol_queue":
        raise MechanismAdmissionError("Structural system is not admitted")
    if receipt.get("eligible_action") != "freeze_confirmatory_protocol_only":
        raise MechanismAdmissionError("Structural receipt eligible_action drift")
    if receipt.get("confirmatory_response_authorized") is not False:
        raise MechanismAdmissionError(
            "Structural admission must not authorize confirmatory response"
        )
    if receipt.get("predictive_denominator_contribution") != 0:
        raise MechanismAdmissionError(
            "Structural pilot must contribute zero predictive denominator"
        )

    return {
        "queue_status": status,
        "queue_entry_system_id": entry["system_id"],
        "queue_entry_protocol_id": entry["protocol_id"],
        "structural_protocol_fingerprint": entry["protocol_fingerprint"],
        "structural_receipt_status": receipt["status"],
        "structural_confirmatory_response_authorized": False,
        "synthetic_queue": status == "synthetic_ci_fixture_nonempirical",
    }


def _lane_decisions_from_dynamic(result: dict, requested: set[str]) -> dict[str, dict]:
    audits = result.get("lane_audits")
    if not isinstance(audits, list):
        raise MechanismAdmissionError("dynamic gate lane_audits missing")
    by_lane = {
        row.get("lane"): row
        for row in audits
        if isinstance(row, dict)
    }
    decisions: dict[str, dict] = {}
    for lane in sorted(requested & DYNAMIC):
        row = by_lane.get(lane)
        if not isinstance(row, dict):
            raise MechanismAdmissionError(f"dynamic gate missing requested lane {lane}")
        qualified = row.get("qualified") is True
        decisions[lane] = {
            "qualified": qualified,
            "source_gate": "mechanism_transition_pilot_v0_2",
            "estimable_blocks": row.get("estimable_blocks"),
            "minimum_estimable_blocks": row.get("minimum_estimable_blocks"),
            "eligible_action": (
                "freeze_confirmatory_mechanism_protocol_only"
                if qualified
                else None
            ),
            "non_estimable_is_neutral": not qualified,
        }
    return decisions


def _lane_decisions_from_auxiliary(result: dict, requested: set[str]) -> dict[str, dict]:
    rows = result.get("lane_results")
    if not isinstance(rows, list):
        raise MechanismAdmissionError("auxiliary gate lane_results missing")
    by_lane = {
        row.get("lane"): row
        for row in rows
        if isinstance(row, dict)
    }
    decisions: dict[str, dict] = {}
    for lane in sorted(requested & AUXILIARY):
        row = by_lane.get(lane)
        if not isinstance(row, dict):
            raise MechanismAdmissionError(f"auxiliary gate missing requested lane {lane}")
        qualified = row.get("qualified") is True
        decisions[lane] = {
            "qualified": qualified,
            "source_gate": "mechanism_auxiliary_gate_v0_3",
            "reasons": row.get("reasons", []),
            "eligible_action": (
                "freeze_confirmatory_mechanism_protocol_only"
                if qualified
                else None
            ),
            "non_estimable_is_neutral": not qualified,
        }
    return decisions


def run(
    mechanism_protocol_path: Path,
    structural_queue_path: Path,
    *,
    transition_pilot_csv: Path | None = None,
    genetic_populations_csv: Path | None = None,
    genetic_pairs_csv: Path | None = None,
    environment_csv: Path | None = None,
    allow_synthetic_structural_queue: bool = False,
) -> tuple[int, dict]:
    protocol = load_json(mechanism_protocol_path)
    try:
        validate_future_protocol(protocol)
    except MechanismProtocolError as exc:
        return 1, _zero_evidence(
            status="invalid_or_unqualified_mechanism_protocol",
            reason=str(exc),
        )

    mech_fp = protocol_fingerprint(protocol)
    try:
        structural = _validate_structural_queue(
            structural_queue_path,
            protocol=protocol,
            allow_synthetic_queue=allow_synthetic_structural_queue,
        )
    except MechanismAdmissionError as exc:
        return 2, _zero_evidence(
            status="STOP_structural_admission_not_replay_validated",
            mechanism_protocol_fingerprint=mech_fp,
            reason=str(exc),
        )

    requested = set(protocol["mechanism_lanes_authorized"])
    decisions: dict[str, dict] = {}
    input_sha256: dict[str, str] = {
        "mechanism_protocol": sha256_file(mechanism_protocol_path),
        "structural_queue": sha256_file(structural_queue_path),
    }

    dynamic_requested = requested & DYNAMIC
    if dynamic_requested:
        if transition_pilot_csv is None:
            return 1, _zero_evidence(
                status="invalid_input",
                mechanism_protocol_fingerprint=mech_fp,
                reason="M1/M2 requested but --transition-pilot not supplied",
            )
        input_sha256["transition_pilot"] = sha256_file(transition_pilot_csv)
        dynamic_code, dynamic = run_dynamic_pilot(
            mechanism_protocol_path,
            transition_pilot_csv,
        )
        dynamic_status = dynamic.get("status")
        if dynamic.get("protocol_fingerprint") != mech_fp:
            return 2, _zero_evidence(
                status="STOP_dynamic_protocol_fingerprint_mismatch",
                mechanism_protocol_fingerprint=mech_fp,
            )
        hard_dynamic = (
            dynamic_code == 1
            or dynamic_status in {
                "invalid_input",
                "invalid_or_unqualified_protocol",
                "STOP_confirmatory_partition_exposed",
                "STOP_unfrozen_partition_unit",
                "STOP_missing_frozen_pilot_partition_units",
            }
        )
        if hard_dynamic:
            return 2, _zero_evidence(
                status="STOP_dynamic_mechanism_protocol_breach",
                mechanism_protocol_fingerprint=mech_fp,
                dynamic_status=dynamic_status,
                dynamic_result=dynamic,
            )
        decisions.update(
            _lane_decisions_from_dynamic(dynamic, requested)
        )
    else:
        dynamic = None

    auxiliary_requested = requested & AUXILIARY
    if auxiliary_requested:
        if M3 in auxiliary_requested and (
            genetic_populations_csv is None or genetic_pairs_csv is None
        ):
            return 1, _zero_evidence(
                status="invalid_input",
                mechanism_protocol_fingerprint=mech_fp,
                reason="M3 requested but genetic metadata inputs are incomplete",
            )
        if M4 in auxiliary_requested and environment_csv is None:
            return 1, _zero_evidence(
                status="invalid_input",
                mechanism_protocol_fingerprint=mech_fp,
                reason="M4 requested but environment input is missing",
            )
        if genetic_populations_csv is not None:
            input_sha256["genetic_populations"] = sha256_file(
                genetic_populations_csv
            )
        if genetic_pairs_csv is not None:
            input_sha256["genetic_pairs"] = sha256_file(genetic_pairs_csv)
        if environment_csv is not None:
            input_sha256["environment"] = sha256_file(environment_csv)

        auxiliary_code, auxiliary = run_auxiliary_gate(
            mechanism_protocol_path,
            genetic_populations_csv=genetic_populations_csv,
            genetic_pairs_csv=genetic_pairs_csv,
            environment_csv=environment_csv,
        )
        aux_status = auxiliary.get("status")
        hard_auxiliary = (
            auxiliary_code == 1
            or aux_status in {
                "invalid_input",
                "invalid_or_unqualified_protocol",
            }
        )
        if hard_auxiliary:
            return 2, _zero_evidence(
                status="STOP_auxiliary_mechanism_protocol_breach",
                mechanism_protocol_fingerprint=mech_fp,
                auxiliary_status=aux_status,
                auxiliary_result=auxiliary,
            )
        decisions.update(
            _lane_decisions_from_auxiliary(auxiliary, requested)
        )
    else:
        auxiliary = None

    missing_decisions = sorted(requested - set(decisions))
    if missing_decisions:
        return 2, _zero_evidence(
            status="STOP_incomplete_mechanism_lane_decisions",
            mechanism_protocol_fingerprint=mech_fp,
            missing_lanes=missing_decisions,
        )

    eligible = sorted(
        lane for lane, row in decisions.items()
        if row["qualified"]
    )
    ineligible = sorted(requested - set(eligible))

    status = (
        "eligible_to_freeze_selected_confirmatory_mechanism_protocols"
        if eligible
        else "stop_no_estimable_mechanism_lanes"
    )
    code = 0 if eligible else 2

    return code, _zero_evidence(
        status=status,
        system_id=protocol["system_id"],
        mechanism_protocol_id=protocol["protocol_id"],
        mechanism_protocol_fingerprint=mech_fp,
        structural_admission=structural,
        requested_lanes=sorted(requested),
        eligible_lanes=eligible,
        ineligible_lanes=ineligible,
        lane_decisions=decisions,
        input_sha256=input_sha256,
        dynamic_gate_status=dynamic.get("status") if dynamic else None,
        auxiliary_gate_status=auxiliary.get("status") if auxiliary else None,
        eligible_action=(
            "freeze_selected_confirmatory_mechanism_protocols_only"
            if eligible else None
        ),
        next_action=(
            "freeze_one_separate_confirmatory_protocol_per_eligible_lane"
            if eligible
            else "stop_without_opening_mechanism_outcomes"
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
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
        code, payload = run(
            args.mechanism_protocol,
            args.structural_queue,
            transition_pilot_csv=args.transition_pilot,
            genetic_populations_csv=args.genetic_populations,
            genetic_pairs_csv=args.genetic_pairs,
            environment_csv=args.environment,
            allow_synthetic_structural_queue=args.allow_synthetic_structural_queue,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        code, payload = 1, _zero_evidence(
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
