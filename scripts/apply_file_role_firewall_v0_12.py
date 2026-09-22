#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from structural.file_roles import (
    FileRoleFirewallError,
    apply_file_role_firewall,
    assignments_from_mapping,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate file roles against a v0.11 inventory and emit semantic-open allowlist."
    )
    parser.add_argument("inventory", type=Path)
    parser.add_argument("roles", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        role_manifest = json.loads(args.roles.read_text(encoding="utf-8"))
        assignments = assignments_from_mapping(role_manifest)
        result = apply_file_role_firewall(inventory, assignments)
    except (OSError, json.JSONDecodeError, ValueError, FileRoleFirewallError) as exc:
        print(json.dumps({
            "schema": "structural.file_role_firewall.v0_12",
            "status": "STOP",
            "reason": str(exc),
        }, indent=2, sort_keys=True))
        return 2

    payload = {
        "schema": "structural.file_role_firewall.v0_12",
        "status": "role_firewall_complete",
        "allowed_for_semantic_open": list(result.allowed_for_semantic_open),
        "denied_for_semantic_open": list(result.denied_for_semantic_open),
        "response_files": list(result.response_files),
        "unknown_files": list(result.unknown_files),
        "code_files": list(result.code_files),
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
