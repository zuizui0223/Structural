#!/usr/bin/env python3
"""NEON RELEASE-2026 original 3-product beetle/vegetation/temperature overlap.

Products:
  Ground beetle pitfall taxonomic observations DP1.10022.001 (47 sites 2026)
  Woody vegetation structure/tree heights DP1.10098.001
  Single aspirated air temperature tower profiles DP1.00002.001

This reads only NEON official public PRODUCT metadata: original site×months.
Does NOT download species or microclimate time series, infer forest habitat from
siteCode, equate beetle pitfall plots with NEON tower sensors, or claim any
beetle thermal escape, vertical migration, or global biological effect.
"""
from __future__ import annotations

import argparse,datetime,json,re,urllib.error,urllib.request
from collections import Counter
from pathlib import Path

RELEASE="RELEASE-2026"
API="https://data.neonscience.org/api/v0/products/"
ROLES={
    "ground_beetle":"DP1.10022.001",
    "vegetation_structure":"DP1.10098.001",
    "tower_air_temperature_profile":"DP1.00002.001"
}
SOURCE_META={
    "ground_beetle":"https://data.neonscience.org/data-products/DP1.10022.001/RELEASE-2026",
    "vegetation_structure":"https://data.neonscience.org/data-products/DP1.10098.001/RELEASE-2026",
    "tower_air_temperature_profile":"https://data.neonscience.org/data-products/DP1.00002.001/RELEASE-2026"
}


def fetch_product(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":"Structural-ForestBeetle-NEON-product-support/1.0",
        "Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=45) as fd:
        raw=fd.read(10_000_001)
    if len(raw)>10_000_000:
        raise ValueError("NEON_public_product_metadata_unexpectedly_large")
    obj=json.loads(raw)
    if not isinstance(obj,dict) or not isinstance(obj.get("data"),dict):
        raise ValueError("NEON_product_JSON_missing_expected_data_object")
    return obj["data"]


def months_of(s):
    """Return an exact release's original months, not all releases combined."""
    rev=s.get("availableReleases")
    if isinstance(rev,list) and len(rev)>0:
        matched=[q for q in rev if q.get("release")==RELEASE]
        if len(matched)!=1:return set()
        vals=matched[0].get("availableMonths") or []
    else:
        vals=s.get("availableMonths") or []
    if not isinstance(vals,list):raise ValueError("NEON_source_months_not_a_list")
    dates=set()
    for v in vals:
        if not re.fullmatch(r"20[0-9]{2}-(?:0[1-9]|1[0-2])",str(v)):
            raise ValueError("source_NEO_month_timestamp_format_changed")
        dates.add(v)
    return dates


def profile(role,original):
    code=ROLES[role]
    if original.get("productCode")!=code:
        raise ValueError("NEON_source_wrong_product_code:"+role)
    locations=original.get("siteCodes")
    if not isinstance(locations,list):
        raise ValueError("NEON_source_siteCodes_missing:"+role)
    sites={}
    for item in locations:
        site=str(item.get("siteCode") or "").strip()
        if not re.fullmatch(r"[A-Z0-9]{4}",site):
            raise ValueError("NEON_original_site_code_invalid")
        if site in sites:raise ValueError("NEON_siteCode_repeated_in_product")
        m=months_of(item)
        if m:sites[site]=m
    return sites


def analyze(products):
    missing=set(ROLES)-set(products)
    if missing:raise ValueError("three_NEON_sources_not_all_downloaded")
    cohorts={role:profile(role,products[role]) for role in ROLES}
    if any(not v for v in cohorts.values()):
        raise ValueError("empty_product_specific_RELEASE_2026_NEON_site_cohort")
    beetles=set(cohorts["ground_beetle"])
    structures=set(cohorts["vegetation_structure"])
    temperatures=set(cohorts["tower_air_temperature_profile"])
    co=beetles&structures&temperatures
    pairs=beetles&structures
    months_by_site={}
    for site in sorted(co):
        same=cohorts["ground_beetle"][site]&cohorts["vegetation_structure"][site]&cohorts["tower_air_temperature_profile"][site]
        shared_beetle_temp=cohorts["ground_beetle"][site]&cohorts["tower_air_temperature_profile"][site]
        shared_beetle_veg=cohorts["ground_beetle"][site]&cohorts["vegetation_structure"][site]
        months_by_site[site]={
            "siteCode":site,
            "original_beetle_month_count":len(cohorts["ground_beetle"][site]),
            "original_vegetation_month_count":len(cohorts["vegetation_structure"][site]),
            "original_vertical_temperature_month_count":len(cohorts["tower_air_temperature_profile"][site]),
            "beetle_and_tree_structure_months":len(shared_beetle_veg),
            "beetle_and_temperature_months":len(shared_beetle_temp),
            "three_product_same_calendar_months_count":len(same),
            "three_product_common_sample_year_count":len({v[:4] for v in same}),
            "three_product_common_calendar_years":sorted({v[:4] for v in same})
        }
    shared_month_all=sum(x["three_product_same_calendar_months_count"] for x in months_by_site.values())
    anysite=sum(x["three_product_same_calendar_months_count"]>=1 for x in months_by_site.values())
    recurring=sum(x["three_product_common_sample_year_count"]>=2 for x in months_by_site.values())
    output={
        "schema":"structural.NEON_forest_beetle_canopy_temperature_2026_product_metadata_support.v1",
        "original_NEON_release":RELEASE,
        "original_product_codes":ROLES,
        "source_product_names":{role:str(products[role].get("productName") or "") for role in ROLES},
        "NEON_product_site_count_BEFORE_forest_habitat_filter":{
            role:len(v) for role,v in cohorts.items()},
        "site_overlap_beetles_and_vegetation":len(pairs),
        "site_overlap_beetles_and_multilevel_tower_temperature":len(beetles&temperatures),
        "three_product_same_site_source_network_overlap":len(co),
        "site_count_any_common_calendar_month_across_three_products":anysite,
        "site_count_2plus_common_sample_years":recurring,
        "total_three_product_same_site_calendar_months_NOT_forest_replicates":shared_month_all,
        "three_product_candidate_site_by_year_support":list(months_by_site.values()),
        "forest_habitat_species_plot_and_tower_geometry_site_admission_passed":0,
        "original_source_ground_beetles_in_pitfall_NOT_vertical_traps":True,
        "original_source_temperature_profile_is_meteorological_tower_not_insect_movement":True,
        "original_source_woody_structure_and_beetle_plotID_join_not_yet_verified":True,
        "monthly_presence_in_product_catalog_not_sampled_beetles_each_day":True,
        "original_species_and_temperature_response_rows_read":0,
        "forest_macro_effect_or_thermal_escape_evaluated":False,
        "no_sensitive_locations_taxa_or_individuals_exported":True,
        "eBird_used":False
    }
    return output


def run(out,request=fetch_product):
    data={role:request(API+product+"?release="+RELEASE) for role,product in ROLES.items()}
    results=analyze(data)
    d=Path(out);d.mkdir(parents=True,exist_ok=True)
    (d/"NEON_three_product_original_release_site_month_support.json").write_text(
        json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Only aggregate counts to CI log; user can inspect site IDs in artifact.
    for k,v in results.items():
        if k!="three_product_candidate_site_by_year_support":
            print(k,":",json.dumps(v,ensure_ascii=False))
    return results


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.out)
