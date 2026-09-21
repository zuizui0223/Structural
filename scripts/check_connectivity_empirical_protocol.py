#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from structural import AdmissionStatus, evaluate_empirical_admission, protocol_from_mapping


def check(path: Path) -> tuple[int, dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        protocol = protocol_from_mapping(data)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return 1, {
            "status": "invalid_protocol",
            "reasons": [str(exc)],
            "path": str(path),
        }

    decision = evaluate_empirical_admission(protocol)
    payload = {
        "status": decision.status.value,
        "reasons": list(decision.reasons),
        "protocol_id": protocol.protocol_id,
        "system_id": protocol.system_id,
        "path": str(path),
    }
    return (0 if decision.status is AdmissionStatus.QUALIFIED else 2), payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Structural connectivity empirical protocol.")
    parser.add_argument("protocol", type=Path)
    args = parser.parse_args()
    code, payload = check(args.protocol)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
