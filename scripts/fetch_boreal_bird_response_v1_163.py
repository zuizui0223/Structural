#!/usr/bin/env python3
"""Fetch exact boreal-bird response bytes; do not decode response semantics."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, build_opener

from scripts.fetch_boreal_mixed_files_v0_72 import (
    StripAuthorizationOnCrossOriginRedirect,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "development/boreal_bird_pilot_contract_v1_163.json"


class BirdResponseTransportError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BirdResponseTransportError("contract must be a JSON object")
    return value


def fetch(destination: Path, *, contract: dict, token: str | None = None) -> dict:
    target = contract["response_file"]
    token = os.environ.get("DRYAD_TOKEN", "") if token is None else str(token)
    if not token or "\n" in token or "\r" in token:
        raise BirdResponseTransportError("DRYAD_TOKEN missing or malformed")
    if destination.exists():
        raise BirdResponseTransportError("refusing to overwrite response bytes")

    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name("." + destination.name + ".part")
    if part.exists():
        part.unlink()

    request = Request(
        target["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-v1.163",
        },
    )
    opener = build_opener(StripAuthorizationOnCrossOriginRedirect())
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
        raise BirdResponseTransportError(
            f"response transport failed: {type(exc).__name__}"
        ) from None

    sha = digest.hexdigest()
    if count != int(target["expected_size_bytes"]) or sha != target["expected_sha256"]:
        part.unlink(missing_ok=True)
        raise BirdResponseTransportError("exact bird-response identity mismatch")
    os.replace(part, destination)
    return {
        "schema": "structural.boreal_bird_response_transport.v1_163",
        "status": "EXACT_BIRD_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED",
        "candidate_id": contract["candidate_id"],
        "size_bytes": count,
        "sha256": sha,
        "response_semantics_opened": False,
        "bird_confirmatory_response_opened": False,
        "counts_as_empirical_evidence": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        result = fetch(args.destination, contract=load_json(args.contract))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError,
            BirdResponseTransportError) as exc:
        result = {
            "schema": "structural.boreal_bird_response_transport.v1_163",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "response_semantics_opened": False,
            "bird_confirmatory_response_opened": False,
            "counts_as_empirical_evidence": False,
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
