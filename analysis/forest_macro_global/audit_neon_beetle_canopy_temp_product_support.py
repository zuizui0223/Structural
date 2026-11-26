#!/usr/bin/env python3
"""NEON RELEASE-2026 public METADATA-only three-product temporal support audit.

Products:
  DP1.10022.001 ground beetle pitfall, 2018+ same three-traps-per-plot design
  DP1.10098.001 field measured vegetation structure (not necessarily forest)
  DP1.00002.001 tower multi-height aspirated air temperature (not beetle plot)

This *does not* download insects, species, temperatures, tree plot coordinates
or infer a thermal refuge. It computes public site×year data availability
only. Three products sharing a SITE/YEAR does NOT prove same physical plot,
forest habitat, trap effort or same air temperatures. NEON /data endpoints
require auth; this uses only no-token /products endpoint.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections import Counter,defaultdict
from pathlib import Path

BASE="https://data.neonscience.org/api/v0/products/"
RELEASE="RELEASE-2026"
PRODUCTS={
    "beetles":"DP1.10022.001",
    "vegetation":"DP1.10098.001",
    "tower_temp":"DP1.00002.001"
}
YEARS=set(range(2018,2024))
USER_AGENT={"User-Agent":"Structural-NEON-Public-Product-Availability-Source-Only/1.0",
            "Accept":"application/json"}


def acquire(code, *, fetch=None):
    if code not in PRODUCTS.values():raise ValueError("source_product_not_predeclared")
    url=BASE+code+"?release="+RELEASE
    if fetch:return fetch(url)
    req=urllib.request.Request(url,headers=USER_AGENT)
    with urllib.request.urlopen(req,timeout=40) as f:
        data=f.read(3_000_001)
    if len(data)>3_000_000:raise ValueError("source_product_metadata_response_exceeds_cap")
    return json.loads(data)


def month(value):
    txt=str(value or "")
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])",txt):
        raise ValueError("NEON_invalid_year_month_format")
    return int(txt[:4]),int(txt[5:])


def site_months(payload,expected):
    data=payload.get("data")
    if not isinstance(data,dict):
        raise ValueError("NEON_response_missing_data_object")
    if data.get("productCode")!=expected:
        raise ValueError("NEON_response_product_identity_mismatch")
    sites=data.get("siteCodes")
    if not isinstance(sites,list) or not sites:
        raise ValueError("NEON_no_public_product_siteCodes")
    out={}
    for item in sites:
        site=str(item.get("siteCode") or "").strip()
        if not re.fullmatch(r"[A-Z0-9]{4}",site):
            raise ValueError("NEON_invalid_public_site_code")
        if site in out:raise ValueError("NEON_duplicate_source_site_code")
        from_release=item.get("availableReleases") or []
        if from_release:
            exact=[r for r in from_release if r.get("release")==RELEASE]
            if len(exact)!=1:
                # Public release-specific API can list other releases.
                # An absent target release is an empty set, not invented data.
                months=[]
            else:
                months=exact[0].get("availableMonths") or []
        else:
            # The /products endpoint was requested with an explicit release.
            months=item.get("availableMonths") or []
        if len(months)!=len(set(months)):
            raise ValueError("NEON_duplicate_month_label_within_site")
        out[site]={month(x) for x in months}
    return out


def overlap(originals):
    if set(originals)!=set(PRODUCTS):raise ValueError("missing_three_predeclared_products")
    src={k:site_months(originals[k],PRODUCTS[k]) for k in PRODUCTS}
    candidate_years=defaultdict(set)
    beetle_months=Counter()
    temp_months=Counter()
    vegetation_years=Counter()
    source_years={}
    for typ,sites in src.items():
        valid={(s,y) for s,months in sites.items() for y,m in months if y in YEARS}
        source_years[typ]=valid
    three=source_years["beetles"] & source_years["vegetation"] & source_years["tower_temp"]
    b_with_v=source_years["beetles"] & source_years["vegetation"]
    all_bsites={s for s,y in source_years["beetles"]}
    common_month=[]
    matched_year_count=Counter()
    for site,y in sorted(three):
        B={m for yr,m in src["beetles"][site] if yr==y}
        T={m for yr,m in src["tower_temp"][site] if yr==y}
        overlap_months=B&T
        if overlap_months:
            candidate_years[site].add(y)
            matched_year_count[y]+=1
            common_month.append((site,y,len(overlap_months)))
    supported_sites=set(candidate_years)
    per_year=[{"year":y,
          "beetle_vegetation_temperature_any_month_candidate_sites":matched_year_count[y],
          "beetle_vegetation_coavailability_sites":sum(yr==y for _,yr in b_with_v),
          "beetle_site_months_matching_tower_temp_month":sum(
              n for s,yr,n in common_month if yr==y)}
        for y in sorted(YEARS)]
    per_site=[{"siteCode":site,"candidate_years":sorted(candidate_years[site]),
               "source_beetle_TOWER_month_overlap_n":sum(n for s,y,n in common_month if s==site),
               "field_forest_habitat_confirmed":False,
               "beetle_and_tower_colocated_at_same_plot":False}
        for site in sorted(supported_sites)]
    return {
        "schema":"structural.neon_2026_forest_beetle_vegetation_tower_public_metadata_gate.v1",
        "NEON_release":RELEASE,
        "source_products":PRODUCTS,
        "study_years_metadata_only":sorted(YEARS),
        "source_sites_with_any_2018_2023_release_product_months":{
            k:len({s for s,y in vals}) for k,vals in source_years.items()},
        "source_site_years_with_any_month_in_2018_2023":{
            k:len(vals) for k,vals in source_years.items()},
        "beetle_and_vegetation_available_site_years":len(b_with_v),
        "three_products_available_site_years_any_month":len(three),
        "same_site_year_beetle_month_and_tower_temp_month_overlap_sites":len(supported_sites),
        "same_site_year_beetle_month_and_tower_temp_month_overlap_site_years":len(common_month),
        "candidate_year_availability":per_year,
        "candidate_public_NEON_site_codes_NOT_independent_forests":per_site,
        "source_original_2018_ground_beetle_protocol_changed_from_four_to_three_traps_per_plot":True,
        "vegetation_product_is_not_forest_only":True,
        "tower_temperature_is_not_plot_level_microclimate":True,
        "NEON_data_files_or_species_values_read":0,
        "forest_habitat_confirmed_at_any_candidate_site":False,
        "plot_level_and_sampling_effort_join_verified":False,
        "canopy_ground_beetle_vertical_stratum_test_eligible":False,
        "thermal_refuge_or_temperature_effect_scored":False,
        "NEON_data_endpoint_access_token_used":False,
        "eBird_used":False
    }


def run(out, *, fetch=None):
    originals={k:acquire(code,fetch=fetch) for k,code in PRODUCTS.items()}
    report=overlap(originals)
    d=Path(out);d.mkdir(parents=True,exist_ok=True)
    (d/"NEON_2026_three_product_site_years_NOT_forest_plots.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    run(args.out)
