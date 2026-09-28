#!/usr/bin/env python3
"""Fetch exact authorized confirmatory response bytes without semantic opening."""
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
    ROOT / "development/boreal_19island_confirmatory_scoring_contract_v1_13.json"
)
DEFAULT_AUTHORIZATION_FREEZE = (
    ROOT
    / "development/boreal_19island_confirmatory_authorization_freeze_v1_12.json"
)


class Boreal19ConfirmatoryTransportError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19ConfirmatoryTransportError(
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
    authorization_freeze: dict,
    *,
    authorization_file_sha256: str,
    contract: dict,
) -> None:
    required = contract["required_authorization"]
    if authorization.get("schema") != required["schema"]:
        raise Boreal19ConfirmatoryTransportError(
            "unexpected confirmatory authorization schema"
        )
    if authorization.get("status") != required["status"]:
        raise Boreal19ConfirmatoryTransportError(
            "confirmatory authorization did not qualify"
        )
    if authorization.get("candidate_id") != contract["candidate_id"]:
        raise Boreal19ConfirmatoryTransportError(
            "confirmatory authorization candidate mismatch"
        )
    if authorization.get("authorization_fingerprint") != required[
        "authorization_fingerprint"
    ]:
        raise Boreal19ConfirmatoryTransportError(
            "confirmatory authorization fingerprint mismatch"
        )
    if authorization_file_sha256 != required["authorization_json_sha256"]:
        raise Boreal19ConfirmatoryTransportError(
            "confirmatory authorization JSON SHA mismatch"
        )
    if authorization.get("confirmatory_response_authorized") is not True:
        raise Boreal19ConfirmatoryTransportError(
            "confirmatory response is not authorized"
        )
    if authorization.get("authorization_consumed") is not False:
        raise Boreal19ConfirmatoryTransportError(
            "confirmatory authorization already consumed"
        )
    if authorization.get("response_values_opened_by_authorization") is not False:
        raise Boreal19ConfirmatoryTransportError(
            "authorization unexpectedly opened response values"
        )
    if authorization.get("counts_as_empirical_evidence") is not False:
        raise Boreal19ConfirmatoryTransportError(
            "authorization evidence ceiling violated"
        )

    if authorization_freeze.get("schema") != (
        "structural.boreal_19island_confirmatory_authorization_freeze.v1_12"
    ):
        raise Boreal19ConfirmatoryTransportError(
            "unexpected authorization freeze schema"
        )
    if authorization_freeze.get("status") != (
        "CONFIRMATORY_AUTHORIZATION_COMMITTED_BY_FINGERPRINT_RESPONSE_UNOPENED"
    ):
        raise Boreal19ConfirmatoryTransportError(
            "authorization freeze did not qualify"
        )
    if authorization_freeze.get("candidate_id") != contract["candidate_id"]:
        raise Boreal19ConfirmatoryTransportError(
            "authorization freeze candidate mismatch"
        )
    if authorization_freeze.get("scoring_execution_may_be_built") is not True:
        raise Boreal19ConfirmatoryTransportError(
            "authorization freeze does not permit scoring execution"
        )
    frozen = authorization_freeze.get("authorization")
    if not isinstance(frozen, dict):
        raise Boreal19ConfirmatoryTransportError(
            "frozen authorization identity missing"
        )
    if frozen.get("authorization_fingerprint") != required[
        "authorization_fingerprint"
    ]:
        raise Boreal19ConfirmatoryTransportError(
            "frozen authorization fingerprint drift"
        )
    if frozen.get("authorization_json_sha256") != required[
        "authorization_json_sha256"
    ]:
        raise Boreal19ConfirmatoryTransportError(
            "frozen authorization JSON SHA drift"
        )

    target = contract["response_file"]
    response = authorization.get("response_file")
    if not isinstance(response, dict):
        raise Boreal19ConfirmatoryTransportError(
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
            raise Boreal19ConfirmatoryTransportError(
                f"authorized response identity drift: {key}"
            )


def fetch(
    authorization: dict,
    authorization_freeze: dict,
    destination: Path,
    *,
    authorization_file_sha256: str,
    contract: dict,
    token: str | None = None,
    opener=None,
) -> dict:
    _validate_authorization(
        authorization,
        authorization_freeze,
        authorization_file_sha256=authorization_file_sha256,
        contract=contract,
    )
    token = os.environ.get("DRYAD_TOKEN", "") if token is None else str(token)
    if not token or "\n" in token or "\r" in token:
        raise Boreal19ConfirmatoryTransportError(
            "DRYAD_TOKEN is missing or malformed"
        )

    target = contract["response_file"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name("." + destination.name + ".part")
    if destination.exists() or part.exists():
        raise Boreal19ConfirmatoryTransportError(
            "refusing to overwrite prior confirmatory response bytes"
        )

    request = Request(
        target["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-v1.13",
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
        raise Boreal19ConfirmatoryTransportError(
            f"confirmatory response transport failed: {type(exc).__name__}"
        ) from None

    observed_sha = digest.hexdigest()
    if (
        count != target["expected_size_bytes"]
        or observed_sha != target["expected_sha256"]
    ):
        if part.exists():
            part.unlink()
        raise Boreal19ConfirmatoryTransportError(
            "confirmatory response exact-byte verification failed"
        )

    os.replace(part, destination)
    return {
        "schema": "structural.boreal_19island_confirmatory_response_transport.v1_13",
        "status": "EXACT_CONFIRMATORY_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED",
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
        "confirmatory_response_authorized": True,
        "counts_as_empirical_evidence": False,
        "next_action": (
            "invoke the v1.13 one-shot confirmatory scorer exactly once; "
            "transport alone does not consume authorization"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--authorization-freeze",
        type=Path,
        default=DEFAULT_AUTHORIZATION_FREEZE,
    )
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_19island_confirmatory_scoring_contract.v1_13"
        ):
            raise Boreal19ConfirmatoryTransportError(
                "unexpected v1.13 scoring contract schema"
            )
        result = fetch(
            _load(args.authorization),
            _load(args.authorization_freeze),
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
        Boreal19ConfirmatoryTransportError,
    ) as exc:
        result = {
            "schema": (
                "structural.boreal_19island_confirmatory_response_transport.v1_13"
            ),
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "response_semantics_opened": False,
            "authorization_consumed": False,
            "confirmatory_response_authorized": False,
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
