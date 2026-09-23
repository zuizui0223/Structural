from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "development/exploratory_ecology_v0_4.json"
F = ROOT / "development/exploratory_ecology_freeze_v0_4.json"
CSV = ROOT / "development/exploratory_ecology_v0_4_reference_gap.csv"
STATUS = ROOT / "development/current_status_v0_41.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_v04_is_reference_gap_discovery_not_new_confirmation():
    x = load_json(E)

    assert x["status"] == "post_outcome_hypothesis_generation_only"
    assert x["changes_frozen_structural_paper"] is False
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["counts_as_new_empirical_replication"] is False
    assert x["may_select_future_confirmatory_systems_by_favourable_outcome"] is False
    assert x["model"]["candidate_C_used_as_response"] is False
    assert x["model"]["candidate_C_used_to_define_predictor_state"] is False


def test_source_decoupling_marks_positive_r3_reference_gap():
    x = load_json(E)
    remote = x["findings"]["E15_reference_gap_source_decoupling"]["remote_panel"]

    assert remote["excess_connectivity"]["beta"] > 0
    assert remote["excess_connectivity"]["p"] < 1e-5
    assert remote["continuous_source_minus_generic"]["beta"] > 0
    assert remote["continuous_source_minus_generic"]["p"] < 1e-6
    assert remote["multihop25"]["beta"] > 0
    assert remote["multihop25"]["p"] < 1e-4


def test_path_state_survives_nearest_source_adjustment():
    x = load_json(E)
    adj = x["findings"]["E16_reference_gap_not_nearest_source_distance"][
        "remote_panel_adjusted_for_log_nearest_source"
    ]

    assert adj["excess_connectivity"]["beta"] > 0
    assert adj["excess_connectivity"]["p"] < 0.01
    assert adj["continuous_source_minus_generic"]["beta"] > 0
    assert adj["continuous_source_minus_generic"]["p"] < 1e-8
    assert adj["multihop25"]["beta"] > 0
    assert adj["multihop25"]["p"] < 0.01


def test_direct_neighbor_is_retained_as_non_detected_boundary():
    x = load_json(E)
    direct = x["findings"]["E15_reference_gap_source_decoupling"][
        "remote_panel"
    ]["direct_source_within_25km"]

    assert direct["beta"] > 0
    assert direct["p"] > 0.05


def test_spatial_fold_robustness_keeps_non_detected_fold5_visible():
    x = load_json(E)
    h = x["findings"]["E17_spatial_fold_robustness"]

    assert h["remote_fold_2"]["excess_beta"] > 0
    assert h["remote_fold_2"]["excess_p"] < 1e-6
    assert h["remote_fold_4"]["excess_beta"] > 0
    assert h["remote_fold_4"]["excess_p"] < 0.001

    assert h["remote_fold_5"]["excess_rows"] == 148
    assert h["remote_fold_5"]["excess_p"] > 0.05


def test_reference_gap_table_preserves_exploratory_and_boundary_labels():
    rows = load_csv(CSV)
    assert rows
    assert all(row["status"] != "confirmatory" for row in rows)
    assert any(row["status"] == "boundary_not_detected" for row in rows)
    assert any(row["status"] == "spatial_robustness" for row in rows)


def test_exploratory_discovery_is_frozen_after_v04():
    f = load_json(F)

    assert f["status"] == "frozen_post_outcome_discovery"
    assert f["latest_interpretive_layer"] == "development/exploratory_ecology_v0_4.json"
    assert f["prospective_hypothesis"] == "development/prospective_extreme_isolation_topology_hypothesis_v0_3.json"
    assert "search additional A-Islands thresholds for a more favourable effect" in f[
        "forbidden_after_freeze"
    ]
    assert "mine additional Tanzania region/trait/fragment subsets to manufacture replication" in f[
        "forbidden_after_freeze"
    ]
    assert f["current_confirmatory_systems"] == []
    assert f["confirmatory_response_authorized"] is False


def test_current_status_points_to_frozen_v04_discovery_lane():
    s = load_json(STATUS)
    e = s["post_outcome_exploratory_ecology"]

    assert e["path"] == "development/exploratory_ecology_v0_4.json"
    assert e["status"] == "frozen_at_v0.4"
    assert e["freeze"] == "development/exploratory_ecology_freeze_v0_4.json"
    assert e["counts_as_confirmatory_evidence"] is False
    assert e["changes_frozen_paper"] is False
    assert e["fresh_hypothesis"] == "development/prospective_extreme_isolation_topology_hypothesis_v0_3.json"
