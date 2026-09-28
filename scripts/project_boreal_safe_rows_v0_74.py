#!/usr/bin/env python3
"""Project only frozen-safe boreal geometry/habitat columns after Stage A.

This is Stage B infrastructure. It refuses to run until a separate committed
header-manifest freeze explicitly authorizes row projection. Protected and
unclassified columns are never returned by the underlying mixed-CSV firewall.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from structural.mixed_csv_firewall import (
    MixedCSVColumnManifest,
    MixedCSVFirewallError,
    project_safe_columns,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_safe_projection_contract_v0_74.json"
)
DEFAULT_V071 = (
    ROOT / "development/boreal_lake_islands_header_freeze_contract_v0_71.json"
)
DEFAULT_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class BorealSafeProjectionError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(ch in "0123456789abcdef" for ch in value.lower())


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict:
    x = _load(path)
    if x.get("schema") != (
        "structural.boreal_lake_islands_safe_projection_contract.v0_74"
    ):
        raise BorealSafeProjectionError("unexpected v0.74 contract schema")
    return x


def load_universe(path: Path = DEFAULT_UNIVERSE) -> tuple[str, ...]:
    x = _load(path)
    if x.get("row_count") != 42 or x.get("unique_island_count") != 42:
        raise BorealSafeProjectionError("unexpected frozen 42-island universe")
    codes = tuple(x["current_study_island_universe"]["codes"])
    if len(codes) != 42 or len(set(codes)) != 42:
        raise BorealSafeProjectionError(
            "frozen island universe must contain exactly 42 unique codes"
        )
    return codes


def validate_manifest_freeze(
    freeze: Mapping,
    *,
    contract: Mapping,
    v071: Mapping,
) -> dict[str, MixedCSVColumnManifest]:
    if freeze.get("schema") != contract["required_manifest_schema"]:
        raise BorealSafeProjectionError("unexpected header-manifest schema")
    if freeze.get("status") != contract["required_manifest_status"]:
        raise BorealSafeProjectionError("header manifests are not frozen")
    if freeze.get("safe_row_projection_authorized") is not True:
        raise BorealSafeProjectionError("safe-row projection is not authorized")

    files = freeze.get("files")
    if not isinstance(files, dict):
        raise BorealSafeProjectionError("manifest freeze files missing")

    manifests: dict[str, MixedCSVColumnManifest] = {}
    for name, projection_spec in contract["projection"].items():
        if name not in files or name not in v071["files"]:
            raise BorealSafeProjectionError(f"manifest missing file: {name}")
        frozen = files[name]
        prior = v071["files"][name]

        file_sha = frozen.get("file_sha256")
        header_sha = frozen.get("header_sha256")
        if file_sha != prior["expected_sha256"]:
            raise BorealSafeProjectionError(f"{name} file SHA drift")
        if not _is_sha256(header_sha):
            raise BorealSafeProjectionError(f"{name} header SHA invalid")

        frozen_safe = frozen.get("safe_pre_response_columns")
        frozen_protected = frozen.get("protected_response_columns")
        if frozen_safe != prior["safe_pre_response_columns"]:
            raise BorealSafeProjectionError(f"{name} safe-column freeze drift")
        if frozen_protected != prior["protected_response_columns"]:
            raise BorealSafeProjectionError(
                f"{name} protected-column freeze drift"
            )

        minimal_safe = tuple(projection_spec["safe_columns"])
        if not set(minimal_safe) <= set(frozen_safe):
            raise BorealSafeProjectionError(
                f"{name} projection exceeds frozen safe columns"
            )

        manifests[name] = MixedCSVColumnManifest(
            file_sha256=file_sha,
            header_sha256=header_sha,
            safe_pre_response_columns=minimal_safe,
            protected_response_columns=tuple(frozen_protected),
        )
    return manifests


def _rows_by_island(
    rows: Sequence[Mapping[str, str]],
    *,
    universe: Sequence[str],
    label: str,
) -> dict[str, Mapping[str, str]]:
    if len(rows) != len(universe):
        raise BorealSafeProjectionError(
            f"{label} row count {len(rows)} != {len(universe)}"
        )
    by_id: dict[str, Mapping[str, str]] = {}
    for row in rows:
        island = str(row.get("Island", "")).strip()
        if not island:
            raise BorealSafeProjectionError(f"{label} blank Island")
        if island in by_id:
            raise BorealSafeProjectionError(
                f"{label} duplicate Island: {island}"
            )
        by_id[island] = row
    if set(by_id) != set(universe):
        missing = sorted(set(universe) - set(by_id))
        extra = sorted(set(by_id) - set(universe))
        raise BorealSafeProjectionError(
            f"{label} island-set mismatch missing={missing} extra={extra}"
        )
    return by_id


def _finite_float(value: object, *, label: str) -> float:
    text = str(value).strip()
    if not text:
        raise BorealSafeProjectionError(f"{label} is missing")
    try:
        out = float(text)
    except ValueError as exc:
        raise BorealSafeProjectionError(f"{label} is not numeric") from exc
    if not math.isfinite(out):
        raise BorealSafeProjectionError(f"{label} is nonfinite")
    return out


def _population_mean_sd(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        raise BorealSafeProjectionError("empty habitat vector")
    mean = math.fsum(values) / len(values)
    variance = math.fsum((x - mean) ** 2 for x in values) / len(values)
    sd = math.sqrt(variance)
    return mean, sd


def _csv_text(
    header: Sequence[str],
    rows: Sequence[Sequence[object]],
) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(list(header))
    writer.writerows(rows)
    return out.getvalue()


def project(
    alpha_csv: Path,
    rda_csv: Path,
    *,
    manifest_freeze: Mapping,
    contract: Mapping | None = None,
    v071: Mapping | None = None,
    universe: Sequence[str] | None = None,
) -> dict:
    contract = load_contract() if contract is None else dict(contract)
    v071 = _load(DEFAULT_V071) if v071 is None else dict(v071)
    universe = load_universe() if universe is None else tuple(universe)

    manifests = validate_manifest_freeze(
        manifest_freeze,
        contract=contract,
        v071=v071,
    )

    alpha_name = "alpha_diversity_ALL_islands.csv"
    rda_name = "RDA_environmental_variables.csv"
    alpha_rows = project_safe_columns(alpha_csv, manifests[alpha_name])
    rda_rows = project_safe_columns(rda_csv, manifests[rda_name])

    alpha_by_id = _rows_by_island(
        alpha_rows,
        universe=universe,
        label="geometry",
    )
    geometry_records = []
    for island in universe:
        row = alpha_by_id[island]
        lat = _finite_float(row["Lat"], label=f"{island}.Lat")
        lon = _finite_float(row["Long"], label=f"{island}.Long")
        if not (-90.0 <= lat <= 90.0):
            raise BorealSafeProjectionError(
                f"{island}.Lat outside [-90,90]"
            )
        if not (-180.0 <= lon <= 180.0):
            raise BorealSafeProjectionError(
                f"{island}.Long outside [-180,180]"
            )
        geometry_records.append((island, lat, lon))

    rda_by_id = _rows_by_island(
        rda_rows,
        universe=universe,
        label="habitat",
    )
    habitat_columns = tuple(
        name for name in contract["projection"][rda_name]["safe_columns"]
        if name != "Island"
    )
    eligible: list[str] = []
    incomplete: list[str] = []
    zero_variance: list[str] = []
    constants: dict[str, dict[str, str]] = {}
    parsed: dict[str, list[float]] = {}

    for column in habitat_columns:
        values: list[float] = []
        complete = True
        for island in universe:
            raw = str(rda_by_id[island].get(column, "")).strip()
            if not raw:
                complete = False
                break
            try:
                value = float(raw)
            except ValueError:
                complete = False
                break
            if not math.isfinite(value):
                complete = False
                break
            values.append(value)
        if not complete:
            incomplete.append(column)
            continue

        mean, sd = _population_mean_sd(values)
        if not math.isfinite(sd) or sd <= 0.0:
            zero_variance.append(column)
            continue
        eligible.append(column)
        parsed[column] = values
        constants[column] = {
            "mean_hex": float(mean).hex(),
            "population_sd_hex": float(sd).hex(),
            "n": len(values),
        }

    if not eligible:
        raise BorealSafeProjectionError(
            "no complete nonconstant habitat variable survives"
        )

    if len(eligible) == 1:
        mode = "single_population_z_variable"
        pca_required = False
    else:
        mode = "pca_required_under_frozen_v0_68_rule"
        pca_required = True

    geometry_text = _csv_text(
        ("Island", "Lat", "Long"),
        [
            (island, float(lat).hex(), float(lon).hex())
            for island, lat, lon in geometry_records
        ],
    )
    habitat_text = _csv_text(
        ("Island", *eligible),
        [
            (
                island,
                *(
                    float(parsed[column][idx]).hex()
                    for column in eligible
                ),
            )
            for idx, island in enumerate(universe)
        ],
    )

    return {
        "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
        "status": "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED",
        "candidate_id": contract["candidate_id"],
        "geometry_csv": geometry_text,
        "habitat_csv": habitat_text,
        "geometry": {
            "row_count": len(geometry_records),
            "unique_island_count": len(geometry_records),
            "sha256": _sha256_text(geometry_text),
            "coordinate_encoding": "python_float_hex",
        },
        "habitat": {
            "row_count": len(universe),
            "eligible_columns": eligible,
            "incomplete_columns": incomplete,
            "zero_variance_columns": zero_variance,
            "standardization_constants": constants,
            "reference_mode": mode,
            "pca_required": pca_required,
            "sha256": _sha256_text(habitat_text),
            "value_encoding": "python_float_hex",
        },
        "protected_response_values_opened": False,
        "unclassified_values_returned": False,
        "counts_as_empirical_evidence": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "freeze the response-independent geometry graph and spatial blocks; "
            "freeze the single z habitat variable if only one survived, or "
            "execute a separately frozen deterministic PCA if two or more survived"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alpha_csv", type=Path)
    parser.add_argument("rda_csv", type=Path)
    parser.add_argument("manifest_freeze", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--geometry-output", type=Path)
    parser.add_argument("--habitat-output", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        result = project(
            args.alpha_csv,
            args.rda_csv,
            manifest_freeze=_load(args.manifest_freeze),
            contract=load_contract(args.contract),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        MixedCSVFirewallError,
        BorealSafeProjectionError,
    ) as exc:
        receipt = {
            "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
            "status": "STOP",
            "reason": str(exc),
            "protected_response_values_opened": False,
            "counts_as_empirical_evidence": False,
            "v0_11_intake_authorized": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2
    else:
        geometry_text = result.pop("geometry_csv")
        habitat_text = result.pop("habitat_csv")
        if args.geometry_output is not None:
            args.geometry_output.parent.mkdir(parents=True, exist_ok=True)
            args.geometry_output.write_text(geometry_text, encoding="utf-8")
        if args.habitat_output is not None:
            args.habitat_output.parent.mkdir(parents=True, exist_ok=True)
            args.habitat_output.write_text(habitat_text, encoding="utf-8")
        receipt = result
        code = 0

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
