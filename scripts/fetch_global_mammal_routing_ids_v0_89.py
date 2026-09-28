#!/usr/bin/env python3
"""Fetch the exact frozen 5,592-island mammal matrix and expose routing IDs only.

This is a semantic-firewall transport. The whole object is necessarily moved as
opaque bytes and verified against the prospectively frozen physical identity,
but only CSV field 1 of the header and each physical data record is decoded.
Species-header fields and occurrence cells are never decoded or parsed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "development/global_mammals_authenticated_routing_contract_v0_89.json"
INTEGERISH = re.compile(r"^[0-9]+(?:\.0+)?$")


class MammalRoutingError(RuntimeError):
    pass


def _origin(url: str) -> tuple[str, str, int | None]:
    p = urlsplit(url)
    return p.scheme.lower(), (p.hostname or "").lower(), p.port


class StripAuthorizationOnCrossOriginRedirect(HTTPRedirectHandler):
    """Do not forward a Dryad bearer token to object storage."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and _origin(req.full_url) != _origin(newurl):
            redirected.remove_header("Authorization")
        return redirected


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict:
    x = json.loads(path.read_text(encoding="utf-8"))
    if x.get("schema") != "structural.global_mammals_authenticated_routing_contract.v0_89":
        raise MammalRoutingError("unexpected routing contract schema")
    return x


def _clean_token(token: str) -> str:
    token = str(token or "")
    if not token or "\n" in token or "\r" in token:
        raise MammalRoutingError("DRYAD_TOKEN is missing or malformed")
    return token


def _request_json(url: str, token: str, *, opener=None) -> dict:
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-API-Version": "2.1.0",
            "User-Agent": "Structural-v0.89",
        },
    )
    opener = opener or build_opener(StripAuthorizationOnCrossOriginRedirect())
    try:
        with opener.open(req, timeout=120) as response:
            raw = response.read()
    except Exception as exc:
        raise MammalRoutingError(
            f"Dryad manifest request failed: {type(exc).__name__}"
        ) from None
    try:
        out = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MammalRoutingError("Dryad manifest was not valid UTF-8 JSON") from exc
    if not isinstance(out, dict):
        raise MammalRoutingError("Dryad manifest root was not an object")
    return out


def _file_entries(manifest: dict) -> list[dict]:
    embedded = manifest.get("_embedded")
    if isinstance(embedded, dict):
        for key, value in embedded.items():
            if "file" in str(key).lower() and isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    files = manifest.get("files")
    if isinstance(files, list):
        return [x for x in files if isinstance(x, dict)]
    raise MammalRoutingError("Dryad manifest did not expose a file collection")


def _exact_manifest_entry(manifest: dict, spec: dict) -> dict:
    target_path = spec["path"]
    target_size = int(spec["size_bytes"])
    target_sha = spec["sha256"].lower()

    matches = []
    for item in _file_entries(manifest):
        if item.get("path") != target_path:
            continue
        try:
            size = int(item.get("size"))
        except (TypeError, ValueError):
            continue
        digest = str(item.get("digest", "")).lower()
        dtype = str(item.get("digestType", "")).lower().replace("_", "-")
        if size != target_size or digest != target_sha:
            continue
        if dtype and dtype not in {"sha-256", "sha256"}:
            continue
        matches.append(item)

    if len(matches) != 1:
        raise MammalRoutingError(
            f"expected one exact Dryad manifest match, found {len(matches)}"
        )
    item = matches[0]
    links = item.get("_links")
    if not isinstance(links, dict):
        raise MammalRoutingError("matched Dryad file omitted _links")
    download = links.get("stash:download")
    if not isinstance(download, dict) or not isinstance(download.get("href"), str):
        raise MammalRoutingError("matched Dryad file omitted stash:download href")
    return item


def _download_exact(
    entry: dict,
    spec: dict,
    destination: Path,
    token: str,
    *,
    opener=None,
) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    part = destination.with_name("." + destination.name + ".part")
    if part.exists():
        part.unlink()

    href = entry["_links"]["stash:download"]["href"]
    download_url = urljoin(spec["manifest_url"], href)
    headers = {
        "Accept": "application/octet-stream",
        "X-API-Version": "2.1.0",
        "User-Agent": "Structural-v0.89",
    }
    if _origin(download_url) == _origin(spec["manifest_url"]):
        headers["Authorization"] = f"Bearer {token}"
    req = Request(download_url, headers=headers)
    opener = opener or build_opener(StripAuthorizationOnCrossOriginRedirect())

    count = 0
    h = hashlib.sha256()
    try:
        with opener.open(req, timeout=180) as response, part.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                h.update(chunk)
                count += len(chunk)
    except Exception as exc:
        if part.exists():
            part.unlink()
        raise MammalRoutingError(
            f"exact response transport failed: {type(exc).__name__}"
        ) from None

    observed = h.hexdigest()
    if count != int(spec["size_bytes"]) or observed != spec["sha256"].lower():
        if part.exists():
            part.unlink()
        raise MammalRoutingError("downloaded response failed exact byte identity")
    os.replace(part, destination)
    return {"size_bytes": count, "sha256": observed}


def first_csv_field_only(raw_record: bytes) -> bytes:
    """Return field 1 while treating the remainder as opaque bytes."""
    if not raw_record:
        raise MammalRoutingError("empty physical CSV record")
    if raw_record.startswith(b'"'):
        out = bytearray()
        i = 1
        while i < len(raw_record):
            b = raw_record[i]
            if b == 34:
                if i + 1 < len(raw_record) and raw_record[i + 1] == 34:
                    out.append(34)
                    i += 2
                    continue
                i += 1
                if i >= len(raw_record) or raw_record[i] != 44:
                    raise MammalRoutingError(
                        "quoted routing field not followed by CSV delimiter"
                    )
                return bytes(out)
            if b in (10, 13):
                raise MammalRoutingError("newline inside quoted routing field")
            out.append(b)
            i += 1
        raise MammalRoutingError("unterminated quoted routing field")

    pos = raw_record.find(b",")
    if pos < 0:
        raise MammalRoutingError("routing field delimiter not found")
    return raw_record[:pos]


def normalize_routing_id(value: str) -> str:
    value = value.strip()
    if not value:
        raise MammalRoutingError("empty routing ID")
    if INTEGERISH.fullmatch(value):
        whole = value.split(".", 1)[0]
        return str(int(whole))
    return value


def extract_routing_ids(path: Path, expected_rows: int) -> tuple[str, list[str]]:
    ids: list[str] = []
    with path.open("rb") as fh:
        header = fh.readline()
        if not header:
            raise MammalRoutingError("response CSV is empty")
        try:
            header_field = first_csv_field_only(header).decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise MammalRoutingError("routing header is not valid UTF-8") from exc

        for raw_record in fh:
            if raw_record in (b"\n", b"\r\n", b""):
                raise MammalRoutingError("blank physical CSV record")
            try:
                raw_id = first_csv_field_only(raw_record).decode("utf-8")
            except UnicodeDecodeError as exc:
                raise MammalRoutingError("routing ID is not valid UTF-8") from exc
            ids.append(normalize_routing_id(raw_id))

    if len(ids) != expected_rows:
        raise MammalRoutingError(
            f"expected {expected_rows} data rows, observed {len(ids)}"
        )
    if len(set(ids)) != len(ids):
        raise MammalRoutingError("normalized routing IDs are not unique")
    return header_field.strip(), ids


def write_ids(path: Path, ids: list[str]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = ("\n".join(ids) + "\n").encode("utf-8")
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def run(
    raw_path: Path,
    ids_output: Path,
    *,
    contract: dict | None = None,
    token: str | None = None,
    opener=None,
) -> dict:
    contract = load_contract() if contract is None else contract
    token = _clean_token(os.environ.get("DRYAD_TOKEN", "") if token is None else token)
    spec = dict(contract["dryad"])
    spec["manifest_url"] = contract["dryad"]["manifest_url"]

    manifest = _request_json(spec["manifest_url"], token, opener=opener)
    entry = _exact_manifest_entry(manifest, spec)
    transport = _download_exact(entry, spec, raw_path, token, opener=opener)

    header, ids = extract_routing_ids(
        raw_path,
        expected_rows=int(contract["semantic_firewall"]["expected_data_rows"]),
    )
    ids_sha = write_ids(ids_output, ids)

    return {
        "schema": "structural.global_mammals_authenticated_routing_result.v0_89",
        "status": "exact_response_verified_routing_ids_only_semantically_opened",
        "candidate_id": contract["candidate_id"],
        "transport": transport,
        "routing_header_field": header,
        "routing_rows": len(ids),
        "distinct_normalized_routing_ids": len(set(ids)),
        "routing_ids_sha256": ids_sha,
        "species_header_fields_semantically_opened": 0,
        "species_occurrence_cells_semantically_opened": 0,
        "raw_response_may_enter_artifact": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": contract["next_gate"],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--ids-output", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = p.parse_args()

    try:
        result = run(
            args.raw,
            args.ids_output,
            contract=load_contract(args.contract),
        )
        code = 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError,
            MammalRoutingError) as exc:
        result = {
            "schema": "structural.global_mammals_authenticated_routing_result.v0_89",
            "status": "STOP",
            "reason": str(exc),
            "species_header_fields_semantically_opened": 0,
            "species_occurrence_cells_semantically_opened": 0,
            "raw_response_may_enter_artifact": False,
            "counts_as_empirical_evidence": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2

    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
