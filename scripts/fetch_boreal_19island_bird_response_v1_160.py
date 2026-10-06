#!/usr/bin/env python3
"""Fetch the exact sealed boreal bird response as opaque bytes for pilot v1.160."""
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
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_birds_pilot_contract_v1_159.json"
)


class BirdResponseTransportError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(destination: Path, *, contract: dict, token: str | None = None) -> dict:
    if contract.get("schema") != "structural.boreal_19island_birds_pilot_contract.v1_159":
        raise BirdResponseTransportError("unexpected pilot contract schema")
    target = contract["response_file"]
    token = os.environ.get("DRYAD_TOKEN", "") if token is None else str(token)
    if not token or "\n" in token or "\r" in token:
        raise BirdResponseTransportError("DRYAD_TOKEN missing or malformed")
    if destination.exists():
        raise BirdResponseTransportError("refusing to overwrite bird response bytes")

    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name("." + destination.name + ".part")
    if part.exists():
        part.unlink()

    req = Request(
        target["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-bird-v1.160",
        },
    )
    opener = build_opener(StripAuthorizationOnCrossOriginRedirect())
    digest = hashlib.sha256()
    count = 0
    try:
        with opener.open(req, timeout=120) as response, part.open("wb") as out:
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
            f"bird response transport failed: {type(exc).__name__}"
        ) from None

    observed = digest.hexdigest()
    if count != int(target["expected_size_bytes"]) or observed != target["expected_sha256"]:
        if part.exists():
            part.unlink()
        raise BirdResponseTransportError("bird response exact-byte verification failed")
    os.replace(part, destination)
    return {
        "schema": "structural.boreal_19island_bird_response_transport.v1_160",
        "status": "EXACT_BIRD_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED",
        "candidate_id": contract["candidate_id"],
        "size_bytes": count,
        "sha256": observed,
        "response_semantics_opened": False,
        "counts_as_empirical_evidence": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        result = fetch(args.destination, contract=contract)
        code = 0
    except (OSError, KeyError, ValueError, json.JSONDecodeError, BirdResponseTransportError) as exc:
        result = {
            "schema": "structural.boreal_19island_bird_response_transport.v1_160",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "response_semantics_opened": False,
            "counts_as_empirical_evidence": False,
        }
        code = 2
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
