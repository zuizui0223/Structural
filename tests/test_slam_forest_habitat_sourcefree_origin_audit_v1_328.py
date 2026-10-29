"""SLAM v1.328 verified original aggregate only: ecological richness & beta limits.

No v1.327 original SLAM taxon/plot/event data, no BALA/PRIBES data access.
"""
import copy,json,math,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from slam_forest_habitat_sourcefree_origin_audit_v1_328 import audit

def source():
    return (
       json.loads((ROOT/"development/slam_three_island_habitat_source_result_freeze_v1_327.json").read_text(encoding="utf-8")),
       json.loads((ROOT/"development/slam_origin_specific_habitat_sourcefree_audit_protocol_v1_328.json").read_text(encoding="utf-8"))
    )

def test_original_three_island_endemic_positive_altered_intro_richer_and_nonendemic_separate():
    original,protocol=source()
    r=audit(original,protocol)
    assert r["status"]=="SLAM_THREE_ISLAND_FOREST_HABITAT_ORIGIN_SOURCEFREE_AUDITED"
    assert r["source_island_contexts"]==["FLO","PIC","TER"]
    assert r["actual_original_physical_forest_plots_compared"]==33
    assert r["actual_original_source_site_yearquarter_Event_rows"]==664
    a=r["main_arthropods"]
    assert a["original_matched_source_year_quarters_by_island"]=={"FLO":6,"PIC":30,"TER":34}
    assert a["islands_endemic_named_taxa_richer_in_native_forest"]==["FLO","PIC","TER"]
    assert a["islands_introduced_named_taxa_richer_in_altered_forest"]==["FLO","PIC","TER"]
    assert a["islands_native_nonendemic_named_taxa_richer_in_altered_forest"]==["PIC","TER"]
    assert a["islands_positive_origin_habitat_double_contrast"]==["FLO","PIC","TER"]
    assert a["original_positive_double_contrast_source_quarters_n"]==54
    m=a["source_island_equal_mean_original"]
    assert math.isclose(m["endemic_native_minus_altered"],2.3350620675620672,abs_tol=1e-12)
    assert math.isclose(m["native_nonendemic_native_minus_altered"],-0.8516143877908583,abs_tol=1e-12)
    assert math.isclose(m["indigenous_native_minus_altered"],1.483447679771209,abs_tol=1e-12)
    assert math.isclose(m["introduced_native_minus_altered"],-2.514627273597862,abs_tol=1e-12)
    assert math.isclose(m["origin_habitat_double_contrast"],3.9980749533690703,abs_tol=1e-12)
    assert .75<a["overall_positive_double_contrast_fraction_attributable_to_largest_island_absolute_sum"]<.76
    assert a["per_island_source_absolute_richness_differences"]["TER"]["indigenous_native_minus_altered"]<0

def test_secondary_beetle_flo_endemic_exception_and_no_uniform_altered_spatial_sharing():
    d,c=source()
    r=audit(d,c)
    b=r["secondary_coleoptera"]
    assert b["islands_positive_origin_habitat_double_contrast"]==["FLO","PIC","TER"]
    assert b["islands_introduced_named_taxa_richer_in_altered_forest"]==["FLO","PIC","TER"]
    assert b["islands_endemic_named_taxa_richer_in_native_forest"]==["PIC","TER"]
    assert b["per_island_source_absolute_richness_differences"]["FLO"]["endemic_native_minus_altered"]<0
    assert b["original_positive_double_contrast_source_quarters_n"]==59
    assert math.isclose(b["source_island_equal_mean_original"]["origin_habitat_double_contrast"],1.1792996328290446,abs_tol=1e-12)
    assert r["main_arthropods"]["islands_with_greater_within_altered_introduced_taxa_Jaccard_sharing"]==["TER"]
    assert b["islands_with_greater_within_altered_introduced_taxa_Jaccard_sharing"]==["TER"]
    assert r["increased_introduced_richness_in_altered_does_not_imply_uniform_within_habitat_spatial_homogenization"]
    assert r["endemic_vs_nonendemic_native_respond_differently"]

def test_original_one_shot_input_is_sealed_no_reopening_or_causal_promotion():
    d,c=source()
    r=audit(d,c)
    assert r["original_species_rank_status_unclassified_fraction"]<.05
    assert r["original_SLAM_v327_Event_Occurrence_rows_reopened"]==0
    assert r["original_BALA_PRIBES_species_rows_reopened"]==0
    assert r["SLAM_original_scorer_SEALED"]
    assert r["original_source_quarters_repeated_not_70_independent_landscapes"]
    assert r["not_forest_type_randomized_or_causally_identified"]
    assert r["no_actual_immigration_or_true_extinction_measured"]
    assert r["not_independent_multi_archipelago_confirmation"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
    assert "scientificName" not in json.dumps(r)
    assert "original_coreid" not in json.dumps(r)

def test_exact_original_source_sha_species_coverage_and_forest_time_denominators_fail_closed():
    d,c=source()
    bad=copy.deepcopy(d)
    bad["original_source"]["response_original_inner_JSON_SHA256"]="tampered"
    with pytest.raises(ValueError,match="response source identity"):
        audit(bad,c)
    bad=copy.deepcopy(d)
    bad["original_source"]["original_fixed_selected_Event_rows"]=665
    with pytest.raises(ValueError,match="response source identity"):
        audit(bad,c)
    bad=copy.deepcopy(d)
    bad["original_source"]["source_taxonomic_status_coverage"]["species_rank_origin_unclassified_n"]+=1
    with pytest.raises(ValueError,match="taxonomic source response count"):
        audit(bad,c)

def test_tampered_per_island_origin_contrast_and_old_guild_exception_fail_closed():
    d,c=source()
    bad=copy.deepcopy(d)
    bad["main_all_arthropods"]["per_island"]["TER"]["endemic_native_minus_altered"]+=1
    with pytest.raises(ValueError,match="arithmetic changed"):
        audit(bad,c)
    bad=copy.deepcopy(d)
    bad["secondary_Coleoptera"]["per_island"]["FLO"]["endemic_native_minus_altered"]=+.2777777777
    with pytest.raises(ValueError):
        audit(bad,c)
    bad=copy.deepcopy(d)
    bad["main_all_arthropods"]["per_island"]["PIC"]["introduced_source_spatial_jaccard_altered"]=.9
    with pytest.raises(ValueError,match="ecological sign contrasts"):
        audit(bad,c)
    bad=copy.deepcopy(d)
    bad["scientific_status"]["SLAM_original_one_shot_scorer_sealed"]=False
    with pytest.raises(ValueError,match="source one-shot seal"):
        audit(bad,c)
