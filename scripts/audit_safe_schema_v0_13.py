#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from structural.safe_schema import (
    SafeSchemaAuditError,
    audit_safe_schema,
    requests_from_mapping,
    to_mapping,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit headers/ID-time structure of v0.12 SAFE_SCHEMA tables only."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("roles", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        roles = json.loads(args.roles.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        requests = requests_from_mapping(plan)
        entries = audit_safe_schema(args.source, inventory, roles, requests)
    except (OSError, json.JSONDecodeError, SafeSchemaAuditError) as exc:
        print(json.dumps({
            "schema": "structural.safe_schema_audit.v0_13",
            "status": "STOP",
            "reason": str(exc),
            "response_files_opened": 0,
            "code_files_opened": 0,
            "unknown_files_opened": 0,
            "model_fit_count": 0,
        }, indent=2, sort_keys=True))
        return 2

    payload = to_mapping(entries)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
