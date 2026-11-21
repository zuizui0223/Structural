"""Known-truth NEON original 3-product site and temporal overlap tests."""
import importlib.util
from pathlib import Path
import pytest

p=Path(__file__).with_name("audit_neon_beetle_vegetation_temp_support.py")
spec=importlib.util.spec_from_file_location("neon_forest_beetle_products",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def raw(role,ids,months=("2019-06","2020-06","2021-06")):
    return {
        "productCode":m.ROLES[role],
        "productName":role,
        "siteCodes":[{"siteCode":sid,
                      "availableMonths":["1900-01"],
                      "availableReleases":[
                          {"release":"RELEASE-2025","availableMonths":["2019-01"]},
                          {"release":"RELEASE-2026","availableMonths":list(months)}
                      ]} for sid in ids]
    }


def testsources():
    sites=[f"S{i:03d}" for i in range(52)]
    return {
        "ground_beetle":raw("ground_beetle",sites[:47]),
        "vegetation_structure":raw("vegetation_structure",sites[:42]),
        "tower_air_temperature_profile":raw("tower_air_temperature_profile",sites[5:51]),
    }


def test_overlaps_must_match_both_site_and_calendar_year():
    q=m.analyze(testsources())
    assert q["NEON_product_site_count_BEFORE_forest_habitat_filter"]=={
        "ground_beetle":47,"vegetation_structure":42,
        "tower_air_temperature_profile":46}
    assert q["site_overlap_beetles_and_vegetation"]==42
    assert q["three_product_same_site_source_network_overlap"]==37
    assert q["site_count_any_common_calendar_month_across_three_products"]==37
    assert q["site_count_2plus_common_sample_years"]==37
    assert q["total_three_product_same_site_calendar_months_NOT_forest_replicates"]==111
    assert q["forest_habitat_species_plot_and_tower_geometry_site_admission_passed"]==0
    assert q["original_species_and_temperature_response_rows_read"]==0
    assert q["original_source_ground_beetles_in_pitfall_NOT_vertical_traps"]
    assert q["no_sensitive_locations_taxa_or_individuals_exported"]


def test_different_months_at_same_sites_do_not_make_time_matched_data():
    q=testsources()
    q["vegetation_structure"]=raw("vegetation_structure",
       [f"S{i:03d}" for i in range(42)],months=("2019-02","2020-02","2021-02"))
    x=m.analyze(q)
    assert x["three_product_same_site_source_network_overlap"]==37
    assert x["site_count_any_common_calendar_month_across_three_products"]==0
    assert x["site_count_2plus_common_sample_years"]==0


def test_only_requested_release_months_and_schema_mismatch_fail_closed():
    src=raw("ground_beetle",["S001"])
    assert m.months_of(src["siteCodes"][0])=={"2019-06","2020-06","2021-06"}
    src["siteCodes"][0]["availableReleases"]=[
        {"release":"RELEASE-2025","availableMonths":["2018-01"]}]
    assert m.months_of(src["siteCodes"][0])==set()
    src=testsources()
    src["ground_beetle"]["productCode"]="DP1.00000.001"
    with pytest.raises(ValueError,match="wrong_product_code"):
        m.analyze(src)
