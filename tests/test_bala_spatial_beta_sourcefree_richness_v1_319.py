"""v1.319 original response-free BALA seven-island spatial beta/richness audit."""
import copy
import json
import math
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_spatial_beta_sourcefree_richness_v1_319 import calculate

def source():
    return (
        json.loads((ROOT/"development/bala_spatial_original_result_freeze_v1_318.json").read_text(encoding="utf-8")),
        json.loads((ROOT/"development/bala_spatial_beta_sourcefree_synthesis_protocol_v1_319.json").read_text(encoding="utf-8")),
    )

def test_beetle_homogenization_on_several_islands_despite_alpha_increases():
    d,c=source()
    r=calculate(d,c)
    assert r["status"]=="SOURCE_FREE_SPATIAL_GUILD_HETEROGENEITY_AND_ALPHA_DECOUPLING_RECONCILED"
    b=r["main_pitfall"]["coleoptera"]
    assert b["independent_forest_transects"]==28
    assert b["dependent_source_pairs"]==49
    assert math.isclose(b["island_equal_spatial_simpson_delta"],-0.17530148423005568,abs_tol=1e-14)
    assert math.isclose(b["island_equal_spatial_sorensen_delta"],-0.12375995060963788,abs_tol=1e-14)
    assert b["islands_homogenizing_spatial_simpson"]==4
    assert b["islands_differentiating_spatial_simpson"]==3
    assert b["islands_homogenizing_while_mean_local_richness_increased"]==["flo","sjg","smr"]
    assert b["source_half_split_simpson_same_sign_n_of_18"]==18
    assert b["source_half_split_sorensen_same_sign_n_of_18"]==18
    assert b["per_island"]["flo"]["mean_site_observed_richness_B1"]==5.
    assert b["per_island"]["flo"]["mean_site_observed_richness_B3"]==8.25
    assert b["per_island"]["flo"]["observed_island_gamma_change"]==2
    assert b["per_island"]["smr"]["mean_site_observed_richness_change"]==3.
    assert b["per_island"]["sjg"]["mean_site_observed_richness_change"]==.75

def test_spider_weak_differentiation_and_guild_discordance_are_kept():
    d,c=source()
    r=calculate(d,c)
    a=r["main_pitfall"]["araneae"]
    assert a["independent_forest_transects"]==29
    assert a["dependent_source_pairs"]==56
    assert math.isclose(a["island_equal_spatial_simpson_delta"],0.02240713745815786,abs_tol=1e-14)
    assert math.isclose(a["island_equal_spatial_sorensen_delta"],0.04871232695717752,abs_tol=1e-14)
    assert a["islands_differentiating_spatial_simpson"]==4
    assert a["islands_homogenizing_spatial_simpson"]==3
    assert a["islands_differentiating_while_mean_local_richness_decreased"]==["fai","flo","smr"]
    assert a["source_half_split_simpson_same_sign_n_of_18"]==13
    assert a["source_half_split_sorensen_same_sign_n_of_18"]==17
    assert r["islands_spider_and_beetle_opposite_simpson_spatial_direction"]==["flo","pic","smr"]
    assert a["islands_Simpson_and_Sorensen_sign_disagreement"]==["fai"]
    assert r["main_pitfall"]["coleoptera"]["islands_Simpson_and_Sorensen_sign_disagreement"]==["fai"]
    assert r["canopy_beetle_spatial_delta_scientifically_STOPPED"]
    assert math.isclose(r["canopy_spider_spatial_delta_simpson"],-0.05791439369620644,abs_tol=1e-14)

def test_source_free_original_scorers_sealed_and_no_false_causality():
    d,c=source()
    r=calculate(d,c)
    assert r["original_BALA_Event_or_Occurrence_rows_reopened"]==0
    assert r["no_new_partitions_no_models_no_p_values"]
    assert r["source_9_hash_salts_times_two_halves_not_independent"]
    assert r["prior_v314_v316_v318_original_scorers_SEALED"]
    assert r["not_causally_explained_by_richness_or_invasive_species"]
    assert r["no_biological_species_extinction_colonization_or_rescue_inferred"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
    assert "scientificName" not in json.dumps(r)
    assert "source_coreid" not in json.dumps(r)

def test_original_source_sha_pair_counts_and_secondary_stop_are_fail_closed():
    d,c=source()
    wrong=copy.deepcopy(d)
    wrong["original_evidence"]["original_result_JSON_SHA256"]="different"
    with pytest.raises(ValueError,match="source-observed site numeric evidence identity"):
        calculate(wrong,c)
    wrong=copy.deepcopy(d)
    wrong["main_pitfall"]["araneae"]["per_island"]["ter"]["delta_spatial_simpson"]=.42
    with pytest.raises(ValueError,match="source spatial beta"):
        calculate(wrong,c)
    wrong=copy.deepcopy(d)
    wrong["secondary_canopy"]["coleoptera"]["status"]="OBSERVED_WITHIN_ISLAND_SPATIAL_BETA_CHANGE"
    with pytest.raises(ValueError,match="scientific STOP"):
        calculate(wrong,c)
    wrong=copy.deepcopy(d)
    wrong["main_pitfall"]["coleoptera"]["per_island"]["fai"]["matched_physical_sites"]+=1
    with pytest.raises(ValueError,match="site/pair sums"):
        calculate(wrong,c)
