from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "development/exploratory_ecology_v0_2.json"
H = ROOT / "development/prospective_extreme_isolation_topology_hypothesis_v0_2.json"
SENS = ROOT / "development/exploratory_ecology_v0_2_threshold_sensitivity.csv"
INTERACTIONS = ROOT / "development/exploratory_ecology_v0_2_state_interactions.csv"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_v02_remains_post_outcome_and_nonconfirmatory():
    x = load_json(E)

    assert x["status"] == "post_outcome_hypothesis_generation_only"
    assert x["changes_frozen_structural_paper"] is False
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["counts_as_new_empirical_replication"] is False
    assert x["may_select_future_confirmatory_systems_by_favourable_outcome"] is False


def test_continuous_remoteness_interaction_is_not_an_area_surrogate():
    x = load_json(E)
    h = x["findings"]["E6_continuous_range_by_remoteness"]["aislands"]

    assert h["breadth_x_log_mainland_distance"]["beta"] < 0
    assert h["breadth_x_log_mainland_distance"]["p"] < 0.001

    joint = h["joint_with_breadth_x_log_area"]
    assert joint["breadth_x_log_mainland_distance_beta"] < 0
    assert joint["breadth_x_log_mainland_distance_p"] < 0.001
    assert joint["breadth_x_log_area_p"] > 0.05


def test_tail_interaction_strengthens_without_replacing_primary_threshold():
    rows = load_csv(SENS)
    by_q = {float(row["upper_tail_start_quantile"]): row for row in rows}

    assert float(by_q[0.75]["breadth_x_extreme_beta"]) < 0
    assert float(by_q[0.80]["breadth_x_extreme_beta"]) < float(
        by_q[0.75]["breadth_x_extreme_beta"]
    )

    h = load_json(H)
    assert "upper 25%" in h["primary_hypothesis"]["extreme_isolation_rule"]
    assert h["predeclared_robustness"]["thresholds"] == [0.70, 0.80]
    assert "cannot rescue" in h["predeclared_robustness"]["success_rule"]


def test_state_diagnostic_encodes_presence_penalty_attenuation_not_universal_exclusion():
    x = load_json(E)
    model = x["findings"]["E8_state_dependent_regime_switch"][
        "aislands_two_way_fixed_effect_model"
    ]

    assert model["observed_presence"]["beta"] > 0
    assert model["observed_presence_x_extreme75"]["beta"] < 0
    assert model["observed_presence_x_breadth"]["beta"] > 0
    assert model["observed_presence_x_breadth_x_extreme75"]["beta"] < 0

    corners = x["findings"]["E8_state_dependent_regime_switch"][
        "aislands_descriptive_corner"
    ]
    near = corners["broadest_quartile_presence_rows_near_Q1"]
    remote = corners["broadest_quartile_presence_rows_remote_Q4"]

    assert near["mean_candidate_minus_reference_probability"] < 0
    assert remote["mean_candidate_minus_reference_probability"] > 0
    assert remote["favourable_fraction"] > 0.5
    assert remote["median_loss_increment"] < 0


def test_original_signal_does_not_become_independent_strong_reference_success():
    x = load_json(E)
    h = x["findings"]["E9_original_signal_persistence"]["aislands"]

    assert abs(h["spearman_rho"]) < 0.1
    assert h["conditional_concordance_quartiles"]["Q4"]["mean_C_minus_R3"] >= 0
    assert (
        h["conditional_concordance_quartiles"]["Q4"]["favourable_fraction"]
        < 0.5
    )


def test_tanzania_is_explicitly_not_independent_replication():
    x = load_json(E)
    h = x["findings"]["E10_tanzania_tail_state_check"]

    assert "all East Usambara" in h["all_panel_limitation"]
    assert h["east_usambara_only"]["species_site_fixed_effect_model"][
        "observed_presence_x_extreme75"
    ]["beta"] < 0
    assert h["east_usambara_only"]["continuous_log_distance_model"][
        "observed_presence_x_log_distance_beta"
    ] > 0
    assert h["exploratory_status"] == "weak_analogue_nonmonotonic_and_not_independent_replication"


def test_future_hypothesis_keeps_observed_state_secondary_and_response_blind():
    h = load_json(H)

    assert h["discovery_sources_may_not_count_as_confirmation"] is True
    assert h["candidate_selection_by_discovery_effect_direction"] is False
    assert h["primary_hypothesis"]["threshold_retuning_after_response"] is False
    assert h["secondary_moderation_hypothesis"]["may_not_become_primary_after_outcome"] is True

    state = h["secondary_state_diagnostic"]
    assert state["observed_state_is_post_outcome_diagnostic_only"] is True
    assert state["not_a_deployable_predictor"] is True
    assert state["not_a_primary_success_gate"] is True

    assert h["current_confirmatory_systems"] == []
    assert h["confirmatory_response_authorized"] is False


def test_interaction_table_preserves_exploratory_labels():
    rows = load_csv(INTERACTIONS)

    assert rows
    assert all(row["status"] != "confirmatory" for row in rows)
    assert any(row["status"] == "secondary_diagnostic" for row in rows)
    assert any(row["status"] == "weak_small_panel_diagnostic" for row in rows)
