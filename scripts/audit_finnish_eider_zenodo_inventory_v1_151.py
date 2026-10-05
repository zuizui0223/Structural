#!/usr/bin/env python3
"""Inventory a Zenodo record without downloading any dataset file."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import urllib.request
from pathlib import Path


class Stop(RuntimeError):
    pass


def canonical_file(row: dict) -> dict:
    key = str(row.get("key") or row.get("filename") or "").strip()
    size = row.get("size")
    checksum = str(row.get("checksum") or "").strip()
    links = row.get("links") or {}
    self_url = str(links.get("self") or "").strip()
    content_url = str(links.get("content") or "").strip()

    if not key:
        raise Stop("Zenodo file missing key/name")
    if not isinstance(size, int) or size < 0:
        raise Stop(f"Zenodo file has invalid size: {key}")
    if not checksum:
        raise Stop(f"Zenodo file missing checksum: {key}")

    suffixes = [s.lower() for s in Path(key).suffixes]
    guessed_mime, _ = mimetypes.guess_type(key)

    return {
        "name": key,
        "size_bytes": size,
        "checksum": checksum,
        "suffixes": suffixes,
        "guessed_mime": guessed_mime,
        "metadata_self_url": self_url or None,
        "metadata_content_url": content_url or None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("schema") != "structural.finnish_eider_zenodo_inventory_contract.v1_151":
        raise Stop("contract schema drift")

    url = contract["source"]["api_url"]
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Structural-response-free-schema-audit/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()

    payload = json.loads(raw.decode("utf-8"))
    record_id = int(payload.get("id"))
    if record_id != int(contract["source"]["record_id"]):
        raise Stop("Zenodo record id drift")

    files = [canonical_file(x) for x in payload.get("files", [])]
    files.sort(key=lambda x: x["name"].casefold())
    if not files:
        raise Stop("Zenodo record has no files")

    total_bytes = sum(x["size_bytes"] for x in files)
    names = [x["name"] for x in files]

    lower_names = [n.casefold() for n in names]
    hints = {
        "pos2_name_hits": [n for n in names if "pos2" in n.casefold()],
        "distance_name_hits": [n for n in names if "dist" in n.casefold() or "distance" in n.casefold()],
        "eider_name_hits": [n for n in names if "eider" in n.casefold()],
        "group_or_redistribution_name_hits": [
            n for n in names
            if any(t in n.casefold() for t in ("group", "redistrib", "reconstruct", "imput"))
        ],
        "tabular_file_names": [
            n for n in names
            if Path(n).suffix.casefold() in (".csv", ".tsv", ".txt", ".xlsx", ".xls")
        ],
        "serialized_R_file_names": [
            n for n in names
            if Path(n).suffix.casefold() in (".rdata", ".rda", ".rds")
        ]
    }

    out = {
        "schema": "structural.finnish_eider_zenodo_inventory_result.v1_151",
        "status": "ZENODO_METADATA_ONLY_FILE_INVENTORY_COMPLETE",
        "candidate_id": contract["candidate_id"],
        "record_id": record_id,
        "doi": str(payload.get("doi") or contract["source"]["doi"]),
        "title": str((payload.get("metadata") or {}).get("title") or ""),
        "file_count": len(files),
        "total_file_bytes": total_bytes,
        "files": files,
        "filename_hints": hints,
        "dataset_files_downloaded": 0,
        "dataset_file_bytes_downloaded": 0,
        "response_values_opened": 0,
        "source_loss_events_computed": 0,
        "source_leverage_effects_computed": 0,
        "counts_as_empirical_source_loss_evidence": False,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_sha = hashlib.sha256(args.output.read_bytes()).hexdigest()

    receipt = {
        "schema": "structural.finnish_eider_zenodo_inventory_receipt.v1_151",
        "status": "RESPONSE_FREE_INVENTORY_FROZEN",
        "inventory_sha256": output_sha,
        "file_count": len(files),
        "record_id": record_id,
        "dataset_files_downloaded": 0,
        "response_values_opened": 0,
        "counts_as_empirical_source_loss_evidence": False,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
