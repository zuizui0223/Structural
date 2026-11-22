#!/usr/bin/env python3
"""Verify archived (not actively developed) EOG Structural assets byte-for-byte."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "archive/eog_structural_legacy_20261122/SOURCE_MANIFEST.json"

def blob_sha(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode()+payload).hexdigest()

def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = data["files"]
    if len(files) != 89:
        raise SystemExit("unexpected total source count")
    frozen = [x for x in files if x["preservation"] == "archived_exact"]
    if len(frozen) != 19 or data["matching_canonical"] != 70:
        raise SystemExit("unexpected archival partition")
    for x in frozen:
        p = ROOT / x["location"]
        if not p.is_file():
            raise SystemExit("missing archived historical file: "+x["location"])
        content = p.read_bytes()
        if len(content) != x["bytes"] or blob_sha(content) != x["sha"]:
            raise SystemExit("archived historical file changed: "+x["location"])
    print("PASS: 19 archival files preserved, plus recorded 70 canonical source-matched files")

if __name__ == "__main__":
    main()
