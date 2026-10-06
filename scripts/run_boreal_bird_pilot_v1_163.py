#!/usr/bin/env python3
"""Run the one-shot boreal-bird pilot gate without opening confirmatory values."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Mapping

from structural.boreal_19island_bird_pilot_router import (
    Boreal19BirdPilotRouterError,
    build_boreal_19island_bird_pilot_surface,
)
from structural.boreal_beetle_pilot_router import decode_binary_vector_hex

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "development/boreal_bird_pilot_contract_v1_163.json"
DEFAULT_TOPOLOGY = ROOT / "development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
DEFAULT_SPATIAL = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
DEFAULT_GEOMETRY_FREEZE = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
DEFAULT_FULL = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"


class BorealBirdPilotError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealBirdPilotError(f"{path.name} must contain an object")
    return value


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def evaluate_gate(
    *,
    routed,
    topology: Mapping,
    contract: Mapping,
) -> tuple[dict, dict]:
    species = list(routed.pilot_species_universe)
    count = len(species)
    vectors = {
        island: decode_binary_vector_hex(bits, count)
        for island, bits in routed.pilot_targets_hex_by_island
    }
    if set(vectors) != set(routed.pilot_island_order):
        raise BorealBirdPilotError("pilot bit-vector island identity drift")

    n_by_species = []
    for j, name in enumerate(species):
        n = sum(vectors[island][j] for island in routed.pilot_island_order)
        n_by_species.append((name, int(n)))

    rule = contract["fixed_species_rule"]
    allowed = set(int(x) for x in rule["allowed_n"])
    if any(n not in allowed for _, n in n_by_species):
        raise BorealBirdPilotError("fixed species n outside frozen domain")

    n_hist = Counter(n for _, n in n_by_species)
    positives = sum(n for _, n in n_by_species)
    negatives = len(routed.pilot_island_order) * count - positives
    failures = []
    if count < int(rule["minimum_species"]):
        failures.append("minimum_species")
    if len(n_hist) < int(rule["minimum_distinct_n"]):
        failures.append("minimum_distinct_n")
    if positives < int(rule["minimum_total_positive_cells"]):
        failures.append("minimum_positive_cells")
    if negatives < int(rule["minimum_total_negative_cells"]):
        failures.append("minimum_negative_cells")

    targets = topology["configuration_sensitivity"]["targets"]
    raw_s = []
    for _, n in n_by_species:
        for target in contract["frozen_confirmatory_islands"]:
            raw_s.append(float.fromhex(targets[target]["S_by_n_hex"][str(n)]))
    if not raw_s:
        failures.append("empty_S_surface")
        s_mean = s_sd = 0.0
    else:
        s_mean = math.fsum(raw_s) / len(raw_s)
        s_var = math.fsum((x - s_mean) ** 2 for x in raw_s) / len(raw_s)
        s_sd = math.sqrt(s_var)
        if not math.isfinite(s_sd) or s_sd <= float(
            contract["configuration_sensitivity"]["minimum_standard_deviation"]
        ):
            failures.append("S_zero_variance")

    gate_passed = not failures
    snapshot = {
        "schema": "structural.boreal_bird_pilot_snapshot.v1_163",
        "status": (
            "BIRD_PILOT_GATE_PASSED"
            if gate_passed else "BIRD_PILOT_GATE_TERMINAL_NOT_ESTIMABLE"
        ),
        "candidate_id": contract["candidate_id"],
        "response_file_sha256": contract["response_file"]["expected_sha256"],
        "fixed_species": species,
        "fixed_species_count": count,
        "fixed_species_sha256": routed.pilot_species_universe_sha256,
        "pilot_island_order": list(routed.pilot_island_order),
        "pilot_island_to_block": dict(routed.pilot_island_to_block),
        "targets_hex_by_island": dict(routed.pilot_targets_hex_by_island),
        "n_by_species": [
            {"species": name, "n": n} for name, n in n_by_species
        ],
        "n_histogram": {str(n): n_hist[n] for n in sorted(n_hist)},
        "distinct_n_count": len(n_hist),
        "pilot_positive_cells": positives,
        "pilot_negative_cells": negatives,
        "S_standardization": {
            "surface_cells": len(raw_s),
            "mean_hex": float(s_mean).hex(),
            "population_sd_hex": float(s_sd).hex(),
        },
        "gate_failures": failures,
        "confirmatory_values_parsed": 0,
        "excluded_values_parsed": 0,
        "effect_size": None,
        "prediction_score": None,
        "counts_as_empirical_evidence": False,
    }
    snapshot["snapshot_fingerprint"] = canonical_sha256(snapshot)
    return snapshot, {
        "gate_passed": gate_passed,
        "failures": failures,
        "fixed_species_count": count,
        "distinct_n_count": len(n_hist),
        "pilot_positive_cells": positives,
        "pilot_negative_cells": negatives,
        "S_sd": s_sd,
    }


def execute(
    response_bytes: bytes,
    *,
    contract: Mapping,
    topology: Mapping,
    spatial: Mapping,
    geometry_freeze: Mapping,
    full_source: Mapping,
) -> tuple[dict, dict | None]:
    if contract.get("schema") != "structural.boreal_bird_pilot_contract.v1_163":
        raise BorealBirdPilotError("unexpected pilot contract schema")
    target = contract["response_file"]
    if len(response_bytes) != int(target["expected_size_bytes"]):
        raise BorealBirdPilotError("bird response byte size mismatch")
    if sha256_bytes(response_bytes) != target["expected_sha256"]:
        raise BorealBirdPilotError("bird response SHA mismatch")
    if topology.get("status") != (
        "RESPONSE_FREE_TOPOLOGY_NULL_AND_SENSITIVITY_SURFACE_FROZEN"
    ):
        raise BorealBirdPilotError("topology surface not frozen")
    if topology.get("candidate_id") != contract["candidate_id"]:
        raise BorealBirdPilotError("topology candidate mismatch")
    if topology["response_boundary"]["bird_values_read"] != 0:
        raise BorealBirdPilotError("topology freeze response boundary violated")
    if spatial.get("species_occurrence_used") is not False:
        raise BorealBirdPilotError("spatial freeze used response")
    full_islands = list(full_source["current_study_island_universe"]["codes"])
    analysis = list(geometry_freeze["island_order"])

    try:
        routed = build_boreal_19island_bird_pilot_surface(
            response_csv_bytes=response_bytes,
            full_expected_islands=full_islands,
            analysis_expected_islands=analysis,
            analysis_island_to_block=spatial["island_to_block"],
            pilot_partition=spatial["pilot_block_ids"],
            confirmatory_partition=spatial["confirmatory_block_ids"],
            expected_species_count=int(target["expected_species_columns"]),
        )
    except Boreal19BirdPilotRouterError as exc:
        return ({
            "schema": "structural.boreal_bird_pilot_execution.v1_163",
            "status": "TERMINAL_BIRD_PILOT_ROUTER_STOP",
            "reason": str(exc),
            "authorization_consumed": True,
            "bird_pilot_response_opened": True,
            "bird_confirmatory_response_opened": False,
            "confirmatory_values_parsed": 0,
            "excluded_values_parsed": 0,
            "counts_as_empirical_evidence": False,
        }, None)

    sem = contract["semantic_access"]
    firewall = []
    if routed.source_response_rows_seen != int(target["expected_source_island_rows"]):
        firewall.append("source_row_count")
    if routed.routing_island_fields_decoded != int(target["expected_source_island_rows"]):
        firewall.append("routing_count")
    if routed.pilot_target_values_parsed != int(
        sem["expected_pilot_occurrence_cells_parsed"]
    ):
        firewall.append("pilot_cell_count")
    if routed.confirmatory_target_values_parsed != int(
        sem["required_confirmatory_occurrence_cells_parsed"]
    ):
        firewall.append("confirmatory_parse")
    if routed.excluded_target_values_parsed != int(
        sem["required_excluded_occurrence_cells_parsed"]
    ):
        firewall.append("excluded_parse")
    if firewall:
        return ({
            "schema": "structural.boreal_bird_pilot_execution.v1_163",
            "status": "TERMINAL_BIRD_PILOT_FIREWALL_STOP",
            "reason": ",".join(firewall),
            "authorization_consumed": True,
            "bird_pilot_response_opened": True,
            "bird_confirmatory_response_opened": False,
            "confirmatory_values_parsed": routed.confirmatory_target_values_parsed,
            "excluded_values_parsed": routed.excluded_target_values_parsed,
            "counts_as_empirical_evidence": False,
        }, None)

    snapshot, gate = evaluate_gate(
        routed=routed,
        topology=topology,
        contract=contract,
    )
    status = (
        contract["qualified_ceiling"]["status"]
        if gate["gate_passed"]
        else "TERMINAL_BIRD_PILOT_GATE_NOT_ESTIMABLE"
    )
    result = {
        "schema": "structural.boreal_bird_pilot_execution.v1_163",
        "status": status,
        "candidate_id": contract["candidate_id"],
        "authorization_consumed": True,
        "bird_pilot_response_opened": True,
        "bird_confirmatory_response_opened": False,
        "source_response_rows_seen": routed.source_response_rows_seen,
        "routing_island_fields_decoded": routed.routing_island_fields_decoded,
        "pilot_occurrence_values_parsed": routed.pilot_target_values_parsed,
        "confirmatory_values_parsed": 0,
        "excluded_values_parsed": 0,
        "fixed_species_count": gate["fixed_species_count"],
        "distinct_n_count": gate["distinct_n_count"],
        "pilot_positive_cells": gate["pilot_positive_cells"],
        "pilot_negative_cells": gate["pilot_negative_cells"],
        "S_population_sd_hex": float(gate["S_sd"]).hex(),
        "gate_failures": gate["failures"],
        "snapshot_fingerprint": snapshot["snapshot_fingerprint"],
        "effect_size": None,
        "prediction_score": None,
        "counts_as_empirical_evidence": False,
        "bird_confirmatory_response_authorized": False,
    }
    return result, snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--topology", type=Path, default=DEFAULT_TOPOLOGY)
    parser.add_argument("--spatial", type=Path, default=DEFAULT_SPATIAL)
    parser.add_argument("--geometry-freeze", type=Path, default=DEFAULT_GEOMETRY_FREEZE)
    parser.add_argument("--full-source", type=Path, default=DEFAULT_FULL)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()

    try:
        result, snapshot = execute(
            args.response_csv.read_bytes(),
            contract=load_json(args.contract),
            topology=load_json(args.topology),
            spatial=load_json(args.spatial),
            geometry_freeze=load_json(args.geometry_freeze),
            full_source=load_json(args.full_source),
        )
    except (
        OSError, KeyError, TypeError, ValueError, json.JSONDecodeError,
        BorealBirdPilotError,
    ) as exc:
        result = {
            "schema": "structural.boreal_bird_pilot_execution.v1_163",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "authorization_consumed": False,
            "bird_pilot_response_opened": False,
            "bird_confirmatory_response_opened": False,
            "confirmatory_values_parsed": 0,
            "excluded_values_parsed": 0,
            "counts_as_empirical_evidence": False,
        }
        snapshot = None
        code = 2
    else:
        code = 0 if result["status"] == (
            "BIRD_PILOT_GATE_PASSED_FREEZE_MODELS_AND_PREDICTIONS_ONLY"
        ) else 2

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.result is not None:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(rendered, encoding="utf-8")
    if snapshot is not None and args.snapshot is not None:
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
