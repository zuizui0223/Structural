#!/usr/bin/env python3
"""Fetch the exact authorized boreal beetle response as opaque bytes."""
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
    ROOT / "development/boreal_beetle_one_shot_pilot_contract_v0_82.json"
)


class BorealBeetleResponseTransportError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    x = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x, dict):
        raise BorealBeetleResponseTransportError(
            f"{path.name} must contain a JSON object"
        )
    return x


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_authorization(auth: dict, contract: dict) -> None:
    pre = contract["pre_access"]
    if auth.get("schema") != pre["authorization_schema"]:
        raise BorealBeetleResponseTransportError(
            "unexpected pilot authorization schema"
        )
    if auth.get("status") != pre["authorization_status"]:
        raise BorealBeetleResponseTransportError(
            "pilot authorization did not qualify"
        )
    if auth.get("candidate_id") != contract["candidate_id"]:
        raise BorealBeetleResponseTransportError(
            "pilot authorization candidate mismatch"
        )
    if auth.get("pilot_response_authorized") is not True:
        raise BorealBeetleResponseTransportError(
            "pilot response is not authorized"
        )
    if auth.get("confirmatory_response_authorized") is not False:
        raise BorealBeetleResponseTransportError(
            "confirmatory response ceiling violated"
        )
    if auth.get("authorization_consumed") is not False:
        raise BorealBeetleResponseTransportError(
            "pilot authorization already consumed"
        )
    if auth.get("response_file") != {
        "name": contract["response_file"]["name"],
        "dryad_file_id": contract["response_file"]["dryad_file_id"],
        "size_bytes": contract["response_file"]["expected_size_bytes"],
        "sha256": contract["response_file"]["expected_sha256"],
    }:
        raise BorealBeetleResponseTransportError(
            "authorized response identity drift"
        )


def fetch(
    authorization: dict,
    destination: Path,
    *,
    contract: dict,
    token: str | None = None,
    opener=None,
) -> dict:
    _validate_authorization(authorization, contract)
    token = os.environ.get("DRYAD_TOKEN", "") if token is None else str(token)
    if not token or "\n" in token or "\r" in token:
        raise BorealBeetleResponseTransportError(
            "DRYAD_TOKEN is missing or malformed"
        )

    target = contract["response_file"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name("." + destination.name + ".part")
    if part.exists():
        part.unlink()

    req = Request(
        target["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-v0.82",
        },
    )
    opener = opener or build_opener(StripAuthorizationOnCrossOriginRedirect())
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
        raise BorealBeetleResponseTransportError(
            f"response transport failed: {type(exc).__name__}"
        ) from None

    observed_sha = digest.hexdigest()
    if (
        count != target["expected_size_bytes"]
        or observed_sha != target["expected_sha256"]
    ):
        if part.exists():
            part.unlink()
        raise BorealBeetleResponseTransportError(
            "response exact-byte verification failed"
        )
    os.replace(part, destination)
    return {
        "schema": "structural.boreal_beetle_response_transport.v0_82",
        "status": "EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED",
        "candidate_id": contract["candidate_id"],
        "response_file": {
            "name": target["name"],
            "dryad_file_id": target["dryad_file_id"],
            "size_bytes": count,
            "sha256": observed_sha,
        },
        "response_semantics_opened": False,
        "authorization_consumed": False,
        "pilot_response_authorized": True,
        "confirmatory_response_authorized": False,
        "counts_as_empirical_evidence": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_beetle_one_shot_pilot_contract.v0_82"
        ):
            raise BorealBeetleResponseTransportError(
                "unexpected v0.82 contract schema"
            )
        result = fetch(
            _load(args.authorization),
            args.destination,
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealBeetleResponseTransportError,
    ) as exc:
        result = {
            "schema": "structural.boreal_beetle_response_transport.v0_82",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "response_semantics_opened": False,
            "authorization_consumed": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "counts_as_empirical_evidence": False,
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
