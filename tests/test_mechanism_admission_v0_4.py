from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_mechanism_admission_v0_4 import run


ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/mechanism_admission_v0_4"
STRUCTURAL_QUEUE = ROOT / "tests/fixtures/confirmatory_admission_v0_38/queue.json"
STRUCTURAL_QUEUE_V42 = ROOT / "tests/fixtures/confirmatory_admission_v0_42/queue.json"
TRANSITION = ROOT / "tests/fixtures/mechanism_transition_pilot_v0_2/pilot.csv"
GENPOP = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_populations.csv"
GENPAIR = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_pairs.csv"
ENV = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/environment.csv"


def load_protocol() -> dict:
    return json.loads((FIX / "protocol.json").read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def write_rows(path: Path, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["partition_unit", "block", "z_t", "z_t1"])
        writer.writerows(rows)


def run_all(protocol_path: Path, transition=TRANSITION, environment=ENV):
    return run(
        protocol_path,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=transition,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=environment,
        allow_synthetic_structural_queue=True,
    )


def test_all_four_lanes_admit_only_to_protocol_freeze(tmp_path: Path):
    p = tmp_path / "protocol.json"
    write_json(p, load_protocol())

    code, out = run_all(p)

    assert code == 0
    assert out["status"] == (
        "eligible_to_freeze_selected_confirmatory_mechanism_protocols"
    )
    assert out["eligible_lanes"] == [
        "M1_contemporary_colonization",
        "M2_rescue_persistence",
        "M3_historical_colonization_legacy",
        "M4_environmental_proxy",
    ]
    assert out["ineligible_lanes"] == []
    assert out["eligible_action"] == (
        "freeze_selected_confirmatory_mechanism_protocols_only"
    )
    assert out["confirmatory_response_authorized"] is False
    assert out["mechanism_claim_authorized"] is False
    assert out["effect_size"] is None
    assert out["prediction_score"] is None
    assert out["predictive_denominator_contribution"] == 0
    assert out["mechanism_claim_contribution"] == 0
    assert out["ttf_handoff_authorized"] is False
    assert out["structural_admission"]["synthetic_queue"] is True


def test_synthetic_structural_queue_requires_explicit_ci_flag(tmp_path: Path):
    p = tmp_path / "protocol.json"
    write_json(p, load_protocol())

    code, out = run(
        p,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=False,
    )

    assert code == 2
    assert out["status"] == "STOP_structural_admission_not_replay_validated"
    assert "not eligible as a production mechanism parent after v0.42" in out["reason"]


def test_mechanism_protocol_must_match_structural_queue_entry(tmp_path: Path):
    p = tmp_path / "protocol.json"
    protocol = load_protocol()
    protocol["structural_admission_protocol_fingerprint"] = "0" * 64
    write_json(p, protocol)

    code, out = run_all(p)

    assert code == 2
    assert out["status"] == "STOP_structural_admission_not_replay_validated"
    assert "exactly one replay-validated" in out["reason"]


def test_m1_nonestimable_allows_other_qualified_lanes_to_freeze(tmp_path: Path):
    p = tmp_path / "protocol.json"
    t = tmp_path / "transition.csv"
    write_json(p, load_protocol())
    rows = []
    for block in ("A", "B", "C", "D"):
        rows.extend([
            ["pilot-A", block, 0, 0],
            ["pilot-A", block, 0, 0],
            ["pilot-A", block, 1, 0],
            ["pilot-A", block, 1, 1],
        ])
    write_rows(t, rows)

    code, out = run_all(p, transition=t)

    assert code == 0
    assert out["status"] == (
        "eligible_to_freeze_selected_confirmatory_mechanism_protocols"
    )
    assert "M1_contemporary_colonization" in out["ineligible_lanes"]
    assert set(out["eligible_lanes"]) == {
        "M2_rescue_persistence",
        "M3_historical_colonization_legacy",
        "M4_environmental_proxy",
    }
    assert out["lane_decisions"]["M1_contemporary_colonization"][
        "non_estimable_is_neutral"
    ] is True


def test_m4_nonestimable_allows_m1_m2_m3_to_freeze(tmp_path: Path):
    p = tmp_path / "protocol.json"
    e = tmp_path / "environment.csv"
    write_json(p, load_protocol())
    with e.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["unit_id", "block", "habitat_pc1", "habitat_pc2"])
        for i, block in enumerate(("A", "A", "B", "B", "C", "C"), start=1):
            writer.writerow([f"U{i}", block, 0.1, ""])

    code, out = run_all(p, environment=e)

    assert code == 0
    assert "M4_environmental_proxy" in out["ineligible_lanes"]
    assert set(out["eligible_lanes"]) == {
        "M1_contemporary_colonization",
        "M2_rescue_persistence",
        "M3_historical_colonization_legacy",
    }


def test_confirmatory_partition_exposure_stops_entire_mechanism_admission(
    tmp_path: Path,
):
    p = tmp_path / "protocol.json"
    t = tmp_path / "transition.csv"
    write_json(p, load_protocol())
    write_rows(t, [["confirm-B", "A", 0, 1]])

    code, out = run_all(p, transition=t)

    assert code == 2
    assert out["status"] == "STOP_dynamic_mechanism_protocol_breach"
    assert out["eligible_action"] if "eligible_action" in out else True
    assert out["confirmatory_response_authorized"] is False


def test_response_open_m3_stops_entire_auxiliary_admission(tmp_path: Path):
    p = tmp_path / "protocol.json"
    protocol = load_protocol()
    protocol["auxiliary_estimability"][
        "M3_historical_colonization_legacy"
    ]["genetic_outcomes_accessed"] = True
    write_json(p, protocol)

    code, out = run_all(p)

    assert code == 2
    assert out["status"] == "STOP_auxiliary_mechanism_protocol_breach"
    assert out["mechanism_claim_authorized"] is False


def test_receipt_hashes_raw_gate_inputs(tmp_path: Path):
    p = tmp_path / "protocol.json"
    write_json(p, load_protocol())

    code, out = run_all(p)

    assert code == 0
    hashes = out["input_sha256"]
    assert set(hashes) == {
        "mechanism_protocol",
        "structural_queue",
        "transition_pilot",
        "genetic_populations",
        "genetic_pairs",
        "environment",
    }
    assert all(len(value) == 64 for value in hashes.values())


def test_future_v042_structural_queue_is_valid_mechanism_parent(tmp_path: Path):
    p = tmp_path / "protocol.json"
    write_json(p, load_protocol())

    code, out = run(
        p,
        STRUCTURAL_QUEUE_V42,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
    )

    assert code == 0
    structural = out["structural_admission"]
    assert structural["queue_schema"] == (
        "structural.confirmatory_admission_queue.v0_42"
    )
    assert structural["structural_generation"] == "future_v0_42"
    assert len(structural["structural_quality_contract_fingerprint"]) == 64
    assert out["confirmatory_response_authorized"] is False
    assert out["mechanism_claim_authorized"] is False


def test_historical_v038_cannot_be_used_as_new_production_parent(tmp_path: Path):
    p = tmp_path / "protocol.json"
    q = tmp_path / "queue.json"
    write_json(p, load_protocol())

    historical = json.loads(STRUCTURAL_QUEUE.read_text(encoding="utf-8"))
    historical["status"] = "active_gate_first_queue_with_raw_pilot_replay"
    write_json(q, historical)

    code, out = run(
        p,
        q,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=False,
    )

    assert code == 2
    assert out["status"] == "STOP_structural_admission_not_replay_validated"
    assert "not eligible as a production mechanism parent after v0.42" in out["reason"]
