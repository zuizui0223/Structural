from __future__ import annotations

import csv
from pathlib import Path

from scripts.freeze_mechanism_scoring_input_v0_8 import freeze_scoring_input


ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "tests/fixtures/mechanism_scoring_input_v0_8"
LANE = ROOT / "tests/fixtures/mechanism_confirmatory_freeze_v0_5"
FREEZE = ROOT / "tests/fixtures/mechanism_confirmatory_freeze_v0_5"
PARENT = ROOT / "tests/fixtures/mechanism_admission_v0_4/protocol.json"
STRUCTURAL_QUEUE = ROOT / "tests/fixtures/confirmatory_admission_v0_38/queue.json"
TRANSITION = ROOT / "tests/fixtures/mechanism_transition_pilot_v0_2/pilot.csv"
GENPOP = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_populations.csv"
GENPAIR = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_pairs.csv"
ENV = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/environment.csv"


def freeze_lane(name: str, scoring: Path | None = None):
    return freeze_scoring_input(
        LANE / f"{name}.json",
        FREEZE / f"{name}_receipt.json",
        scoring or SCORE / f"{name}_scoring.csv",
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_freeze_receipt=True,
    )


def write_rows(path: Path, header, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_all_four_scoring_inputs_freeze_before_response():
    expected = {
        "m1": "M1_contemporary_colonization",
        "m2": "M2_rescue_persistence",
        "m3": "M3_historical_colonization_legacy",
        "m4": "M4_environmental_proxy",
    }

    for name, lane in expected.items():
        code, out = freeze_lane(name)

        assert code == 0
        assert out["status"] == "mechanism_scoring_inputs_frozen_before_response"
        assert out["mechanism_lane"] == lane
        assert out["scoring_input_frozen"] is True
        assert out["confirmatory_response_authorized"] is False
        assert out["mechanism_claim_authorized"] is False
        assert out["effect_size"] is None
        assert out["prediction_score"] is None
        assert out["predictive_denominator_contribution"] == 0
        assert out["mechanism_claim_contribution"] == 0
        assert out["ttf_handoff_authorized"] is False
        assert out["synthetic_ci_freeze"] is True
        assert out["counts_as_empirical_evidence"] is False
        assert out["next_action"] == "run_v0_6_response_authorization_only"
        assert len(out["scoring_input_file_sha256"]) == 64
        assert len(out["scoring_input_audit"]["key_set_sha256"]) == 64


def test_dynamic_scoring_surface_rejects_target_column(tmp_path: Path):
    path = tmp_path / "m1.csv"
    write_rows(
        path,
        [
            "partition_unit",
            "block",
            "unit_id",
            "p_reference",
            "p_candidate",
            "target",
        ],
        [["confirm-B", "A", "C1", 0.3, 0.5, 1]],
    )

    code, out = freeze_lane("m1", path)

    assert code == 1
    assert out["status"] == "invalid_input"
    assert "header must be exactly" in out["reason"]


def test_dynamic_probability_boundaries_are_rejected(tmp_path: Path):
    path = tmp_path / "m1.csv"
    write_rows(
        path,
        [
            "partition_unit",
            "block",
            "unit_id",
            "p_reference",
            "p_candidate",
        ],
        [["confirm-B", "A", "C1", 0.0, 1.0]],
    )

    code, out = freeze_lane("m1", path)

    assert code == 1
    assert "strictly between 0 and 1" in out["reason"]


def test_dynamic_scoring_partition_must_equal_response_partition(tmp_path: Path):
    path = tmp_path / "m2.csv"
    write_rows(
        path,
        [
            "partition_unit",
            "block",
            "unit_id",
            "p_reference",
            "p_candidate",
        ],
        [["other", "A", "P1", 0.3, 0.5]],
    )

    code, out = freeze_lane("m2", path)

    assert code == 1
    assert "partitions must equal frozen response partition exactly" in out["reason"]


def test_m3_scoring_design_cannot_drop_frozen_pair(tmp_path: Path):
    path = tmp_path / "m3.csv"
    write_rows(
        path,
        [
            "focal_population",
            "source_population",
            "comparison_class",
            "weight",
        ],
        [
            ["F1", "S1", "graph_connected", 1],
            ["F1", "S2", "alternative", 1],
        ],
    )

    code, out = freeze_lane("m3", path)

    assert code == 1
    assert "exact frozen pair set" in out["reason"]


def test_m3_scoring_design_cannot_add_unfrozen_pair(tmp_path: Path):
    path = tmp_path / "m3.csv"
    write_rows(
        path,
        [
            "focal_population",
            "source_population",
            "comparison_class",
            "weight",
        ],
        [
            ["F1", "S1", "graph_connected", 1],
            ["F1", "S2", "alternative", 1],
            ["F2", "S2", "graph_connected", 1],
            ["F2", "S3", "alternative", 1],
            ["F3", "S3", "graph_connected", 1],
            ["F3", "S4", "alternative", 1],
            ["F1", "S4", "graph_connected", 1],
        ],
    )

    code, out = freeze_lane("m3", path)

    assert code == 1
    assert "unfrozen pair" in out["reason"]


def test_m3_weight_must_be_positive_and_response_blind(tmp_path: Path):
    path = tmp_path / "m3.csv"
    write_rows(
        path,
        [
            "focal_population",
            "source_population",
            "comparison_class",
            "weight",
        ],
        [
            ["F1", "S1", "graph_connected", 1],
            ["F1", "S2", "alternative", 1],
            ["F2", "S2", "graph_connected", 1],
            ["F2", "S3", "alternative", 1],
            ["F3", "S3", "graph_connected", 1],
            ["F3", "S4", "alternative", 0],
        ],
    )

    code, out = freeze_lane("m3", path)

    assert code == 1
    assert "finite and >0" in out["reason"]


def test_m4_scoring_input_rejects_unknown_unit(tmp_path: Path):
    path = tmp_path / "m4.csv"
    write_rows(
        path,
        [
            "partition_unit",
            "block",
            "unit_id",
            "p_original_reference",
            "p_original_topology",
            "p_enriched_reference",
            "p_enriched_topology",
        ],
        [["confirm-B", "A", "UNKNOWN", 0.5, 0.6, 0.5, 0.55]],
    )

    code, out = freeze_lane("m4", path)

    assert code == 1
    assert "not in frozen environment matrix" in out["reason"]


def test_m4_scoring_surface_rejects_target_or_post_response_column(tmp_path: Path):
    path = tmp_path / "m4.csv"
    write_rows(
        path,
        [
            "partition_unit",
            "block",
            "unit_id",
            "p_original_reference",
            "p_original_topology",
            "p_enriched_reference",
            "p_enriched_topology",
            "target",
        ],
        [["confirm-B", "A", "U1", 0.5, 0.6, 0.5, 0.55, 1]],
    )

    code, out = freeze_lane("m4", path)

    assert code == 1
    assert "header must be exactly" in out["reason"]


def test_scoring_file_sha_changes_receipt_identity(tmp_path: Path):
    path = tmp_path / "m1.csv"
    write_rows(
        path,
        ["partition_unit", "block", "unit_id", "p_reference", "p_candidate"],
        [["confirm-B", "A", "C1", 0.3, 0.5]],
    )
    code1, out1 = freeze_lane("m1", path)
    assert code1 == 0

    write_rows(
        path,
        ["partition_unit", "block", "unit_id", "p_reference", "p_candidate"],
        [["confirm-B", "A", "C1", 0.31, 0.5]],
    )
    code2, out2 = freeze_lane("m1", path)
    assert code2 == 0

    assert out1["scoring_input_file_sha256"] != out2["scoring_input_file_sha256"]
