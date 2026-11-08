#!/usr/bin/env python3
"""NEON 2026 forest landcover qualification for 3-product beetle sites.

Match original official NEON field-site CSV (2026-08-05 pinned SHA) to the
original 2026 beetle + vegetation structure + multi-level tower air temperature
product site-month manifest. Strict source NLCD forest-only sites are *site
context candidates*, NOT beetle forest PLOT habitat certified.

Do not equate all 42 overlapping sites with forests or infer insect canopy
movement from meteorological tower temperatures.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from collections import Counter,defaultdict
from pathlib import Path

SITE_SHA="d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461"
FOREST={"Deciduous Forest","Evergreen Forest","Mixed Forest"}
WOODY="Woody Wetlands"

def nlcd_class(label):
    values={x.strip() for x in str(label or "").split("|") if x.strip()}
    if not values:return "UNCLASSIFIED_SOURCE_NLCD"
    unknown={x for x in values if x not in FOREST and x!=WOODY}
    if values<=FOREST:return "STRICT_FOREST_ONLY_SOURCE_SITE"
    if values<=FOREST|{WOODY} and values&FOREST:
        return "FOREST_PLUS_WOODY_WETLANDS_SEPARATE"
    if values=={WOODY}:return "WOODY_WETLAND_ONLY_SEPARATE"
    if values&FOREST and unknown:return "FOREST_MIXED_NONFOREST_NLCD_CONTEXT"
    if WOODY in values and unknown:return "WOODY_WETLAND_MIXED_NONFOREST_CONTEXT"
    return "NONFOREST_SOURCE_NLCD"

def number(x):
    try:r=float(str(x or "").strip().replace(",",""))
    except ValueError:return None
    return r if math.isfinite(r) else None

def table_rows(raw, *, expected_sha=SITE_SHA):
    if hashlib.sha256(raw).hexdigest()!=expected_sha:
        raise ValueError("NEON_original_20260805_source_version_changed")
    s=raw.decode("utf-8-sig")
    d=csv.DictReader(s.splitlines(),delimiter=",")
    names=[str(x or "").strip() for x in (d.fieldnames or [])]
    req={"site_id","dominant_nlcd_classes","mean_canopy_height_m",
         "tower_height_m","number_tower_levels","domain_id","site_subtype"}
    if not req.issubset(names):
        raise ValueError("NEON_source_original_site_landcover_and_tower_schema_changed")
    d.fieldnames=names
    rows=[{k:(v or "").strip() for k,v in r.items() if k} for r in d]
    if len(rows)!=81:raise ValueError("NEON_official_site_metadata_count_changed")
    if len({r["site_id"] for r in rows})!=81:
        raise ValueError("NEON_source_repeated_site_code")
    return rows

def classify(original,site_manifest):
    if site_manifest.get("schema")!="structural.NEON_forest_beetle_canopy_temperature_2026_product_metadata_support.v1":
        raise ValueError("NEON_original_2026_three_product_cohort_manifest_mismatch")
    if site_manifest.get("original_NEON_release")!="RELEASE-2026":
        raise ValueError("NEON_product_release_mismatch")
    candidates=site_manifest["three_product_candidate_site_by_year_support"]
    if len(candidates)!=42:
        raise ValueError("NEON_original_three_product_support_expected_42_sites")
    bysite={r["site_id"]:r for r in original}
    counts=Counter()
    summary=Counter()
    per=[]
    for item in candidates:
        sid=item["siteCode"]
        src=bysite.get(sid)
        if src is None:
            raise ValueError("NEON_product_SITE_missing_in_official_landcover_table")
        cl=nlcd_class(src["dominant_nlcd_classes"])
        counts[cl]+=1
        months=int(item["three_product_same_calendar_months_count"])
        years=int(item["three_product_common_sample_year_count"])
        height=number(src["mean_canopy_height_m"])
        tower=number(src["tower_height_m"])
        levels=number(src["number_tower_levels"])
        if not 0<=months<=200 or not 0<=years<=20:
            raise ValueError("NEON_source_bad_calendar_month_count")
        eligible_nlcd=cl=="STRICT_FOREST_ONLY_SOURCE_SITE"
        if eligible_nlcd:
            summary["strict_forest_only_sites"]+=1
            if months>=1:summary["strict_forest_with_common_month"]+=1
            if years>=2:summary["strict_forest_with_2plus_common_years"]+=1
            if height is not None and height>0:summary["strict_forest_with_positive_site_mean_canopy_height"]+=1
            if tower is not None and tower>0 and levels is not None and levels>=2:
                summary["strict_forest_with_2plus_tower_levels"]+=1
        per.append({
          "NEON_siteCode_public":sid,
          "source_ecoclimatic_domain":src["domain_id"],
          "source_NLCD_site_context":cl,
          "source_site_mean_canopy_height_m":height,
          "source_tower_height_m":tower,
          "source_declared_tower_sensor_levels":levels,
          "three_product_site_month_overlap":months,
          "three_product_sample_year_overlap":years,
          "strict_forest_site_context_candidate":eligible_nlcd,
          "strict_forest_with_temporal_match_candidate":eligible_nlcd and months>=1,
          "strict_forest_2plus_year_temporal_match_candidate":eligible_nlcd and years>=2,
          "field_beetle_and_tree_stations_verified_same_physical_plot":False,
          "site_level_NLCD_not_guaranteed_beetle_plot_forest":True
        })
    domains={r["source_ecoclimatic_domain"] for r in per
             if r["strict_forest_with_temporal_match_candidate"]}
    result={
        "schema":"structural.NEON_forest_beetle_site_NLCD_temporal_gate.v1",
        "NEON_site_table_source_version":"2026-08-05",
        "NEON_official_site_source_sha256":SITE_SHA,
        "NEON_data_release":"RELEASE-2026",
        "official_NEON_site_metadata_rows":len(original),
        "original_three_product_site_N":len(per),
        "site_NLCD_context_category_counts":dict(counts),
        "strict_forest_only_dominant_NLCD_sites":summary["strict_forest_only_sites"],
        "strict_forest_only_with_same_calendar_month_three_products":summary["strict_forest_with_common_month"],
        "strict_forest_only_with_2plus_sample_years":summary["strict_forest_with_2plus_common_years"],
        "strict_forest_only_with_positive_mean_canopy_height":summary["strict_forest_with_positive_site_mean_canopy_height"],
        "strict_forest_only_with_2plus_declared_tower_sensor_levels":summary["strict_forest_with_2plus_tower_levels"],
        "ecoclimatic_domains_in_strict_forest_time_matched_cohort":len(domains),
        "original_site_source_crosswalk":per,
        "original_plot_scale_habitat_identity_qualified":0,
        "actual_original_air_temperature_level_data_observed":False,
        "actual_original_species_and_vegetation_structural_rows_read":0,
        "original_NEON_biological_thermal_effect_scored":False,
        "NEON_ground_beetle_pitfall_not_an_insect_canopy_trap":True,
        "no_original_species_or_trap_ID_values_exported":True,
        "eBird_used":False
    }
    return result

def run(site_csv,month_manifest,out):
    raw=Path(site_csv).read_bytes()
    data=table_rows(raw)
    site=json.loads(Path(month_manifest).read_text(encoding="utf-8"))
    res=classify(data,site)
    p=Path(out);p.mkdir(parents=True,exist_ok=True)
    (p/"NEON_2026_strict_forest_nlcd_three_product_source_gate.json").write_text(
        json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for k,v in res.items():
        if k!="original_site_source_crosswalk":print(k,":",json.dumps(v,ensure_ascii=False))
    return res

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--site_csv",required=True)
    p.add_argument("--month_manifest",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.site_csv,a.month_manifest,a.out)
