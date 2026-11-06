"""v1.350 original-source-free pitfall versus lower foliage method audit.

No original 2024 BALA species/host trees/Events reopened.
"""
import copy,json,math,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_sourcefree_ground_foliage_method_audit_v1_350 import assess

def sources():
    d=ROOT/"development"
    return [
        json.loads((d/name).read_text(encoding="utf-8")) for name in (
          "bala_ground_foliage_method_sourcefree_protocol_v1_350.json",
          "bala_within_campaign_detection_original_result_freeze_v1_316.json",
          "bala_spatial_original_result_freeze_v1_318.json")
    ]

def test_known_observed_spider_temporal_and_spatial_contrasts_are_separate():
    r=assess(*sources())
    assert r["status"]=="SOURCE_FREE_BALA_METHOD_SPECIFIC_SPIDER_DESCRIPTIVE_CONTRAST_BEETLE_STOP"
    assert r["original_physical_transects"]==29
    assert r["source_original_equal_per_campaign_sampling_Events"]=={
        "ground_pitfall":781,"foliage_beating":759}
    assert r["field_beating_height_metres_approx"]==[1.5,2.0]
    p=r["spider"]["ground_pitfall"]
    f=r["spider"]["foliage_beating"]
    assert p["eligible_original_temporal_sites"]==29
    assert f["eligible_original_temporal_sites"]==29
    assert p["eligible_original_spatial_sites"]==29
    assert f["eligible_original_spatial_sites"]==29
    assert math.isclose(p["temporal_sorensen_excess"],.19077547226911137,abs_tol=1e-14)
    assert math.isclose(f["temporal_sorensen_excess"],.11194698570877122,abs_tol=1e-14)
    assert math.isclose(p["spatial_simpson_beta_B3_minus_B1"],.02240713745815786,abs_tol=1e-14)
    assert math.isclose(f["spatial_simpson_beta_B3_minus_B1"],-.05791439369620644,abs_tol=1e-14)
    assert math.isclose(r["spider"]["observed_temporal_excess_ground_minus_foliage"],.07882848656034015,abs_tol=1e-14)
    assert math.isclose(r["spider"]["observed_spatial_Simpson_beta_ground_minus_foliage"],.0803215311543643,abs_tol=1e-14)

def test_original_beetle_foliage_scientific_stop_is_not_reinterpreted_as_null():
    r=assess(*sources())
    assert r["beetle"]["foliage_temporal"]=={"status":"SCIENTIFIC_STOP","eligible_sites":13,"effect":None}
    assert r["beetle"]["foliage_spatial"]=={"status":"SCIENTIFIC_STOP","eligible_sites":22,"effect":None}
    assert math.isclose(r["beetle"]["ground_temporal_sorensen_excess"],.22120879931840728,abs_tol=1e-14)
    assert math.isclose(r["beetle"]["ground_spatial_simpson_beta_B3_minus_B1"],-.17530148423005568,abs_tol=1e-14)
    assert r["upper_tree_canopy_height_stratification_not_measured"]
    assert r["sampling_method_and_microhabitat_completely_confound_the_comparison"]
    assert r["host_tree_species_effect_not_tested"]
    assert r["foliage_per_island_uncertainty_and_method_interaction_not_estimable"]
    assert r["no_original_BALA_Event_Occurrence_or_taxon_rows_reopened"]
    assert r["old_v314_v316_v318_biological_scorers_SEALED"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]

def test_any_unauthorized_positive_beetle_foliage_result_is_rejected():
    p,t,s=sources()
    bad=copy.deepcopy(t)
    bad["secondary_beating"]["coleoptera"]["excess_sorensen"]=.02
    with pytest.raises(ValueError,match="hard scientific STOP"):
        assess(p,bad,s)
    bad=copy.deepcopy(s)
    bad["secondary_canopy"]["coleoptera"]["spatial_beta_delta"]=-.5
    with pytest.raises(ValueError,match="hard scientific STOP"):
        assess(p,t,bad)

def test_old_bala_field_source_identity_and_29_site_denominator_fail_closed():
    p,t,s=sources()
    bad=copy.deepcopy(s)
    bad["original_evidence"]["original_result_JSON_SHA256"]="changed"
    with pytest.raises(ValueError,match="source or scientific cohort"):
        assess(p,t,bad)
    bad=copy.deepcopy(t)
    bad["pitfall"]["araneae"]["eligible_original_sites"]=28
    with pytest.raises(AssertionError):
        assess(p,bad,s)
    bad=copy.deepcopy(p)
    bad["firewall"]["new_confirmatory_systems"]=1
    with pytest.raises(ValueError,match="biological holdout|source seal"):
        assess(bad,t,s)
