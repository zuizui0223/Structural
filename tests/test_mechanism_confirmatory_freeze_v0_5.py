from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.freeze_mechanism_confirmatory_protocol_v0_5 import freeze


ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/mechanism_confirmatory_freeze_v0_5"
PARENT = ROOT / "tests/fixtures/mechanism_admission_v0_4/protocol.json"
STRUCTURAL_QUEUE = ROOT / "tests/fixtures/confirmatory_admission_v0_38/queue.json"
TRANSITION = ROOT / "tests/fixtures/mechanism_transition_pilot_v0_2/pilot.csv"
GENPOP = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_populations.csv"
GENPAIR = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_pairs.csv"
ENV = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/environment.csv"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def freeze_lane(path: Path):
    return freeze(
        path,
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
    )


def test_all_four_lane_protocols_freeze_response_sealed():
    expected = {
        "m1.json": "M1_contemporary_colonization",
        "m2.json": "M2_rescue_persistence",
        "m3.json": "M3_historical_colonization_legacy",
        "m4.json": "M4_environmental_proxy",
    }
    fingerprints = set()

    for filename, lane in expected.items():
        code, out = freeze_lane(FIX / filename)

        assert code == 0
        assert out["status"] == (
            "frozen_confirmatory_mechanism_protocol_response_still_sealed"
        )
        assert out["mechanism_lane"] == lane
        assert out["confirmatory_response_authorized"] is False
        assert out["mechanism_claim_authorized"] is False
        assert out["effect_size"] is None
        assert out["prediction_score"] is None
        assert out["predictive_denominator_contribution"] == 0
        assert out["mechanism_claim_contribution"] == 0
        assert out["ttf_handoff_authorized"] is False
        assert out["eligible_next_action"] == (
            "run_separate_lane_response_authorization_gate_only"
        )
        assert len(out["protocol_fingerprint"]) == 64
        fingerprints.add(out["protocol_fingerprint"])

    assert len(fingerprints) == 4


def test_parent_fingerprints_are_bound_from_replayed_admission():
    code, out = freeze_lane(FIX / "m1.json")

    assert code == 0
    assert len(out["parent_mechanism_protocol_fingerprint"]) == 64
    assert out["parent_structural_protocol_fingerprint"] == (
        "def335af364183f05562e18ffb432a7ff123c00e9477b2822fcb85885abaf29d"
    )


def test_wrong_parent_binding_mode_is_rejected(tmp_path: Path):
    x = load(FIX / "m1.json")
    x["parent_binding_mode"] = "manual_old_receipt"
    p = tmp_path / "m1.json"
    write(p, x)

    code, out = freeze_lane(p)

    assert code == 2
    assert out["status"] == "STOP_invalid_confirmatory_mechanism_protocol"
    assert "parent_binding_mode" in out["reason"]


def test_response_open_protocol_is_rejected(tmp_path: Path):
    x = load(FIX / "m2.json")
    x["confirmatory_response_accessed"] = True
    p = tmp_path / "m2.json"
    write(p, x)

    code, out = freeze_lane(p)

    assert code == 2
    assert "response must remain unopened" in out["reason"]


def test_protocol_selected_after_response_is_rejected(tmp_path: Path):
    x = load(FIX / "m1.json")
    x["protocol_selected_after_response"] = True
    p = tmp_path / "m1.json"
    write(p, x)

    code, out = freeze_lane(p)

    assert code == 2
    assert "may not be selected after response" in out["reason"]


def test_m1_transition_semantics_cannot_be_swapped(tmp_path: Path):
    x = load(FIX / "m1.json")
    x["lane_specific"]["transition_target"] = "1_to_0"
    p = tmp_path / "m1.json"
    write(p, x)

    code, out = freeze_lane(p)

    assert code == 2
    assert "M1 transition_target must be 0_to_1" in out["reason"]


def test_m2_transition_semantics_cannot_be_swapped(tmp_path: Path):
    x = load(FIX / "m2.json")
    x["lane_specific"]["transition_non_event"] = "0_to_0"
    p = tmp_path / "m2.json"
    write(p, x)

    code, out = freeze_lane(p)

    assert code == 2
    assert "M2 transition_non_event must be 1_to_1" in out["reason"]


def test_dynamic_response_partition_must_match_parent_freeze(tmp_path: Path):
    x = load(FIX / "m1.json")
    x["response_partition"] = ["some-other-confirmatory-partition"]
    p = tmp_path / "m1.json"
    write(p, x)

    code, out = freeze_lane(p)

    assert code == 2
    assert "must equal frozen mechanism confirmatory partition" in out["reason"]


def test_m3_genetic_outcome_must_still_be_unopened(tmp_path: Path):
    x = load(FIX / "m3.json")
    x["lane_specific"]["genetic_outcome_accessed"] = True
    p = tmp_path / "m3.json"
    write(p, x)

    code, out = freeze_lane(p)

    assert code == 2
    assert "genetic outcome must remain unopened" in out["reason"]


def test_m4_enriched_predictor_list_cannot_drift(tmp_path: Path):
    x = load(FIX / "m4.json")
    x["lane_specific"]["enriched_predictors"].append("new_after_qualification")
    p = tmp_path / "m4.json"
    write(p, x)

    code, out = freeze_lane(p)

    assert code == 2
    assert "must exactly match frozen parent list" in out["reason"]


def test_unqualified_lane_cannot_be_frozen(tmp_path: Path):
    t = tmp_path / "transition.csv"
    with t.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["partition_unit", "block", "z_t", "z_t1"])
        for block in ("A", "B", "C", "D"):
            writer.writerows([
                ["pilot-A", block, 0, 0],
                ["pilot-A", block, 0, 0],
                ["pilot-A", block, 1, 0],
                ["pilot-A", block, 1, 1],
            ])

    code, out = freeze(
        FIX / "m1.json",
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=t,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
    )

    assert code == 2
    assert out["status"] == "STOP_invalid_confirmatory_mechanism_protocol"
    assert "was not admitted by v0.4" in out["reason"]


def test_scoring_rule_is_part_of_protocol_fingerprint(tmp_path: Path):
    base = load(FIX / "m1.json")
    changed = load(FIX / "m1.json")
    changed["scoring_rule"] = (
        "different scoring rule that would be illegal after response"
    )
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    write(p1, base)
    write(p2, changed)

    code1, out1 = freeze_lane(p1)
    code2, out2 = freeze_lane(p2)

    assert code1 == code2 == 0
    assert out1["protocol_fingerprint"] != out2["protocol_fingerprint"]


def test_receipt_binds_lane_specific_qualification_inputs():
    expected = {
        "m1.json": {"lane_protocol", "mechanism_protocol", "structural_queue", "transition_pilot"},
        "m2.json": {"lane_protocol", "mechanism_protocol", "structural_queue", "transition_pilot"},
        "m3.json": {"lane_protocol", "mechanism_protocol", "structural_queue", "genetic_populations", "genetic_pairs"},
        "m4.json": {"lane_protocol", "mechanism_protocol", "structural_queue", "environment"},
    }

    for filename, keys in expected.items():
        code, out = freeze_lane(FIX / filename)
        assert code == 0
        assert set(out["input_sha256"]) == keys
        assert all(len(value) == 64 for value in out["input_sha256"].values())
