"""NEON public site/year availability: no inferred field forest plots or tower co-location."""
import importlib.util,json
from pathlib import Path
import pytest

src=Path(__file__).with_name("audit_neon_beetle_canopy_temp_product_support.py")
spec=importlib.util.spec_from_file_location("neon_beetles_meta",src)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def make(code, availability):
    sites=[]
    for site,months in sorted(availability.items()):
        sites.append({"siteCode":site,
              "availableMonths":months,
              "availableReleases":[{"release":m.RELEASE,"availableMonths":months}]})
    return {"data":{"productCode":code,"siteCodes":sites}}


def sources():
    return {
        "beetles":make(m.PRODUCTS["beetles"],{
            "HARV":["2018-06","2018-07","2022-06"],
            "SCBI":["2019-05","2020-03"],
            "ABBY":["2021-05"]
        }),
        "vegetation":make(m.PRODUCTS["vegetation"],{
            "HARV":["2018-05","2022-05"],
            "SCBI":["2019-06"],
            "ABBY":["2022-05"]
        }),
        "tower_temp":make(m.PRODUCTS["tower_temp"],{
            "HARV":["2018-06","2022-04"],
            "SCBI":["2019-08","2020-03"],
            "ABBY":["2021-05"]
        })
    }


def test_same_site_year_not_equivalent_to_same_observation_month_or_forest():
    r=m.overlap(sources())
    assert r["NEON_release"]=="RELEASE-2026"
    assert r["beetle_and_vegetation_available_site_years"]==3
    assert r["three_products_available_site_years_any_month"]==3
    assert r["same_site_year_beetle_month_and_tower_temp_month_overlap_sites"]==1
    assert r["same_site_year_beetle_month_and_tower_temp_month_overlap_site_years"]==1
    assert r["candidate_public_NEON_site_codes_NOT_independent_forests"][0]["siteCode"]=="HARV"
    assert r["candidate_public_NEON_site_codes_NOT_independent_forests"][0]["candidate_years"]==[2018]
    assert not r["forest_habitat_confirmed_at_any_candidate_site"]
    assert not r["plot_level_and_sampling_effort_join_verified"]
    assert not r["canopy_ground_beetle_vertical_stratum_test_eligible"]
    assert r["NEON_data_files_or_species_values_read"]==0


def test_api_product_id_release_and_duplicate_months_fail():
    s=sources()
    wrong=make("DP1.99999.001",{"HARV":["2018-06"]})
    with pytest.raises(ValueError,match="product_identity_mismatch"):
        m.site_months(wrong,m.PRODUCTS["beetles"])
    repeated=make(m.PRODUCTS["beetles"],{"HARV":["2018-06","2018-06"]})
    with pytest.raises(ValueError,match="duplicate_month_label"):
        m.site_months(repeated,m.PRODUCTS["beetles"])
    wrong_release=make(m.PRODUCTS["beetles"],{"HARV":["2018-06"]})
    wrong_release["data"]["siteCodes"][0]["availableReleases"][0]["release"]="RELEASE-2024"
    assert m.site_months(wrong_release,m.PRODUCTS["beetles"])["HARV"]==set()


def test_fetch_uses_public_metadata_only_and_never_calls_data_endpoint(tmp_path):
    lookup={m.BASE+code+"?release="+m.RELEASE:sources()[name]
            for name,code in m.PRODUCTS.items()}
    called=[]
    def f(url):
        assert "/products/" in url
        assert "/data/" not in url
        called.append(url)
        return lookup[url]
    q=m.run(tmp_path/"out",fetch=f)
    assert len(called)==3
    assert q["NEON_data_endpoint_access_token_used"] is False
    assert q["tower_temperature_is_not_plot_level_microclimate"]
    result=(tmp_path/"out"/"NEON_2026_three_product_site_years_NOT_forest_plots.json").read_text()
    assert "HARV" in result and "SCBI" not in result
    assert "2018" in result
