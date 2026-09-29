#!/usr/bin/env python3
"""Freeze the global mammal response-independent spatial/pilot design v1.25."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/global_mammals_spatial_pilot_contract_v1_25.json"
)


class GlobalMammalSpatialError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalSpatialError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_order_sha(ids: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for value in ids:
        digest.update(str(value).encode("utf-8"))
        digest.update(b"\n")
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
        raise GlobalMammalSpatialError(f"invalid numeric {label}") from exc
    if not math.isfinite(out):
        raise GlobalMammalSpatialError(f"nonfinite numeric {label}")
    return out


def type7_quantile(values: Sequence[float], p: float) -> float:
    if not values or not 0.0 <= p <= 1.0:
        raise GlobalMammalSpatialError("invalid type-7 quantile input")
    xs = sorted(float(x) for x in values)
    if len(xs) == 1:
        return xs[0]
    h = (len(xs) - 1) * p
    lo = int(math.floor(h))
    hi = int(math.ceil(h))
    if lo == hi:
        return xs[lo]
    frac = h - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def block_key(*, bioregion: str, latitude: float, longitude: float) -> str:
    width = 10.0
    lat_index = min(
        17,
        max(0, int(math.floor((float(latitude) + 90.0) / width))),
    )
    lon_index = int(
        math.floor(((float(longitude) + 180.0) % 360.0) / width)
    )
    return f"{bioregion}|lat{lat_index:02d}|lon{lon_index:02d}"


def block_id(key: str) -> str:
    return "GB_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def load_safe_rows(path: Path, contract: Mapping) -> list[dict]:
    safe = contract["safe_artifact"]
    if sha256_file(path) != safe["safe_csv_sha256"]:
        raise GlobalMammalSpatialError("safe CSV SHA mismatch")
    expected_header = (
        "ID",
        "Longitude_centroid",
        "Latitude_centroid",
        "Area",
        "Current_isolation",
        "Past_isolation",
        "Climate_velocity",
        "Temperature_mean",
        "Temperature_sd",
        "Precipitation_mean",
        "Precipitation_sd",
        "Elevation_sd",
        "bioregion",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise GlobalMammalSpatialError("safe CSV header drift")
        source = list(reader)

    if len(source) != safe["safe_row_count"]:
        raise GlobalMammalSpatialError("safe CSV row count drift")
    ids = [str(row["ID"]).strip() for row in source]
    if len(set(ids)) != safe["safe_distinct_id_count"]:
        raise GlobalMammalSpatialError("safe CSV IDs are not exact unique support")
    if id_order_sha(ids) != safe["safe_id_order_sha256"]:
        raise GlobalMammalSpatialError("safe CSV ID order fingerprint drift")

    rows = []
    coords = set()
    for raw in source:
        island_id = str(raw["ID"]).strip()
        region = str(raw["bioregion"]).strip()
        if not island_id or not region:
            raise GlobalMammalSpatialError("blank safe routing/bioregion value")
        lon = parse_number(raw["Longitude_centroid"], label="longitude")
        lat = parse_number(raw["Latitude_centroid"], label="latitude")
        if not -180.0 <= lon <= 180.0 or not -90.0 <= lat <= 90.0:
            raise GlobalMammalSpatialError("coordinate outside valid range")
        pair = (float(lat).hex(), float(lon).hex())
        if pair in coords:
            raise GlobalMammalSpatialError("duplicate exact coordinate pair")
        coords.add(pair)

        current = parse_number(
            raw["Current_isolation"],
            label="Current_isolation",
        )
        rows.append({
            "ID": island_id,
            "bioregion": region,
            "longitude": lon,
            "latitude": lat,
            "current_isolation": current,
            "block_key": block_key(
                bioregion=region,
                latitude=lat,
                longitude=lon,
            ),
        })
    return rows


def freeze(rows: Sequence[Mapping[str, object]], contract: Mapping) -> tuple[dict, str, str]:
    validation = contract["validation"]
    split_rule = contract["pilot_split"]
    blocks_cfg = contract["spatial_blocks"]
    regime_cfg = contract["primary_regime_freeze"]

    if len(rows) != validation["expected_total_islands"]:
        raise GlobalMammalSpatialError("safe population island count drift")

    block_rows: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        block_rows[str(row["block_key"])].append(row)
    if len(block_rows) != blocks_cfg["expected_total_block_count"]:
        raise GlobalMammalSpatialError("global spatial block count drift")

    singleton_count = sum(len(group) == 1 for group in block_rows.values())
    if singleton_count != blocks_cfg["expected_singleton_block_count"]:
        raise GlobalMammalSpatialError("singleton block count drift")

    by_region: dict[str, list[str]] = defaultdict(list)
    for key in block_rows:
        by_region[key.split("|", 1)[0]].append(key)
    if len(by_region) != split_rule["expected_bioregion_count"]:
        raise GlobalMammalSpatialError("bioregion count drift")

    salt = str(split_rule["ranking_salt"])
    pilot_blocks: set[str] = set()
    regional_audit = {}
    for region in sorted(by_region):
        keys = sorted(
            by_region[region],
            key=lambda key: (
                hashlib.sha256(f"{salt}|{key}".encode("utf-8")).hexdigest(),
                key,
            ),
        )
        b = len(keys)
        if b < 3:
            raise GlobalMammalSpatialError(
                f"bioregion has fewer than three blocks: {region}"
            )
        k = max(1, int(math.ceil(float(split_rule["pilot_block_fraction"]) * b)))
        k = min(k, b - int(validation["minimum_confirmatory_blocks_per_bioregion"]))
        if k < 1 or b - k < int(validation["minimum_confirmatory_blocks_per_bioregion"]):
            raise GlobalMammalSpatialError(
                f"invalid regional pilot split: {region}"
            )
        chosen = keys[:k]
        pilot_blocks.update(chosen)
        regional_audit[region] = {
            "total_blocks": b,
            "pilot_blocks": k,
            "confirmatory_blocks": b - k,
            "total_islands": sum(len(block_rows[key]) for key in keys),
            "pilot_islands": sum(len(block_rows[key]) for key in chosen),
            "confirmatory_islands": sum(
                len(block_rows[key]) for key in keys[k:]
            ),
        }

    confirmatory_blocks = set(block_rows) - pilot_blocks
    if len(pilot_blocks) != split_rule["expected_pilot_block_count"]:
        raise GlobalMammalSpatialError("pilot block count drift")
    if len(confirmatory_blocks) != split_rule["expected_confirmatory_block_count"]:
        raise GlobalMammalSpatialError("confirmatory block count drift")

    pilot_ids = {
        str(row["ID"])
        for key in pilot_blocks
        for row in block_rows[key]
    }
    confirmatory_ids = {
        str(row["ID"])
        for key in confirmatory_blocks
        for row in block_rows[key]
    }
    if pilot_ids & confirmatory_ids:
        raise GlobalMammalSpatialError("pilot/confirmatory island overlap")
    if len(pilot_ids) != split_rule["expected_pilot_island_count"]:
        raise GlobalMammalSpatialError("pilot island count drift")
    if len(confirmatory_ids) != split_rule["expected_confirmatory_island_count"]:
        raise GlobalMammalSpatialError("confirmatory island count drift")
    if len(pilot_ids | confirmatory_ids) != len(rows):
        raise GlobalMammalSpatialError("split does not cover exact island population")

    confirm_current = [
        float(row["current_isolation"])
        for row in rows
        if str(row["ID"]) in confirmatory_ids
    ]
    q75 = type7_quantile(confirm_current, 0.75)
    if float(q75).hex() != regime_cfg["expected_q75_hex"]:
        raise GlobalMammalSpatialError("confirmatory isolation q75 drift")
    extreme_ids = {
        str(row["ID"])
        for row in rows
        if str(row["ID"]) in confirmatory_ids
        and float(row["current_isolation"]) >= q75
    }
    if len(extreme_ids) != regime_cfg["expected_extreme_island_count"]:
        raise GlobalMammalSpatialError("extreme-isolation island count drift")

    island_out = io.StringIO(newline="")
    iw = csv.writer(island_out, lineterminator="\n")
    iw.writerow([
        "ID",
        "bioregion",
        "block_key",
        "block_id",
        "split",
        "Current_isolation_hex",
        "extreme_current_isolation",
    ])
    for row in rows:
        key = str(row["block_key"])
        island_id = str(row["ID"])
        split = "pilot" if key in pilot_blocks else "confirmatory"
        iw.writerow([
            island_id,
            str(row["bioregion"]),
            key,
            block_id(key),
            split,
            float(row["current_isolation"]).hex(),
            "1" if island_id in extreme_ids else "0",
        ])
    island_text = island_out.getvalue()

    block_out = io.StringIO(newline="")
    bw = csv.writer(block_out, lineterminator="\n")
    bw.writerow([
        "block_key",
        "block_id",
        "bioregion",
        "island_count",
        "split",
    ])
    for key in sorted(block_rows):
        bw.writerow([
            key,
            block_id(key),
            key.split("|", 1)[0],
            len(block_rows[key]),
            "pilot" if key in pilot_blocks else "confirmatory",
        ])
    block_text = block_out.getvalue()

    receipt = {
        "schema": "structural.global_mammals_spatial_pilot_result.v1_25",
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "analysis_route": contract["analysis_route"],
        "source_safe_csv_sha256": contract["safe_artifact"]["safe_csv_sha256"],
        "island_count": len(rows),
        "bioregion_count": len(by_region),
        "total_block_count": len(block_rows),
        "singleton_block_count": singleton_count,
        "pilot_block_count": len(pilot_blocks),
        "confirmatory_block_count": len(confirmatory_blocks),
        "pilot_island_count": len(pilot_ids),
        "confirmatory_island_count": len(confirmatory_ids),
        "pilot_island_fraction_hex": float(len(pilot_ids) / len(rows)).hex(),
        "regional_audit": regional_audit,
        "current_isolation_q75_hex": float(q75).hex(),
        "extreme_confirmatory_island_count": len(extreme_ids),
        "island_partition_sha256": hashlib.sha256(
            island_text.encode("utf-8")
        ).hexdigest(),
        "block_table_sha256": hashlib.sha256(
            block_text.encode("utf-8")
        ).hexdigest(),
        "response_used_in_spatial_design": False,
        "Appendix_1_reopened": False,
        "mammal_species_names_opened": False,
        "mammal_occurrence_values_opened": False,
        "counts_as_fresh_confirmation": False,
        "fresh_system_denominator_contribution": 0,
        "original_fresh_chain_restored": False,
        "macro_model_reference_may_be_built": True,
        "mammal_response_access_authorized": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return receipt, island_text, block_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("safe_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--island-partition", type=Path)
    parser.add_argument("--block-table", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.global_mammals_spatial_pilot_contract.v1_25"
        ):
            raise GlobalMammalSpatialError("unexpected v1.25 contract schema")
        if contract.get("status") != (
            "GLOBAL_RESPONSE_INDEPENDENT_SPATIAL_PILOT_DESIGN_PREDECLARED"
        ):
            raise GlobalMammalSpatialError("v1.25 contract status drift")
        receipt, island_text, block_text = freeze(
            load_safe_rows(args.safe_csv, contract),
            contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        GlobalMammalSpatialError,
    ) as exc:
        receipt = {
            "schema": "structural.global_mammals_spatial_pilot_result.v1_25",
            "status": "HOLD_GLOBAL_SPATIAL_PILOT_DESIGN_FAILED",
            "reason": str(exc),
            "response_used_in_spatial_design": False,
            "Appendix_1_reopened": False,
            "mammal_species_names_opened": False,
            "mammal_occurrence_values_opened": False,
            "counts_as_fresh_confirmation": False,
            "fresh_system_denominator_contribution": 0,
            "original_fresh_chain_restored": False,
            "macro_model_reference_may_be_built": False,
            "mammal_response_access_authorized": False,
        }
        island_text = block_text = None
        code = 2
    else:
        code = 0

    if island_text is not None and args.island_partition is not None:
        args.island_partition.parent.mkdir(parents=True, exist_ok=True)
        args.island_partition.write_text(island_text, encoding="utf-8")
    if block_text is not None and args.block_table is not None:
        args.block_table.parent.mkdir(parents=True, exist_ok=True)
        args.block_table.write_text(block_text, encoding="utf-8")

    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
