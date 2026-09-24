from __future__ import annotations

import csv
from pathlib import Path

from scripts.record_mechanism_response_access_v0_7 import record_access


ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "tests/fixtures/mechanism_response_authorization_v0_6"
RESP = ROOT / "tests/fixtures/mechanism_response_access_v0_7"
LANE = ROOT / "tests/fixtures/mechanism_confirmatory_freeze_v0_5"
SCORE = ROOT / "tests/fixtures/mechanism_scoring_input_v0_8"
PARENT = ROOT / "tests/fixtures/mechanism_admission_v0_4/protocol.json"
STRUCTURAL_QUEUE = ROOT / "tests/fixtures/confirmatory_admission_v0_38/queue.json"
TRANSITION = ROOT / "tests/fixtures/mechanism_transition_pilot_v0_2/pilot.csv"
GENPOP = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_populations.csv"
GENPAIR = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_pairs.csv"
ENV = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/environment.csv"


def write_rows(path: Path, header, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def record(name: str, response: Path | None = None):
    return record_access(
        LANE / f"{name}.json",
        AUTH / f"{name}_authorization.json",
        SCORE / f"{name}_scoring_receipt.json",
        SCORE / f"{name}_scoring.csv",
        response or RESP / f"{name}_response.csv",
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_authorization=True,
    )


def test_all_four_tracked_v08_bound_authorizations_record_access():
    expected = {
        "m1": "M1_contemporary_colonization",
        "m2": "M2_rescue_persistence",
        "m3": "M3_historical_colonization_legacy",
        "m4": "M4_environmental_proxy",
    }
    ids = set()

    for name, lane in expected.items():
        code, out = record(name)

        assert code == 0
        assert out["status"] == "confirmatory_mechanism_response_access_recorded"
        assert out["mechanism_lane"] == lane
        assert out["response_access_consumed"] is True
        assert out["confirmatory_response_authorized"] is False
        assert out["scoring_authorized"] is True
        assert out["mechanism_claim_authorized"] is False
        assert out["effect_size"] is None
        assert out["prediction_score"] is None
        assert len(out["authorization_receipt_sha256"]) == 64
        assert len(out["scoring_receipt_sha256"]) == 64
        assert len(out["scoring_input_file_sha256"]) == 64
        assert len(out["scoring_input_key_set_sha256"]) == 64
        assert len(out["response_file_sha256"]) == 64
        ids.add(out["access_id"])

    assert len(ids) == 4


def test_m1_authorization_cannot_open_state1_rows(tmp_path: Path):
    response = tmp_path / "m1.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "z_t", "z_t1"],
        [["confirm-B", "A", "X", 1, 0]],
    )
    code, out = record("m1", response)
    assert code == 2
    assert out["status"] == "STOP_invalid_or_unauthorized_response_surface"


def test_m2_authorization_cannot_open_state0_rows(tmp_path: Path):
    response = tmp_path / "m2.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "z_t", "z_t1"],
        [["confirm-B", "A", "X", 0, 1]],
    )
    code, out = record("m2", response)
    assert code == 2
    assert out["status"] == "STOP_invalid_or_unauthorized_response_surface"


def test_unauthorized_partition_is_rejected(tmp_path: Path):
    response = tmp_path / "m1.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "z_t", "z_t1"],
        [["other-partition", "A", "X", 0, 1]],
    )
    code, out = record("m1", response)
    assert code == 2
    assert out["status"] == "STOP_invalid_or_unauthorized_response_surface"


def test_m3_pair_not_frozen_is_rejected(tmp_path: Path):
    response = tmp_path / "m3.csv"
    write_rows(
        response,
        [
            "partition_unit",
            "focal_population",
            "source_population",
            "comparison_class",
            "genetic_value",
        ],
        [["confirm-B", "F1", "S4", "graph_connected", 0.9]],
    )
    code, out = record("m3", response)
    assert code == 2
    assert out["status"] == "STOP_invalid_or_unauthorized_response_surface"


def test_m4_unknown_unit_is_rejected(tmp_path: Path):
    response = tmp_path / "m4.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "target"],
        [["confirm-B", "A", "UNKNOWN", 1]],
    )
    code, out = record("m4", response)
    assert code == 2
    assert out["status"] == "STOP_invalid_or_unauthorized_response_surface"


def test_missing_outcome_stays_missing(tmp_path: Path):
    response = tmp_path / "m1.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "z_t", "z_t1"],
        [
            ["confirm-B", "A", "X1", 0, 1],
            ["confirm-B", "A", "X2", 0, ""],
        ],
    )
    code, out = record("m1", response)
    assert code == 0
    assert out["response_audit"]["outcome_nonmissing_rows"] == 1
    assert out["response_audit"]["outcome_missing_rows"] == 1


def test_untracked_authorization_receipt_is_rejected(tmp_path: Path):
    auth = tmp_path / "authorization.json"
    auth.write_text(
        (AUTH / "m1_authorization.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    code, out = record_access(
        LANE / "m1.json",
        auth,
        SCORE / "m1_scoring_receipt.json",
        SCORE / "m1_scoring.csv",
        RESP / "m1_response.csv",
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_authorization=True,
    )
    assert code == 2
    assert out["status"] == "STOP_authorization_receipt_not_committed"


def test_tracked_authorization_is_exact_v08_bound_replay():
    code, out = record("m4")
    assert code == 0
    assert out["scoring_receipt_path"] == (
        "tests/fixtures/mechanism_scoring_input_v0_8/m4_scoring_receipt.json"
    )
    assert out["scoring_input_file_sha256"] == (
        "622327857f59a88306707c7097b2d887be88449565646380a52e3b6a19c8b808"
    )
