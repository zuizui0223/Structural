#!/usr/bin/env python3
"""Verify the frozen 19-island file identity, then decode its header only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "development/boreal_19island_header_audit_contract_v0_94.json"
DEFAULT_FREEZE = ROOT / "development/boreal_19island_geometry_identity_freeze_v0_93.json"


class Boreal19HeaderError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19HeaderError(f"{path.name} must contain a JSON object")
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


def validate_contract_and_freeze(contract: dict, freeze: dict) -> dict:
    if contract.get("schema") != "structural.boreal_19island_header_audit_contract.v0_94":
        raise Boreal19HeaderError("unexpected v0.94 contract schema")
    if freeze.get("schema") != "structural.boreal_19island_geometry_identity_freeze.v0_93":
        raise Boreal19HeaderError("unexpected v0.93 identity-freeze schema")
    if freeze.get("status") != "OPAQUE_BYTE_IDENTITY_FROZEN_BEFORE_HEADER_ACCESS":
        raise Boreal19HeaderError("v0.93 identity freeze did not qualify")
    if freeze.get("header_access_authorized_by_this_freeze") is not False:
        raise Boreal19HeaderError("v0.93 identity freeze access boundary drift")
    if freeze.get("safe_row_projection_authorized") is not False:
        raise Boreal19HeaderError("v0.93 unexpectedly authorized row projection")

    target = contract["target"]
    frozen = freeze["file"]
    checks = {
        "name": target["name"],
        "dryad_file_id": target["dryad_file_id"],
        "dryad_version_id": target["dryad_version_id"],
        "dryad_version_number": target["dryad_version_number"],
        "size_bytes": target["expected_size_bytes"],
        "sha256": target["expected_sha256"],
    }
    if frozen != checks:
        raise Boreal19HeaderError("v0.94 target does not exact-match v0.93 identity freeze")
    access = freeze["access_state_at_freeze"]
    if access.get("header_decoded") is not False:
        raise Boreal19HeaderError("header was already decoded before v0.94")
    if access.get("data_rows_semantically_opened") != 0:
        raise Boreal19HeaderError("data rows were already opened before v0.94")
    if access.get("biological_response_values_opened") is not False:
        raise Boreal19HeaderError("biological response was already opened before v0.94")
    return target


def _download_exact(
    output: Path,
    target: dict,
    token: str,
    *,
    opener=None,
) -> None:
    if not token or "\n" in token or "\r" in token:
        raise Boreal19HeaderError("DRYAD_TOKEN is missing or malformed")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise Boreal19HeaderError("refusing to overwrite prior target bytes")
    part = output.with_name("." + output.name + ".part")
    if part.exists():
        part.unlink()

    request = Request(
        target["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-v0.94",
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
        raise Boreal19HeaderError(
            f"exact transport failed: {type(exc).__name__}"
        ) from None

    if count != int(target["expected_size_bytes"]):
        part.unlink(missing_ok=True)
        raise Boreal19HeaderError("exact transport byte-size mismatch")
    if digest.hexdigest() != target["expected_sha256"]:
        part.unlink(missing_ok=True)
        raise Boreal19HeaderError("exact transport SHA-256 mismatch")
    os.replace(part, output)


def audit_header(
    output: Path,
    *,
    contract: dict,
    freeze: dict,
    token: str,
    opener=None,
) -> dict:
    target = validate_contract_and_freeze(contract, freeze)
    _download_exact(output, target, token, opener=opener)

    # The full file is byte-verified above while opaque. Only now is the first
    # physical record read. No second readline/read call is made.
    with output.open("rb") as handle:
        first_record = handle.readline()

    if not first_record:
        raise Boreal19HeaderError("empty first physical record")
    if b"\n" not in first_record and len(first_record) == target["expected_size_bytes"]:
        raise Boreal19HeaderError("file has no separable header record")

    try:
        text = first_record.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise Boreal19HeaderError("header is not UTF-8") from exc

    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        raise Boreal19HeaderError("header CSV parse failed") from exc
    if len(rows) != 1 or not rows[0]:
        raise Boreal19HeaderError("first physical record is not one nonempty CSV row")
    header = rows[0]
    if any(not isinstance(name, str) or not name.strip() for name in header):
        raise Boreal19HeaderError("header contains a blank column name")
    if len(header) != len(set(header)):
        raise Boreal19HeaderError("header contains duplicate exact column names")

    return {
        "schema": "structural.boreal_19island_header_audit_result.v0_94",
        "status": "HEADER_ONLY_AUDIT_COMPLETE_ROWS_REMAIN_SEALED",
        "candidate_id": contract["candidate_id"],
        "file": {
            "name": target["name"],
            "dryad_file_id": target["dryad_file_id"],
            "size_bytes": target["expected_size_bytes"],
            "sha256": target["expected_sha256"],
        },
        "header": header,
        "column_count": len(header),
        "header_physical_record_sha256": hashlib.sha256(first_record).hexdigest(),
        "header_decoded": True,
        "data_rows_semantically_opened": 0,
        "safe_row_values_opened": False,
        "biological_response_values_opened": False,
        "all_header_columns_closed_until_next_revision": True,
        "safe_row_projection_authorized": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "commit this exact header in a separate revision; only then may "
            "exact identity/Lat/Long projection columns be frozen"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_file", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--identity-freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        result = audit_header(
            args.output_file,
            contract=_load(args.contract),
            freeze=_load(args.identity_freeze),
            token=os.environ.get("DRYAD_TOKEN", ""),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19HeaderError,
    ) as exc:
        result = {
            "schema": "structural.boreal_19island_header_audit_result.v0_94",
            "status": "STOP",
            "reason": str(exc),
            "header_decoded": False,
            "data_rows_semantically_opened": 0,
            "safe_row_values_opened": False,
            "biological_response_values_opened": False,
            "safe_row_projection_authorized": False,
            "counts_as_empirical_evidence": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2
    else:
        code = 0

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
