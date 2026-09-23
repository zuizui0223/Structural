#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = ROOT / "development/prospective_mechanism_discrimination_v0_1.json"


class MechanismProtocolError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MechanismProtocolError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MechanismProtocolError(f"{path} must contain a JSON object")
    return value


def validate_framework(value: dict) -> dict:
    if value.get("schema") != "structural.prospective_mechanism_discrimination.v0_1":
        raise MechanismProtocolError("unexpected mechanism framework schema")
    if value.get("status") != "prospective_mechanism_framework_not_yet_tested":
        raise MechanismProtocolError("unexpected mechanism framework status")

    origin = value.get("origin")
    if not isinstance(origin, dict):
        raise MechanismProtocolError("origin block missing")
    if origin.get("ecological_hypothesis") != (
        "development/prospective_extreme_isolation_topology_hypothesis_v0_3.json"
    ):
        raise MechanismProtocolError("mechanism framework must inherit frozen v0.3 hypothesis")

    entry = value.get("entry_conditions")
    if not isinstance(entry, dict):
        raise MechanismProtocolError("entry_conditions missing")
    required_true = (
        "independent_system_required",
        "normal_structural_admission_required",
        "v0_3_extreme_isolation_protocol_frozen_before_response_access",
        "mechanism_module_frozen_before_confirmatory_response_access_when_data_lane_is_available",
        "favourable_structural_result_may_not_be_used_to_choose_system",
        "mechanism_result_may_not_change_structural_primary",
    )
    for key in required_true:
        if entry.get(key) is not True:
            raise MechanismProtocolError(f"entry condition must be true: {key}")

    lanes = value.get("mechanism_lanes")
    if not isinstance(lanes, dict):
        raise MechanismProtocolError("mechanism_lanes missing")
    expected = {
        "M1_contemporary_colonization",
        "M2_rescue_persistence",
        "M3_historical_colonization_legacy",
        "M4_environmental_proxy",
    }
    if set(lanes) != expected:
        raise MechanismProtocolError("mechanism lane set drift")

    if lanes["M1_contemporary_colonization"].get("target_transition") != "0_to_1":
        raise MechanismProtocolError("M1 must target 0_to_1")
    if lanes["M2_rescue_persistence"].get("target_transition") != (
        "1_to_0 or equivalently 1_to_1 persistence"
    ):
        raise MechanismProtocolError("M2 must target extinction/persistence separately")

    dynamic = value.get("dynamic_separation_contract")
    if not isinstance(dynamic, dict):
        raise MechanismProtocolError("dynamic separation contract missing")
    if dynamic.get("colonization_and_extinction_are_separate_estimands") is not True:
        raise MechanismProtocolError("colonization/extinction separation lost")
    if dynamic.get(
        "pooling_0_to_1_and_1_to_0_into_one_binary_endpoint_for_mechanism_claims"
    ) is not False:
        raise MechanismProtocolError("transition pooling must remain forbidden")
    if dynamic.get("non_estimable_transition_lane_counts_as_neither_support_nor_refutation") is not True:
        raise MechanismProtocolError("non-estimability neutrality lost")
    if dynamic.get("pilot_event_counts_may_not_contribute_effect_size_or_prediction_score") is not True:
        raise MechanismProtocolError("pilot denominator firewall lost")

    current = value.get("current_systems")
    if current != []:
        raise MechanismProtocolError("current mechanism systems must remain empty until independent arrival")
    if value.get("confirmatory_response_authorized") is not False:
        raise MechanismProtocolError("confirmatory response must remain unauthorized")
    if value.get("mechanism_claim_authorized") is not False:
        raise MechanismProtocolError("mechanism claim must remain unauthorized")

    return {
        "schema": "structural.mechanism_framework_validation.v0_1",
        "status": "VALID_PROSPECTIVE_FRAMEWORK",
        "mechanism_lanes": sorted(expected),
        "current_system_count": 0,
        "confirmatory_response_authorized": False,
        "mechanism_claim_authorized": False,
    }


def validate_future_protocol(protocol: dict) -> dict:
    required = {
        "protocol_id",
        "system_id",
        "source_commit_or_data_fingerprint",
        "structural_admission_protocol_fingerprint",
        "response_firewall_state",
        "spatial_units",
        "extreme_isolation_metric",
        "extreme_isolation_threshold_rule",
        "generic_connectivity_definition",
        "source_conditioned_connectivity_definition",
        "smallest_graph_scale",
        "source_definition",
        "strong_reference_predictors",
        "local_holdout_design",
        "spatial_transfer_design",
        "mechanism_lanes_authorized",
        "response_access_authorized",
    }
    missing = sorted(required - set(protocol))
    if missing:
        raise MechanismProtocolError(
            "future protocol missing required fields: " + ", ".join(missing)
        )
    if protocol["response_access_authorized"] is not False:
        raise MechanismProtocolError("new mechanism protocol must start response-sealed")
    if protocol["response_firewall_state"] not in {
        "response_sealed",
        "predictor_only_metadata_open",
    }:
        raise MechanismProtocolError("unexpected response firewall state")

    threshold = protocol["extreme_isolation_threshold_rule"]
    if not isinstance(threshold, str) or not threshold.strip():
        raise MechanismProtocolError("extreme isolation threshold rule must be explicit")

    lanes = protocol["mechanism_lanes_authorized"]
    if not isinstance(lanes, list) or not lanes:
        raise MechanismProtocolError("mechanism_lanes_authorized must be non-empty")
    allowed = {
        "M1_contemporary_colonization",
        "M2_rescue_persistence",
        "M3_historical_colonization_legacy",
        "M4_environmental_proxy",
    }
    unknown = sorted(set(lanes) - allowed)
    if unknown:
        raise MechanismProtocolError("unknown mechanism lanes: " + ", ".join(unknown))

    if any(lane in lanes for lane in ("M1_contemporary_colonization", "M2_rescue_persistence")):
        dynamic_required = {
            "time_axis_if_dynamic",
            "colonization_transition_definition_if_M1",
            "extinction_transition_definition_if_M2",
            "transition_event_minima_if_dynamic",
        }
        dynamic_missing = sorted(dynamic_required - set(protocol))
        if dynamic_missing:
            raise MechanismProtocolError(
                "dynamic mechanism protocol missing fields: "
                + ", ".join(dynamic_missing)
            )
        minima = protocol["transition_event_minima_if_dynamic"]
        if not isinstance(minima, dict):
            raise MechanismProtocolError("transition_event_minima_if_dynamic must be object")
        if "minimum_0_to_1" not in minima or "minimum_1_to_0" not in minima:
            raise MechanismProtocolError("both transition event minima must be frozen")

    if "M3_historical_colonization_legacy" in lanes:
        if "genetic_estimand_and_null_if_M3" not in protocol:
            raise MechanismProtocolError("M3 requires genetic estimand and null")

    if "M4_environmental_proxy" in lanes:
        if "enriched_environment_predictors_if_M4" not in protocol:
            raise MechanismProtocolError("M4 requires frozen enriched environment predictors")

    return {
        "schema": "structural.future_mechanism_protocol_validation.v0_1",
        "status": "VALID_RESPONSE_SEALED_PROTOCOL",
        "protocol_id": protocol["protocol_id"],
        "system_id": protocol["system_id"],
        "mechanism_lanes_authorized": lanes,
        "response_access_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol", type=Path, nargs="?")
    args = parser.parse_args()
    try:
        if args.protocol is None:
            result = validate_framework(load_json(FRAMEWORK))
        else:
            result = validate_future_protocol(load_json(args.protocol))
    except MechanismProtocolError as exc:
        print(f"mechanism protocol validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
