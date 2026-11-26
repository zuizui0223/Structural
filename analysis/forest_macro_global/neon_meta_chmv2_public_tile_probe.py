#!/usr/bin/env python3
"""Independent public Meta/WRI CHMv2 1m canopy tile and provenance support.

NEON original plot-coordinate/private sample keys stay in GitHub runner.
This is a PURE SOURCE AVAILABILITY gate; no canopy pixels, NEON organismal
responses, tree measurements, biological effects or source identifiers
are exported. Imagery mostly 2018-2020, NOT a 2019-2023 annual CHM.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,io,json,math,urllib.error,urllib.request
from concurrent.futures import ThreadPoolExecutor
from collections import Counter,defaultdict
from pathlib import Path

DATASET="Meta/WRI canopy height v2 (DINOv3, CHMv2)"
AWS="https://dataforgood-fb-data.s3.us-east-1.amazonaws.com/forests/v2/global/dinov3_global_chm_v2_ml3/chm/"
SOURCECOOP="https://data.source.coop/tge-labs/meta-chm-v2/chm/"
DATEINDEX="https://data.source.coop/tge-labs/meta-chm-v2/acq_dates.parquet"
MAX_PARQUET_BYTES=120_000_000
YEAR_WINDOW=(2019,2023)
def quadkey(lat:float,lon:float,zoom:int=10)->str:
    if not (math.isfinite(lat) and math.isfinite(lon)
            and abs(lat)<=85.05112878 and -180<=lon<=180 and zoom==10):
        raise ValueError("STOP_INVALID_ORIGINAL_NEON_PLOT_CENTRE")
    n=1<<zoom
    x=min(n-1,max(0,int((lon+180.0)/360.0*n)))
    sinlat=math.sin(math.radians(lat))
    y=min(n-1,max(0,int((1.0-math.log((1+sinlat)/(1-sinlat))/(2*math.pi))/2.0*n)))
    out=[]
    for bit in range(zoom-1,-1,-1):
        out.append(str((1 if x&(1<<bit) else 0)+(2 if y&(1<<bit) else 0)))
    return "".join(out)
def reqstatus(url,method="HEAD",max_seconds=17):
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url,method=method,headers={
                "User-Agent":"Structural-Forest-Macro-SourceMetadata-Probe/1.0"}),
            timeout=max_seconds) as resp:
            length=resp.headers.get("Content-Length")
            return {"status":resp.status,"length":int(length) if length and length.isdigit() else None,
                    "accept_ranges":resp.headers.get("Accept-Ranges","")}
    except urllib.error.HTTPError as e:
        return {"status":e.code,"length":None,"accept_ranges":""}
    except Exception:
        return {"status":"NETWORK_UNKNOWN","length":None,"accept_ranges":""}
def probe_pair(key):
    # Public sourcecooperative mirror first; fall back to original public AWS
    # but do not reinterpret one 404 as "no canopy at any place in the plot".
    a=reqstatus(SOURCECOOP+key+".tif")
    if a["status"]==200 and (a["length"] is None or a["length"]>1000):
        return key,{"source":"SOURCE_COOP","status":"HEAD_200","length":a["length"]}
    b=reqstatus(AWS+key+".tif")
    if b["status"]==200 and (b["length"] is None or b["length"]>1000):
        return key,{"source":"ORIGINAL_S3","status":"HEAD_200","length":b["length"]}
    return key,{"source":"NONE","status":f"PUBLIC_SOURCE_HEAD_{a['status']}_AWS_{b['status']}","length":None}
def date_index_metadata(keys):
    # Optional separately published per-tile acquisition-date source. Do not
    # infer the plot date from publication year or a general imagery epoch.
    head=reqstatus(DATEINDEX)
    result={"public_CHMv2_acquisition_date_index_http_status":head["status"],
            "public_CHMv2_acquisition_date_index_length_bytes":head["length"],
            "public_CHMv2_date_index_siteplot_tile_keys_matched":None,
            "source_acquisition_date_context_verified_at_plot_time":False}
    if head["status"]!=200:
        result["public_CHMv2_acquisition_date_index_status"]="UNAVAILABLE_NO_DATE_CLAIM"
        return result
    if head["length"] and head["length"]>MAX_PARQUET_BYTES:
        result["public_CHMv2_acquisition_date_index_status"]="TOO_LARGE_NO_DATE_CLAIM"
        return result
    try:
        import pyarrow.parquet as pq
    except ImportError:
        result["public_CHMv2_acquisition_date_index_status"]="PYARROW_NOT_INSTALLED"
        return result
    try:
        dest=Path("/tmp/structural_metasource_acq_dates.parquet")
        with urllib.request.urlopen(
          urllib.request.Request(DATEINDEX,headers={"User-Agent":"Structural-Forest-Macro-SourceMetadata-Probe/1.0"}),
          timeout=40) as response,dest.open("wb") as output:
            total=0
            while True:
                chunk=response.read(2*1024*1024)
                if not chunk:break
                total+=len(chunk)
                if total>MAX_PARQUET_BYTES:raise ValueError("DATE_INDEX_OVER_MAX_GUARD")
                output.write(chunk)
        p=pq.ParquetFile(str(dest))
        cols=p.schema_arrow.names
        result["public_CHMv2_acquisition_date_index_columns_METADATA_ONLY"]=cols
        # Authoritative index tile name inferred from schema, no point dates
        # are guessed when fields are missing.
        lk=next((v for v in ("quadkey","tile","id","quad_key","tile_id") if v in cols),None)
        mincol=next((v for v in ("acq_start","start_date","date_start","min_date","acquisition_start","start","first_date") if v in cols),None)
        maxcol=next((v for v in ("acq_end","end_date","date_end","max_date","acquisition_end","end","last_date") if v in cols),None)
        if not (lk and mincol and maxcol):
            result["public_CHMv2_acquisition_date_index_status"]="UNRECOGNIZED_SOURCE_DATE_SCHEMA_NO_DATE_INFERENCE"
            return result
        tb=pq.read_table(str(dest),columns=[lk,mincol,maxcol])
        found=Counter(str(x) for x in tb.column(lk).to_pylist() if str(x) in keys)
        result["public_CHMv2_date_index_siteplot_tile_keys_matched"]=len(found)
        result["public_CHMv2_acquisition_date_index_status"]="SOURCE_TILE_WINDOW_ONLY_NO_ORIGINAL_PLOT_YEAR_PROOF"
        # Avoid exporting individual dates or site-specific plot locations.
        return result
    except Exception as e:
        result["public_CHMv2_acquisition_date_index_status"]="SOURCE_DATE_INDEX_UNREADABLE_OR_TOO_LARGE"
        result["source_date_index_failure_class"]=type(e).__name__
        return result
def load(path):
    with Path(path).open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    required={"siteID","plotID","source_year","lat","lon","coordinate_source"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("STOP_ORIGINAL_NEON_PRIVATE_SOURCE_PLOT_CENTRE_SCHEMA")
    if len(rows)>1300:raise ValueError("STOP_NEON_ORIGINAL_SOURCE_YEAR_DENOMINATOR")
    seen=set()
    for r in rows:
        if not all(r.get(x) for x in required):raise ValueError("STOP_ORIGINAL_COORDINATE_ROW_NULL")
        k=(r["siteID"],r["plotID"],r["source_year"])
        if k in seen:raise ValueError("STOP_DUPLICATED_PRIVATE_SITE_PLOT_YEAR")
        seen.add(k)
        if not YEAR_WINDOW[0]<=int(r["source_year"])<=YEAR_WINDOW[1]:
            raise ValueError("STOP_UNINTENDED_ORIGINAL_YEAR_RANGE")
    return rows
def audit(path,out):
    rows=load(path)
    quads=defaultdict(list)
    for r in rows:
        key=quadkey(float(r["lat"]),float(r["lon"]))
        quads[key].append(r)
    keys=sorted(quads)
    with ThreadPoolExecutor(max_workers=8) as pool:
        resp=dict(pool.map(probe_pair,keys))
    sites=set();plotyears=0;legacy_window=0
    by_status=Counter()
    by_source=Counter()
    for q,rs in quads.items():
        p=resp[q]
        by_status[p["status"]]+=1
        by_source[p["source"]]+=1
        if p["status"]!="HEAD_200":continue
        for r in rs:
            plotyears+=1;sites.add(r["siteID"])
            if int(r["source_year"])<=2020:legacy_window+=1
    date_meta=date_index_metadata(set(keys))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    result={
      "schema":"structural.NEON_2019_2023_forest_plot_Meta_CHMv2_public_source_coverage.v1",
      "source_name":DATASET,
      "original_Meta_WRI_CHMv2_public_S3":"dataforgood-fb-data/forests/v2/global/dinov3_global_chm_v2_ml3/",
      "independently_published_public_mirror":"tge-labs/meta-chm-v2",
      "source_license":"CC-BY-4.0",
      "source_original_NEON_private_plotyear_rows_tested":len(rows),
      "original_NEON_distinct_plots_tested":len({(r["siteID"],r["plotID"]) for r in rows}),
      "original_NEON_distinct_sites_tested":len({r["siteID"] for r in rows}),
      "original_source_quadkey_zoom10_unique_tiled_areas_tested":len(keys),
      "public_source_quadkeys_head200":sum(x["status"]=="HEAD_200" for x in resp.values()),
      "public_source_quadkeys_head_statuses":dict(sorted(by_status.items())),
      "public_source_head_provenance":dict(sorted(by_source.items())),
      "NEON_forest_original_plotyears_whose_source_tile_exists":plotyears,
      "NEON_forest_distinct_original_sites_with_source_tile_exists":len(sites),
      "NEON_plotyears_in_2019_2020_with_public_chm_tile_NOT_ACQUISITION_DATE_VERIFIED":legacy_window,
      "original_public_source_tile_does_NOT_prove_pixel_has_valid_canopy":True,
      "original_plot_centre_not_surveyed_plot_polygon":True,
      "Meta_CHMv2_single_composite_image_epoch_not_NEON_annual_measurement":True,
      "imagery_mostly_2018_2020_but_tile_dates_require_separate_author_data":True,
      "NEON_2019_2023_woody_plotyear_12siteyear_STOP_preserved":True,
      "previous_NEON_cross_taxon_temporal_R_minus0p0664_p0p536_preserved":True,
      "previous_PREDICTS_39_study_beta0p0942_and_sensitivity_beta0p0847_preserved":True,
      "original_beetle_plant_taxon_abundance_species_did_not_open":True,
      "no_CHM_pixel_values_read_or_effect_fitted":True,
      "no_original_site_plot_coordinates_quadkeys_identifiers_exported":True,
      "independent_chm_source_not_independent_ecological_outcome":True,
      "eBird_used":False,
      **date_meta
    }
    outpath=out/"neon_forest_patch_META_CHMv2_public_tile_and_date_source_coverage.json"
    outpath.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result
def synthetic():
    assert quadkey(0.,0.)=="3000000000"
    assert quadkey(39.0,-105.0)==quadkey(39.00001,-104.99999)
    assert quadkey(38.0,-122.0)!=quadkey(38.0,-80.0)
    for lat,lon in ((86,0),(0,181),(float("nan"),1)):
        try:quadkey(lat,lon)
        except ValueError:pass
        else:raise AssertionError("SOURCE_INVALID_COORDINATE_NOT_REJECTED")
    print("CHMv2 source-only quadkey z10 and original-coordinate validators PASS")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--private-neon-plotyears")
    parser.add_argument("--out")
    a=parser.parse_args()
    synthetic()
    if a.private_neon_plotyears and a.out:
        audit(a.private_neon_plotyears,a.out)
