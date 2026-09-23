from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.run_mechanism_auxiliary_gate_v0_3 import run


ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3"


def load_protocol() -> dict:
    return json.loads((FIX / "protocol.json").read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def write_csv(path: Path, header, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def run_fixture(tmp_path: Path, protocol=None):
    p = tmp_path / "protocol.json"
    write_json(p, protocol or load_protocol())
    return run(
        p,
        genetic_populations_csv=FIX / "genetic_populations.csv",
        genetic_pairs_csv=FIX / "genetic_pairs.csv",
        environment_csv=FIX / "environment.csv",
    )


def test_balanced_response_blind_auxiliary_design_qualifies_both_lanes(
    tmp_path: Path,
):
    code, out = run_fixture(tmp_path)

    assert code == 0
    assert out["status"] == (
        "qualified_to_freeze_auxiliary_confirmatory_mechanism_protocols"
    )
    assert set(out["qualified_lanes"]) == {
        "M3_historical_colonization_legacy",
        "M4_environmental_proxy",
    }
    assert out["genetic_outcome_opened"] is False
    assert out["confirmatory_response_opened"] is False
    assert out["effect_size"] is None
    assert out["prediction_score"] is None
    assert out["predictive_denominator_contribution"] == 0
    assert out["mechanism_claim_contribution"] == 0
    assert out["confirmatory_response_authorized"] is False


def test_m3_sampling_failure_does_not_block_m4_qualification(tmp_path: Path):
    p = tmp_path / "protocol.json"
    g = tmp_path / "genetic.csv"
    write_json(p, load_protocol())
    write_csv(
        g,
        ["population_id", "block", "role", "sample_n"],
        [
            ["F1", "A", "focal", 6],
            ["F2", "B", "focal", 5],
            ["F3", "C", "focal", 7],
            ["S1", "A", "source", 8],
            ["S2", "B", "source", 2],
            ["S3", "C", "source", 2],
            ["S4", "D", "source", 2],
        ],
    )

    code, out = run(
        p,
        genetic_populations_csv=g,
        genetic_pairs_csv=FIX / "genetic_pairs.csv",
        environment_csv=FIX / "environment.csv",
    )

    assert code == 2
    assert out["status"] == "partial_auxiliary_mechanism_estimability_only"
    by_lane = {row["lane"]: row for row in out["lane_results"]}
    assert by_lane["M3_historical_colonization_legacy"]["qualified"] is False
    assert by_lane["M4_environmental_proxy"]["qualified"] is True
    assert out["qualified_lanes"] == ["M4_environmental_proxy"]


def test_m4_support_failure_does_not_block_m3_qualification(tmp_path: Path):
    p = tmp_path / "protocol.json"
    e = tmp_path / "environment.csv"
    write_json(p, load_protocol())
    write_csv(
        e,
        ["unit_id", "block", "habitat_pc1", "habitat_pc2"],
        [
            ["U1", "A", 0.1, 1.0],
            ["U2", "A", 0.1, ""],
            ["U3", "B", 0.1, ""],
            ["U4", "B", 0.1, ""],
            ["U5", "C", 0.1, ""],
            ["U6", "C", 0.1, ""],
        ],
    )

    code, out = run(
        p,
        genetic_populations_csv=FIX / "genetic_populations.csv",
        genetic_pairs_csv=FIX / "genetic_pairs.csv",
        environment_csv=e,
    )

    assert code == 2
    assert out["status"] == "partial_auxiliary_mechanism_estimability_only"
    by_lane = {row["lane"]: row for row in out["lane_results"]}
    assert by_lane["M3_historical_colonization_legacy"]["qualified"] is True
    assert by_lane["M4_environmental_proxy"]["qualified"] is False
    assert out["qualified_lanes"] == ["M3_historical_colonization_legacy"]


def test_m3_rejects_genetic_outcomes_already_accessed(tmp_path: Path):
    protocol = load_protocol()
    protocol["auxiliary_estimability"][
        "M3_historical_colonization_legacy"
    ]["genetic_outcomes_accessed"] = True

    code, out = run_fixture(tmp_path, protocol)

    assert code == 1
    assert out["status"] == "invalid_or_unqualified_protocol"
    assert "genetic outcomes must remain unopened" in out["reason"]


def test_m3_rejects_sample_selection_using_structural_outcome(tmp_path: Path):
    protocol = load_protocol()
    protocol["auxiliary_estimability"][
        "M3_historical_colonization_legacy"
    ]["sample_selection_used_structural_outcome"] = True

    code, out = run_fixture(tmp_path, protocol)

    assert code == 1
    assert "sample selection may not use Structural outcome direction" in out["reason"]


def test_m4_rejects_predictor_selection_after_response(tmp_path: Path):
    protocol = load_protocol()
    protocol["auxiliary_estimability"][
        "M4_environmental_proxy"
    ]["predictors_selected_after_response"] = True

    code, out = run_fixture(tmp_path, protocol)

    assert code == 1
    assert "selected before response" in out["reason"]


def test_m4_rejects_topology_outcome_selected_predictors(tmp_path: Path):
    protocol = load_protocol()
    protocol["auxiliary_estimability"][
        "M4_environmental_proxy"
    ]["topology_outcome_used_to_select_predictors"] = True

    code, out = run_fixture(tmp_path, protocol)

    assert code == 1
    assert "topology outcome direction" in out["reason"]


def test_m4_rejects_overlap_with_strong_reference(tmp_path: Path):
    protocol = load_protocol()
    protocol["enriched_environment_predictors_if_M4"] = [
        "habitat",
        "habitat_pc2",
    ]

    code, out = run_fixture(tmp_path, protocol)

    assert code == 1
    assert "overlap strong reference" in out["reason"]


def test_genetic_population_surface_rejects_extra_genotype_column(tmp_path: Path):
    p = tmp_path / "protocol.json"
    g = tmp_path / "genetic.csv"
    write_json(p, load_protocol())
    write_csv(
        g,
        ["population_id", "block", "role", "sample_n", "heterozygosity"],
        [["F1", "A", "focal", 6, 0.5]],
    )

    with pytest.raises(ValueError, match="header must be exactly"):
        run(
            p,
            genetic_populations_csv=g,
            genetic_pairs_csv=FIX / "genetic_pairs.csv",
            environment_csv=FIX / "environment.csv",
        )


def test_genetic_pair_surface_rejects_effect_column(tmp_path: Path):
    p = tmp_path / "protocol.json"
    pairs = tmp_path / "pairs.csv"
    write_json(p, load_protocol())
    write_csv(
        pairs,
        [
            "focal_population",
            "source_population",
            "comparison_class",
            "fst",
        ],
        [["F1", "S1", "graph_connected", 0.1]],
    )

    with pytest.raises(ValueError, match="header must be exactly"):
        run(
            p,
            genetic_populations_csv=FIX / "genetic_populations.csv",
            genetic_pairs_csv=pairs,
            environment_csv=FIX / "environment.csv",
        )


def test_environment_surface_rejects_unfrozen_predictor_column(tmp_path: Path):
    p = tmp_path / "protocol.json"
    e = tmp_path / "environment.csv"
    write_json(p, load_protocol())
    write_csv(
        e,
        ["unit_id", "block", "habitat_pc1", "habitat_pc2", "extra_after_outcome"],
        [["U1", "A", 0.1, 1.1, 9]],
    )

    with pytest.raises(ValueError, match="header must be exactly"):
        run(
            p,
            genetic_populations_csv=FIX / "genetic_populations.csv",
            genetic_pairs_csv=FIX / "genetic_pairs.csv",
            environment_csv=e,
        )


def test_environment_missing_values_are_not_zero_filled(tmp_path: Path):
    p = tmp_path / "protocol.json"
    e = tmp_path / "environment.csv"
    write_json(p, load_protocol())
    write_csv(
        e,
        ["unit_id", "block", "habitat_pc1", "habitat_pc2"],
        [
            ["U1", "A", 0.1, 1.1],
            ["U2", "A", 0.2, 1.2],
            ["U3", "B", 0.3, 1.3],
            ["U4", "B", 0.4, 1.4],
            ["U5", "C", 0.5, 1.5],
            ["U6", "C", "", 1.6],
        ],
    )

    code, out = run(
        p,
        genetic_populations_csv=FIX / "genetic_populations.csv",
        genetic_pairs_csv=FIX / "genetic_pairs.csv",
        environment_csv=e,
    )

    assert code == 2
    m4 = {
        row["lane"]: row for row in out["lane_results"]
    }["M4_environmental_proxy"]
    pc1 = {
        row["predictor"]: row for row in m4["predictor_audits"]
    }["habitat_pc1"]
    assert pc1["nonmissing_rows"] == 5
    assert pc1["nonmissing_fraction"] == pytest.approx(5 / 6)
