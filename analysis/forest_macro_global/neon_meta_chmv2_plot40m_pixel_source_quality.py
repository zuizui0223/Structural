#!/usr/bin/env python3
"""Meta/WRI CHMv2 independently public ~1m canopy pixel SOURCE QA at NEON plots.

No NEON beetle/plant taxa/abundance or previous scores read. Original location
keys stay runner-private, static image is not a series of NEON annual LiDAR.
The original Meta/WRI CHMv2 uint8 value 0 can mean nodata OR no canopy:
never infer 0m canopy, absence or deforestation from 0 pixels.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,json,math,statistics,tempfile,urllib.request
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import from_origin
from rasterio.warp import transform

from neon_meta_chmv2_public_tile_probe import quadkey,load,SOURCECOOP,AWS,DATEINDEX

SOURCE_COMPOSITE="Meta/WRI Canopy Height v2 DINOv3 ~1.19m global COG"
CRS="EPSG:3857"
SIDE_METRES=40.0
HALF=SIDE_METRES/2
POSITIVE_COUNT_MIN=25
POSITIVE_FRACTION_MIN=.20
def parse_date(v):
    if isinstance(v,dt.datetime):return v.date()
    if isinstance(v,dt.date):return v
    if v is None:return None
    x=str(v).strip()
    try:return dt.date.fromisoformat(x[:10])
    except (ValueError,TypeError):pass
    try:
        num=float(x)
        if num>1e12:return dt.datetime.fromtimestamp(num/1000,tz=dt.timezone.utc).date()
        if num>1e9:return dt.datetime.fromtimestamp(num,tz=dt.timezone.utc).date()
    except (ValueError,OverflowError,OSError):pass
    return None
def read_date_index(keys):
    import pyarrow.parquet as pq
    dst=Path("/tmp/structural_chmv2_source_date_plot_qa.parquet")
    with urllib.request.urlopen(
        urllib.request.Request(DATEINDEX,headers={"User-Agent":"Structural-Forest-Sampling-SourceQA/1.0"}),
        timeout=45) as response,dst.open("wb") as output:
        size=0
        while True:
            part=response.read(1024*1024)
            if not part:break
            size+=len(part)
            if size>15_000_000:raise ValueError("SOURCE_DATE_METADATA_TOO_LARGE")
            output.write(part)
    d=pq.read_table(str(dst),columns=["quadkey","acq_start","acq_end","acq_n"])
    columns={k:d.column(k).to_pylist() for k in ("quadkey","acq_start","acq_end","acq_n")}
    outcome={}
    for key,start,end,n in zip(*(columns[k] for k in columns)):
        q=str(key)
        if q not in keys:continue
        a=parse_date(start);b=parse_date(end)
        if a is None or b is None or b<a:continue
        outcome[q]=(a,b,n)
    return outcome
def measure_window(dataset,lat,lon):
    if not (dataset.crs and dataset.crs.to_epsg()==3857 and
            dataset.count==1):
        return {"status":"SOURCE_CHM_EXPECTED_3857_SINGLE_BAND_SCHEMA_MISSING"}
    x,y=transform("EPSG:4326",dataset.crs,[lon],[lat])
    x=x[0];y=y[0]
    if not (math.isfinite(x) and math.isfinite(y)):
        return {"status":"SOURCE_ORIGINAL_PLOT_CENTRE_TRANSFORM_UNDEFINED"}
    win=from_bounds(x-HALF,y-HALF,x+HALF,y+HALF,transform=dataset.transform)
    if not (0<=win.col_off and 0<=win.row_off
            and win.col_off+win.width<=dataset.width
            and win.row_off+win.height<=dataset.height):
        return {"status":"SOURCE_PLOT40M_WINDOW_CROSSES_PUBLIC_TILE_BOUNDARY"}
    arr=dataset.read(1,window=win,masked=True)
    if arr.size<200:return {"status":"SOURCE_PLOT40M_RASTER_WINDOW_TOO_SMALL"}
    mask=np.ma.getmaskarray(arr)
    data=np.asarray(arr.data)
    valid=data[~mask]
    positive=valid[valid>0]
    denom=arr.size
    fraction=len(positive)/denom if denom else 0
    if len(positive)==0:
        return {"status":"SOURCE_PLOT40M_ALL_ZERO_OR_NODATA_NOT_PROVEN_TREES_ABSENT",
                "pixels":denom,"positive_fraction":0.0}
    okay=len(positive)>=POSITIVE_COUNT_MIN and fraction>=POSITIVE_FRACTION_MIN
    return {"status":"SOURCE_PLOT40M_CHM_POSITIVE_PIXEL_QA_PASS" if okay else
                    "SOURCE_PLOT40M_POSITIVE_COVERAGE_TOO_LOW_NO_HEIGHT_ZERO_CLAIM",
            "pixels":denom,
            "positive_pixels":len(positive),
            "positive_fraction":float(fraction),
            "height_positive_p90_m":float(np.percentile(positive,90)),
            "height_positive_median_m":float(np.median(positive))}
def unique_plots(rows):
    out={}
    for r in rows:
        key=(r["siteID"],r["plotID"])
        one=(float(r["lat"]),float(r["lon"]))
        if key in out:
            if max(abs(a-b) for a,b in zip(one,out[key]))>1e-7:
                raise ValueError("STOP_ORIGINAL_PLOT_CENTER_DIFFERS_ACROSS_YEARS")
        out[key]=one
    return out
def audit(private_csv,official_csv,out):
    rows=load(private_csv)
    if len(rows)!=952:raise ValueError("STOP_PRIVATE_SOURCE_952_FIXED_COHORT_DRIFT")
    plots=unique_plots(rows)
    if len(plots)!=237:raise ValueError("STOP_PRIVATE_237_ORIGINAL_PLOTS_CHANGED")
    official=list(csv.DictReader(Path(official_csv).open(encoding="utf-8")))
    domain={r["site_id"]:r["domain_id"] for r in official}
    if len(official)!=81 or len(domain)!=81:raise ValueError("STOP_OFFICIAL_NEON_SOURCE_81_SITE_METADATA_DRIFT")
    grouped=defaultdict(list)
    for (site,plot),(lat,lon) in plots.items():
        if site not in domain:raise ValueError("STOP_NEON_SOURCE_SITE_DOMAIN_NOT_VERIFIED")
        grouped[quadkey(lat,lon)].append((site,plot,lat,lon))
    if len(grouped)!=39:raise ValueError("STOP_FROZEN_39_CHMV2_SOURCE_TILE_COUNT_CHANGED")
    dates=read_date_index(set(grouped))
    if len(dates)!=39:raise ValueError("STOP_SOURCE_CHMV2_SOURCE_ACQ_DATE_INDEX_NOT_39")
    qa={}
    errors=Counter()
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      VSI_CACHE="TRUE",GDAL_HTTP_MAX_RETRY="2",
                      GDAL_HTTP_RETRY_DELAY="1",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        for key,locations in sorted(grouped.items()):
            ds=None
            for url in (SOURCECOOP+key+".tif",AWS+key+".tif"):
                try:
                    ds=rasterio.open(url)
                    break
                except Exception as e:
                    errors[type(e).__name__]+=1
            if ds is None:
                for site,plot,lat,lon in locations:
                    qa[(site,plot)]={"status":"SOURCE_COG_PIXEL_READ_PUBLIC_ACCESS_FAILED"}
                continue
            with ds:
                for site,plot,lat,lon in locations:
                    try:
                        qa[(site,plot)]=measure_window(ds,lat,lon)
                    except Exception as e:
                        errors[type(e).__name__]+=1
                        qa[(site,plot)]={"status":"SOURCE_PLOT40M_PIXEL_READ_ERROR"}
    counts=Counter(v["status"] for v in qa.values())
    passing={key for key,v in qa.items() if v["status"]=="SOURCE_PLOT40M_CHM_POSITIVE_PIXEL_QA_PASS"}
    sites={site for site,plot in passing}
    p90=[qa[key]["height_positive_p90_m"] for key in passing]
    f=[qa[key]["positive_fraction"] for key in passing]
    site_means=[]
    for site in sorted(sites):
        vals=[qa[key]["height_positive_p90_m"] for key in passing if key[0]==site]
        site_means.append(float(np.mean(vals)))
    dateyears=Counter()
    tilecounts=Counter()
    for key,(start,end,n) in dates.items():
        if end<dt.date(2019,1,1):band="ALL_SOURCE_IMAGERY_DATES_BEFORE_2019"
        elif start>dt.date(2020,12,31):band="ALL_SOURCE_IMAGERY_DATES_AFTER_2020"
        else:band="TILE_SOURCE_DATE_WINDOW_OVERLAPS_2019_2020"
        dateyears[band]+=1
        if n is not None:tilecounts["TILES_WITH_ACQUISITION_SCENE_COUNT"]+=1
    # Source calendar year is not image acquisition date! Only plot-year source
    # cohort counts whose TILE's aggregate date window happens to overlap year.
    cohort_any=0;cohort_sites=set()
    for r in rows:
        k=quadkey(float(r["lat"]),float(r["lon"]))
        start,end,n=dates[k]
        yr=int(r["source_year"])
        if start<=dt.date(yr,12,31) and end>=dt.date(yr,1,1):
            cohort_any+=1;cohort_sites.add(r["siteID"])
    n_2019_2020=sum(1 for r in rows if int(r["source_year"])<=2020 and
      (r["siteID"],r["plotID"]) in passing)
    output={
        "schema":"structural.NEON_forestpatch_META_WRI_CHMv2_2026_40m_original_plot_pixel_sourceQA.v1",
        "source":"Meta/WRI Global CHMv2 DINOv3 1m composite COG published 2026",
        "source_original_NEON_forest_sites_fixed":35,
        "original_NEON_forest_plot_years_fixed":len(rows),
        "original_unique_NEON_original_field_plots_QA_attempted":len(plots),
        "source_CHMv2_quadkey_tiles_covered":len(grouped),
        "source_CHMv2_date_index_tiles_verified":len(dates),
        "source_original_plot_40m_window_status_counts":dict(sorted(counts.items())),
        "source_40m_COG_window_positive_QA_passing_original_plots":len(passing),
        "source_40m_COG_window_positive_QA_passing_distinct_sites":len(sites),
        "source_40m_COG_window_positive_QA_passing_independent_NEON_domains":len({domain[s] for s in sites}),
        "source_40m_COG_window_p90_height_m_median_over_QA_passed_plots":float(np.median(p90)) if p90 else None,
        "source_40m_COG_window_p90_height_m_median_of_original_site_means":float(np.median(site_means)) if site_means else None,
        "source_40m_COG_window_positive_fraction_median_over_QA_passed_plots":float(np.median(f)) if f else None,
        "source_2019_2020_NEON_original_plotyears_with_CHM40m_positive_window_QA_but_SCENE_YEAR_UNVERIFIED":n_2019_2020,
        "source_CHMv2_tile_imagery_acquisition_DATE_WINDOW_categories":dict(sorted(dateyears.items())),
        "source_NEON_2019_2023_plotyears_with_SOURCE_TILE_DATE_WINDOWS_OVERLAPPING_NEON_YEAR_NOT_PIXEL_DATE":cohort_any,
        "source_distinct_NEON_sites_with_SOURCE_TILE_DATE_WINDOWS_OVERLAPPING_NEON_YEAR_NOT_PIXEL_DATE":len(cohort_sites),
        "source_CHM_public_remote_pixel_access_failure_classes":dict(sorted(errors.items())),
        "source_CHM_uint8_zero_indistinguishable_no_canopy_or_nodata":True,
        "source_original_field_plot_40m_square_NOT_AUTHOR_POLYGON":True,
        "source_imagery_date_SOURCE_TILE_WINDOW_NOT_PIXEL_ACQUISITION":True,
        "CHMv2_2026_composite_not_2019_2023_repeat_annual_measurements":True,
        "positive_pixel_source_quality_not_an_environmental_ecological_effect":True,
        "same_original_NEON_sites_not_a_new_independent_field_validation":True,
        "old_VST_2019_23_10siteyear_and_2014_18_QA_scientific_STOP_preserved":True,
        "previous_PREDICTS_positive_and_NEON_cross_taxon_null_sealed":True,
        "no_original_NEON_site_plot_lat_lon_quadkey_taxon_species_or_raw_pixel_arrays_exported":True,
        "original_species_taxon_or_abundance_response_values_NOT_READ":True,
        "eBird_used":False,
    }
    folder=Path(out);folder.mkdir(parents=True,exist_ok=True)
    (folder/"neon_35forest_META_CHMv2_40m_plot_pixel_quality_source_aggregate.json").write_text(
        json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))
    return output
def synthetic():
    # Read a local 1m GeoTIFF, not any external or non-open source image.
    with tempfile.TemporaryDirectory() as root:
        f=Path(root)/"known.tif"
        arr=np.zeros((200,200),dtype=np.uint8)
        arr[80:120,80:120]=12
        with rasterio.open(f,mode="w",driver="GTiff",width=200,height=200,
              count=1,dtype="uint8",crs="EPSG:3857",
              transform=from_origin(-100,100,1,1)) as ds:
            ds.write(arr,1)
        with rasterio.open(f) as ds:
            result=measure_window(ds,0,0)
            assert result["status"]=="SOURCE_PLOT40M_CHM_POSITIVE_PIXEL_QA_PASS"
            assert result["height_positive_p90_m"]==12
            assert abs(result["positive_fraction"]-1)<1e-9
        arr[:]=0
        with rasterio.open(f,mode="w",driver="GTiff",width=200,height=200,
              count=1,dtype="uint8",crs="EPSG:3857",
              transform=from_origin(-100,100,1,1)) as ds:
            ds.write(arr,1)
        with rasterio.open(f) as ds:
            z=measure_window(ds,0,0)
            assert z["status"]=="SOURCE_PLOT40M_ALL_ZERO_OR_NODATA_NOT_PROVEN_TREES_ABSENT"
    assert parse_date("2019-08-01T13:30:00") == dt.date(2019,8,1)
    assert parse_date(None) is None
    print("Synthetic source CHMv2 40m EPSG3857 plot window, zero-vs-nodata, date parsing PASS")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--private-original-neon-plots")
    parser.add_argument("--official-neon-site-source")
    parser.add_argument("--out")
    args=parser.parse_args()
    synthetic()
    if args.private_original_neon_plots and args.official_neon_site_source and args.out:
        audit(args.private_original_neon_plots,args.official_neon_site_source,args.out)
