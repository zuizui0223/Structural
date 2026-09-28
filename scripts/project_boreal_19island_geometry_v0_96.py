#!/usr/bin/env python3
"""Project only frozen-safe Island/Lat/Long for the boreal 19-island route."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from structural.mixed_csv_firewall import (
    MixedCSVColumnManifest,
    MixedCSVFirewallError,
    project_safe_columns,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_geometry_projection_contract_v0_96.json"
)
DEFAULT_FREEZE = (
    ROOT / "development/boreal_19island_header_projection_freeze_v0_95.json"
)
DEFAULT_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class Boreal19ProjectionError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19ProjectionError(f"{path.name} must contain a JSON object")
    return value


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port


class StripAuthorizationOnCrossOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None
        if _origin(req.full_url) != _origin(newurl):
            redirected.remove_header("Authorization")
        return redirected


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_exact(
    output: Path,
    *,
    file_id: int,
    expected_size: int,
    expected_sha: str,
    token: str,
    opener=None,
) -> None:
    if not token or "\n" in token or "\r" in token:
        raise Boreal19ProjectionError("DRYAD_TOKEN is missing or malformed")
    if output.exists():
        raise Boreal19ProjectionError("refusing to overwrite prior raw bytes")
    output.parent.mkdir(parents=True, exist_ok=True)
    part = output.with_name("." + output.name + ".part")
    if part.exists():
        part.unlink()

    request = Request(
        f"https://datadryad.org/api/v2/files/{file_id}/download",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-v0.96",
        },
    )
    opener = opener or build_opener(StripAuthorizationOnCrossOriginRedirect())
    digest = hashlib.sha256()
    count = 0
    try:
        with opener.open(request, timeout=120) as response, part.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                digest.update(chunk)
                count += len(chunk)
    except Exception as exc:
        if part.exists():
            part.unlink()
        raise Boreal19ProjectionError(
            f"exact transport failed: {type(exc).__name__}"
        ) from None

    if count != int(expected_size) or digest.hexdigest() != expected_sha:
        part.unlink(missing_ok=True)
        raise Boreal19ProjectionError("exact transport identity mismatch")
    os.replace(part, output)


def _load_universe(mapping: Mapping) -> tuple[str, ...]:
    if mapping.get("row_count") != 42 or mapping.get("unique_island_count") != 42:
        raise Boreal19ProjectionError("frozen parent universe is not exact 42 islands")
    codes = tuple(mapping["current_study_island_universe"]["codes"])
    if len(codes) != 42 or len(set(codes)) != 42:
        raise Boreal19ProjectionError("frozen parent island codes are invalid")
    return codes


def _validate(contract: Mapping, freeze: Mapping) -> MixedCSVColumnManifest:
    if contract.get("schema") != (
        "structural.boreal_19island_geometry_projection_contract.v0_96"
    ):
        raise Boreal19ProjectionError("unexpected v0.96 contract schema")
    if freeze.get("schema") != (
        "structural.boreal_19island_header_projection_freeze.v0_95"
    ):
        raise Boreal19ProjectionError("unexpected v0.95 projection-freeze schema")
    if freeze.get("status") != (
        "HEADER_AND_SAFE_GEOMETRY_COLUMNS_FROZEN_BEFORE_ROW_ACCESS"
    ):
        raise Boreal19ProjectionError("v0.95 projection freeze did not qualify")
    if freeze.get("candidate_id") != contract.get("candidate_id"):
        raise Boreal19ProjectionError("candidate identity drift")
    if freeze.get("row_values_opened_by_freezer") != 0:
        raise Boreal19ProjectionError("v0.95 row-access boundary violated")
    if freeze.get("biological_response_values_opened_by_freezer") is not False:
        raise Boreal19ProjectionError("v0.95 biological-response boundary violated")
    if freeze.get("safe_geometry_projection_authorized_for_later_revision") is not True:
        raise Boreal19ProjectionError("v0.95 did not authorize geometry projection")

    target = contract["target_file"]
    frozen_file = freeze["file"]
    for key, expected in (
        ("name", target["name"]),
        ("dryad_file_id", target["dryad_file_id"]),
        ("size_bytes", target["expected_size_bytes"]),
        ("sha256", target["expected_sha256"]),
    ):
        if frozen_file.get(key) != expected:
            raise Boreal19ProjectionError(f"frozen target drift: {key}")

    safe = tuple(contract["projection"]["safe_columns"])
    frozen_manifest = freeze["projection_manifest"]
    if tuple(frozen_manifest["safe_pre_response_columns"]) != safe:
        raise Boreal19ProjectionError("safe projection columns drift from v0.95")
    if safe != ("Island", "Lat", "Long"):
        raise Boreal19ProjectionError("v0.96 may project only Island/Lat/Long")

    return MixedCSVColumnManifest(
        file_sha256=target["expected_sha256"],
        header_sha256=frozen_file["header_canonical_sha256"],
        safe_pre_response_columns=safe,
        protected_response_columns=tuple(
            frozen_manifest["protected_response_columns"]
        ),
    )


def _finite_float(value: object, label: str) -> float:
    try:
        x = float(str(value).strip())
    except ValueError as exc:
        raise Boreal19ProjectionError(f"{label} is not numeric") from exc
    if not math.isfinite(x):
        raise Boreal19ProjectionError(f"{label} is nonfinite")
    return x


def _csv_text(rows: Sequence[tuple[str, float, float]]) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["Island", "Lat", "Long"])
    for island, lat, lon in rows:
        writer.writerow([island, float(lat).hex(), float(lon).hex()])
    return out.getvalue()


def project_geometry(
    raw_csv: Path,
    *,
    contract: Mapping,
    freeze: Mapping,
    universe_mapping: Mapping,
) -> tuple[str, dict]:
    manifest = _validate(contract, freeze)
    rows = project_safe_columns(raw_csv, manifest)
    expected_n = int(contract["projection"]["expected_row_count"])
    if len(rows) != expected_n:
        raise Boreal19ProjectionError(
            f"safe geometry row count {len(rows)} != {expected_n}"
        )

    parent_universe = set(_load_universe(universe_mapping))
    parsed: list[tuple[str, float, float]] = []
    seen: set[str] = set()
    for row in rows:
        island = str(row.get("Island", "")).strip()
        if not island:
            raise Boreal19ProjectionError("blank Island")
        if island in seen:
            raise Boreal19ProjectionError(f"duplicate Island: {island}")
        seen.add(island)
        if island not in parent_universe:
            raise Boreal19ProjectionError(
                f"19-island geometry contains unknown parent island: {island}"
            )
        lat = _finite_float(row.get("Lat", ""), f"{island}.Lat")
        lon = _finite_float(row.get("Long", ""), f"{island}.Long")
        if not (-90.0 <= lat <= 90.0):
            raise Boreal19ProjectionError(f"{island}.Lat outside [-90,90]")
        if not (-180.0 <= lon <= 180.0):
            raise Boreal19ProjectionError(f"{island}.Long outside [-180,180]")
        parsed.append((island, lat, lon))

    if len(seen) != expected_n:
        raise Boreal19ProjectionError("19-island geometry IDs are not unique")

    parsed.sort(key=lambda x: x[0])
    geometry = _csv_text(parsed)
    receipt = {
        "schema": "structural.boreal_19island_geometry_projection_result.v0_96",
        "status": "SAFE_19_ISLAND_GEOMETRY_PROJECTED_RESPONSE_REMAINS_SEALED",
        "candidate_id": contract["candidate_id"],
        "row_count": len(parsed),
        "unique_island_count": len(seen),
        "island_order": [row[0] for row in parsed],
        "parent_42_island_subset_verified": True,
        "latitude_min_hex": float(min(row[1] for row in parsed)).hex(),
        "latitude_max_hex": float(max(row[1] for row in parsed)).hex(),
        "longitude_min_hex": float(min(row[2] for row in parsed)).hex(),
        "longitude_max_hex": float(max(row[2] for row in parsed)).hex(),
        "geometry_sha256": hashlib.sha256(geometry.encode("utf-8")).hexdigest(),
        "coordinate_encoding": "python_float_hex",
        "safe_row_values_opened": True,
        "safe_columns_returned": ["Island", "Lat", "Long"],
        "protected_response_values_exposed": False,
        "closed_unclassified_values_exposed": False,
        "biological_response_values_opened": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "inspect only this safe 19-island geometry and prospectively freeze "
            "a spatial validation design before any beetle occurrence response"
        ),
    }
    return geometry, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE)
    parser.add_argument("--geometry-output", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        freeze = _load(args.freeze)
        universe = _load(args.universe)
        if args.download:
            target = contract["target_file"]
            _download_exact(
                args.raw_csv,
                file_id=int(target["dryad_file_id"]),
                expected_size=int(target["expected_size_bytes"]),
                expected_sha=str(target["expected_sha256"]),
                token=os.environ.get("DRYAD_TOKEN", ""),
            )
        if _sha256_file(args.raw_csv) != contract["target_file"]["expected_sha256"]:
            raise Boreal19ProjectionError("local raw file identity mismatch")
        geometry, result = project_geometry(
            args.raw_csv,
            contract=contract,
            freeze=freeze,
            universe_mapping=universe,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        MixedCSVFirewallError,
        Boreal19ProjectionError,
    ) as exc:
        result = {
            "schema": "structural.boreal_19island_geometry_projection_result.v0_96",
            "status": "STOP",
            "reason": str(exc),
            "safe_row_values_opened": False,
            "protected_response_values_exposed": False,
            "biological_response_values_opened": False,
            "counts_as_empirical_evidence": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2
    else:
        if args.geometry_output is not None:
            args.geometry_output.parent.mkdir(parents=True, exist_ok=True)
            args.geometry_output.write_text(geometry, encoding="utf-8")
        code = 0

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
