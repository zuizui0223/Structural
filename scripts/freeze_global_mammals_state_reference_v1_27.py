#!/usr/bin/env python3
"""Freeze global mammal R0/R1 state reference v1.27 from safe covariates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/global_mammals_state_reference_contract_v1_27.json"
)


class GlobalMammalStateError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalStateError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_number(value: object, *, label: str) -> float:
    text = str(value).strip()
    try:
        out = (
            float.fromhex(text)
            if text.lower().startswith(("0x", "+0x", "-0x"))
            else float(text)
        )
    except ValueError as exc:
        raise GlobalMammalStateError(f"invalid numeric {label}") from exc
    if not math.isfinite(out):
        raise GlobalMammalStateError(f"nonfinite numeric {label}")
    return out


def mean_sd(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        raise GlobalMammalStateError("empty standardization vector")
    mean = math.fsum(values) / len(values)
    var = math.fsum((value - mean) ** 2 for value in values) / len(values)
    sd = math.sqrt(var)
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 0.0:
        raise GlobalMammalStateError("zero/nonfinite standardization SD")
    return mean, sd


def load_inputs(
    safe_csv: Path,
    partition_csv: Path,
    contract: Mapping,
) -> tuple[list[dict], list[dict]]:
    artifacts = contract["source_artifacts"]
    if sha256_file(safe_csv) != artifacts["safe_rows"]["safe_csv_sha256"]:
        raise GlobalMammalStateError("safe CSV SHA mismatch")
    if sha256_file(partition_csv) != artifacts["spatial_partition"][
        "island_partition_sha256"
    ]:
        raise GlobalMammalStateError("partition CSV SHA mismatch")

    with safe_csv.open("r", encoding="utf-8", newline="") as handle:
        safe_reader = csv.DictReader(handle)
        safe_rows = list(safe_reader)
    with partition_csv.open("r", encoding="utf-8", newline="") as handle:
        part_reader = csv.DictReader(handle)
        part_rows = list(part_reader)

    if len(safe_rows) != contract["population"]["island_count"]:
        raise GlobalMammalStateError("safe island count drift")
    if len(part_rows) != contract["population"]["island_count"]:
        raise GlobalMammalStateError("partition island count drift")

    safe_ids = [str(row["ID"]).strip() for row in safe_rows]
    part_ids = [str(row["ID"]).strip() for row in part_rows]
    if safe_ids != part_ids:
        raise GlobalMammalStateError(
            "safe and partition ID order does not match exactly"
        )
    if len(set(safe_ids)) != len(safe_ids):
        raise GlobalMammalStateError("duplicate island IDs")
    return safe_rows, part_rows


def freeze(
    safe_rows: Sequence[Mapping[str, str]],
    part_rows: Sequence[Mapping[str, str]],
    contract: Mapping,
) -> tuple[dict, str]:
    levels = tuple(contract["bioregion_encoding"]["levels_in_frozen_order"])
    reference = contract["bioregion_encoding"]["reference_level"]
    dummies = tuple(contract["bioregion_encoding"]["dummy_columns"])
    if reference != levels[0] or len(levels) != 12 or len(dummies) != 11:
        raise GlobalMammalStateError("bioregion encoding drift")

    observed_levels = tuple(sorted({str(row["bioregion"]).strip() for row in safe_rows}))
    if observed_levels != levels:
        raise GlobalMammalStateError("bioregion level set/order drift")

    split_counts = {"pilot": 0, "confirmatory": 0}
    part_by_id = {}
    for row in part_rows:
        island_id = str(row["ID"]).strip()
        split = str(row["split"]).strip()
        if split not in split_counts:
            raise GlobalMammalStateError("invalid partition split")
        split_counts[split] += 1
        if island_id in part_by_id:
            raise GlobalMammalStateError("duplicate partition ID")
        part_by_id[island_id] = row
    if split_counts != contract["validation"]["partition_split_counts"]:
        raise GlobalMammalStateError("partition split counts drift")

    r0_sources = tuple(contract["R0"]["continuous_source_columns"])
    r1_sources = tuple(contract["R1_add"]["source_columns"])

    raw_rows = []
    past_values = set()
    for row in safe_rows:
        island_id = str(row["ID"]).strip()
        region = str(row["bioregion"]).strip()
        values = {}
        for column in r0_sources:
            values[column] = parse_number(row[column], label=column)
        area = parse_number(row["Area"], label="Area")
        if area <= 0.0:
            raise GlobalMammalStateError("Area must be positive")
        values["log10_Area"] = math.log10(area)
        values["Current_isolation"] = parse_number(
            row["Current_isolation"], label="Current_isolation"
        )
        past = parse_number(row["Past_isolation"], label="Past_isolation")
        if past not in (0.0, 1.0):
            raise GlobalMammalStateError("Past_isolation must be exact 0/1")
        values["Past_isolation"] = int(past)
        past_values.add(int(past))
        values["Climate_velocity"] = parse_number(
            row["Climate_velocity"], label="Climate_velocity"
        )
        raw_rows.append({
            "ID": island_id,
            "bioregion": region,
            "values": values,
        })
    if past_values != {0, 1}:
        raise GlobalMammalStateError("Past_isolation lacks both binary states")

    standardized_sources = (
        r0_sources
        + ("log10_Area", "Current_isolation", "Climate_velocity")
    )
    constants = {}
    for column in standardized_sources:
        mean, sd = mean_sd([
            float(row["values"][column]) for row in raw_rows
        ])
        constants[column] = {"mean": mean, "sd": sd}

    dummy_by_level = {
        level: (
            None
            if level == reference
            else dummies[levels[1:].index(level)]
        )
        for level in levels
    }

    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    header = (
        tuple(contract["output"]["state_table_columns_prefix"])
        + tuple(contract["R0"]["feature_columns_in_order"])
        + tuple(contract["R1_add"]["feature_columns_in_order"])
    )
    writer.writerow(header)

    for row in raw_rows:
        island_id = row["ID"]
        part = part_by_id[island_id]
        if str(part["bioregion"]).strip() != row["bioregion"]:
            raise GlobalMammalStateError(
                "safe/partition bioregion mismatch"
            )
        values = row["values"]
        z = {
            column: (
                (float(values[column]) - constants[column]["mean"])
                / constants[column]["sd"]
            )
            for column in standardized_sources
        }
        if not all(math.isfinite(value) for value in z.values()):
            raise GlobalMammalStateError("nonfinite standardized state feature")

        realm = {
            name: 0
            for name in dummies
        }
        active = dummy_by_level[row["bioregion"]]
        if active is not None:
            realm[active] = 1

        r0 = [
            z["Temperature_mean"],
            z["Temperature_sd"],
            z["Precipitation_mean"],
            z["Precipitation_sd"],
            z["Elevation_sd"],
        ] + [realm[name] for name in dummies]
        r1 = [
            z["log10_Area"],
            z["Current_isolation"],
            int(values["Past_isolation"]),
            z["Climate_velocity"],
        ]
        writer.writerow([
            island_id,
            str(part["block_id"]).strip(),
            str(part["split"]).strip(),
            str(part["extreme_current_isolation"]).strip(),
            row["bioregion"],
            *(float(value).hex() if isinstance(value, float) else str(value)
              for value in r0),
            *(float(value).hex() if isinstance(value, float) else str(value)
              for value in r1),
        ])

    text = out.getvalue()
    state_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    constants_hex = {
        column: {
            "mean_hex": float(values["mean"]).hex(),
            "sd_hex": float(values["sd"]).hex(),
        }
        for column, values in constants.items()
    }

    receipt = {
        "schema": "structural.global_mammals_state_reference_result.v1_27",
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "analysis_route": contract["analysis_route"],
        "row_count": len(raw_rows),
        "pilot_island_count": split_counts["pilot"],
        "confirmatory_island_count": split_counts["confirmatory"],
        "bioregion_levels": list(levels),
        "bioregion_reference": reference,
        "R0_feature_columns": list(contract["R0"]["feature_columns_in_order"]),
        "R1_add_feature_columns": list(
            contract["R1_add"]["feature_columns_in_order"]
        ),
        "standardization_constants": constants_hex,
        "Past_isolation_domain": [0, 1],
        "state_table_sha256": state_sha,
        "source_safe_csv_sha256": contract["source_artifacts"][
            "safe_rows"
        ]["safe_csv_sha256"],
        "source_partition_sha256": contract["source_artifacts"][
            "spatial_partition"
        ]["island_partition_sha256"],
        "Appendix_1_reopened": False,
        "mammal_species_names_opened": False,
        "mammal_occurrence_values_opened": False,
        "counts_as_fresh_confirmation": False,
        "fresh_system_denominator_contribution": 0,
        "original_fresh_chain_restored": False,
        "global_source_operator_may_be_built": True,
        "mammal_response_access_authorized": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return receipt, text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("safe_csv", type=Path)
    parser.add_argument("partition_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--state-table", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.global_mammals_state_reference_contract.v1_27"
        ):
            raise GlobalMammalStateError("unexpected v1.27 contract schema")
        safe_rows, part_rows = load_inputs(
            args.safe_csv,
            args.partition_csv,
            contract,
        )
        receipt, text = freeze(safe_rows, part_rows, contract)
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        GlobalMammalStateError,
    ) as exc:
        receipt = {
            "schema": "structural.global_mammals_state_reference_result.v1_27",
            "status": "HOLD_GLOBAL_STATE_REFERENCE_FAILED",
            "reason": str(exc),
            "Appendix_1_reopened": False,
            "mammal_species_names_opened": False,
            "mammal_occurrence_values_opened": False,
            "counts_as_fresh_confirmation": False,
            "fresh_system_denominator_contribution": 0,
            "original_fresh_chain_restored": False,
            "global_source_operator_may_be_built": False,
            "mammal_response_access_authorized": False,
        }
        text = None
        code = 2
    else:
        code = 0

    if text is not None and args.state_table is not None:
        args.state_table.parent.mkdir(parents=True, exist_ok=True)
        args.state_table.write_text(text, encoding="utf-8")
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
