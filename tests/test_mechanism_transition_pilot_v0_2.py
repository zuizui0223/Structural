from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.run_mechanism_transition_pilot_v0_2 import run


ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/mechanism_transition_pilot_v0_2"


def load_protocol() -> dict:
    return json.loads((FIX / "protocol.json").read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def write_rows(path: Path, rows, header=None) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            header or ["partition_unit", "block", "z_t", "z_t1"]
        )
        writer.writerows(rows)


def balanced_rows():
    rows = []
    for block in ("A", "B", "C", "D"):
        rows.extend([
            ["pilot-A", block, 0, 0],
            ["pilot-A", block, 0, 1],
            ["pilot-A", block, 1, 0],
            ["pilot-A", block, 1, 1],
        ])
    return rows


def test_balanced_burned_pilot_qualifies_both_lanes_without_effect_output(
    tmp_path: Path,
):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    write_json(p, load_protocol())
    write_rows(c, balanced_rows())

    code, out = run(p, c)

    assert code == 0
    assert out["status"] == "qualified_to_freeze_confirmatory_mechanism_protocol"
    lanes = {row["lane"]: row for row in out["lane_audits"]}
    assert lanes["M1_contemporary_colonization"]["qualified"] is True
    assert lanes["M2_rescue_persistence"]["qualified"] is True
    assert out["transition_counts"] == {
        "0_to_0": 4,
        "0_to_1": 4,
        "1_to_0": 4,
        "1_to_1": 4,
    }
    assert out["effect_size"] is None
    assert out["prediction_score"] is None
    assert out["predictive_denominator_contribution"] == 0
    assert out["mechanism_claim_contribution"] == 0
    assert out["confirmatory_response_authorized"] is False
    assert out["next_action"] == "freeze_separate_confirmatory_mechanism_protocol_only"


def test_colonization_collapse_does_not_block_estimable_persistence_lane(
    tmp_path: Path,
):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    write_json(p, load_protocol())
    rows = []
    for block in ("A", "B", "C", "D"):
        rows.extend([
            ["pilot-A", block, 0, 0],
            ["pilot-A", block, 0, 0],
            ["pilot-A", block, 1, 0],
            ["pilot-A", block, 1, 1],
        ])
    write_rows(c, rows)

    code, out = run(p, c)

    assert code == 2
    assert out["status"] == "partial_mechanism_estimability_only"
    lanes = {row["lane"]: row for row in out["lane_audits"]}
    assert lanes["M1_contemporary_colonization"]["qualified"] is False
    assert lanes["M2_rescue_persistence"]["qualified"] is True
    assert out["mechanism_claim_contribution"] == 0
    assert out["next_action"] == "do_not_open_confirmatory_mechanism_response"


def test_extinction_collapse_does_not_block_estimable_colonization_lane(
    tmp_path: Path,
):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    write_json(p, load_protocol())
    rows = []
    for block in ("A", "B", "C", "D"):
        rows.extend([
            ["pilot-A", block, 0, 0],
            ["pilot-A", block, 0, 1],
            ["pilot-A", block, 1, 1],
            ["pilot-A", block, 1, 1],
        ])
    write_rows(c, rows)

    code, out = run(p, c)

    assert code == 2
    assert out["status"] == "partial_mechanism_estimability_only"
    lanes = {row["lane"]: row for row in out["lane_audits"]}
    assert lanes["M1_contemporary_colonization"]["qualified"] is True
    assert lanes["M2_rescue_persistence"]["qualified"] is False


def test_confirmatory_partition_exposure_stops_immediately(tmp_path: Path):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    write_json(p, load_protocol())
    write_rows(c, [["confirm-B", "A", 0, 1]])

    code, out = run(p, c)

    assert code == 2
    assert out["status"] == "STOP_confirmatory_partition_exposed"
    assert out["effect_size"] is None
    assert out["mechanism_claim_contribution"] == 0
    assert out["confirmatory_response_authorized"] is False


def test_unfrozen_partition_exposure_stops(tmp_path: Path):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    write_json(p, load_protocol())
    write_rows(c, [["other", "A", 0, 1]])

    code, out = run(p, c)

    assert code == 2
    assert out["status"] == "STOP_unfrozen_partition_unit"


def test_missing_transition_is_non_estimable_not_absence(tmp_path: Path):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    write_json(p, load_protocol())
    rows = balanced_rows()
    rows.append(["pilot-A", "A", "", ""])
    write_rows(c, rows)

    code, out = run(p, c)

    assert code == 0
    assert out["applicable_rows"] == 16
    assert out["non_estimable_rows"] == 1
    assert out["transition_counts"]["0_to_0"] == 4
    assert out["transition_counts"]["1_to_0"] == 4


def test_extra_column_is_rejected_from_burned_pilot_surface(tmp_path: Path):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    write_json(p, load_protocol())
    write_rows(
        c,
        [["pilot-A", "A", 0, 1, 0.99]],
        header=["partition_unit", "block", "z_t", "z_t1", "topology_score"],
    )

    with pytest.raises(ValueError, match="header must be exactly"):
        run(p, c)


def test_reordered_columns_are_rejected(tmp_path: Path):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    write_json(p, load_protocol())
    write_rows(
        c,
        [["A", "pilot-A", 0, 1]],
        header=["block", "partition_unit", "z_t", "z_t1"],
    )

    with pytest.raises(ValueError, match="header must be exactly"):
        run(p, c)


def test_m1_only_protocol_does_not_require_m2_to_qualify(tmp_path: Path):
    p = tmp_path / "protocol.json"
    c = tmp_path / "pilot.csv"
    protocol = load_protocol()
    protocol["mechanism_lanes_authorized"] = [
        "M1_contemporary_colonization",
        "M3_historical_colonization_legacy",
        "M4_environmental_proxy",
    ]
    write_json(p, protocol)
    rows = []
    for block in ("A", "B", "C", "D"):
        rows.extend([
            ["pilot-A", block, 0, 0],
            ["pilot-A", block, 0, 1],
            ["pilot-A", block, 1, 1],
        ])
    write_rows(c, rows)

    code, out = run(p, c)

    assert code == 0
    lanes = {row["lane"]: row for row in out["lane_audits"]}
    assert lanes["M1_contemporary_colonization"]["requested"] is True
    assert lanes["M1_contemporary_colonization"]["qualified"] is True
    assert lanes["M2_rescue_persistence"]["requested"] is False


def test_protocol_minima_are_bound_into_fingerprint(tmp_path: Path):
    p1 = tmp_path / "p1.json"
    p2 = tmp_path / "p2.json"
    c = tmp_path / "pilot.csv"
    one = load_protocol()
    two = load_protocol()
    two["dynamic_estimability"]["minimum_train_transition_counts"]["0_to_1"] = 3
    write_json(p1, one)
    write_json(p2, two)
    write_rows(c, balanced_rows())

    _, out1 = run(p1, c)
    _, out2 = run(p2, c)

    assert out1["protocol_fingerprint"] != out2["protocol_fingerprint"]
