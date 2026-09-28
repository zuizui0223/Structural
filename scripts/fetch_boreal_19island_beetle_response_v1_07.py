#!/usr/bin/env python3
"""Fetch the exact authorized 19-island boreal beetle response as opaque bytes."""
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
    ROOT / "development/boreal_19island_one_shot_pilot_contract_v1_07.json"
)


class Boreal19ResponseTransportError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19ResponseTransportError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_authorization(
    authorization: dict,
    *,
    authorization_file_sha256: str,
    contract: dict,
) -> None:
    rule = contract["authorization"]
    if authorization.get("schema") != rule["schema"]:
        raise Boreal19ResponseTransportError(
            "unexpected pilot authorization schema"
        )
    if authorization.get("status") != rule["status"]:
        raise Boreal19ResponseTransportError(
            "pilot authorization did not qualify"
        )
    if authorization.get("candidate_id") != contract["candidate_id"]:
        raise Boreal19ResponseTransportError(
            "pilot authorization candidate mismatch"
        )
    if authorization.get("authorization_fingerprint") != (
        rule["expected_fingerprint"]
    ):
        raise Boreal19ResponseTransportError(
            "pilot authorization fingerprint mismatch"
        )
    if authorization_file_sha256 != rule["expected_json_sha256"]:
        raise Boreal19ResponseTransportError(
            "pilot authorization JSON SHA mismatch"
        )
    if authorization.get("pilot_response_authorized") is not True:
        raise Boreal19ResponseTransportError(
            "pilot response is not authorized"
        )
    if authorization.get("confirmatory_response_authorized") is not False:
        raise Boreal19ResponseTransportError(
            "confirmatory response ceiling violated"
        )
    if authorization.get("authorization_consumed") is not False:
        raise Boreal19ResponseTransportError(
            "pilot authorization already consumed"
        )
    if authorization.get("response_values_opened_by_authorization") is not False:
        raise Boreal19ResponseTransportError(
            "authorization unexpectedly opened response values"
        )

    target = contract["response_file"]
    response = authorization.get("response_file")
    if not isinstance(response, dict):
        raise Boreal19ResponseTransportError(
            "authorized response identity missing"
        )
    for key, expected in (
        ("name", target["name"]),
        ("dryad_file_id", target["dryad_file_id"]),
        ("size_bytes", target["expected_size_bytes"]),
        ("sha256", target["expected_sha256"]),
        ("expected_species_columns", target["expected_species_columns"]),
    ):
        if response.get(key) != expected:
            raise Boreal19ResponseTransportError(
                f"authorized response identity drift: {key}"
            )


def fetch(
    authorization: dict,
    destination: Path,
    *,
    authorization_file_sha256: str,
    contract: dict,
    token: str | None = None,
    opener=None,
) -> dict:
    _validate_authorization(
        authorization,
        authorization_file_sha256=authorization_file_sha256,
        contract=contract,
    )
    token = os.environ.get("DRYAD_TOKEN", "") if token is None else str(token)
    if not token or "\n" in token or "\r" in token:
        raise Boreal19ResponseTransportError(
            "DRYAD_TOKEN is missing or malformed"
        )

    target = contract["response_file"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name("." + destination.name + ".part")
    if destination.exists() or part.exists():
        raise Boreal19ResponseTransportError(
            "refusing to overwrite prior response transport bytes"
        )

    request = Request(
        target["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-v1.07",
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
        raise Boreal19ResponseTransportError(
            f"response transport failed: {type(exc).__name__}"
        ) from None

    observed_sha = digest.hexdigest()
    if (
        count != target["expected_size_bytes"]
        or observed_sha != target["expected_sha256"]
    ):
        if part.exists():
            part.unlink()
        raise Boreal19ResponseTransportError(
            "response exact-byte verification failed"
        )

    os.replace(part, destination)
    return {
        "schema": "structural.boreal_19island_response_transport.v1_07",
        "status": "EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED",
        "candidate_id": contract["candidate_id"],
        "authorization_fingerprint": authorization["authorization_fingerprint"],
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
        "next_action": (
            "invoke the v1.07 semantic pilot executor exactly once; "
            "transport alone does not consume authorization"
        ),
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
            "structural.boreal_19island_one_shot_pilot_contract.v1_07"
        ):
            raise Boreal19ResponseTransportError(
                "unexpected v1.07 pilot contract schema"
            )
        result = fetch(
            _load(args.authorization),
            args.destination,
            authorization_file_sha256=sha256_file(args.authorization),
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19ResponseTransportError,
    ) as exc:
        result = {
            "schema": "structural.boreal_19island_response_transport.v1_07",
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
