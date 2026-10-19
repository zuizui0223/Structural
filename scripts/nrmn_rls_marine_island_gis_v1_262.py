#!/usr/bin/env python3
"""Geography-only RLS Method-1 repeated reef locations near official GSHHG islands.

READS: AODN original eleven survey-event fields and official GSHHG coastlines.
NEVER READS: fish species labels, biomass, fish observations or mammal heldout.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import statistics
import tempfile
import urllib.request
import zipfile

import shapefile
from shapely.geometry import Point, box, shape
from shapely.ops import nearest_points
from shapely.strtree import STRtree
from pyproj import Geod

from nrmn_marine_survey_event_frame_v1_260 import physical_row, source_rows
from nrmn_rls_method1_physical_v1_261 import method_codes

SCHEMA="structural.nrmn_rls_marine_island_gis.v1_262"
SOURCE="https://github.com/GenericMappingTools/gshhg-gmt/releases/download/2.3.7/gshhg-shp-2.3.7.zip"
SOURCE_SHA256="8dbbe7e071e77e9e75f2d639239099ebca8d5c16d6a07df8169729d49f15cf41"
SOURCE_BYTES=149157845
GIS_LAYER="GSHHS_shp/h/GSHHS_h_L1"
GEOD=Geod(ellps="WGS84")

def validate_geometry_protocol(proto):
    if proto.get("schema")!="structural.nrmn_rls_marine_island_geo_protocol.v1_262":
        raise ValueError("Original pre-fish marine island protocol changed")
    g=proto["geography"]
    s=proto["official_data"]
    exact=(g["operational_primary_island_area_min_km2"]==0.1 and
           g["operational_mainland_area_min_km2"]==7000000 and
           g["max_site_to_island_shore_km"]==5 and
           g["mainland_versus_island_exclusion_margin_km"]==1 and
           g["two_nearest_island_ambiguity_margin_km"]==1 and
           g["source_bounding_box_selection_buffer_degrees"]==2 and
           s["GSHHG_zip_sha256"]==SOURCE_SHA256 and
           s["GSHHG_zip_bytes"]==SOURCE_BYTES and
           s["source_GIS"]==SOURCE)
    if not exact:raise ValueError("Modified source geometry threshold or original GIS source; fail closed")
    return g

def _geodesic_shore_km(point,geometry):
    try:
        q=nearest_points(geometry.boundary,point)[0]
        _,_,meters=GEOD.inv(point.x,point.y,q.x,q.y)
    except Exception as exc:
        raise ValueError("Cannot calculate source coastline distance") from exc
    return abs(float(meters))/1000

def classify_marine_site(lat,lon,polygons,protocol,*,area_floor=None,max_km=None):
    g=validate_geometry_protocol(protocol)
    minimum=g["operational_primary_island_area_min_km2"] if area_floor is None else float(area_floor)
    reach=g["max_site_to_island_shore_km"] if max_km is None else float(max_km)
    if minimum not in (0.01,0.1,1,5) or reach not in (2,5,10):
        raise ValueError("Unregistered marine island sensitivity threshold")
    if not (-90<=float(lat)<=90 and -180<=float(lon)<=180):
        raise ValueError("Invalid RLS survey coordinate")
    pt=Point(float(lon),float(lat))
    islands=[]
    mainland_dist=float("inf")
    inside=False
    for polygon_id,area,geom in polygons:
        area=float(area)
        if geom is None or geom.is_empty:continue
        if geom.covers(pt):
            inside=True
        # Candidates have been preselected by source-independent geographic bounding.
        d=_geodesic_shore_km(pt,geom)
        if area>=g["operational_mainland_area_min_km2"]:
            mainland_dist=min(mainland_dist,d)
        elif area>=minimum:
            islands.append((d,str(polygon_id),area))
    if inside:
        return {"class":"marine_location_inside_landmass_polygon","island_id":None}
    islands.sort(key=lambda x:(x[0],x[1]))
    if mainland_dist<=1:
        return {"class":"mainland_or_ambiguous","island_id":None}
    if not islands or islands[0][0]>reach:
        return {"class":"no_eligible_island_within_5km","island_id":None}
    first=islands[0]
    if mainland_dist<=first[0]+g["mainland_versus_island_exclusion_margin_km"]:
        return {"class":"mainland_or_ambiguous","island_id":None}
    if len(islands)>1 and islands[1][0]<=10 and (islands[1][0]-first[0])<=g[
        "two_nearest_island_ambiguity_margin_km"]:
        return {"class":"ambiguous_near_two_islands","island_id":None}
    return {"class":"island_nearby","island_id":first[1]}

def frozen_ten(method_proto):
    if method_proto.get("schema")!="structural.nrmn_rls_method1_physical_protocol.v1_261":
        raise ValueError("Exact ten source-frozen RLS regions unavailable")
    groups=method_proto["frozen_RLS_geographic_groups"]
    out={}
    for g in groups:
        key=tuple(str(g[k]).casefold() for k in ("country","area","location"))
        if key in out:raise ValueError("Frozen RLS region duplication")
        out[key]=int(g["previous_strict_all_method_pairs"])
    if len(out)!=10:raise ValueError("Expected exactly ten prior identified physical RLS regions")
    return out

def strict_eligible_RLS_sites(rows,geo_contract,method_proto):
    validate_geometry_protocol(geo_contract)
    groups=frozen_ten(method_proto)
    seen=set()
    site_obs=defaultdict(list)
    surveys_by_site_month=Counter()
    all_sites=defaultdict(list)
    stats=Counter()
    for raw in rows:
        stats["source_survey_rows_seen"]+=1
        try:
            sid,pg,parts,d,lat,lon,methods=physical_row(raw)
        except ValueError:
            stats["invalid_physical_survey"]+=1
            continue
        if sid in seen:
            stats["duplicate_survey_id"]+=1
            continue
        seen.add(sid)
        if pg!="RLS" or parts[:3] not in groups:continue
        key=(parts[:3],parts[3])
        all_sites[key].append((lat,lon))
        codes=method_codes(methods)
        if codes is None:
            stats["unparseable_source_method"]+=1
            continue
        if 1 not in codes:continue
        stats["valid_method1_survey_events_in_frozen_10_groups"]+=1
        site_obs[key].append((lat,lon))
        surveys_by_site_month[(key,d.year,d.month)]+=1
    out=[]
    for site,xy in site_obs.items():
        all_xy=all_sites[site]
        lat_span=max(x[0] for x in all_xy)-min(x[0] for x in all_xy)
        lon_span=max(x[1] for x in all_xy)-min(x[1] for x in all_xy)
        if lat_span>0.01 or lon_span>0.01:
            stats["unstable_site_code_excluded"]+=1
            continue
        n=0;years=set()
        for (key,y,m),k in surveys_by_site_month.items():
            if key!=site or k<2 or surveys_by_site_month.get((site,y+1,m),0)<2:continue
            n+=1;years.add(y)
        if not n:continue
        group,sitecode=site
        out.append({
          "program":"RLS","country":group[0],"area":group[1],"location":group[2],
          "lat":statistics.median(x[0] for x in xy),
          "lon":statistics.median(x[1] for x in xy),
          "strict_pairs":n,
          # No source_site_label, survey_id or coordinates allowed in OUTBOUND artifact.
          "source_site_label":sitecode
        })
    stats["method1_eligible_unique_sites_in_frozen_10_groups"]=len(out)
    stats["method1_strict_pairs_in_frozen_10_groups"]=sum(r["strict_pairs"] for r in out)
    stats["fish_responses_read"]=False
    if stats["method1_strict_pairs_in_frozen_10_groups"]>sum(groups.values()):
        raise ValueError("Method1 strict pairs exceed frozen method-agnostic prior sample frame")
    return out,dict(stats)

def summarize_island_regions(sites,polygon_records,geo_contract,method_proto):
    groups=frozen_ten(method_proto)
    assigned=defaultdict(list)
    for site in sites:
        k=tuple(site[x] for x in ("country","area","location"))
        if k not in groups:raise ValueError("Unfrozen survey geography found in site list")
        result=classify_marine_site(site["lat"],site["lon"],polygon_records,geo_contract)
        assigned[k].append((site,result))
    output=[]
    for key,old in groups.items():
        choices=assigned[key]
        classes=Counter(result["class"] for _,result in choices)
        per_island=defaultdict(list)
        pairs=0
        for site,result in choices:
            if result["class"]=="island_nearby":
                per_island[result["island_id"]].append(site)
                pairs+=site["strict_pairs"]
        eligible=sum(len(site_rows)>=3 for site_rows in per_island.values())
        q=(eligible>=2 and pairs>=10)
        sensitivities={}
        for area,km in ((0.01,5),(1,5),(5,5),(0.1,2),(0.1,10)):
            yes=sum(
                classify_marine_site(s["lat"],s["lon"],polygon_records,geo_contract,
                                     area_floor=area,max_km=km)["class"]=="island_nearby"
                for s,_ in choices
            )
            sensitivities[f"area_{area:g}km2_distance_{km:g}km"]=yes
        output.append({
            "country":key[0],"area":key[1],"location":key[2],
            "pre_frozen_method_agnostic_strict_pairs":old,
            "physical_RLS_method1_strict_sites":len(choices),
            "method1_strict_site_month_year_pairs":sum(s["strict_pairs"] for s,_ in choices),
            "marine_sites_mapped_near_any_island":classes["island_nearby"],
            "marine_sites_near_mainland_or_ambiguous":classes["mainland_or_ambiguous"],
            "marine_land_interior_flags":classes["marine_location_inside_landmass_polygon"],
            "ambiguous_near_multiple_island_coastlines":classes["ambiguous_near_two_islands"],
            "marine_sites_no_eligible_island_within_5km":classes["no_eligible_island_within_5km"],
            "island_polygons_with_3plus_eligible_sites":eligible,
            "distinct_mapped_nearest_island_polygons":len(per_island),
            "method1_annual_pairs_at_island_assigned_sites":pairs,
            "two_island_survey_geometry_eligible":q,
            "sensitivity_counts":sensitivities
        })
    output.sort(key=lambda x:(-x["method1_strict_site_month_year_pairs"],x["country"],x["location"]))
    return {
        "schema":SCHEMA,
        "status":"SOURCE_VERIFIED_MARINE_SHORELINE_PHYSICAL_ONLY",
        "frozen_ten_RLS_regions":output,
        "two_island_survey_geometry_qualified_regions":sum(x["two_island_survey_geometry_eligible"] for x in output),
        "fish_biological_rows_accessed":0,
        "actual_island_colonization_measured":False,
        "original_global_mammal_holdout_reopened":False,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def download_GSHHG(zip_path):
    r=urllib.request.Request(SOURCE,headers={
        "User-Agent":"Structural-marine-reef-geography/1.0","Accept":"application/zip"
    })
    h=hashlib.sha256();size=0
    with urllib.request.urlopen(r,timeout=180) as stream,zip_path.open("wb") as out:
        while chunk:=stream.read(1_048_576):
            size+=len(chunk)
            if size>SOURCE_BYTES:raise ValueError("Original GSHHG official archive too large")
            h.update(chunk);out.write(chunk)
    if size!=SOURCE_BYTES or h.hexdigest()!=SOURCE_SHA256:
        raise ValueError("Official GSHHG tag-locked 2.3.7 ZIP source changed; STOP")
    return {"url":SOURCE,"tag":"2.3.7","bytes":size,"sha256":h.hexdigest()}

def load_nearby_original_GSHHG(zip_path,root,sites,geo_contract):
    validate_geometry_protocol(geo_contract)
    with zipfile.ZipFile(zip_path) as z:
        out_dir=root/"GSHHS_shp"/"h";out_dir.mkdir(parents=True,exist_ok=True)
        for ext in (".shp",".shx",".dbf"):
            filename=GIS_LAYER+ext
            candidates=[x for x in z.namelist() if x.endswith(filename)]
            if len(candidates)!=1:
                raise ValueError("Official GSHHG high resolution L1 sidecar missing")
            (out_dir/("GSHHS_h_L1"+ext)).write_bytes(z.read(candidates[0]))
    shp=shapefile.Reader(str(out_dir/"GSHHS_h_L1.shp"))
    cols={str(x[0]).casefold() for x in shp.fields[1:]}
    if not {"area","id"}<=cols:
        raise ValueError("GSHHG original area/id attributes changed")
    points=[Point(s["lon"],s["lat"]) for s in sites]
    if not points:raise ValueError("No prior physically sampled RLS sites")
    index=STRtree(points)
    expanded=geo_contract["geography"]["source_bounding_box_selection_buffer_degrees"]
    records=[]
    n_candidates=0
    n_invalid=0
    for sr in shp.iterShapeRecords():
        bbox=sr.shape.bbox
        if not bbox:continue
        possible=index.query(box(bbox[0]-expanded,bbox[1]-expanded,
                                 bbox[2]+expanded,bbox[3]+expanded))
        if len(possible)==0:continue
        n_candidates+=1
        attrs={str(k).casefold():v for k,v in sr.record.as_dict().items()}
        area=float(attrs["area"])
        if area<0:raise ValueError("Negative official GSHHG landmass area")
        poly=shape(sr.shape.__geo_interface__)
        if not poly.is_valid:
            from shapely import make_valid
            poly=make_valid(poly);n_invalid+=1
        if poly.is_empty:continue
        records.append((str(attrs["id"]),area,poly))
    if not records:raise ValueError("No GSHHG polygons around original RLS site coordinates")
    return records,{"source_original_L1_polygons":len(shp),
                    "nearby_candidate_polygon_bounds":n_candidates,
                    "repaired_invalid_polygons":n_invalid,
                    "eligible_site_coordinates_processed":len(points)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--method-protocol",type=Path,required=True)
    p.add_argument("--survey-contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    geoproto=json.loads(args.protocol.read_text(encoding="utf-8"))
    meth=json.loads(args.method_protocol.read_text(encoding="utf-8"))
    source=json.loads(args.survey_contract.read_text(encoding="utf-8"))
    validate_geometry_protocol(geoproto)
    if (source.get("schema")!="structural.nrmn_marine_event_frame_contract.v1_260"
        or geoproto["official_data"]["survey_sidecar_sha256"]!=source["source"]["survey_metadata_sidecar_sha256"]
        or geoproto["official_data"]["methods_protocol"]!="development/nrmn_rls_method1_physical_protocol_v1_261.json"):
        raise ValueError("Original AODN method source reference mismatch")
    try:
        physical,frame=strict_eligible_RLS_sites(source_rows(source),geoproto,meth)
        if frame["source_survey_rows_seen"]!=36974 or frame["method1_strict_pairs_in_frozen_10_groups"]!=442:
            raise ValueError("Frozen 10-group original physical source denominator unexpectedly changed")
        with tempfile.TemporaryDirectory(prefix="structural-nrmn-gshhg-") as tmp:
            root=Path(tmp);z=root/"gshhg-2.3.7.zip"
            src_info=download_GSHHG(z)
            polygons,geo_info=load_nearby_original_GSHHG(z,root,physical,geoproto)
            result=summarize_island_regions(physical,polygons,geoproto,meth)
        result["source_GSHHG"]=src_info
        result["source_nearby_polygon_scope"]=geo_info
        result["source_survey_rows_seen"]=frame["source_survey_rows_seen"]
        result["method1_strict_pairs_in_frozen_10_groups"]=frame["method1_strict_pairs_in_frozen_10_groups"]
        result["method1_eligible_unique_sites_in_frozen_10_groups"]=frame[
            "method1_eligible_unique_sites_in_frozen_10_groups"]
        result["source_survey_metadata_sha256"]=geoproto["official_data"]["survey_sidecar_sha256"]
    except Exception as exc:
        result={
            "schema":SCHEMA,"status":"SOURCE_ONLY_STOP_NO_ISLAND_ADMISSION",
            "error_type":type(exc).__name__,"error":str(exc)[:500],
            "fish_biological_rows_accessed":0,
            "GEB_scientific_HOLD":True
        }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in (
        "status","two_island_survey_geometry_qualified_regions",
        "method1_eligible_unique_sites_in_frozen_10_groups","error"
    )},sort_keys=True))
    if result["status"]!="SOURCE_VERIFIED_MARINE_SHORELINE_PHYSICAL_ONLY":
        raise SystemExit(2)

if __name__=="__main__":
    main()
