#!/usr/bin/env python3
"""Source-only cross-sensor spatial height concordance:
published CHMv2 40m plot p90 vs independently published VST field tree p90.

Original NEON site/plot coordinates, field tree heights, and CHM raster
arrays are runner-private. NEVER read beetle or plant biodiversity outcomes.
Calibration is NOT an annual canopy, nor a causal ecology model.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,json,math,statistics
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import spearmanr,pearsonr

from neon_meta_chmv2_public_tile_probe import quadkey,load,SOURCECOOP,AWS
from neon_meta_chmv2_plot40m_pixel_source_quality import (
    measure_window,read_date_index,unique_plots
)

def read_field(private_field_csv):
    with Path(private_field_csv).open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=73:raise ValueError("STOP_ORIGINAL_VST_73_PLOTYEAR_COHORT_DRIFT")
    required=("siteID","plotID","year","VST_field_p90_live_DBH10_height_m",
              "source_distinct_live_tree_individuals","source_original_tree_sample_area_m2")
    if not all(set(required)<=r.keys() for r in rows):
        raise ValueError("STOP_AUTHOR_VST_HEIGHT_P90_PRIVATE_SCHEMA_CHANGED")
    seen=set()
    for r in rows:
        key=(r["siteID"],r["plotID"],r["year"])
        if key in seen:raise ValueError("STOP_DUPLICATE_ORIGINAL_VST_SITEPLOT_YEAR")
        seen.add(key)
        if int(r["year"]) not in range(2019,2024) or \
           int(r["source_distinct_live_tree_individuals"])<3 or \
           not (float(r["VST_field_p90_live_DBH10_height_m"])>0 and
                math.isfinite(float(r["VST_field_p90_live_DBH10_height_m"]))):
            raise ValueError("STOP_VST_FROZEN_POSITIVE_P90_OR_3TREES_QA")
    source_sites={r["siteID"] for r in rows}
    if len(source_sites)!=22:raise ValueError("STOP_PREVIOUS_NEON_FIELD_22SITE_COHORT_CHANGED")
    return rows

def select_unique_plot(rows):
    # Original VST siteplot independent unit. Year nearest 2020, ties
    # earlier year, no CHM outcome information used in selection.
    ret={}
    for r in sorted(rows,key=lambda r:(abs(int(r["year"])-2020),int(r["year"]))):
        key=(r["siteID"],r["plotID"])
        ret.setdefault(key,r)
    return ret

def source_site_stats(records,domain,B=4000,seed=20261114):
    plots_by_site=defaultdict(list)
    for r in records:
        plots_by_site[r["siteID"]].append(r)
    sites=sorted(plots_by_site)
    med_field=[];med_CHM=[];withinX=[];withinY=[]
    for site in sites:
        obs=plots_by_site[site]
        f=np.asarray([x["field_p90_m"] for x in obs],dtype=float)
        c=np.asarray([x["CHM_p90_m"] for x in obs],dtype=float)
        med_field.append(float(np.median(f)))
        med_CHM.append(float(np.median(c)))
        if len(obs)>1:
            withinX.extend((f-f.mean()).tolist())
            withinY.extend((c-c.mean()).tolist())
    med_field=np.asarray(med_field)
    med_CHM=np.asarray(med_CHM)
    if len(sites)<10 or len(records)<25 or len({domain[s] for s in sites})<6:
        return {"status":"SCIENTIFIC_STOP_FEWER_THAN_TEN_SITES_TWENTYFIVE_PLOTS_SIX_DOMAINS",
                "source_sites":len(sites),"source_plots":len(records),
                "source_domains":len({domain[s] for s in sites})}
    if np.std(med_field)==0 or np.std(med_CHM)==0:
        return {"status":"SCIENTIFIC_STOP_CROSSSENSOR_SOURCE_UNIDENTIFIABLE_VARIANCE",
                "source_sites":len(sites)}
    rho=float(spearmanr(med_field,med_CHM).statistic)
    rng=np.random.default_rng(seed)
    boot=[]
    for _ in range(B):
        ix=rng.integers(len(sites),size=len(sites))
        a=med_field[ix];b=med_CHM[ix]
        if len(np.unique(a))<2 or len(np.unique(b))<2:continue
        z=float(spearmanr(a,b).statistic)
        if math.isfinite(z):boot.append(z)
    if len(boot)<.95*B:
        return {"status":"SCIENTIFIC_STOP_TOO_FEW_VALID_SITE_BOOTSTRAP_REPLICATES",
                "source_sites":len(sites),"bootstrap_valid":len(boot)}
    diffs=np.asarray([x["CHM_p90_m"]-x["field_p90_m"] for x in records])
    site_abs_median=np.asarray([np.median(np.abs(
        np.asarray([o["CHM_p90_m"]-o["field_p90_m"] for o in plots_by_site[site]])))
        for site in sites])
    plot_median=np.asarray([x["CHM_p90_m"] for x in records])
    field_median=np.asarray([x["field_p90_m"] for x in records])
    withinrho=None
    if len(withinX)>=8 and np.std(withinX)>0 and np.std(withinY)>0:
        withinrho=float(pearsonr(withinX,withinY).statistic)
    return {
      "status":"INDEPENDENT_CHMV2_VST_CROSSSENSOR_SPATIAL_CONCORDANCE_DESCRIPTIVE",
      "original_independent_NEON_sites":len(sites),
      "NEON_ecoclimatic_domains":len({domain[s] for s in sites}),
      "distinct_original_field_plots_one_field_survey_per_plot":len(records),
      "primary_site_equal_spearman_rho_satellite40m_p90_vs_VST_live_tree_p90":rho,
      "primary_site_block_bootstrap_95_percentile_CI":list(map(float,np.quantile(boot,[.025,.975]))),
      "original_site_bootstrap_B":B,
      "median_CHMv2_p90_minus_VST_p90_m":float(np.median(diffs)),
      "median_absolute_CHMv2_minus_VST_p90_m":float(np.median(np.abs(diffs))),
      "site_equal_median_absolute_height_difference_m":float(np.mean(site_abs_median)),
      "CHMv2_p90_median_on_matched_source_plots":float(np.median(plot_median)),
      "VST_field_p90_median_on_matched_source_plots":float(np.median(field_median)),
      "sites_with_at_least_two_matched_original_field_plots":sum(len(plots_by_site[s])>=2 for s in sites),
      "plot_level_within_site_centered_pearson_descriptive_ONLY":withinrho,
      "published_CHM40m_area_1600m2_NOT_equal_original_VST_field_area":True,
      "site_level_spatial_concordance_not_sameyear_pixel_acquisition_validation":True,
      "source_sensors_are_independent_but_original_forest_sites_NOT_independent_ecological_replication":True
    }
def audit(private_location,private_vst,official_csv,out):
    coords=load(private_location)
    if len(coords)!=952:raise ValueError("STOP_952_NEON_FOREST_PLOTYEAR_FRAME_CHANGED")
    positions=unique_plots(coords)
    if len(positions)!=237:raise ValueError("STOP_237_ORIGINAL_NEON_FOREST_PLOT_FRAME_CHANGED")
    field=read_field(private_vst)
    selected=select_unique_plot(field)
    with Path(official_csv).open(encoding="utf-8-sig",newline="") as f:
        official=list(csv.DictReader(f))
    if len(official)!=81 or not all("site_id" in r and "domain_id" in r for r in official):
        raise ValueError("STOP_OFFICIAL_NEON_FIELD_SITE_DOMAIN_SCHEMA_CHANGED")
    domain={r["site_id"]:r["domain_id"] for r in official}
    if len(domain)!=81:raise ValueError("STOP_OFFICIAL_NEON_SITE_DUPLICATED")
    missing_positions=sum(k not in positions for k in selected)
    if missing_positions:
        raise ValueError("STOP_ORIGINAL_FIELD_SITEPLOT_GEO_CROSSWALK_MISSING")
    grouped=defaultdict(list)
    for k,row in selected.items():
        lat,lon=positions[k]
        grouped[quadkey(lat,lon)].append((k,row,lat,lon))
    dates=read_date_index(set(grouped))
    if len(dates)!=len(grouped):
        raise ValueError("STOP_CHM_SOURCE_DATE_INDEX_MISSING_FOR_VST_MATCHES")
    passed=[]
    status=Counter()
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      VSI_CACHE="TRUE",GDAL_HTTP_MAX_RETRY="2",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        for key,points in sorted(grouped.items()):
            ds=None
            for url in (SOURCECOOP+key+".tif",AWS+key+".tif"):
                try:ds=rasterio.open(url);break
                except Exception:pass
            if ds is None:
                status["SOURCE_COG_PUBLIC_ACCESS_UNAVAILABLE"]+=len(points)
                continue
            with ds:
                for k,r,lat,lon in points:
                    try:z=measure_window(ds,lat,lon)
                    except Exception:z={"status":"SOURCE_COG_PIXEL_ERROR"}
                    status[z["status"]]+=1
                    if z["status"]!="SOURCE_PLOT40M_CHM_POSITIVE_PIXEL_QA_PASS":
                        continue
                    fieldyear=int(r["year"])
                    a,b,n=dates[key]
                    scene_window_overlap=(a<=dt.date(fieldyear,12,31) and
                                          b>=dt.date(fieldyear,1,1))
                    passed.append({
                       "siteID":k[0],"plotID":k[1],
                       "field_year":fieldyear,
                       "field_p90_m":float(r["VST_field_p90_live_DBH10_height_m"]),
                       "CHM_p90_m":float(z["height_positive_p90_m"]),
                       "scene_tile_date_window_overlaps_field_year":scene_window_overlap,
                       "original_VST_field_tree_count":int(r["source_distinct_live_tree_individuals"]),
                       "original_VST_sample_area_m2":float(r["source_original_tree_sample_area_m2"])
                    })
    stats=source_site_stats(passed,domain)
    overlap=[r for r in passed if r["scene_tile_date_window_overlaps_field_year"]]
    seen=dict(
      schema="structural.NEON_CHMv2_public_40m_vs_RE2026_VST_field_height_crosssensor.v1",
      published_vst_source_commit="3391e702e7be80a3f049c905782661f043be8db8",
      CHMv2_static_composite_2018_2020_majority_not_annual=True,
      forest_2019_2023_73_original_VST_field_plotyears_reproduced=len(field),
      forest_original_VST_independent_source_sites_before_CHM=22,
      distinct_original_siteplot_selected_nearest_to_2020_before_CHMv2=len(selected),
      original_field_year_selected_nearest_2020_counts=dict(sorted(Counter(
          str(r["year"]) for r in selected.values()).items())),
      CHMv2_matched_field_height_positive_window_plot_status=dict(sorted(status.items())),
      original_field_height_plot_CHM40m_positive_QA_matched=len(passed),
      original_field_height_plot_CHM40m_positive_QA_independent_sites=len({r["siteID"] for r in passed}),
      original_field_height_plot_CHM40m_positive_QA_domains=len({domain[r["siteID"]] for r in passed}),
      source_tile_acquisition_DATE_WINDOW_overlap_original_field_selected_year_plots=len(overlap),
      source_tile_date_window_field_year_overlap_sites=len({r["siteID"] for r in overlap}),
      source_scene_window_not_proof_of_actual_plot_pixel_acquisition=True,
      original_neon_2019_2023_woody_10siteyear_SEASON_EFFORT_STOP_retained=True,
      source_VST_original_measured_height_and_CHM40m_positive_p90_not_equivalent_area_or_time=True,
      original_beetle_plant_taxon_species_or_abundance_OUTCOMES_NOT_READ=True,
      original_site_plot_height_individual_pixel_or_coordinates_NOT_EXPORTED=True,
      no_ecological_effect_of_canopy_height_or_biodiversity_causality_claim=True,
      eBird_used=False,
      crosssensor_calibration=stats
    )
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"NEON_2026_CHMv2_vs_original_VST_height_crosssensor_aggregate.json").write_text(
        json.dumps(seen,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(seen,ensure_ascii=False,indent=2))
    return seen
def synthetic():
    # Known monotonic relationship at n=10 independent source sites,
    # multiple plots per site, with no original NEON IDs in the aggregate.
    sites=[f"PRIVATE_SITE_{i}" for i in range(10)]
    domain={s:f"D{i%7}" for i,s in enumerate(sites)}
    rows=[]
    for i,site in enumerate(sites):
        for plot in range(3):
            x=float(4+i*2+plot*.3)
            rows.append({"siteID":site,"plotID":f"PRIVATE_PLOT_{plot}",
                         "field_p90_m":x,"CHM_p90_m":x+1})
    res=source_site_stats(rows,domain,B=199)
    assert res["status"]=="INDEPENDENT_CHMV2_VST_CROSSSENSOR_SPATIAL_CONCORDANCE_DESCRIPTIVE"
    assert res["original_independent_NEON_sites"]==10
    assert res["distinct_original_field_plots_one_field_survey_per_plot"]==30
    assert res["primary_site_equal_spearman_rho_satellite40m_p90_vs_VST_live_tree_p90"]>.99
    assert res["median_CHMv2_p90_minus_VST_p90_m"]==1
    assert "PRIVATE_SITE" not in str(res)
    assert "PRIVATE_PLOT" not in str(res)
    print("Crosssensor source-only synthetic site bootstrap, field+CHM agreement and private ID omission PASS")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--private-neon-locations")
    p.add_argument("--private-vst-field-source")
    p.add_argument("--official-neon-sites")
    p.add_argument("--out")
    a=p.parse_args()
    synthetic()
    if a.private_neon_locations and a.private_vst_field_source and a.official_neon_sites and a.out:
        audit(a.private_neon_locations,a.private_vst_field_source,a.official_neon_sites,a.out)
