#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from structural import OperatorConnectivityState, scalar_insufficiency_witness

FIXTURE = ROOT / "benchmarks/connectivity_scalar_insufficiency_v0_1.json"


def run() -> dict:
    cfg = json.loads(FIXTURE.read_text(encoding="utf-8"))
    a = OperatorConnectivityState(tuple(cfg["state_a"].items()))
    b = OperatorConnectivityState(tuple(cfg["state_b"].items()))
    witness = scalar_insufficiency_witness(
        a,
        b,
        cfg["declared_endpoint_operator"],
    )
    return {
        "schema": cfg["schema"],
        "collapsed_mean_a": a.collapsed_mean,
        "collapsed_mean_b": b.collapsed_mean,
        "operator": witness.operator,
        "transition_a": witness.transition_a,
        "transition_b": witness.transition_b,
        "transition_difference": witness.transition_difference,
        "conclusion": "collapsed_connectivity_not_transition_sufficient_for_declared_operator",
    }


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
