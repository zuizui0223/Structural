#!/usr/bin/env python3
"""Consume one authorized boreal beetle burned pilot and run v0.32/v0.42."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from scripts.run_transition_pilot_v0_32 import run as run_v032
from structural.boreal_beetle_pilot_router import (
    BorealBeetlePilotRouterError,
    build_boreal_beetle_pilot_surface,
)
from structural.future_admission_v0_42 import (
    FutureAdmissionStatus,
    evaluate_future_admission_v0_42,
    future_admission_receipt_mapping,
)
from structural.response_quality_attrition import contract_from_mapping
from structural.transition_pilot_protocol import (
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_beetle_one_shot_pilot_contract_v0_82.json"
)
DEFAULT_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class BorealPilotExecutionError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        raise BorealPilotExecutionError(f"{path.name} must contain a JSON object")
    return x


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_universe(path: Path = DEFAULT_UNIVERSE) -> tuple[str, ...]:
    x = _load(path)
    codes = tuple(x["current_study_island_universe"]["codes"])
    if len(codes) != 42 or len(set(codes)) != 42:
        raise BorealPilotExecutionError(
            "unexpected frozen 42-island universe"
        )
    return codes


def _validate_pre_access(
    authorization: dict,
    protocol_mapping: dict,
    quality_mapping: dict,
    spatial_receipt: dict,
    response_bytes: bytes,
    *,
    contract: dict,
    spatial_receipt_sha256: str,
) -> tuple:
    pre = contract["pre_access"]
    if authorization.get("schema") != pre["authorization_schema"]:
        raise BorealPilotExecutionError(
            "unexpected v0.81 authorization schema"
        )
    if authorization.get("status") != pre["authorization_status"]:
        raise BorealPilotExecutionError(
            "v0.81 authorization did not qualify"
        )
    if authorization.get("candidate_id") != contract["candidate_id"]:
        raise BorealPilotExecutionError("authorization candidate mismatch")
    if authorization.get("pilot_response_authorized") is not True:
        raise BorealPilotExecutionError("pilot response not authorized")
    if authorization.get("confirmatory_response_authorized") is not False:
        raise BorealPilotExecutionError("confirmatory response ceiling violated")
    if authorization.get("authorization_consumed") is not False:
        raise BorealPilotExecutionError("authorization already consumed")

    protocol = protocol_from_mapping(protocol_mapping)
    quality = contract_from_mapping(quality_mapping)
    pfp = protocol_fingerprint(protocol)
    if authorization.get("protocol_fingerprint") != pfp:
        raise BorealPilotExecutionError("protocol fingerprint mismatch")
    if quality.parent_protocol_fingerprint != pfp:
        raise BorealPilotExecutionError("quality contract parent mismatch")
    if authorization.get("quality_contract_fingerprint") is None:
        raise BorealPilotExecutionError("quality fingerprint missing")

    from structural.response_quality_attrition import contract_fingerprint
    if authorization["quality_contract_fingerprint"] != contract_fingerprint(quality):
        raise BorealPilotExecutionError("quality fingerprint mismatch")

    if spatial_receipt.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealPilotExecutionError("unexpected v0.75 spatial receipt")
    if authorization.get("source_spatial_receipt_sha256") != spatial_receipt_sha256:
        raise BorealPilotExecutionError("spatial receipt SHA mismatch")
    island_to_block = spatial_receipt.get("island_to_block")
    if not isinstance(island_to_block, dict) or len(island_to_block) != 42:
        raise BorealPilotExecutionError("invalid 42-island routing map")
    if tuple(spatial_receipt.get("pilot_block_ids") or ()) != protocol.pilot_partition:
        raise BorealPilotExecutionError("pilot blocks drift from protocol")
    if tuple(spatial_receipt.get("confirmatory_block_ids") or ()) != (
        protocol.confirmatory_partition
    ):
        raise BorealPilotExecutionError("confirmatory blocks drift from protocol")

    target = contract["response_file"]
    if len(response_bytes) != target["expected_size_bytes"]:
        raise BorealPilotExecutionError("response byte size mismatch")
    if sha256_bytes(response_bytes) != target["expected_sha256"]:
        raise BorealPilotExecutionError("response SHA mismatch")
    if authorization.get("response_file") != {
        "name": target["name"],
        "dryad_file_id": target["dryad_file_id"],
        "size_bytes": target["expected_size_bytes"],
        "sha256": target["expected_sha256"],
    }:
        raise BorealPilotExecutionError("authorized response identity drift")
    return protocol, quality, island_to_block


def execute(
    authorization: dict,
    protocol_mapping: dict,
    quality_mapping: dict,
    spatial_receipt: dict,
    response_bytes: bytes,
    *,
    contract: dict,
    spatial_receipt_sha256: str,
    expected_islands: tuple[str, ...],
) -> dict:
    protocol, quality, island_to_block = _validate_pre_access(
        authorization,
        protocol_mapping,
        quality_mapping,
        spatial_receipt,
        response_bytes,
        contract=contract,
        spatial_receipt_sha256=spatial_receipt_sha256,
    )

    # From this point onward, the one-shot authorization is consumed even if
    # a pilot value/domain/estimability gate fails.
    try:
        routed = build_boreal_beetle_pilot_surface(
            response_csv_bytes=response_bytes,
            island_to_block=island_to_block,
            pilot_partition=protocol.pilot_partition,
            confirmatory_partition=protocol.confirmatory_partition,
            expected_islands=expected_islands,
            expected_species_count=466,
        )
    except BorealBeetlePilotRouterError as exc:
        return {
            "schema": "structural.boreal_beetle_burned_pilot_execution.v0_82",
            "status": "TERMINAL_PILOT_ROUTER_STOP",
            "reason": str(exc),
            "authorization_consumed": True,
            "pilot_response_opened": True,
            "confirmatory_target_values_parsed": 0,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }

    if routed.confirmatory_target_values_parsed != 0:
        return {
            "schema": "structural.boreal_beetle_burned_pilot_execution.v0_82",
            "status": "TERMINAL_FIREWALL_VIOLATION",
            "authorization_consumed": True,
            "pilot_response_opened": True,
            "confirmatory_target_values_parsed": (
                routed.confirmatory_target_values_parsed
            ),
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        p = tmpdir / "protocol.json"
        surface = tmpdir / "pilot.csv"
        p.write_text(
            json.dumps(protocol_mapping, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        surface.write_text(routed.csv_text, encoding="utf-8")
        v032_code, pilot_result = run_v032(p, surface)

    admission = evaluate_future_admission_v0_42(
        protocol=protocol,
        pilot_result=pilot_result,
        quality_contract=quality,
        confirmatory_response_accessed=False,
    )
    admission_receipt = future_admission_receipt_mapping(admission)
    qualified = admission.status is FutureAdmissionStatus.ADMITTED

    return {
        "schema": "structural.boreal_beetle_burned_pilot_execution.v0_82",
        "status": (
            contract["qualified_ceiling"]["status"]
            if qualified
            else "TERMINAL_PILOT_GATE_STOP"
        ),
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
        "pilot_species_universe": list(routed.pilot_species_universe),
        "pilot_species_universe_count": routed.pilot_species_universe_count,
        "pilot_species_universe_sha256": (
            routed.pilot_species_universe_sha256
        ),
        "pilot_result": pilot_result,
        "v0_32_exit_code": v032_code,
        "future_admission_receipt": admission_receipt,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "confirmatory_response_authorized": False,
        "eligible_action": (
            "freeze_confirmatory_protocol_only" if qualified else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("quality", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("response_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--pilot-surface", type=Path)
    parser.add_argument("--species-universe", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_beetle_one_shot_pilot_contract.v0_82"
        ):
            raise BorealPilotExecutionError(
                "unexpected v0.82 contract schema"
            )
        response_bytes = args.response_csv.read_bytes()
        result = execute(
            _load(args.authorization),
            _load(args.protocol),
            _load(args.quality),
            _load(args.spatial_receipt),
            response_bytes,
            contract=contract,
            spatial_receipt_sha256=hashlib.sha256(
                args.spatial_receipt.read_bytes()
            ).hexdigest(),
            expected_islands=load_universe(),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealPilotExecutionError,
    ) as exc:
        result = {
            "schema": "structural.boreal_beetle_burned_pilot_execution.v0_82",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "authorization_consumed": False,
            "pilot_response_opened": False,
            "confirmatory_target_values_parsed": 0,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }
        code = 2
    else:
        code = 0 if result["status"] == (
            "QUALIFIED_TO_FREEZE_CONFIRMATORY_PROTOCOL_ONLY"
        ) else 2

    if args.pilot_surface is not None and result.get(
        "raw_pilot_surface_sha256"
    ):
        # Re-route only from exact verified bytes to persist the already
        # consumed surface. This repeats pilot semantics locally but cannot
        # change the execution result.
        protocol = protocol_from_mapping(_load(args.protocol))
        spatial = _load(args.spatial_receipt)
        routed = build_boreal_beetle_pilot_surface(
            response_csv_bytes=args.response_csv.read_bytes(),
            island_to_block=spatial["island_to_block"],
            pilot_partition=protocol.pilot_partition,
            confirmatory_partition=protocol.confirmatory_partition,
            expected_islands=load_universe(),
            expected_species_count=466,
        )
        if routed.raw_surface_sha256 != result["raw_pilot_surface_sha256"]:
            raise SystemExit("pilot surface replay SHA mismatch")
        args.pilot_surface.parent.mkdir(parents=True, exist_ok=True)
        args.pilot_surface.write_text(routed.csv_text, encoding="utf-8")
        if args.species_universe is not None:
            args.species_universe.parent.mkdir(parents=True, exist_ok=True)
            args.species_universe.write_text(
                json.dumps(
                    {
                        "species": list(routed.pilot_species_universe),
                        "count": routed.pilot_species_universe_count,
                        "sha256": routed.pilot_species_universe_sha256,
                    },
                    indent=2,
                    sort_keys=True,
                ) + "\n",
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
