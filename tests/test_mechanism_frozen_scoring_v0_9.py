from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.score_mechanism_lane_v0_9 import (
    _score_dynamic,
    _score_m3,
    _score_m4,
    score_lane,
)


ROOT = Path(__file__).resolve().parents[1]
ACCESS = ROOT / "tests/fixtures/mechanism_response_access_v0_7"
RESP = ROOT / "tests/fixtures/mechanism_response_access_v0_7"
LANE = ROOT / "tests/fixtures/mechanism_confirmatory_freeze_v0_5"
SCORE = ROOT / "tests/fixtures/mechanism_scoring_input_v0_8"
PARENT = ROOT / "tests/fixtures/mechanism_admission_v0_4/protocol.json"
STRUCTURAL_QUEUE = ROOT / "tests/fixtures/confirmatory_admission_v0_38/queue.json"
TRANSITION = ROOT / "tests/fixtures/mechanism_transition_pilot_v0_2/pilot.csv"
GENPOP = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_populations.csv"
GENPAIR = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_pairs.csv"
ENV = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/environment.csv"


def score(name: str):
    return score_lane(
        LANE / f"{name}.json",
        ACCESS / f"{name}_access_receipt.json",
        SCORE / f"{name}_scoring_receipt.json",
        SCORE / f"{name}_scoring.csv",
        RESP / f"{name}_response.csv",
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
    )


def write_rows(path: Path, header, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_m1_frozen_score_is_exact_and_no_claim():
    code, out = score("m1")
    assert code == 0
    assert out["status"] == "scored_confirmatory_mechanism_lane_no_claim_adjudication"
    assert out["primary_metric_name"] == "candidate_minus_reference_log_loss"
    assert out["primary_metric"] == pytest.approx(-0.27995362407967816)
    assert out["prediction_score"] == pytest.approx(-0.27995362407967816)
    assert out["effect_size"] is None
    assert out["mechanism_claim_authorized"] is False
    assert out["mechanism_claim_contribution"] == 0
    assert out["adjudication_blockers"] == ["separate_spatial_transfer_not_combined"]
    assert out["synthetic_ci_score"] is True
    assert out["counts_as_empirical_evidence"] is False


def test_m2_scores_extinction_endpoint_not_persistence_label():
    code, out = score("m2")
    assert code == 0
    details = out["metric_details"]
    assert details["target_event"] == "1_to_0"
    assert out["primary_metric"] == pytest.approx(-0.36840909281875966)
    assert details["candidate_mean_log_loss"] < details["reference_mean_log_loss"]
    assert out["mechanism_claim_authorized"] is False


def test_m3_frozen_weighted_contrast_is_scored_without_claim():
    code, out = score("m3")
    assert code == 0
    assert out["primary_metric_name"] == (
        "graph_connected_minus_alternative_genetic_value"
    )
    assert out["primary_metric"] == pytest.approx(0.44)
    assert out["effect_size"] == pytest.approx(0.44)
    assert out["prediction_score"] is None
    assert out["metric_details"]["nonmissing_pairs_by_class"] == {
        "graph_connected": 3,
        "alternative": 3,
    }
    assert out["mechanism_claim_authorized"] is False
    assert "predeclared_geographic_spatial_null_adjudication_not_combined" in (
        out["adjudication_blockers"]
    )


def test_m4_reports_components_but_does_not_invent_practical_null():
    code, out = score("m4")
    assert code == 0
    details = out["metric_details"]
    assert details["mean_log_loss"]["original_reference"] == pytest.approx(
        0.5886015123644734
    )
    assert details["original_topology_increment"] == pytest.approx(
        -0.18775464874626074
    )
    assert details["enriched_topology_increment"] == pytest.approx(
        -0.01762151855209515
    )
    assert details[
        "enriched_reference_minus_original_reference_log_loss"
    ] == pytest.approx(-0.17176166902861473)
    assert out["primary_metric"] == pytest.approx(0.1701331301941656)
    assert "practical_null_interval_not_machine_frozen" in out[
        "adjudication_blockers"
    ]
    assert out["mechanism_claim_authorized"] is False


def test_all_score_receipts_have_unique_deterministic_ids():
    ids = set()
    for name in ("m1", "m2", "m3", "m4"):
        code, out = score(name)
        assert code == 0
        assert len(out["score_id"]) == 64
        ids.add(out["score_id"])
    assert len(ids) == 4


def test_untracked_access_receipt_is_rejected(tmp_path: Path):
    access = tmp_path / "access.json"
    access.write_text(
        (ACCESS / "m1_access_receipt.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    code, out = score_lane(
        LANE / "m1.json",
        access,
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
    )
    assert code == 2
    assert out["status"] == "STOP_access_receipt_not_committed"


def test_dynamic_scorer_rejects_scoring_response_key_mismatch(tmp_path: Path):
    scoring = tmp_path / "score.csv"
    response = tmp_path / "response.csv"
    write_rows(
        scoring,
        ["partition_unit", "block", "unit_id", "p_reference", "p_candidate"],
        [["confirm-B", "A", "C1", 0.3, 0.5]],
    )
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "z_t", "z_t1"],
        [["confirm-B", "A", "OTHER", 0, 1]],
    )
    with pytest.raises(Exception, match="unit sets must match exactly"):
        _score_dynamic(
            scoring,
            response,
            lane="M1_contemporary_colonization",
        )


def test_m3_scorer_rejects_pair_selection_after_response(tmp_path: Path):
    scoring = tmp_path / "score.csv"
    response = tmp_path / "response.csv"
    write_rows(
        scoring,
        ["focal_population", "source_population", "comparison_class", "weight"],
        [
            ["F1", "S1", "graph_connected", 1],
            ["F1", "S2", "alternative", 1],
        ],
    )
    write_rows(
        response,
        [
            "partition_unit",
            "focal_population",
            "source_population",
            "comparison_class",
            "genetic_value",
        ],
        [["confirm-B", "F1", "S1", "graph_connected", 0.8]],
    )
    with pytest.raises(Exception, match="pair sets must match exactly"):
        _score_m3(scoring, response)


def test_m4_scorer_rejects_response_unit_selection(tmp_path: Path):
    scoring = tmp_path / "score.csv"
    response = tmp_path / "response.csv"
    write_rows(
        scoring,
        [
            "partition_unit",
            "block",
            "unit_id",
            "p_original_reference",
            "p_original_topology",
            "p_enriched_reference",
            "p_enriched_topology",
        ],
        [["confirm-B", "A", "U1", 0.4, 0.5, 0.45, 0.46]],
    )
    write_rows(
        response,
        ["partition_unit", "block", "unit_id", "target"],
        [["confirm-B", "A", "U2", 1]],
    )
    with pytest.raises(Exception, match="unit sets must match exactly"):
        _score_m4(scoring, response)
