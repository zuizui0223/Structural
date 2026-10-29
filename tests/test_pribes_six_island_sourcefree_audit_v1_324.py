"""v1.324 original PRIBES and BALA source-free negative control tests."""
import copy,json,math,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from pribes_six_island_sourcefree_audit_v1_324 import audit

def source():
    return (json.loads((ROOT/"development/pribes_ruderal_external_source_result_freeze_v1_323.json").read_text(encoding="utf-8")),
            json.loads((ROOT/"development/pribes_external_source_sourcefree_audit_protocol_v1_324.json").read_text(encoding="utf-8")))

def test_six_island_primary_non_support_and_native_equal_control():
    original,contract=source()
    r=audit(original,contract)
    assert r["status"]=="SOURCE_FREE_INDEPENDENT_PRIBES_SOURCE_POOL_NON_SUPPORT_RECONFIRMED"
    p=r["cross_source_exact_rank_correlation"]
    assert math.isclose(p["introduced_beetle"]["spearman_rho"],1/7,abs_tol=1e-12)
    assert math.isclose(p["introduced_beetle"]["one_sided_positive_association_permutation_p"],289/720,abs_tol=1e-12)
    assert math.isclose(p["introduced_beetle"]["two_sided_absolute_association_permutation_p"],578/720,abs_tol=1e-12)
    assert p["introduced_beetle"]["exact_island_label_permutations"]==720
    assert p["native_endemic_beetle"]["spearman_rho"]==p["introduced_beetle"]["spearman_rho"]
    assert p["native_endemic_beetle"]["one_sided_positive_association_permutation_p"]==p["introduced_beetle"]["one_sided_positive_association_permutation_p"]
    assert math.isclose(p["introduced_spider"]["spearman_rho"],3/35,abs_tol=1e-12)
    assert not r["introduced_specific_vs_native_control_stronger"]
    assert not r["introduced_source_mechanism_exploratorily_supported"]

def test_source_original_six_island_standards_and_time_confounds_are_exact():
    original,contract=source()
    r=audit(original,contract)
    assert r["total_independent_standardized_ruderal_sites"]==72
    assert r["original_PRIBES_1hour_site_range"]==[6,24]
    assert len(r["source_introduced_Beetle_island_order_values"])==6
    assert r["six_overlap_source_islands"]==["FAI","FLO","PIC","TER","SMG","SMR"]
    assert math.isclose(r["source_introduced_Beetle_site_Jaccard_range"][0],0.10601095993953136)
    assert math.isclose(r["source_introduced_Beetle_site_Jaccard_range"][1],0.35555555555555557)
    assert math.isclose(r["source_and_response_survey_year_confound_rhos"]["intro_beetle_source_similarity_vs_survey_year"],-0.44136741475237473)
    assert math.isclose(r["source_and_response_survey_year_confound_rhos"]["BALA_forest_beetle_homogenization_vs_survey_year"],-0.3530939318018998)
    assert r["different_methods_and_survey_years_not_reconciled"]
    assert r["six_islands_not_six_independent_archipelagos"]

def test_original_biological_sources_sealed_and_no_causal_promotion():
    o,c=source()
    r=audit(o,c)
    assert r["no_original_BALA_or_PRIBES_Event_Occurrence_rows_reopened"]
    assert r["old_PRIBES_v321_scientific_STOP_and_v323_source_seal_preserved"]
    assert r["actual_species_movement_across_habitats_not_observed"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0
    assert not r["eBird_used"]
    assert "scientificName" not in json.dumps(r)
    assert "original_coreid" not in json.dumps(r)

def test_original_SHA_six_island_membership_and_72_site_count_fail_closed():
    d,c=source()
    bad=copy.deepcopy(d)
    bad["original"]["original_v323_result_JSON_SHA256"]="tampered"
    with pytest.raises(ValueError,match="source identity mismatch"):
        audit(bad,c)
    bad=copy.deepcopy(d)
    bad["original_independent_PRIBES_onehour_source_islands"]["FAI"]["sites"]+=1
    with pytest.raises(ValueError,match="site counts"):
        audit(bad,c)
    bad=copy.deepcopy(d)
    del bad["original_independent_PRIBES_onehour_source_islands"]["FLO"]
    with pytest.raises(ValueError,match="six overlapping islands"):
        audit(bad,c)
    bad=copy.deepcopy(d)
    bad["evidence_ceiling"]["original_PRIBES_v323_scorer_SEALED"]=False
    with pytest.raises(ValueError,match="scorer seal"):
        audit(bad,c)
