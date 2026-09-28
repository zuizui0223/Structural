#!/usr/bin/env python3
"""Consume the frozen 19-island pilot authorization exactly once."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Mapping

from scripts.run_transition_pilot_v0_32 import run as run_v032
from structural.boreal_19island_beetle_pilot_router import (
    Boreal19BeetlePilotRouterError,
    build_boreal_19island_beetle_pilot_surface,
)
from structural.future_admission_v0_42 import (
    FutureAdmissionStatus,
    evaluate_future_admission_v0_42,
    future_admission_receipt_mapping,
)
from structural.response_quality_attrition import (
    contract_fingerprint,
    contract_from_mapping,
)
from structural.transition_pilot_protocol import (
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_one_shot_pilot_contract_v1_07.json"
)
DEFAULT_PROTOCOL = (
    ROOT / "development/boreal_19island_v031_protocol_v1_03.json"
)
DEFAULT_QUALITY = (
    ROOT / "development/boreal_19island_v042_quality_contract_v1_03.json"
)


class Boreal19PilotExecutionError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19PilotExecutionError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_pre_access(
    authorization: Mapping,
    protocol_mapping: Mapping,
    quality_mapping: Mapping,
    response_bytes: bytes,
    *,
    authorization_file_sha256: str,
    contract: Mapping,
):
    rule = contract["authorization"]
    if authorization.get("schema") != rule["schema"]:
        raise Boreal19PilotExecutionError(
            "unexpected v1.05 authorization schema"
        )
    if authorization.get("status") != rule["status"]:
        raise Boreal19PilotExecutionError("v1.05 authorization did not qualify")
    if authorization.get("candidate_id") != contract["candidate_id"]:
        raise Boreal19PilotExecutionError("authorization candidate mismatch")
    if authorization.get("authorization_fingerprint") != (
        rule["expected_fingerprint"]
    ):
        raise Boreal19PilotExecutionError(
            "authorization fingerprint mismatch"
        )
    if authorization_file_sha256 != rule["expected_json_sha256"]:
        raise Boreal19PilotExecutionError(
            "authorization JSON SHA mismatch"
        )
    if authorization.get("pilot_response_authorized") is not True:
        raise Boreal19PilotExecutionError("pilot response not authorized")
    if authorization.get("confirmatory_response_authorized") is not False:
        raise Boreal19PilotExecutionError(
            "confirmatory response ceiling violated"
        )
    if authorization.get("authorization_consumed") is not False:
        raise Boreal19PilotExecutionError("authorization already consumed")
    if authorization.get("response_values_opened_by_authorization") is not False:
        raise Boreal19PilotExecutionError(
            "authorization unexpectedly opened response values"
        )
    for key, expected in (
        ("effect_size", None),
        ("prediction_score", None),
        ("predictive_denominator_contribution", 0),
        ("counts_as_empirical_evidence", False),
    ):
        if authorization.get(key) != expected:
            raise Boreal19PilotExecutionError(
                f"authorization ceiling mismatch: {key}"
            )

    protocol = protocol_from_mapping(dict(protocol_mapping))
    quality = contract_from_mapping(dict(quality_mapping))
    pfp = protocol_fingerprint(protocol)
    qfp = contract_fingerprint(quality)
    if authorization.get("protocol_fingerprint") != pfp:
        raise Boreal19PilotExecutionError("protocol fingerprint mismatch")
    if authorization.get("quality_contract_fingerprint") != qfp:
        raise Boreal19PilotExecutionError("quality fingerprint mismatch")
    if quality.parent_protocol_fingerprint != pfp:
        raise Boreal19PilotExecutionError(
            "quality contract is not bound to exact protocol"
        )

    population = contract["population"]
    full = authorization.get("full_source_island_order")
    analysis = authorization.get("analysis_island_order")
    pilot_islands = authorization.get("pilot_islands")
    confirmatory_islands = authorization.get("confirmatory_islands")
    excluded = authorization.get("excluded_islands")
    island_to_block = authorization.get("island_to_block")
    if not isinstance(full, list) or len(full) != population["full_source_island_count"]:
        raise Boreal19PilotExecutionError("full source island count drift")
    if not isinstance(analysis, list) or len(analysis) != population["analysis_island_count"]:
        raise Boreal19PilotExecutionError("analysis island count drift")
    if not isinstance(pilot_islands, list) or len(pilot_islands) != population["pilot_island_count"]:
        raise Boreal19PilotExecutionError("pilot island count drift")
    if (
        not isinstance(confirmatory_islands, list)
        or len(confirmatory_islands) != population["confirmatory_island_count"]
    ):
        raise Boreal19PilotExecutionError("confirmatory island count drift")
    if not isinstance(excluded, list) or len(excluded) != population["excluded_island_count"]:
        raise Boreal19PilotExecutionError("excluded island count drift")
    if len(set(full)) != len(full) or len(set(analysis)) != len(analysis):
        raise Boreal19PilotExecutionError("island universe contains duplicates")
    if not set(analysis) < set(full):
        raise Boreal19PilotExecutionError(
            "analysis population is not a strict subset of full source universe"
        )
    if set(pilot_islands) & set(confirmatory_islands):
        raise Boreal19PilotExecutionError(
            "pilot and confirmatory islands overlap"
        )
    if set(pilot_islands) | set(confirmatory_islands) != set(analysis):
        raise Boreal19PilotExecutionError(
            "pilot/confirmatory islands do not cover analysis population"
        )
    if set(excluded) != set(full) - set(analysis):
        raise Boreal19PilotExecutionError("excluded island set drift")
    if not isinstance(island_to_block, dict) or set(island_to_block) != set(analysis):
        raise Boreal19PilotExecutionError("analysis island routing map drift")

    pilot_blocks = authorization.get("pilot_block_ids")
    confirmatory_blocks = authorization.get("confirmatory_block_ids")
    if tuple(pilot_blocks or ()) != protocol.pilot_partition:
        raise Boreal19PilotExecutionError("pilot blocks drift from protocol")
    if tuple(confirmatory_blocks or ()) != protocol.confirmatory_partition:
        raise Boreal19PilotExecutionError(
            "confirmatory blocks drift from protocol"
        )
    if len(protocol.pilot_partition) != population["pilot_block_count"]:
        raise Boreal19PilotExecutionError("pilot block count drift")
    if len(protocol.confirmatory_partition) != population["confirmatory_block_count"]:
        raise Boreal19PilotExecutionError("confirmatory block count drift")

    semantic = authorization.get("allowed_semantic_access")
    if not isinstance(semantic, dict):
        raise Boreal19PilotExecutionError(
            "authorization semantic-access map missing"
        )
    for key, expected in (
        ("species_header_names", True),
        ("routing_island_field_all_42_rows", True),
        ("pilot_island_occurrence_cells", True),
        ("analysis_confirmatory_occurrence_cells", False),
        ("excluded_23_island_occurrence_cells", False),
    ):
        if semantic.get(key) is not expected:
            raise Boreal19PilotExecutionError(
                f"authorization semantic-access drift: {key}"
            )

    router = authorization.get("router")
    if not isinstance(router, dict):
        raise Boreal19PilotExecutionError("authorization router rule missing")
    if router.get("implementation") != contract["semantic_access"]["router"]:
        raise Boreal19PilotExecutionError("router implementation drift")
    if router.get("confirmatory_target_values_parsed_must_equal") != 0:
        raise Boreal19PilotExecutionError(
            "confirmatory parse ceiling drift"
        )
    if router.get("excluded_target_values_parsed_must_equal") != 0:
        raise Boreal19PilotExecutionError("excluded parse ceiling drift")

    target = contract["response_file"]
    if len(response_bytes) != target["expected_size_bytes"]:
        raise Boreal19PilotExecutionError("response byte size mismatch")
    if sha256_bytes(response_bytes) != target["expected_sha256"]:
        raise Boreal19PilotExecutionError("response SHA mismatch")
    response = authorization.get("response_file")
    if not isinstance(response, dict):
        raise Boreal19PilotExecutionError(
            "authorized response identity missing"
        )
    for key, expected in (
        ("name", target["name"]),
        ("dryad_file_id", target["dryad_file_id"]),
        ("size_bytes", target["expected_size_bytes"]),
        ("sha256", target["expected_sha256"]),
        ("expected_species_columns", target["expected_species_columns"]),
    ):
        if response.get(key) != expected:
            raise Boreal19PilotExecutionError(
                f"authorized response identity drift: {key}"
            )
    return protocol, quality, full, analysis, island_to_block


def build_snapshot(
    *,
    routed,
    candidate_id: str,
    response_file_sha256: str,
    qualified_for_confirmatory_model_freeze: bool,
) -> dict:
    island_to_block = dict(routed.pilot_island_to_block)
    targets = dict(routed.pilot_targets_hex_by_island)
    if tuple(island_to_block) != routed.pilot_island_order:
        raise Boreal19PilotExecutionError(
            "pilot island/block snapshot order drift"
        )
    if tuple(targets) != routed.pilot_island_order:
        raise Boreal19PilotExecutionError(
            "pilot target snapshot order drift"
        )

    snapshot = {
        "schema": "structural.boreal_19island_pilot_training_snapshot.v1_07",
        "status": "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN",
        "candidate_id": candidate_id,
        "response_file_sha256": response_file_sha256,
        "raw_pilot_surface_sha256": routed.raw_surface_sha256,
        "pilot_species_universe": list(routed.pilot_species_universe),
        "pilot_species_universe_count": routed.pilot_species_universe_count,
        "pilot_species_universe_sha256": routed.pilot_species_universe_sha256,
        "pilot_island_order": list(routed.pilot_island_order),
        "pilot_island_to_block": island_to_block,
        "target_bit_count": routed.pilot_species_universe_count,
        "targets_hex_by_island": targets,
        "source_response_rows_seen": routed.source_response_rows_seen,
        "routing_island_fields_decoded": routed.routing_island_fields_decoded,
        "pilot_island_count": routed.pilot_island_count,
        "confirmatory_island_count": routed.confirmatory_island_count,
        "excluded_island_count": routed.excluded_island_count,
        "pilot_block_count": routed.pilot_block_count,
        "confirmatory_target_values_parsed": 0,
        "excluded_target_values_parsed": 0,
        "confirmatory_occurrence_values_stored": False,
        "excluded_occurrence_values_stored": False,
        "single_semantic_router_pass": True,
        "qualified_for_confirmatory_model_freeze": bool(
            qualified_for_confirmatory_model_freeze
        ),
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
    }
    snapshot["snapshot_fingerprint"] = canonical_sha256(snapshot)
    return snapshot


def execute(
    authorization: dict,
    protocol_mapping: dict,
    quality_mapping: dict,
    response_bytes: bytes,
    *,
    authorization_file_sha256: str,
    contract: dict,
) -> tuple[dict, dict | None]:
    (
        protocol,
        quality,
        full,
        analysis,
        island_to_block,
    ) = _validate_pre_access(
        authorization,
        protocol_mapping,
        quality_mapping,
        response_bytes,
        authorization_file_sha256=authorization_file_sha256,
        contract=contract,
    )

    # The semantic router is the irreversible boundary. From this line onward,
    # any failure consumes the one-shot authorization.
    try:
        routed = build_boreal_19island_beetle_pilot_surface(
            response_csv_bytes=response_bytes,
            full_expected_islands=full,
            analysis_expected_islands=analysis,
            analysis_island_to_block=island_to_block,
            pilot_partition=protocol.pilot_partition,
            confirmatory_partition=protocol.confirmatory_partition,
            expected_species_count=contract["response_file"][
                "expected_species_columns"
            ],
        )
    except Boreal19BeetlePilotRouterError as exc:
        return ({
            "schema": "structural.boreal_19island_burned_pilot_execution.v1_07",
            "status": "TERMINAL_PILOT_ROUTER_STOP",
            "reason": str(exc),
            "authorization_consumed": True,
            "pilot_response_opened": True,
            "confirmatory_target_values_parsed": 0,
            "excluded_target_values_parsed": 0,
            "model_snapshot_frozen": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }, None)

    semantic = contract["semantic_access"]
    firewall_failures = []
    if routed.source_response_rows_seen != contract["population"][
        "full_source_island_count"
    ]:
        firewall_failures.append("source_response_row_count")
    if routed.routing_island_fields_decoded != contract["population"][
        "full_source_island_count"
    ]:
        firewall_failures.append("routing_island_field_count")
    if routed.pilot_island_count != contract["population"]["pilot_island_count"]:
        firewall_failures.append("pilot_island_count")
    if routed.confirmatory_island_count != contract["population"][
        "confirmatory_island_count"
    ]:
        firewall_failures.append("confirmatory_island_count")
    if routed.excluded_island_count != contract["population"]["excluded_island_count"]:
        firewall_failures.append("excluded_island_count")
    if routed.pilot_target_values_parsed != semantic[
        "expected_pilot_target_values_parsed"
    ]:
        firewall_failures.append("pilot_target_values_parsed")
    if routed.confirmatory_target_values_parsed != semantic[
        "required_confirmatory_target_values_parsed"
    ]:
        firewall_failures.append("confirmatory_target_values_parsed")
    if routed.excluded_target_values_parsed != semantic[
        "required_excluded_target_values_parsed"
    ]:
        firewall_failures.append("excluded_target_values_parsed")
    if firewall_failures:
        return ({
            "schema": "structural.boreal_19island_burned_pilot_execution.v1_07",
            "status": "TERMINAL_FIREWALL_VIOLATION",
            "reason": ",".join(firewall_failures),
            "authorization_consumed": True,
            "pilot_response_opened": True,
            "confirmatory_target_values_parsed": (
                routed.confirmatory_target_values_parsed
            ),
            "excluded_target_values_parsed": routed.excluded_target_values_parsed,
            "model_snapshot_frozen": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }, None)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        protocol_path = tmpdir / "protocol.json"
        pilot_path = tmpdir / "pilot.csv"
        protocol_path.write_text(
            json.dumps(protocol_mapping, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pilot_path.write_text(routed.csv_text, encoding="utf-8")
        v032_code, pilot_result = run_v032(protocol_path, pilot_path)

    admission = evaluate_future_admission_v0_42(
        protocol=protocol,
        pilot_result=pilot_result,
        quality_contract=quality,
        confirmatory_response_accessed=False,
    )
    admission_receipt = future_admission_receipt_mapping(admission)
    qualified = admission.status is FutureAdmissionStatus.ADMITTED

    snapshot = build_snapshot(
        routed=routed,
        candidate_id=contract["candidate_id"],
        response_file_sha256=contract["response_file"]["expected_sha256"],
        qualified_for_confirmatory_model_freeze=qualified,
    )

    result = {
        "schema": "structural.boreal_19island_burned_pilot_execution.v1_07",
        "status": (
            contract["qualified_ceiling"]["status"]
            if qualified
            else "TERMINAL_PILOT_GATE_STOP"
        ),
        "authorization_fingerprint": authorization[
            "authorization_fingerprint"
        ],
        "authorization_consumed": True,
        "pilot_response_opened": True,
        "response_file_sha256": contract["response_file"]["expected_sha256"],
        "raw_pilot_surface_sha256": routed.raw_surface_sha256,
        "source_response_rows_seen": routed.source_response_rows_seen,
        "routing_island_fields_decoded": routed.routing_island_fields_decoded,
        "pilot_island_rows_semantically_parsed": (
            routed.pilot_island_rows_semantically_parsed
        ),
        "pilot_target_values_parsed": routed.pilot_target_values_parsed,
        "confirmatory_target_values_parsed": 0,
        "excluded_target_values_parsed": 0,
        "pilot_species_universe_count": routed.pilot_species_universe_count,
        "pilot_species_universe_sha256": (
            routed.pilot_species_universe_sha256
        ),
        "model_snapshot_frozen": True,
        "model_snapshot_fingerprint": snapshot["snapshot_fingerprint"],
        "pilot_result": pilot_result,
        "v0_32_exit_code": v032_code,
        "future_admission_receipt": admission_receipt,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "confirmatory_response_authorized": False,
        "eligible_action": (
            contract["qualified_ceiling"]["eligible_action"]
            if qualified
            else None
        ),
    }
    return result, snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("response_csv", type=Path)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--quality", type=Path, default=DEFAULT_QUALITY)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--training-snapshot", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_19island_one_shot_pilot_contract.v1_07"
        ):
            raise Boreal19PilotExecutionError(
                "unexpected v1.07 pilot contract schema"
            )
        response_bytes = args.response_csv.read_bytes()
        result, snapshot = execute(
            _load(args.authorization),
            _load(args.protocol),
            _load(args.quality),
            response_bytes,
            authorization_file_sha256=sha256_file(args.authorization),
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19PilotExecutionError,
    ) as exc:
        result = {
            "schema": "structural.boreal_19island_burned_pilot_execution.v1_07",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "authorization_consumed": False,
            "pilot_response_opened": False,
            "confirmatory_target_values_parsed": 0,
            "excluded_target_values_parsed": 0,
            "model_snapshot_frozen": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }
        snapshot = None
        code = 2
    else:
        code = 0 if result["status"] == (
            "QUALIFIED_TO_FREEZE_19ISLAND_CONFIRMATORY_MODEL_WITH_PILOT_SNAPSHOT"
        ) else 2

    if snapshot is not None and args.training_snapshot is not None:
        args.training_snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.training_snapshot.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.execution_receipt is not None:
        args.execution_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.execution_receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
