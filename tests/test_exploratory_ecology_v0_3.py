from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "development/exploratory_ecology_v0_3.json"
H = ROOT / "development/prospective_extreme_isolation_topology_hypothesis_v0_3.json"
RET = ROOT / "development/exploratory_source_artifact_retention_20260923.json"
S = ROOT / "development/exploratory_ecology_v0_3_source_states.csv"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_v03_stays_post_outcome_and_outside_frozen_denominator():
    x = load_json(E)

    assert x["status"] == "post_outcome_hypothesis_generation_only"
    assert x["changes_frozen_structural_paper"] is False
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["counts_as_new_empirical_replication"] is False
    assert x["may_select_future_confirmatory_systems_by_favourable_outcome"] is False
    assert x["analysis_subset"]["selection_uses_candidate_direction"] is False


def test_excess_connectivity_has_exact_predictor_only_graph_meaning():
    x = load_json(E)
    h = x["findings"]["E11_species_specific_excess_connectivity"]

    assert h["rows"] == 15225
    assert h["nonremote_rows_under_frozen_q75_rule"] == 0
    assert h["only_observed_state_pair"]["species_conditioned_eog_frequency"] == 1.0
    assert h["only_observed_state_pair"]["generic_mainland_step_frequency"] == 0.75
    assert h["mainland_distance_range_km"][0] > 70


def test_remote_presence_alignment_is_directionally_strong_but_exploratory():
    x = load_json(E)
    h = x["findings"]["E12_remote_presence_alignment"]

    ex = h["row_level"]["excess_connectivity"]
    no = h["row_level"]["no_excess_connectivity"]

    assert ex["mean_C_minus_R3_log_loss"] < 0
    assert no["mean_C_minus_R3_log_loss"] > 0
    assert ex["favourable_fraction"] > 0.75
    assert no["favourable_fraction"] < 0.5
    assert ex["mean_candidate_minus_reference_probability"] > 0
    assert no["mean_candidate_minus_reference_probability"] < 0

    paired = h["species_paired"]
    assert paired["species_n"] == 155
    assert paired["mean_excess_minus_no_excess"] < 0
    assert paired["wilcoxon_p"] < 1e-10


def test_multihop_state_requires_path_not_direct_source():
    x = load_json(E)
    h = x["findings"]["E13_multihop_stepping_stone_state"]

    assert "nearest occupied training source is farther than 25 km" in h["definition"]

    multi = h["true_presence_rows"]["multihop25"]
    no = h["true_presence_rows"]["not_multihop25"]
    assert multi["mean_C_minus_R3_log_loss"] < 0
    assert no["mean_C_minus_R3_log_loss"] > 0
    assert multi["favourable_fraction"] > 0.75
    assert no["favourable_fraction"] < 0.5

    paired = h["species_paired"]
    assert paired["species_n"] == 211
    assert paired["mean_difference"] < 0
    assert paired["wilcoxon_p"] < 1e-15


def test_v03_refines_but_does_not_replace_extreme_isolation_primary():
    h = load_json(H)

    assert h["primary_hypothesis"]["unchanged_from_v0_2"] is True
    assert "upper 25%" in h["primary_hypothesis"]["extreme_isolation_rule"]
    assert h["predeclared_robustness"]["thresholds"] == [0.70, 0.80]

    excess = h["secondary_source_decoupling_hypothesis"]
    assert excess["primary_role"] is False
    assert excess["may_not_rescue_failed_extreme_isolation_primary"] is True

    multihop = h["secondary_multihop_hypothesis"]
    assert multihop["smallest_scale_must_be_frozen_before_response"] is True
    assert multihop["may_not_choose_scale_after_response"] is True
    assert multihop["primary_role"] is False

    assert h["current_confirmatory_systems"] == []
    assert h["confirmatory_response_authorized"] is False


def test_source_state_csv_preserves_sign_reversal():
    rows = load_csv(S)
    key = {(r["contrast"], r["state"]): r for r in rows}

    ex = key[("remote_true_presence", "excess_species_specific_connectivity")]
    no = key[("remote_true_presence", "no_excess_connectivity")]
    assert float(ex["mean_loss_delta"]) < 0
    assert float(no["mean_loss_delta"]) > 0

    multi = key[("nearest_source_25_100_true_presence", "multihop25")]
    nomulti = key[("nearest_source_25_100_true_presence", "no_multihop25")]
    assert float(multi["mean_loss_delta"]) < 0
    assert float(nomulti["mean_loss_delta"]) > 0


def test_exploratory_source_artifacts_have_verified_private_backups():
    r = load_json(RET)

    assert r["status"] == "verified_private_backups_final_public_archive_pending"
    assert r["public_or_doi_archive"] is False
    assert len(r["artifacts"]) == 3
    assert all(a["drive_roundtrip_sha256_verified"] is True for a in r["artifacts"])
    assert all(len(a["sha256"]) == 64 for a in r["artifacts"])
    assert r["boundary"]["private_backup_is_not_final_release_archive"] is True
    assert r["boundary"]["frozen_scientific_results_changed"] is False
    assert r["boundary"]["final_public_archive_still_required"] is True


def test_claim_ceiling_blocks_movement_and_rescue_overclaim():
    x = load_json(E)
    claims = " ".join(x["claim_ceiling"])

    assert "do not infer realized stepping-stone movement" in claims
    assert "do not claim remote islands are maintained by rescue effects" in claims
    assert "do not treat the 687-species reconstruction subset as a new confirmatory denominator" in claims
    assert "do not change the frozen 75%-tail future primary" in claims
