#!/usr/bin/env python3
"""v1.261 NRMN Method-1 marine island survey feasibility, no fish outcomes.

Physically checks the 20 frozen RLS/ATRC survey groups against GSHHG 2.3.7.
Only AODN survey metadata's ten fields are ever scanned. Marine GPS points
are assigned to a *nearby coastline*, not placed inside island land polygons.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile
import urllib.request
import zipfile

from shapely.geometry import Point, box, shape
from shapely.ops import nearest_points
from shapely.strtree import STRtree
from pyproj import Geod
import shapefile

SCHEMA="structural.nrmn_marine_island_feasibility.v1_261"
SHORE_ARCHIVE="https://github.com/GenericMappingTools/gshhg-gmt/releases/download/2.3.7/gshhg-shp-2.3.7.zip"
SHORE_BYTES=149_157_845
SHORE_SHA="8dbbe7e071e77e9e75f2d639239099ebca8d5c16d6a07df8169729d49f15cf41"
SHORE_NAME="GSHHS_shp/h/GSHHS_h_L1"
SOURCE_SURVEY_SHA="6bb15e9aff7600c7e429c989d929a4eb6841ffff423915e041adf263a8603dce"
GEO=Geod(ellps="WGS84")
MAX_SRC_ROWS=3_000_000
VALID_LAST=date(2026,10,19)


def methods_have_m1(value):
    """Method 1 must be its own numeric token: 13 or 10 are NOT Method 1."""
    if value is None: return False
    return "1" in re.findall(r"\d+",str(value))


def program_class(value):
    labels=set(re.findall(r"[A-Z0-9]+",str(value or "").upper()))
    if "RLS" in labels and "ATRC" not in labels:return "RLS"
    if "ATRC" in labels and "RLS" not in labels:return "ATRC"
    return "OTHER"


def repeated_m1_site_summary(rows,allowed_groups):
    """Return site coordinates locally only; no survey IDs or fish rows exported.

    'sites' records include only sites with the original frozen strict
    same-month t→t+1 >=2 transects both years. All years are observation
    years, not inferred occupancy or sampled taxon absence.
    """
    if len(allowed_groups)!=20 and len(allowed_groups)!=1:
        raise ValueError("Expected original 20 source groups or one synthetic group")
    seen=set(); month=Counter(); state={}; stats=Counter()
    for record in rows:
        stats["source_rows_seen"]+=1
        if stats["source_rows_seen"]>MAX_SRC_ROWS:
            raise ValueError("Survey exceeds predeclared original source record cap")
        try:
            sid=int(record["survey_id"])
            d=date.fromisoformat(str(record["survey_date"])[:10])
            lat=float(record["latitude"]);lon=float(record["longitude"])
            parts=tuple(str(record.get(k) or "").strip().casefold()
                        for k in ("country","area","location","site_code"))
        except (TypeError,ValueError,KeyError):
            stats["invalid_physical_survey"]+=1;continue
        if (sid<0 or not date(1992,1,1)<=d<=VALID_LAST
            or not -90<=lat<=90 or not -180<=lon<=180
            or not (math.isfinite(lat) and math.isfinite(lon))
            or not parts[0] or not parts[3]):
            stats["invalid_physical_survey"]+=1;continue
        if sid in seen:
            stats["duplicated_survey_id"]+=1;continue
        seen.add(sid);stats["unique_valid_survey_ids"]+=1
        grp=(program_class(record.get("program")),)+parts[:3]
        if grp not in allowed_groups:
            stats["excluded_group_event_count"]+=1;continue
        if not methods_have_m1(record.get("methods")):
            stats["excluded_no_m1_in_frozen_group"]+=1;continue
        stats["method1_surveys_in_frozen_groups"]+=1
        site=(grp,parts[3])
        month[(site,d.year,d.month)]+=1
        if site not in state:
            state[site]={"years":set(),"min_lat":lat,"max_lat":lat,
                         "min_lon":lon,"max_lon":lon,"sum_lat":0.0,
                         "sum_lon":0.0,"n":0}
        rec=state[site]
        rec["years"].add(d.year)
        rec["min_lat"]=min(rec["min_lat"],lat)
        rec["max_lat"]=max(rec["max_lat"],lat)
        rec["min_lon"]=min(rec["min_lon"],lon)
        rec["max_lon"]=max(rec["max_lon"],lon)
        rec["sum_lat"]+=lat;rec["sum_lon"]+=lon;rec["n"]+=1
    sites=[]
    for (grp,code),rec in state.items():
        if (rec["max_lat"]-rec["min_lat"]>0.01
            or rec["max_lon"]-rec["min_lon"]>0.01):
            stats["unstable_M1_site_codes"]+=1
            continue
        strict=[]
        for (s,year,mo),n in month.items():
            if s==(grp,code) and n>=2 and month.get((s,year+1,mo),0)>=2:
                strict.append((year,mo))
        if not strict:continue
        years={year for year,_ in strict}
        sites.append({
            "group":grp,"site_code":code,
            "lat":rec["sum_lat"]/rec["n"],
            "lon":rec["sum_lon"]/rec["n"],
            "strict_pairs":len(strict),
            "n_observed_years":len(rec["years"]),
            "prior_years":sorted(years),
            "n_prior_years":len(years),
        })
    sites.sort(key=lambda s:(s["group"],s["site_code"]))
    stats["stable_M1_sites_with_any_strict_pair"]=len(sites)
    stats["strict_M1_site_month_consecutive_year_pairs"]=sum(s["strict_pairs"] for s in sites)
    return sites,dict(stats)


def coast_distance_km(lon,lat,polygon):
    """Geodesic distance from marine point to nominal nearest polygon boundary."""
    x=Point(lon,lat)
    y=nearest_points(x,polygon.boundary)[1]
    _,_,distance=GEO.inv(lon,lat,y.x,y.y)
    return max(0.0,distance/1000)


def marine_nearest_landmass(lon,lat,polygon_records,
                            max_coast_km=5.0,min_margin_km=1.0,
                            candidate_limit_km=15.0):
    """Classify point relative to closest L1 land, never as an island land site.

    Input records are (unique GSHHG polygon ID, original area km², geometry).
    Ties, small islands, mainland adjacency, and georeference-on-land are
    reported as non-island-primary outcomes rather than reassigned posthoc.
    """
    point=Point(float(lon),float(lat))
    dist=[]
    for land_id,area,geom in polygon_records:
        if geom is None or geom.is_empty:continue
        if geom.covers(point):
            return {"class":"on_land_ambiguous","polygon_id":None,
                    "coast_km":0.0}
        km=coast_distance_km(lon,lat,geom)
        if km<=candidate_limit_km:
            dist.append((km,str(land_id),float(area)))
    dist.sort(key=lambda a:(a[0],a[1]))
    if not dist or dist[0][0]>max_coast_km:
        return {"class":"no_polygon_within_radius","polygon_id":None,
                "coast_km":dist[0][0] if dist else None}
    nearest=dist[0]
    km,land_id,area=nearest
    if len(dist)>1 and dist[1][0]-km<min_margin_km:
        return {"class":"ambiguous_coast_multiple_landmasses",
                "polygon_id":None,"coast_km":km}
    if area>=7_000_000:
        return {"class":"mainland_nearshore","polygon_id":None,"coast_km":km}
    if area<5:
        return {"class":"small_landmass_nearshore","polygon_id":None,"coast_km":km}
    return {"class":"island_nearshore","polygon_id":land_id,
            "coast_km":km}


def network_island_support(sites,groups):
    """Summarize *only* island counts; never emit site code, GPS or fish records."""
    grouped=defaultdict(list)
    for s in sites: grouped[tuple(s["group"])].append(s)
    output=[]
    for group in sorted(groups):
        local=grouped[group]
        islands=defaultdict(list)
        classes=Counter(s.get("class","unclassified") for s in local)
        for s in local:
            if s.get("class")=="island_nearshore" and s.get("polygon_id"):
                islands[s["polygon_id"]].append(s)
        island_good=0
        for island,records in islands.items():
            dates=set(y for s in records for y in s["prior_years"])
            if (len(records)>=3
                and sum(s["strict_pairs"] for s in records)>=3
                and len(dates)>=2):
                island_good+=1
        output.append({
            "program":group[0],"country":group[1],
            "area":group[2],"location":group[3],
            "stable_m1_sites_with_strict_pairs":len(local),
            "strict_adjacent_year_site_month_pairs":sum(s["strict_pairs"] for s in local),
            "distinct_nearshore_island_polygons":len(islands),
            "island_site_counts":sum(len(v) for v in islands.values()),
            "island_strict_pairs":sum(s["strict_pairs"] for vs in islands.values() for s in vs),
            "island_polygons_with_3plus_sites_and_3plus_pairs_and_2plus_years":island_good,
            "qualified_multi_island_reef_network":island_good>=2,
            "mainland_nearshore_sites":classes["mainland_nearshore"],
            "small_landmass_nearshore_sites":classes["small_landmass_nearshore"],
            "on_land_ambiguous_sites":classes["on_land_ambiguous"],
            "ambiguous_coast_sites":classes["ambiguous_coast_multiple_landmasses"],
            "remote_from_shore_sites":classes["no_polygon_within_radius"],
        })
    return output


def _archive(zip_path,source_config):
    if source_config["GSHHG_tagged_zip_url"]!=SHORE_ARCHIVE:
        raise ValueError("GSHHG source URL no longer matches frozen original")
    with urllib.request.urlopen(urllib.request.Request(
        SHORE_ARCHIVE,headers={"User-Agent":"Structural-reef-geography-source-audit/1.0"}),
        timeout=180) as inp,zip_path.open("wb") as out:
        checksum=hashlib.sha256();size=0
        while True:
            block=inp.read(1_048_576)
            if not block:break
            size+=len(block)
            if size>SHORE_BYTES:
                raise ValueError("GSHHG archive exceeds original frozen bytes")
            checksum.update(block);out.write(block)
    if size!=SHORE_BYTES or checksum.hexdigest()!=SHORE_SHA:
        raise ValueError("Exact GSHHG 2.3.7 published archive size/SHA256 differs")
    return checksum.hexdigest()


def _extract_source_shapefile(archive,root):
    with zipfile.ZipFile(archive) as z:
        base=root/"GSHHS_h_L1"
        for ext in (".shp",".shx",".dbf"):
            suffix=f"{SHORE_NAME}{ext}"
            found=[x for x in z.namelist() if x.endswith(suffix)]
            if len(found)!=1:raise ValueError("Original GSHHG high-res L1 source missing/duplicated "+ext)
            base.with_suffix(ext).write_bytes(z.read(found[0]))
    return base.with_suffix(".shp")


def _nearby_source_polygons(shp_file,sites):
    """Only deserialize GSHHG polygons with bbox near the frozen physical points."""
    points=[Point(s["lon"],s["lat"]) for s in sites]
    tree=STRtree(points)
    candidates=[];reader=shapefile.Reader(str(shp_file))
    fields={str(desc[0]).lower() for desc in reader.fields[1:]}
    if not {"id","area"}<=fields:
        raise ValueError("GSHHG L1 source lacks original ID/AREA attributes")
    for row in reader.iterShapeRecords():
        bounds=row.shape.bbox
        if not bounds:continue
        if len(tree.query(box(bounds[0]-.5,bounds[1]-.5,bounds[2]+.5,bounds[3]+.5)))==0:
            continue
        attrs={str(k).lower():v for k,v in row.record.as_dict().items()}
        if float(attrs["area"])<0:raise ValueError("Invalid GSHHG polygon source area")
        geom=shape(row.shape.__geo_interface__)
        if not geom.is_valid:
            from shapely import make_valid
            geom=make_valid(geom)
        candidates.append((str(attrs["id"]),float(attrs["area"]),geom))
    if not candidates:raise ValueError("GSHHG no land polygons near source-selected sites")
    return candidates,{"source_total_GSHHG_L1_polygons":len(reader),
                       "candidate_coastline_polygons":len(candidates)}


def _official_source_rows():
    """v1.260 already SHA256-locks the *survey*, not the fish, sidecar."""
    from nrmn_marine_survey_event_frame_v1_260 import source_rows
    root=Path(__file__).resolve().parents[1]
    frame=json.loads((root/"development/nrmn_marine_survey_event_frame_protocol_v1_260.json").read_text())
    if frame["source"]["survey_metadata_sidecar_sha256"]!=SOURCE_SURVEY_SHA:
        raise ValueError("Original survey metadata SHA changed")
    yield from source_rows(frame)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",required=True,type=Path)
    p.add_argument("--summary-out",required=True,type=Path)
    p.add_argument("--groups-out",required=True,type=Path)
    args=p.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    if (contract.get("schema")!="structural.nrmn_rls_atrc_marine_island_feasibility_protocol.v1_261"
        or contract["status"]!="RESPONSE_BLIND_SOURCE_LOCKED_BEFORE_MARINE_GIS_SURVEY_QUERY"
        or contract["source"]["AODN_metadata_sha256"]!=SOURCE_SURVEY_SHA
        or contract["source"]["GSHHG_zip_sha256"]!=SHORE_SHA):
        raise ValueError("Study groups or GSHHG source identity not original frozen contract")
    rows=contract["frozen_physical_groups"]
    allowed={(r["program"],r["country"],r["area"],r["location"]) for r in rows}
    if len(rows)!=20 or len(allowed)!=20 or sum(g[0]=="RLS" for g in allowed)!=10 or sum(g[0]=="ATRC" for g in allowed)!=10:
        raise ValueError("Exactly the 20 response-free original source groups required")
    sites,stats=repeated_m1_site_summary(_official_source_rows(),allowed)
    if stats["source_rows_seen"]!=36974:
        raise ValueError("Original validated AODN 36,974 survey rows changed")
    if stats["unique_valid_survey_ids"]!=36971:
        raise ValueError("Original validated 36,971 survey IDs changed")
    with tempfile.TemporaryDirectory(prefix="structural-nrmn-shore-") as folder:
        root=Path(folder)
        archive=root/"gshhg-shp-2.3.7.zip"
        checksum=_archive(archive,contract["source"])
        shp=_extract_source_shapefile(archive,root)
        polygons,meta=_nearby_source_polygons(shp,sites)
        geom_tree=STRtree([p[2] for p in polygons])
        for site in sites:
            lon,lat=site["lon"],site["lat"]
            indices=geom_tree.query(box(lon-.5,lat-.5,lon+.5,lat+.5))
            nearby=[polygons[int(i)] for i in indices]
            site.update(marine_nearest_landmass(lon,lat,nearby))
    groups=network_island_support(sites,allowed)
    for g in groups:
        expected=next(x["prior_strict_site_month_year_pairs"] for x in rows
                      if tuple(x[k] for k in ("program","country","area","location"))==
                          tuple(g[k] for k in ("program","country","area","location")))
        g["prior_all_method_pairs"]=int(expected)
        if g["strict_adjacent_year_site_month_pairs"]>expected:
            raise ValueError("Method1-only pairs cannot exceed all-method frozen same-group pairs")
    report={
        "schema":SCHEMA,"status":"ORIGINAL_SURVEY_METADATA_ONLY_GIS_MATCHED",
        "source_only_AODN_survey_sidecar_sha256":SOURCE_SURVEY_SHA,
        "GSHHG_source_sha256":checksum,"GSHHG_source_zip_bytes":SHORE_BYTES,
        "GSHHG_source_polygon_counts":meta,
        "group_count":len(groups),"groups_RLS":10,"groups_ATRC":10,
        "physical_sites_with_strict_Method1_pairs":len(sites),
        "total_strict_M1_pairs_in_20_selected_groups":sum(g["strict_adjacent_year_site_month_pairs"] for g in groups),
        "qualified_multi_island_reef_networks":sum(g["qualified_multi_island_reef_network"] for g in groups),
        "qualified_multi_island_reef_networks_RLS":sum(g["qualified_multi_island_reef_network"] and g["program"]=="RLS" for g in groups),
        "qualified_multi_island_reef_networks_ATRC":sum(g["qualified_multi_island_reef_network"] and g["program"]=="ATRC" for g in groups),
        "survey_only_census_audit":stats,
        "geology_of_islands_not_inferred":True,
        "marine_sites_not_land_population_locations":True,
        "between_island_fish_larval_dispersal_not_observed":True,
        "biological_fish_response_rows_opened":0,
        "GEB_scientific_HOLD":True,"eBird_used":False,
        "new_confirmatory_systems_admitted":0,
    }
    args.summary_out.parent.mkdir(parents=True,exist_ok=True)
    args.summary_out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    args.groups_out.parent.mkdir(parents=True,exist_ok=True)
    import csv
    with args.groups_out.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(groups[0]))
        writer.writeheader();writer.writerows(groups)
    print(json.dumps({
        "status":report["status"],
        "qualified_multi_island_reef_networks":report["qualified_multi_island_reef_networks"],
        "qualifying_RLS":report["qualified_multi_island_reef_networks_RLS"],
        "qualifying_ATRC":report["qualified_multi_island_reef_networks_ATRC"],
        "M1_strict_pairs":report["total_strict_M1_pairs_in_20_selected_groups"],
        "fish_observations_opened":0
    },sort_keys=True))

if __name__=="__main__":main()
