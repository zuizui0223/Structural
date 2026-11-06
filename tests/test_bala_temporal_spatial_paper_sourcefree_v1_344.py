"""BALA original seven-island temporal/spatial source-free paper robustness v1.344."""
import copy,json,math,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_temporal_spatial_paper_sourcefree_v1_344 import analyze

def source():
    def load(path):return json.loads((ROOT/"development"/path).read_text(encoding="utf-8"))
    return (
      load("bala_within_campaign_detection_original_result_freeze_v1_316.json"),
      load("bala_spatial_original_result_freeze_v1_318.json"),
      load("bala_temporal_spatial_cross_axis_sourcefree_protocol_v1_344.json")
    )

def test_seven_island_temporal_positive_and_beetle_loo_spatial_negative():
    first,second,protocol=source()
    r=analyze(first,second,protocol)
    assert r["status"]=="BALA_SEVEN_ISLAND_BEETLE_HOMOGENIZATION_LOO_SOURCEFREE_VALIDATED"
    assert r["original_island_context_n"]==7 and r["original_29_physical_transects"]==29
    beetle=r["source_pitfall_guilds"]["coleoptera"]
    spider=r["source_pitfall_guilds"]["araneae"]
    assert beetle["same_camp_half_sample_temporal_excess_positive_islands"]==7
    assert spider["same_camp_half_sample_temporal_excess_positive_islands"]==7
    assert math.isclose(beetle["island_equal_spatial_simpson_B3_minus_B1"],-0.17530148423005568,abs_tol=1e-14)
    assert math.isclose(spider["island_equal_spatial_simpson_B3_minus_B1"],0.02240713745815786,abs_tol=1e-14)
    assert beetle["source_one_island_delete_negative_count"]==7
    assert beetle["source_one_island_delete_positive_count"]==0
    assert all(v<0 for v in beetle["source_one_island_delete_spatial_simpson_mean"].values())
    assert math.isclose(beetle["source_one_island_delete_spatial_simpson_mean"]["flo"],-0.1111321548821549,abs_tol=1e-10)
    assert beetle["source_islands_homogenizing_despite_mean_local_richness_gain"]==["flo","sjg","smr"]
    assert beetle["recorded_source_half_effort_sensitivity"]["same_spatial_simpson_direction_half_count"]==18

def test_spider_beta_not_robust_and_no_false_seven_island_direction_claim():
    v316,v318,p=source()
    r=analyze(v316,v318,p)
    spider=r["source_pitfall_guilds"]["araneae"]
    assert spider["source_one_island_delete_negative_count"]==2
    assert spider["source_one_island_delete_positive_count"]==5
    assert spider["recorded_source_half_effort_sensitivity"]["same_spatial_simpson_direction_half_count"]==13
    assert spider["source_islands_homogenizing_despite_mean_local_richness_gain"]!=["flo","sjg","smr"]
    assert r["spider_positive_spatial_direction_not_stable_under_every_one_island_deletion"]

def test_all_old_source_response_sealed_and_not_independent_bootstrap():
    v316,v318,p=source()
    r=analyze(v316,v318,p)
    assert r["original_arthropod_Event_or_Occurrence_rows_reopened"]==0
    assert r["prior_v314_v316_v318_one_shot_source_scorers_SEALED"]
    assert r["LOO_and_half_splits_not_independent_ecological_replications"]
    assert r["published_BALA_overall_richness_stability_is_prior_art"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0
    assert not r["eBird_used"]
    assert "scientificName" not in json.dumps(r)

def test_original_source_sha_island_n_and_source_pair_counts_fail_closed():
    v316,v318,p=source()
    bad=copy.deepcopy(v316);bad["original"]["v316_original_inner_JSON_SHA256"]="tampered"
    with pytest.raises(ValueError,match="source field data identity"):
        analyze(bad,v318,p)
    bad=copy.deepcopy(v318);bad["main_pitfall"]["araneae"]["per_island"]["ter"]["dependent_pairs"]+=1
    with pytest.raises(ValueError,match="site and dependent-pair"):
        analyze(v316,bad,p)
    bad=copy.deepcopy(v318);bad["limitations"]["original_v318_scorer_sealed_after_success"]=False
    with pytest.raises(ValueError,match="scorer seal"):
        analyze(v316,bad,p)
