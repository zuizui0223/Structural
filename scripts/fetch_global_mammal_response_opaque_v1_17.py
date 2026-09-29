#!/usr/bin/env python3
"""Perform the single credentialed opaque-byte transport for global mammals v1.17."""
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
    ROOT / "development/global_mammals_credentialed_opaque_transport_contract_v1_17.json"
)


class GlobalMammalTransportError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalTransportError(
            f"{path.name} must contain a JSON object"
        )
    return value


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port


class StripAuthorizationOnCrossOriginRedirect(HTTPRedirectHandler):
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
    x = _load(path)
    if x.get("schema") != (
        "structural.global_mammals_credentialed_opaque_transport_contract.v1_17"
    ):
        raise GlobalMammalTransportError(
            "unexpected v1.17 transport contract schema"
        )
    if x.get("status") != (
        "ONE_CREDENTIALED_EXACT_TRANSPORT_ATTEMPT_PREDECLARED"
    ):
        raise GlobalMammalTransportError(
            "v1.17 transport contract status drift"
        )
    return x


def transport(
    output_path: Path,
    *,
    contract: dict,
    token: str,
    opener=None,
) -> dict:
    target = contract["target"]
    if not token or "\n" in token or "\r" in token:
        raise GlobalMammalTransportError(
            "DRYAD_TOKEN is missing or malformed"
        )
    if int(contract["attempt_policy"]["credentialed_attempt_limit"]) != 1:
        raise GlobalMammalTransportError("attempt limit is not exactly one")
    if contract["attempt_policy"]["blind_endpoint_retry_authorized"] is not False:
        raise GlobalMammalTransportError("blind endpoint retry became authorized")
    if contract["attempt_policy"]["alternate_file_id_retry_authorized"] is not False:
        raise GlobalMammalTransportError("alternate file-id retry became authorized")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    part = output_path.with_name("." + output_path.name + ".part")
    if output_path.exists() or part.exists():
        raise GlobalMammalTransportError(
            "refusing to overwrite prior response transport bytes"
        )

    request = Request(
        target["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-global-mammals-v1.17",
        },
    )
    opener = opener or build_opener(
        StripAuthorizationOnCrossOriginRedirect()
    )

    digest = hashlib.sha256()
    count = 0
    try:
        with opener.open(request, timeout=180) as response, part.open("wb") as out:
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
        raise GlobalMammalTransportError(
            f"credentialed opaque transport failed: {type(exc).__name__}"
        ) from None

    observed_sha = digest.hexdigest()
    if (
        count != int(target["expected_size_bytes"])
        or observed_sha != target["expected_sha256"]
    ):
        if part.exists():
            part.unlink()
        raise GlobalMammalTransportError(
            "exact byte identity verification failed"
        )

    os.replace(part, output_path)
    return {
        "schema": "structural.global_mammals_opaque_transport_result.v1_17",
        "status": "EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED",
        "candidate_id": contract["candidate_id"],
        "target": {
            "name": target["name"],
            "dryad_file_id": target["dryad_file_id"],
            "size_bytes": count,
            "sha256": observed_sha,
        },
        "response_bytes_read_as_opaque": count,
        "header_decoded": False,
        "routing_ids_decoded": 0,
        "species_header_fields_decoded": 0,
        "occurrence_values_decoded": 0,
        "biological_response_values_opened": False,
        "counts_as_empirical_evidence": False,
        "counts_as_fresh_confirmation": False,
        "raw_response_artifact_authorized": False,
        "semantic_crosswalk_authorized_in_same_revision": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "fresh_system_denominator_contribution": 0,
        "credentialed_attempt_consumed": True,
        "next_action": (
            "commit this exact transport receipt; only a later separate "
            "revision may re-download exact bytes and run the frozen ID-only "
            "semantic crosswalk"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = load_contract(args.contract)
        result = transport(
            args.output_path,
            contract=contract,
            token=os.environ.get("DRYAD_TOKEN", ""),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        GlobalMammalTransportError,
    ) as exc:
        result = {
            "schema": "structural.global_mammals_opaque_transport_result.v1_17",
            "status": "HOLD_NO_RETRY",
            "reason": str(exc),
            "credentialed_attempt_consumed": True,
            "header_decoded": False,
            "routing_ids_decoded": 0,
            "species_header_fields_decoded": 0,
            "occurrence_values_decoded": 0,
            "biological_response_values_opened": False,
            "counts_as_empirical_evidence": False,
            "counts_as_fresh_confirmation": False,
            "raw_response_artifact_authorized": False,
            "semantic_crosswalk_authorized_in_same_revision": False,
            "v0_11_intake_authorized": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "fresh_system_denominator_contribution": 0,
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
