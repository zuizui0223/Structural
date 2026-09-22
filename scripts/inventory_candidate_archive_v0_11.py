#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from structural.file_inventory import InventoryError, inventory_source, to_mapping


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory a directory or ZIP without parsing file contents."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        result = inventory_source(args.source)
    except (InventoryError, OSError) as exc:
        print(json.dumps({
            "schema": "structural.content_blind_inventory.v0_11",
            "status": "STOP",
            "reason": str(exc),
            "semantic_text_parse_count": 0,
            "response_value_parse_count": 0,
            "model_fit_count": 0,
        }, indent=2, sort_keys=True))
        return 2

    payload = to_mapping(result)
    payload["status"] = "inventory_complete"
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
