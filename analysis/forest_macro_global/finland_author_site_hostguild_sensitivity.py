#!/usr/bin/env python3
"""ONE post-result Finland 142-author-site Host_tree physical-site sensitivity.

Original source-only 2022×2023 identity counts, frozen before biological read:
153 source survey columns => exactly 142 author 2023 site-year matches,
10 extra year entries at known source Sites, one unmatched Site (excluded).
No site identifiers, raw taxon/count/trait data or per-site scores exported.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from finland_author_2023_siteyear_source_crosswalk import (
    SOURCE_2022, SOURCE_2023, ScientificStop as IdentityStop,
    pinned, source22_header_only, source23_author_identity_fields_only, compare,
)
from three_region_beetle_host_guild_turnover import (
    read_country, mean_guild_sqrt_js, N_PERM, SEED,
)


class ScientificStop(Exception):
    pass


def author_site_or(meta2022, site2023, source_matrix):
    original_sites = {x[1] for x in site2023}
    if len(original_sites) != 142 or source_matrix.shape[0] != len(meta2022):
        raise ScientificStop("STOP_AUTHOR_SITE_ORIGINAL_METADATA_GRAIN")
    matched = [j for j, row in enumerate(meta2022) if row[1] in original_sites]
    excluded = [j for j, row in enumerate(meta2022) if row[1] not in original_sites]
    if len(matched) != 152 or len(excluded) != 1:
        raise ScientificStop("STOP_SOURCE_ONLY_152_LINKED_ONE_UNLINKED_DRIFT")
    sites = sorted(original_sites)  # private runner only, not exported
    index = {label: j for j, label in enumerate(sites)}
    grouped = np.zeros((len(sites), source_matrix.shape[1]), dtype=np.uint8)
    counts = Counter()
    for j in matched:
        physical = meta2022[j][1]
        grouped[index[physical]] |= source_matrix[j].astype(np.uint8)
        counts[physical] += 1
    if not counts or len(counts) != len(sites):
        raise ScientificStop("STOP_ORIGINAL_AUTHOR_SITE_WITHOUT_LINKED_YEAR")
    if sum(n-1 for n in counts.values()) != 10:
        raise ScientificStop("STOP_ORIGINAL_AUTHOR_SITE_TEN_REPEAT_YEARS_DRIFT")
    return grouped, {
        "source_survey_year_events_author_linked": len(matched),
        "original_unlinked_survey_year_events_excluded_pre_species": len(excluded),
        "independent_source_author_site_keys_from_published_2023_fields": len(sites),
        "linked_author_sites_with_repeat_year_events": sum(v>1 for v in counts.values()),
        "linked_repeated_source_event_excess": sum(n-1 for n in counts.values()),
        "linked_max_source_years_per_site": max(counts.values()),
        "original_author_site_IDs_not_reexported": True,
    }


def known_truth():
    m = np.array([
        [1, 0, 1, 0],
        [0, 1, 1, 0],
        [1, 0, 0, 1],
    ], dtype=np.uint8)
    old = [
        ("2001_SYNTH_A123", "SYNTH_A123", 2001),
        ("2002_SYNTH_A123", "SYNTH_A123", 2002),
        ("2003_SYNTH_B456", "SYNTH_B456", 2003),
    ]
    # Synthetic separate from 142-production gate.
    def generic_or(labels, values):
        groups = sorted(set(labels))
        return np.stack([
            np.bitwise_or.reduce(values[[j for j, x in enumerate(labels) if x==group]],axis=0)
            for group in groups
        ])
    got = generic_or([v[1] for v in old], m)
    assert got.tolist() == [[1,1,1,0],[1,0,0,1]]
    assert np.array_equal(m, np.array([[1,0,1,0],[0,1,1,0],[1,0,0,1]],dtype=np.uint8))
    assert mean_guild_sqrt_js(np.array([[1,1,0],[1,0,1]],dtype=np.uint8),
                              np.array([0,0,1],dtype=int)) > 0
    print("SYNTHETIC_AUTHOR_PHYSICAL_SITE_OR_AND_GUILD_DISTANCE_PASS")


def score(folder: Path):
    pinned(folder / SOURCE_2022[0],SOURCE_2022[1])
    pinned(folder / SOURCE_2023[0],SOURCE_2023[1])
    # All source-site membership selection BEFORE examining biological values.
    source_old = source22_header_only(folder / SOURCE_2022[0])
    source_new = source23_author_identity_fields_only(folder / SOURCE_2023[0])
    source_gate = compare(source_old,source_new)
    expected = {
        "source_2022_original_sample_year_columns":153,
        "source_2022_candidate_unique_non_year_tokens":143,
        "source_2023_author_site_year_rows":142,
        "source_2023_author_unique_Site_fields":142,
        "same_exact_original_year_site_rows_in_both_author_releases":142,
        "2022_sample_year_labels_not_in_2023_author_table":11,
        "2022_sample_years_unmatched_but_Site_known_in_2023":10,
        "2022_unmatched_sample_years_with_Site_not_in_2023":1,
    }
    for key,value in expected.items():
        if source_gate.get(key)!=value:
            raise ScientificStop("STOP_ORIGINAL_PREBIOLOGY_AUTHOR_SITE_CROSSWALK_DRIFT")
    if source_gate["full_original_2022_physical_site_crosswalk_author_verified"]:
        raise ScientificStop("STOP_ONLY_PARTIAL_AUTHOR_SITE_COHORT_ALLOWED")

    # This is the sole biological response-opening point; reuse prior frozen
    # read_country species, Host_tree categories, event eligibility and taxon code.
    matrix, guild_codes, input_diag = read_country(folder, "Finland")
    if matrix is None or matrix.shape[0] != 153 or (
        input_diag["eligible_source_sampling_columns"] != 153
    ):
        raise ScientificStop("STOP_PRIOR_153_SOURCE_EVENT_ELIGIBILITY_DRIFT")
    if matrix.dtype != np.uint8 or np.any((matrix != 0) & (matrix != 1)):
        raise ScientificStop("STOP_ORIGINAL_BEETLE_INCIDENCE_BINARY_CONTRACT")
    physical, source_counts = author_site_or(source_old, source_new, matrix)
    original_species_with_Host_tree = physical.shape[1]
    active = physical.sum(axis=0)>0
    physical = physical[:,active]
    guild_codes = guild_codes[active]
    if physical.shape[0] != 142 or len(guild_codes) < 30:
        raise ScientificStop("STOP_FINLAND_PHYSICAL_SITE_HOSTGUILD_SOURCE_SUPPORT")
    if np.any(physical.sum(axis=1) < 5):
        raise ScientificStop("STOP_AUTHOR_SITE_HOSTGUILD_INCIDENCE_NOT_DEFINED")
    obs = float(mean_guild_sqrt_js(physical,guild_codes))
    if not np.isfinite(obs):
        raise ScientificStop("STOP_AUTHOR_SITE_OBSERVED_JSD_UNDEFINED")
    rng = np.random.default_rng(SEED)
    null = np.array([
        mean_guild_sqrt_js(physical,rng.permutation(guild_codes))
        for _ in range(N_PERM)
    ],dtype=float)
    if np.any(~np.isfinite(null)):
        raise ScientificStop("STOP_AUTHOR_SITE_SHUFFLE_NULL_UNDEFINED")
    null_mean = float(null.mean())
    delta = obs-null_mean
    p = float((1+np.count_nonzero(np.abs(null-null_mean)>=abs(delta)-1e-12))/(N_PERM+1))
    # Deterministic, source-identity-fixed, once-only secondary result.
    return {
        "schema":"structural.Finland2023author_142sites_2022hosttree_postresult_single_sensitivity.v1",
        "status":"COMPLETED_POSTRESULT_AUTHOR_142SITE_SENSITIVITY_CONDITIONAL_NULL",
        "original_source_2022_DOI":"10.5281/zenodo.5950610",
        "author_source_site_2023_DOI":"10.5281/zenodo.8322080",
        "postresult_not_independent_confirmatory":True,
        "source_metadata_142_10_1_verified_before_beetle_rescore":True,
        "original_2022_finland_event_eligibility_153_of_153_preserved":True,
        "excluded_unlinked_event_by_site_identity_not_outcome":True,
        "source_author_site_grain":source_counts,
        "author_142_physical_site_pair_count_NONINDEPENDENT":int(142*141/2),
        "original_hosttree_active_species_before_unlinked_event_exclusion":int(original_species_with_Host_tree),
        "hosttree_active_species_after_author_site_OR_and_source_exclusion":int(len(guild_codes)),
        "observed_sitelevel_hostguild_sqrt_JSD":round(obs,6),
        "trait_label_permutation_null_sitelevel_sqrt_JSD":round(null_mean,6),
        "observed_minus_conditional_null_D":round(delta,6),
        "conditional_null_P":N_PERM,
        "two_sided_conditional_permutation_p":round(p,6),
        "conditional_null_centered_95pct_reference_NOT_sampling_CI":[
            round(float(z),6) for z in np.quantile(null-null_mean,[.025,.975])
        ],
        "old_frozen_Finland_eventlevel_obs_0p117609_and_null_0p082926_UNCHANGED":True,
        "old_frozen_threecountry_D_0p091059_p_0p000333_UNCHANGED":True,
        "no_other_country_physical_site_effect_scored":True,
        "no_forest_host_resource_canopy_microclimate_or_abundance_effect_scored":True,
        "original_source_site_IDs_taxa_env_and_capture_counts_not_reexported":True,
        "source_site_pairwise_pseudoreplication_avoided_in_null":True,
        "sitelevel_conditional_null_not_spatial_cluster_or_population_CI":True,
        "prior_PREDICTS_NEON_BALA_GEB_all_sealed":True,
        "eBird_used":False,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--folder",type=Path)
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    known_truth()
    if a.test:
        return
    if not a.folder or not a.out:
        ap.error("need --folder --out")
    try:
        result=score(a.folder)
    except (ScientificStop,IdentityStop) as err:
        result={
            "schema":"structural.Finland2023author_142sites_2022hosttree_postresult_single_sensitivity.v1",
            "status":str(err),
            "scientific_source_STOP_not_biological_null":True,
            "no_significance_claim_from_STOP":True,
            "old_original_threecountry_guild_score_UNCHANGED":True,
        }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out / "finland_author142_site_hostguild_postresult_sensitivity.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8"
    )
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
