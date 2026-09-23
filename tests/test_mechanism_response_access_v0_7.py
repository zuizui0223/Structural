from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.record_mechanism_response_access_v0_7 import record_access


ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "tests/fixtures/mechanism_response_authorization_v0_6"
RESP = ROOT / "tests/fixtures/mechanism_response_access_v0_7"
LANE = ROOT / "tests/fixtures/mechanism_confirmatory_freeze_v0_5"
PARENT = ROOT / "tests/fixtures/mechanism_admission_v0_4/protocol.json"
STRUCTURAL_QUEUE = ROOT / "tests/fixtures/confirmatory_admission_v0_38/queue.json"
TRANSITION = ROOT / "tests/fixtures/mechanism_transition_pilot_v0_2/pilot.csv"
GENPOP = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_populations.csv"
GENPAIR = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_pairs.csv"
ENV = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/environment.csv"


def record(name: str, response: Path | None = None):
    return record_access(
        LANE / f"{name}.json",
        AUTH / f"{name}_authorization.json",
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


def write_rows(path: Path, header, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_all_four_lane_responses_record_access_without_scoring():
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
        assert out["predictive_denominator_contribution"] == 0
        assert out["mechanism_claim_contribution"] == 0
        assert out["ttf_handoff_authorized"] is False
        assert out["synthetic_ci_access"] is True
        assert out["counts_as_empirical_evidence"] is False
        assert out["next_action"] == "run_frozen_lane_scoring_only"
        assert len(out["response_file_sha256"]) == 64
        assert len(out["authorization_receipt_sha256"]) == 64
        assert len(out["access_id"]) == 64
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
    assert "may contain only z_t=0 rows" in out["reason"]


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
    assert "may contain only z_t=1 rows" in out["reason"]


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
    assert "unauthorized partition units" in out["reason"]


def test_m3_pair_not_frozen_at_qualification_is_rejected(tmp_path: Path):
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
    assert "pair not frozen at qualification" in out["reason"]


def test_m4_unit_not_in_environment_matrix_is_rejected(tmp_path: Path):
    response = tmp_path / "m4.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "target"],
        [["confirm-B", "A", "UNKNOWN", 1]],
    )

    code, out = record("m4", response)

    assert code == 2
    assert out["status"] == "STOP_invalid_or_unauthorized_response_surface"
    assert "not in frozen environment matrix" in out["reason"]


def test_missing_dynamic_outcome_is_recorded_not_zero_filled(tmp_path: Path):
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
    audit = out["response_audit"]
    assert audit["row_count"] == 2
    assert audit["outcome_nonmissing_rows"] == 1
    assert audit["outcome_missing_rows"] == 1


def test_missing_m4_target_is_recorded_not_zero_filled(tmp_path: Path):
    response = tmp_path / "m4.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "target"],
        [
            ["confirm-B", "A", "U1", 1],
            ["confirm-B", "A", "U2", ""],
        ],
    )

    code, out = record("m4", response)

    assert code == 0
    audit = out["response_audit"]
    assert audit["outcome_nonmissing_rows"] == 1
    assert audit["outcome_missing_rows"] == 1


def test_response_sha_changes_access_identity(tmp_path: Path):
    response = tmp_path / "m1.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "z_t", "z_t1"],
        [["confirm-B", "A", "X", 0, 1]],
    )
    code1, out1 = record("m1", response)
    assert code1 == 0

    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "z_t", "z_t1"],
        [["confirm-B", "A", "X", 0, 0]],
    )
    code2, out2 = record("m1", response)
    assert code2 == 0

    assert out1["response_file_sha256"] != out2["response_file_sha256"]
    assert out1["access_id"] != out2["access_id"]


def test_extra_response_column_is_rejected(tmp_path: Path):
    response = tmp_path / "m4.csv"
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "target", "candidate_prediction"],
        [["confirm-B", "A", "U1", 1, 0.9]],
    )

    code, out = record("m4", response)

    assert code == 2
    assert out["status"] == "STOP_invalid_or_unauthorized_response_surface"
    assert "header must be exactly" in out["reason"]


def test_untracked_authorization_receipt_is_rejected(tmp_path: Path):
    auth = tmp_path / "authorization.json"
    auth.write_text(
        (AUTH / "m1_authorization.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    code, out = record_access(
        LANE / "m1.json",
        auth,
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
    assert out["scoring_authorized"] is False
