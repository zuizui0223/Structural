from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "development/exploratory_ecology_v0_1.json"
AIS = ROOT / "development/exploratory_ecology_v0_1_aislands_summary.csv"
TAN = ROOT / "development/exploratory_ecology_v0_1_tanzania_summary.csv"
MANIFEST = ROOT / "manuscript/submission/submission_manifest.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_exploratory_layer_cannot_change_frozen_paper_or_denominator():
    x = load_json(RESULT)

    assert x["status"] == "post_outcome_hypothesis_generation_only"
    assert x["changes_frozen_structural_paper"] is False
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["counts_as_new_empirical_replication"] is False
    assert x["may_select_future_confirmatory_systems_by_favourable_outcome"] is False


def test_exploratory_sources_match_frozen_primary_fingerprints():
    x = load_json(RESULT)
    manifest = load_json(MANIFEST)
    frozen = manifest["frozen_evidence"]

    assert (
        x["source_provenance"]["aislands_strong_reference"]["result_fingerprint"]
        == frozen["aislands_strong_reference_result_fingerprint"]
    )
    assert (
        x["source_provenance"]["tanzania_primary"]["result_fingerprint"]
        == frozen["tanzania_result_fingerprint"]
    )


def test_reference_absorption_pattern_is_encoded_without_causal_claim():
    x = load_json(RESULT)
    tiers = x["hypotheses"]["E1_reference_absorption"]["aislands"][
        "prevalence_tertile_mean_log_loss_increments"
    ]

    for group in ("narrow", "mid", "wide"):
        assert tiers[group]["R1_minus_R0"] < 0
        assert tiers[group]["C_minus_R3"] >= 0

    assert (
        x["hypotheses"]["E1_reference_absorption"]["exploratory_status"]
        == "supported_as_cross_system_pattern_but_not_causal_mechanism"
    )


def test_range_saturation_is_island_specific_not_promoted_to_portability():
    x = load_json(RESULT)
    h = x["hypotheses"]["E2_range_source_saturation"]

    bins = h["aislands"]["presence_count_bins"]
    assert bins["61_plus"]["mean_C_minus_R3"] > bins["10_12"]["mean_C_minus_R3"]
    assert bins["61_plus"]["favourable_fraction"] < bins["10_12"]["favourable_fraction"]
    assert abs(h["tanzania"]["occupied_site_count_vs_species_mean_delta"]["spearman_rho"]) < 0.05
    assert h["exploratory_status"] == "supported_in_islands_not_portable_to_tanzania"


def test_extreme_isolation_pattern_keeps_tanzania_confounding_explicit():
    x = load_json(RESULT)
    h = x["hypotheses"]["E3_extreme_isolation_threshold"]

    assert h["aislands"]["mainland_distance_quartile_mean_C_minus_R3"]["Q4_remote"] < 0
    assert (
        h["tanzania"]["distance_to_large_fragment_quartile_mean_delta"]["Q4_farLarge"]
        < 0
    )
    assert "all Q4_farLarge fragments are East Usambara" in h["tanzania"][
        "critical_confounding"
    ]
    assert h["exploratory_status"] == "fresh_prospective_hypothesis_generated_not_confirmed_cross_system"


def test_exclusion_asymmetry_is_not_claimed_spatially_portable():
    x = load_json(RESULT)
    h = x["hypotheses"]["E4_exclusion_constraint_asymmetry"]

    assert h["aislands"]["species_macro_mean_delta_absence"] < 0
    assert h["aislands"]["species_macro_mean_delta_presence"] > 0
    assert h["tanzania_primary_loso"]["species_macro_presence_minus_absence_mean"] > 0
    assert (
        h["tanzania_spatial_block_sensitivity"][
            "species_macro_presence_minus_absence_mean"
        ]
        < 0
    )
    assert h["exploratory_status"] == "strong_in_islands_local_in_tanzania_not_spatially_portable"


def test_summary_tables_retain_expected_directional_rows():
    ais = {row["group"]: row for row in load_csv(AIS)}
    tan = {(row["analysis"], row["group"]): row for row in load_csv(TAN)}

    assert float(ais["presence_count_61_plus"]["mean_delta"]) > 0
    assert float(ais["mainland_distance_Q4_remote"]["mean_delta"]) < 0
    assert float(tan[("primary_loso", "presence")]["mean_delta"]) > float(
        tan[("primary_loso", "absence")]["mean_delta"]
    )
    assert float(tan[("spatial_mst_block", "presence")]["mean_delta"]) < 0


def test_claim_ceiling_forbids_causal_or_confirmatory_promotion():
    x = load_json(RESULT)
    claims = " ".join(x["claim_ceiling"])

    assert "do not claim that EOG estimates colonization probability" in claims
    assert "do not claim that Tanzania confirms the extreme-isolation threshold" in claims
    assert "do not promote any exploratory subgroup result into the frozen paper denominator" in claims
