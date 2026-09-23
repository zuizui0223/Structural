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

from scripts.run_mechanism_admission_v0_4 import (  # noqa: E402
    M1,
    M2,
    M3,
    M4,
    protocol_fingerprint as mechanism_protocol_fingerprint,
    run as run_mechanism_admission,
)

SCHEMA = "structural.mechanism_confirmatory_protocol.v0_5"
RECEIPT_SCHEMA = "structural.mechanism_confirmatory_freeze_receipt.v0_5"
LANES = {M1, M2, M3, M4}


class MechanismConfirmatoryFreezeError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MechanismConfirmatoryFreezeError(
            f"cannot read JSON {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MechanismConfirmatoryFreezeError(
            f"{path} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_fingerprint(value: dict) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_nonempty_string(protocol: dict, key: str) -> str:
    value = protocol.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MechanismConfirmatoryFreezeError(
            f"{key} must be a non-empty string"
        )
    return value


def _require_string_list(protocol: dict, key: str, *, allow_empty: bool = False) -> list[str]:
    value = protocol.get(key)
    if not isinstance(value, list):
        raise MechanismConfirmatoryFreezeError(f"{key} must be a list")
    if not allow_empty and not value:
        raise MechanismConfirmatoryFreezeError(f"{key} must be non-empty")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise MechanismConfirmatoryFreezeError(
            f"{key} must contain non-empty strings"
        )
    if len(value) != len(set(value)):
        raise MechanismConfirmatoryFreezeError(f"{key} contains duplicates")
    return value


def _validate_common(
    lane_protocol: dict,
    *,
    mechanism_protocol: dict,
    admission: dict,
) -> tuple[str, str]:
    if lane_protocol.get("schema") != SCHEMA:
        raise MechanismConfirmatoryFreezeError(
            "unexpected confirmatory mechanism protocol schema"
        )
    if lane_protocol.get("status") != "response_sealed_confirmatory_protocol_draft":
        raise MechanismConfirmatoryFreezeError(
            "confirmatory mechanism protocol must start response-sealed"
        )

    protocol_id = _require_nonempty_string(lane_protocol, "protocol_id")
    system_id = _require_nonempty_string(lane_protocol, "system_id")
    lane = _require_nonempty_string(lane_protocol, "mechanism_lane")

    if lane not in LANES:
        raise MechanismConfirmatoryFreezeError(
            f"unknown mechanism lane: {lane}"
        )
    if system_id != mechanism_protocol.get("system_id"):
        raise MechanismConfirmatoryFreezeError(
            "confirmatory mechanism protocol system_id mismatch"
        )
    if lane not in admission.get("eligible_lanes", []):
        raise MechanismConfirmatoryFreezeError(
            f"mechanism lane was not admitted by v0.4: {lane}"
        )

    if lane_protocol.get("parent_binding_mode") != (
        "bind_from_replayed_v0_4_admission_at_freeze"
    ):
        raise MechanismConfirmatoryFreezeError(
            "parent_binding_mode must bind from replayed v0.4 admission"
        )

    structural = admission.get("structural_admission")
    if not isinstance(structural, dict):
        raise MechanismConfirmatoryFreezeError(
            "v0.4 admission lacks Structural parent receipt"
        )
    if lane_protocol.get("response_firewall_state") != "response_sealed":
        raise MechanismConfirmatoryFreezeError(
            "response_firewall_state must be response_sealed"
        )
    if lane_protocol.get("confirmatory_response_accessed") is not False:
        raise MechanismConfirmatoryFreezeError(
            "confirmatory mechanism response must remain unopened"
        )
    if lane_protocol.get("protocol_selected_after_response") is not False:
        raise MechanismConfirmatoryFreezeError(
            "confirmatory mechanism protocol may not be selected after response"
        )
    if lane_protocol.get("mechanism_claim_authorized") is not False:
        raise MechanismConfirmatoryFreezeError(
            "protocol draft may not authorize a mechanism claim"
        )

    _require_string_list(lane_protocol, "response_partition")
    _require_nonempty_string(lane_protocol, "local_holdout_design")
    _require_nonempty_string(lane_protocol, "spatial_transfer_design")
    _require_nonempty_string(lane_protocol, "primary_estimand")
    _require_nonempty_string(lane_protocol, "reference_definition")
    _require_nonempty_string(lane_protocol, "candidate_definition")
    _require_nonempty_string(lane_protocol, "scoring_rule")
    _require_nonempty_string(lane_protocol, "uncertainty_rule")
    _require_nonempty_string(lane_protocol, "success_rule")
    _require_string_list(
        lane_protocol, "secondary_diagnostics", allow_empty=True
    )

    if lane in {M1, M2}:
        frozen = mechanism_protocol.get("mechanism_confirmatory_partition")
        if isinstance(frozen, list) and lane_protocol["response_partition"] != frozen:
            raise MechanismConfirmatoryFreezeError(
                "dynamic lane response_partition must equal frozen mechanism "
                "confirmatory partition"
            )

    return protocol_id, lane


def _validate_lane_specific(
    lane_protocol: dict,
    *,
    mechanism_protocol: dict,
    lane: str,
) -> None:
    details = lane_protocol.get("lane_specific")
    if not isinstance(details, dict):
        raise MechanismConfirmatoryFreezeError(
            "lane_specific must be a JSON object"
        )

    if lane == M1:
        if details.get("transition_target") != "0_to_1":
            raise MechanismConfirmatoryFreezeError(
                "M1 transition_target must be 0_to_1"
            )
        if details.get("transition_non_event") != "0_to_0":
            raise MechanismConfirmatoryFreezeError(
                "M1 transition_non_event must be 0_to_0"
            )
        _require_nonempty_string(details, "detection_model")
        if details.get("pilot_minima_bound") is not True:
            raise MechanismConfirmatoryFreezeError(
                "M1 confirmatory protocol must bind frozen pilot minima"
            )

    elif lane == M2:
        if details.get("transition_target") != "1_to_0":
            raise MechanismConfirmatoryFreezeError(
                "M2 transition_target must be 1_to_0"
            )
        if details.get("transition_non_event") != "1_to_1":
            raise MechanismConfirmatoryFreezeError(
                "M2 transition_non_event must be 1_to_1"
            )
        _require_nonempty_string(details, "detection_model")
        if details.get("pilot_minima_bound") is not True:
            raise MechanismConfirmatoryFreezeError(
                "M2 confirmatory protocol must bind frozen pilot minima"
            )

    elif lane == M3:
        _require_nonempty_string(details, "genetic_outcome")
        _require_nonempty_string(details, "genetic_null")
        _require_nonempty_string(details, "geographic_control")
        if details.get("source_comparison") != "graph_connected_vs_alternative":
            raise MechanismConfirmatoryFreezeError(
                "M3 source_comparison must be graph_connected_vs_alternative"
            )
        if details.get("genetic_outcome_accessed") is not False:
            raise MechanismConfirmatoryFreezeError(
                "M3 genetic outcome must remain unopened at freeze"
            )
        parent_null = mechanism_protocol.get("genetic_estimand_and_null_if_M3")
        if not isinstance(parent_null, str) or not parent_null.strip():
            raise MechanismConfirmatoryFreezeError(
                "parent mechanism protocol lacks frozen M3 genetic null"
            )

    elif lane == M4:
        enriched = details.get("enriched_predictors")
        if enriched != mechanism_protocol.get(
            "enriched_environment_predictors_if_M4"
        ):
            raise MechanismConfirmatoryFreezeError(
                "M4 enriched predictors must exactly match frozen parent list"
            )
        if not isinstance(enriched, list) or not enriched:
            raise MechanismConfirmatoryFreezeError(
                "M4 enriched predictors must be non-empty"
            )
        if details.get("confirmatory_response_accessed") is not False:
            raise MechanismConfirmatoryFreezeError(
                "M4 confirmatory response must remain unopened at freeze"
            )
        if details.get("predictors_selected_after_response") is not False:
            raise MechanismConfirmatoryFreezeError(
                "M4 predictors may not be selected after response"
            )
        _require_nonempty_string(details, "proxy_decision_rule")


def freeze(
    lane_protocol_path: Path,
    mechanism_protocol_path: Path,
    structural_queue_path: Path,
    *,
    transition_pilot_csv: Path | None = None,
    genetic_populations_csv: Path | None = None,
    genetic_pairs_csv: Path | None = None,
    environment_csv: Path | None = None,
    allow_synthetic_structural_queue: bool = False,
) -> tuple[int, dict]:
    mechanism_protocol = load_json(mechanism_protocol_path)

    admission_code, admission = run_mechanism_admission(
        mechanism_protocol_path,
        structural_queue_path,
        transition_pilot_csv=transition_pilot_csv,
        genetic_populations_csv=genetic_populations_csv,
        genetic_pairs_csv=genetic_pairs_csv,
        environment_csv=environment_csv,
        allow_synthetic_structural_queue=allow_synthetic_structural_queue,
    )
    if admission_code != 0:
        return 2, {
            "schema": RECEIPT_SCHEMA,
            "status": "STOP_parent_mechanism_admission_not_eligible",
            "parent_admission_status": admission.get("status"),
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "mechanism_claim_contribution": 0,
        }

    lane_protocol = load_json(lane_protocol_path)
    try:
        protocol_id, lane = _validate_common(
            lane_protocol,
            mechanism_protocol=mechanism_protocol,
            admission=admission,
        )
        _validate_lane_specific(
            lane_protocol,
            mechanism_protocol=mechanism_protocol,
            lane=lane,
        )
    except MechanismConfirmatoryFreezeError as exc:
        return 2, {
            "schema": RECEIPT_SCHEMA,
            "status": "STOP_invalid_confirmatory_mechanism_protocol",
            "reason": str(exc),
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "mechanism_claim_contribution": 0,
        }

    input_hashes = {
        "lane_protocol": sha256_file(lane_protocol_path),
        "mechanism_protocol": sha256_file(mechanism_protocol_path),
        "structural_queue": sha256_file(structural_queue_path),
    }
    if lane in {M1, M2}:
        if transition_pilot_csv is None:
            raise MechanismConfirmatoryFreezeError(
                "dynamic lane freeze requires transition pilot input"
            )
        input_hashes["transition_pilot"] = sha256_file(transition_pilot_csv)
    if lane == M3:
        if genetic_populations_csv is None or genetic_pairs_csv is None:
            raise MechanismConfirmatoryFreezeError(
                "M3 freeze requires genetic sampling/source-pair inputs"
            )
        input_hashes["genetic_populations"] = sha256_file(
            genetic_populations_csv
        )
        input_hashes["genetic_pairs"] = sha256_file(genetic_pairs_csv)
    if lane == M4:
        if environment_csv is None:
            raise MechanismConfirmatoryFreezeError(
                "M4 freeze requires environment input"
            )
        input_hashes["environment"] = sha256_file(environment_csv)

    lane_fp = canonical_fingerprint(lane_protocol)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "frozen_confirmatory_mechanism_protocol_response_still_sealed",
        "system_id": mechanism_protocol["system_id"],
        "mechanism_lane": lane,
        "protocol_id": protocol_id,
        "protocol_fingerprint": lane_fp,
        "parent_mechanism_protocol_fingerprint":
            mechanism_protocol_fingerprint(mechanism_protocol),
        "parent_structural_protocol_fingerprint":
            admission["structural_admission"][
                "structural_protocol_fingerprint"
            ],
        "parent_mechanism_admission_status": admission["status"],
        "input_sha256": input_hashes,
        "response_partition": lane_protocol["response_partition"],
        "scoring_rule": lane_protocol["scoring_rule"],
        "success_rule": lane_protocol["success_rule"],
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "confirmatory_response_authorized": False,
        "mechanism_claim_authorized": False,
        "ttf_handoff_authorized": False,
        "eligible_next_action":
            "run_separate_lane_response_authorization_gate_only",
    }
    return 0, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_protocol", type=Path)
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
        code, payload = freeze(
            args.lane_protocol,
            args.mechanism_protocol,
            args.structural_queue,
            transition_pilot_csv=args.transition_pilot,
            genetic_populations_csv=args.genetic_populations,
            genetic_pairs_csv=args.genetic_pairs,
            environment_csv=args.environment,
            allow_synthetic_structural_queue=args.allow_synthetic_structural_queue,
        )
    except (OSError, ValueError, json.JSONDecodeError, MechanismConfirmatoryFreezeError) as exc:
        code, payload = 1, {
            "schema": RECEIPT_SCHEMA,
            "status": "invalid_input",
            "reason": str(exc),
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "mechanism_claim_contribution": 0,
        }

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
