#!/usr/bin/env python3
"""Schema-only audit for the Davis 2026 retrospective connectivity pilot.

This tool intentionally does not fit models, rank connectivity metrics, or
summarize genetic endpoint values. It inspects file presence, headers,
identifier support, repeated-year structure, and cryptographic fingerprints.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable


REQUIRED = {
    "genetic": "Genetic_Data_Master.csv",
    "hummingbird": "Hummingbird_Data.csv",
    "patches": "Data_Patches.csv",
    "whole_metrics": "whole_landscape_metrics.RData",
    "patch_metrics": "patch_based_metrics.RData",
}

EXPECTED_HEADERS = {
    "genetic": {
        "Mom_ID",
        "Year",
        "Pop",
        "n_Seeds",
        "h_Pollen_Pool",
        "Bootstrap_SE",
        "Outcrossing",
        "Outcrossing_SE",
        "Biparental_Inbreeding",
        "Biparental_Inbreeding_SE",
        "Area_ha",
        "Percent_Forest",
        "Elevation",
        "Proportion_High_Mobility",
        "SE_High_Mobility",
    },
    "hummingbird": {
        "Patch",
        "Area_ha",
        "Percent_Forest",
        "Elevation",
        "Proportion_High_Mobility",
        "SE_High_Mobility",
    },
    "patches": {
        "Pop",
        "n_Seeds",
        "Area_ha",
        "Percent_Forest",
        "Elevation",
        "Proportion_High_Mobility",
        "SE_High_Mobility",
    },
}

ENDPOINT_COLUMNS = {
    "h_Pollen_Pool",
    "Outcrossing",
    "Biparental_Inbreeding",
}


class SchemaAuditError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_unique(root: Path, basename: str) -> Path:
    matches = [path for path in root.rglob(basename) if path.is_file()]
    if len(matches) != 1:
        raise SchemaAuditError(
            f"expected exactly one {basename!r} below {root}; found {len(matches)}"
        )
    return matches[0]


def csv_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return tuple(next(reader))
        except StopIteration as exc:
            raise SchemaAuditError(f"empty CSV: {path}") from exc


def selected_columns(
    path: Path,
    names: Iterable[str],
) -> tuple[dict[str, str], ...]:
    wanted = tuple(names)
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SchemaAuditError(f"missing CSV header: {path}")
        missing = [name for name in wanted if name not in reader.fieldnames]
        if missing:
            raise SchemaAuditError(
                f"missing selected columns in {path.name}: {', '.join(missing)}"
            )
        for raw in reader:
            rows.append({name: raw.get(name, "") for name in wanted})
    return tuple(rows)


def normalized_nonblank(values: Iterable[str]) -> tuple[str, ...]:
    cleaned = {str(value).strip() for value in values if str(value).strip()}
    return tuple(sorted(cleaned))


def audit(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise SchemaAuditError(f"archive root is not a directory: {root}")

    files = {key: locate_unique(root, basename) for key, basename in REQUIRED.items()}

    headers = {
        key: csv_header(files[key])
        for key in ("genetic", "hummingbird", "patches")
    }

    header_checks = {}
    for key, expected in EXPECTED_HEADERS.items():
        observed = set(headers[key])
        missing = sorted(expected - observed)
        header_checks[key] = {
            "required_count": len(expected),
            "observed_count": len(headers[key]),
            "missing_required": missing,
            "pass": not missing,
            "endpoint_columns_present": sorted(observed & ENDPOINT_COLUMNS),
        }

    if any(not value["pass"] for value in header_checks.values()):
        problems = {
            key: value["missing_required"]
            for key, value in header_checks.items()
            if not value["pass"]
        }
        raise SchemaAuditError(f"required header mismatch: {problems}")

    genetic_ids = selected_columns(files["genetic"], ("Mom_ID", "Year", "Pop"))
    patch_ids = selected_columns(files["patches"], ("Pop",))
    hummingbird_ids = selected_columns(files["hummingbird"], ("Patch",))

    genetic_pops = normalized_nonblank(row["Pop"] for row in genetic_ids)
    patch_pops = normalized_nonblank(row["Pop"] for row in patch_ids)
    hummingbird_patches = normalized_nonblank(row["Patch"] for row in hummingbird_ids)
    years = normalized_nonblank(row["Year"] for row in genetic_ids)
    maternal_ids = normalized_nonblank(row["Mom_ID"] for row in genetic_ids)

    # This is only a literal identifier-set diagnostic. Equality does not prove
    # ecological identity, and inequality does not authorize a repair/alias.
    literal_patch_pop_relation = {
        "genetic_pop_equals_patch_table_pop": genetic_pops == patch_pops,
        "hummingbird_patch_equals_genetic_pop": hummingbird_patches == genetic_pops,
        "hummingbird_patch_equals_patch_table_pop": hummingbird_patches == patch_pops,
        "genetic_pop_only": sorted(set(genetic_pops) - set(hummingbird_patches)),
        "hummingbird_patch_only": sorted(set(hummingbird_patches) - set(genetic_pops)),
        "interpretation": (
            "literal string-set comparison only; ecological Patch-to-Pop mapping "
            "still requires source documentation or an explicit mapping table"
        ),
    }

    file_inventory = {}
    for key, path in files.items():
        file_inventory[key] = {
            "basename": path.name,
            "relative_path": str(path.relative_to(root)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    return {
        "schema": "structural.davis_schema_audit.v0_7",
        "status": "schema_only_no_model_fit",
        "counts_as_fresh_evidence": False,
        "root": str(root),
        "files": file_inventory,
        "headers": {key: list(value) for key, value in headers.items()},
        "header_checks": header_checks,
        "identifier_summary": {
            "genetic_rows": len(genetic_ids),
            "maternal_ids": len(maternal_ids),
            "genetic_pop_count": len(genetic_pops),
            "patch_table_pop_count": len(patch_pops),
            "hummingbird_patch_count": len(hummingbird_patches),
            "years": list(years),
            "repeated_year_structure_present": len(years) > 1,
        },
        "literal_patch_pop_relation": literal_patch_pop_relation,
        "model_fit_count": 0,
        "candidate_ranking_count": 0,
        "endpoint_value_summary_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        result = audit(args.archive_root)
    except SchemaAuditError as exc:
        print(json.dumps({
            "schema": "structural.davis_schema_audit.v0_7",
            "status": "STOP",
            "reason": str(exc),
            "model_fit_count": 0,
        }, indent=2, sort_keys=True))
        return 2

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
