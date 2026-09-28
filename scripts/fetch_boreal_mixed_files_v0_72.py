#!/usr/bin/env python3
"""Transport the two frozen boreal mixed CSVs without opening their semantics.

The script accepts no arbitrary URL or file id. It reads DRYAD_TOKEN from the
environment, downloads only the exact targets frozen in v0.72, strips
Authorization on cross-origin redirects, verifies byte size and SHA-256, and
stops before decoding any CSV header or data row.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_exact_transport_contract_v0_72.json"
)


class BorealTransportError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), parsed.port


class StripAuthorizationOnCrossOriginRedirect(HTTPRedirectHandler):
    """Never forward Dryad bearer credentials to an object-storage origin."""

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
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != (
        "structural.boreal_lake_islands_exact_transport_contract.v0_72"
    ):
        raise BorealTransportError("unexpected v0.72 transport contract schema")
    return data


def _verify_existing(path: Path, spec: dict) -> bool:
    if not path.exists():
        return False
    if not path.is_file():
        raise BorealTransportError(f"destination is not a file: {path}")
    if path.stat().st_size != int(spec["expected_size_bytes"]):
        raise BorealTransportError(
            f"existing {path.name} has wrong byte size; refusing overwrite"
        )
    if sha256_file(path) != spec["expected_sha256"]:
        raise BorealTransportError(
            f"existing {path.name} has wrong SHA-256; refusing overwrite"
        )
    return True


def _download_one(
    name: str,
    spec: dict,
    output_dir: Path,
    token: str,
    *,
    opener=None,
) -> dict:
    destination = output_dir / name
    if _verify_existing(destination, spec):
        return {
            "file_id": spec["dryad_file_id"],
            "size_bytes": destination.stat().st_size,
            "sha256": spec["expected_sha256"],
            "transport": "reused_existing_exact_file",
        }

    if not token or "\n" in token or "\r" in token:
        raise BorealTransportError("DRYAD_TOKEN is missing or malformed")

    output_dir.mkdir(parents=True, exist_ok=True)
    part = output_dir / f".{name}.part"
    if part.exists():
        part.unlink()

    request = Request(
        spec["download_url"],
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "Structural-v0.72",
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
        # Never surface an HTTP/redirect exception string because it can
        # contain a request or presigned object-storage URL. The exception
        # class is sufficient for an auditable STOP receipt.
        raise BorealTransportError(
            f"{name} transport failed: {type(exc).__name__}"
        ) from None

    observed_sha = digest.hexdigest()
    expected_size = int(spec["expected_size_bytes"])
    expected_sha = spec["expected_sha256"]
    if count != expected_size or observed_sha != expected_sha:
        if part.exists():
            part.unlink()
        raise BorealTransportError(
            f"{name} exact-byte verification failed"
        )

    os.replace(part, destination)
    return {
        "file_id": spec["dryad_file_id"],
        "size_bytes": count,
        "sha256": observed_sha,
        "transport": "downloaded_and_verified",
    }


def transport(
    output_dir: Path,
    *,
    contract: dict | None = None,
    token: str | None = None,
    opener=None,
) -> dict:
    contract = load_contract() if contract is None else contract
    token = os.environ.get("DRYAD_TOKEN", "") if token is None else token

    results = {}
    for name, spec in contract["targets"].items():
        results[name] = _download_one(
            name,
            spec,
            output_dir,
            token,
            opener=opener,
        )

    return {
        "schema": "structural.boreal_lake_islands_exact_transport_result.v0_72",
        "status": "exact_mixed_file_bytes_verified",
        "candidate_id": contract["candidate_id"],
        "files": results,
        "header_decoded": False,
        "data_rows_semantically_opened": 0,
        "safe_row_values_opened": False,
        "biological_response_values_opened": False,
        "model_fit_count": 0,
        "counts_as_empirical_evidence": False,
        "safe_row_projection_authorized": False,
        "v0_11_intake_authorized": False,
        "next_action": (
            "run the v0.71 header-only audit on these exact files; commit the "
            "resulting header SHA/manifests in a separate revision before any "
            "safe-row projection"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = load_contract(args.contract)
        result = transport(args.output_dir, contract=contract)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError,
            BorealTransportError) as exc:
        result = {
            "schema": "structural.boreal_lake_islands_exact_transport_result.v0_72",
            "status": "STOP",
            "reason": str(exc),
            "header_decoded": False,
            "data_rows_semantically_opened": 0,
            "safe_row_values_opened": False,
            "biological_response_values_opened": False,
            "counts_as_empirical_evidence": False,
            "safe_row_projection_authorized": False,
            "v0_11_intake_authorized": False,
        }
        code = 2
    except Exception as exc:
        # Network/HTTP exceptions are deliberately reduced to type only so a
        # redirect URL or request metadata cannot leak into the receipt.
        result = {
            "schema": "structural.boreal_lake_islands_exact_transport_result.v0_72",
            "status": "STOP_transport_error",
            "error_type": type(exc).__name__,
            "header_decoded": False,
            "data_rows_semantically_opened": 0,
            "safe_row_values_opened": False,
            "biological_response_values_opened": False,
            "counts_as_empirical_evidence": False,
            "safe_row_projection_authorized": False,
            "v0_11_intake_authorized": False,
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
