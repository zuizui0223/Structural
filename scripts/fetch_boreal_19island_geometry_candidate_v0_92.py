#!/usr/bin/env python3
"""Discover exact byte identity for the frozen boreal 19-island geometry candidate.

This stage treats the target CSV as opaque bytes. It computes only byte count and
SHA-256, never decodes the header or any row, and is intended to be followed by
a separate committed identity freeze before header-only inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_geometry_identity_contract_v0_92.json"
)


class Boreal19IdentityError(RuntimeError):
    pass


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port


class StripAuthorizationOnCrossOriginRedirect(HTTPRedirectHandler):
    """Never forward the Dryad bearer token to object storage."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(
            req, fp, code, msg, headers, newurl
        )
        if redirected is None:
            return None
        if _origin(req.full_url) != _origin(newurl):
            redirected.remove_header("Authorization")
        return redirected


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != (
        "structural.boreal_19island_geometry_identity_contract.v0_92"
    ):
        raise Boreal19IdentityError("unexpected v0.92 contract schema")
    return value


def discover_identity(
    output_path: Path,
    *,
    contract: dict | None = None,
    token: str | None = None,
    opener=None,
) -> dict:
    contract = load_contract() if contract is None else contract
    source = contract["source"]
    token = os.environ.get("DRYAD_TOKEN", "") if token is None else token
    if not token or "\n" in token or "\r" in token:
        raise Boreal19IdentityError("DRYAD_TOKEN is missing or malformed")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    part = output_path.with_name("." + output_path.name + ".part")
    if output_path.exists() or part.exists():
        raise Boreal19IdentityError("refusing to overwrite prior transport bytes")

    request = Request(
        source["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-v0.92",
        },
    )
    opener = opener or build_opener(StripAuthorizationOnCrossOriginRedirect())

    digest = hashlib.sha256()
    count = 0
    try:
        with opener.open(request, timeout=120) as response, part.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                count += len(chunk)
    except Exception as exc:
        if part.exists():
            part.unlink()
        raise Boreal19IdentityError(
            f"opaque transport failed: {type(exc).__name__}"
        ) from None

    if count <= 0:
        if part.exists():
            part.unlink()
        raise Boreal19IdentityError("opaque transport returned zero bytes")

    os.replace(part, output_path)
    return {
        "schema": "structural.boreal_19island_geometry_identity_result.v0_92",
        "status": "OPAQUE_BYTE_IDENTITY_DISCOVERED",
        "candidate_id": contract["candidate_id"],
        "source": {
            "file_name": source["file_name"],
            "dryad_file_id": source["dryad_file_id"],
            "dryad_version_id": source["dryad_version_id"],
            "dryad_version_number": source["dryad_version_number"],
        },
        "size_bytes": count,
        "sha256": digest.hexdigest(),
        "header_decoded": False,
        "data_rows_semantically_opened": 0,
        "safe_row_values_opened": False,
        "biological_response_values_opened": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "raw_bytes_may_be_committed_or_uploaded": False,
        "next_action": (
            "commit this exact size and SHA-256 in a separate revision, then "
            "re-download and perform header-only classification"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        result = discover_identity(
            args.output_path,
            contract=load_contract(args.contract),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19IdentityError,
    ) as exc:
        result = {
            "schema": "structural.boreal_19island_geometry_identity_result.v0_92",
            "status": "STOP",
            "reason": str(exc),
            "header_decoded": False,
            "data_rows_semantically_opened": 0,
            "safe_row_values_opened": False,
            "biological_response_values_opened": False,
            "counts_as_empirical_evidence": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2
    else:
        code = 0

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
