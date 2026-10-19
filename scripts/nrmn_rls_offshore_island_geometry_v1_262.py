#!/usr/bin/env python3
"""Marine-appropriate AODN RLS Method 1 reef-to-island physical geometry gate.

No fish species, abundance, larval identity or recipient success values are read.
Official AODN survey fields are joined to official GSHHG v2.3.7 L1 coastline
ONLY after the ten regional identities and all thresholds have been frozen.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import statistics
import tempfile
import urllib.request
import zipfile

import shapefile
from shapely.geometry import Point,box,shape
from shapely.ops import nearest_points
from shapely.strtree import STRtree
from shapely import make_valid
from pyproj import Geod

from nrmn_marine_survey_event_frame_v1_260 import source_rows, physical_row
from nrmn_rls_method1_physical_v1_261 import method_codes

PROTOCOL_SCHEMA="structural.nrmn_rls_offshore_island_geometry_protocol.v1_262"
RESULT_SCHEMA="structural.nrmn_rls_offshore_island_geometry_result.v1_262"
GSHHG_URL="https://github.com/GenericMappingTools/gshhg-gmt/releases/download/2.3.7/gshhg-shp-2.3.7.zip"
GSHHG_SIZE=149_157_845
GSHHG_SHA="8dbbe7e071e77e9e75f2d639239099ebca8d5c16d6a07df8169729d49f15cf41"
SHAPE_LAYER="GSHHS_shp/h/GSHHS_h_L1"
GEOD=Geod(ellps="WGS84")


def shoreline_type(area):
    """GSHHG geometric landmass size classes; geology/colonization are NOT inferred."""
    if area<0: raise ValueError("Negative original GSHHG polygon area")
    if area<5: return "tiny_islet"
    if area>=7_000_000: return "mainland"
    return "island"


def nearest_island_assignment(is_inside_land, island_distances, mainland_distance, small_islet_distance,
                              max_shore_km=5.0, min_margin_km=1.0):
    """No nearest-island assignment if another shoreline is comparably close."""
    if is_inside_land: return ("on_land_or_uncertain",None)
    items=sorted((float(distance),str(ident)) for ident,distance in island_distances)
    if items and items[0][0]<=max_shore_km:
        nearest_d,nearest_id=items[0]
        competitors=[float(z[0]) for z in items[1:]]
        if mainland_distance is not None: competitors.append(float(mainland_distance))
        if small_islet_distance is not None:competitors.append(float(small_islet_distance))
        if any(x-nearest_d<min_margin_km for x in competitors):
            return ("ambiguous_competing_coast",None)
        return ("near_island",nearest_id)
    if mainland_distance is not None and mainland_distance<=max_shore_km:
        return ("mainland_nearshore",None)
    if small_islet_distance is not None and small_islet_distance<=max_shore_km:
        return ("small_islet_nearshore",None)
    return ("offshore_or_other",None)


def summarize_regions(sites,group_order=None):
    """Aggregate survey IDs and offshore island polygon identities only."""
    by_group=defaultdict(list)
    for site in sites:
        by_group[site["group"]].append(site)
    keys=group_order if group_order is not None else sorted(by_group)
    out=[]
    for group in keys:
        members=by_group.get(group,[])
        seen=set()
        islands=defaultdict(set)
        labels=Counter()
        for record in members:
            site=str(record["site_key"])
            if site in seen: raise ValueError("Same physical site counted twice")
            seen.add(site)
            label=record["assignment"]
            labels[label]+=1
            if label=="near_island" and record["island_id"] is not None:
                islands[str(record["island_id"])].add(site)
        n_islands=sum(len(v)>=3 for v in islands.values())
        out.append({
            "program":group[0],
            "country":group[1],
            "area":group[2],
            "location":group[3],
            "strict_repeated_method1_sites":len(members),
            "strict_site_month_year_pair_count":sum(int(r["strict_pairs"]) for r in members),
            "near_island_repeated_site_count":labels["near_island"],
            "candidate_assigned_island_polygons":len(islands),
            "separate_islands_with_3plus_repeated_sites":n_islands,
            "on_land_or_uncertain_sites":labels["on_land_or_uncertain"],
            "ambiguous_competing_coast_sites":labels["ambiguous_competing_coast"],
            "mainland_nearshore_sites":labels["mainland_nearshore"],
            "small_islet_nearshore_sites":labels["small_islet_nearshore"],
            "offshore_or_other_sites":labels["offshore_or_other"],
            "qualified_archipelago_sampling_network":n_islands>=2,
        })
    return out


def strict_RLS_repeat_sites(rows,contract,method1_protocol):
    """Retrieve site medians only transiently; no point positions emitted."""
    if contract.get("schema")!=PROTOCOL_SCHEMA:
        raise ValueError("Frozen marine island protocol missing")
    frozen=method1_protocol["frozen_RLS_geographic_groups"]
    expected={tuple(x[k].casefold() for k in ("country","area","location")):
              int(x["previous_strict_all_method_pairs"]) for x in frozen}
    if len(expected)!=10: raise ValueError("Expected ten fixed Method1 source regions")
    n=0;valid=0;rls=0;seen=set()
    all_source_coords=defaultdict(list)
    m1_event_counts=Counter()
    for r in rows:
        n+=1
        try:
            sid,program,parts,d,lat,lon,methods=physical_row(r)
        except ValueError:
            continue
        if sid in seen:continue
        seen.add(sid);valid+=1
        if program!="RLS":continue
        rls+=1
        if parts[:3] not in expected:continue
        site=(program,)+parts
        all_source_coords[site].append((lat,lon))
        codes=method_codes(methods)
        if codes is not None and 1 in codes:
            m1_event_counts[(site,d.year,d.month)]+=1
    if (n,valid,rls)!=(36974,36971,20657):
        raise ValueError("Public AODN physical survey population deviates from v1.260 source freeze")
    by_site=Counter()
    for (site,year,month),value in m1_event_counts.items():
        if value>=2 and m1_event_counts.get((site,year+1,month),0)>=2:
            by_site[site]+=1
    outputs=[]
    for site,pairs in by_site.items():
        coords=all_source_coords[site]
        if not coords: raise ValueError("Missing physical coordinates")
        lats=[x[0] for x in coords];lons=[x[1] for x in coords]
        if max(lats)-min(lats)>0.01 or max(lons)-min(lons)>0.01:
            continue
        outputs.append({
            "group":site[:4],
            "site_key":site[-1],
            "lat":statistics.median(lats),
            "lon":statistics.median(lons),
            "strict_pairs":pairs,
        })
    found=Counter()
    for rec in outputs:found[rec["group"][1:]]+=rec["strict_pairs"]
    for group,prior in expected.items():
        if found[group]!=prior:
            raise ValueError("Source-locked ten Method1 strict pairs differ from first v1.261 run: "+str(group))
    if len(outputs)<30: raise ValueError("Too few physical eligible reef sites")
    return outputs,{
        "input_survey_metadata_rows":n,
        "unique_valid_source_survey_ids":valid,
        "RLS_source_survey_ids":rls,
        "ten_fixed_group_strict_method1_pairs":sum(found.values()),
        "ten_fixed_group_repeated_method1_sites":len(outputs)
    }


def download_gshhg(dst):
    req=urllib.request.Request(GSHHG_URL,headers={"User-Agent":"Structural-Marine-Survey-GIS/1.0",
                                                   "Accept":"application/zip"})
    digest=hashlib.sha256()
    size=0
    with urllib.request.urlopen(req,timeout=180) as r,dst.open("wb") as f:
        while True:
            block=r.read(1_048_576)
            if not block:break
            size+=len(block)
            if size>GSHHG_SIZE:raise ValueError("GSHHG release exceeds frozen original byte size")
            digest.update(block);f.write(block)
    if size!=GSHHG_SIZE or digest.hexdigest()!=GSHHG_SHA:
        raise ValueError("Original GSHHG published release bytes have changed; STOP")
    return {"tag":"2.3.7","bytes":size,"sha256":digest.hexdigest()}


def extract_original_land(zip_path,root):
    with zipfile.ZipFile(zip_path) as z:
        folder=root/"GSHHS_shp"/"h"
        folder.mkdir(parents=True,exist_ok=True)
        for ext in (".shp",".shx",".dbf"):
            matches=[x for x in z.namelist() if x.endswith(SHAPE_LAYER+ext)]
            if len(matches)!=1:
                raise ValueError("GSHHG L1 original source polygon file not unique")
            (folder/("GSHHS_h_L1"+ext)).write_bytes(z.read(matches[0]))
    return folder/"GSHHS_h_L1.shp"


def coast_distance_km(point,geometry):
    boundary=nearest_points(point,geometry.boundary)[1]
    _,_,distance=GEOD.inv(point.x,point.y,boundary.x,boundary.y)
    return max(0.0,float(distance)/1000)


def coastline_assignments(points,shape_path):
    """Only source polygons within wide non-outcome buffer around eligible marine sites."""
    p=[Point(x["lon"],x["lat"]) for x in points]
    buffer_boxes=[box(x["lon"]-.8,x["lat"]-.45,x["lon"]+.8,x["lat"]+.45) for x in points]
    spatial=STRtree(buffer_boxes)
    # Retain only nearby source polygon distances for each point, not the geometry.
    islands=[[] for _ in points]
    mainlands=[[] for _ in points]
    small=[[] for _ in points]
    onland=[False for _ in points]
    reader=shapefile.Reader(str(shape_path))
    fields={str(descriptor[0]).casefold() for descriptor in reader.fields[1:]}
    if not {"id","area"}<=fields:
        raise ValueError("GSHHG publisher polygon area/id schema changed")
    candidates=0
    for sr in reader.iterShapeRecords():
        if not sr.shape.bbox:continue
        indexes=spatial.query(box(*sr.shape.bbox))
        if not len(indexes):continue
        attrs={k.casefold():v for k,v in sr.record.as_dict().items()}
        ident=str(attrs["id"])
        area=float(attrs["area"])
        cls=shoreline_type(area)
        polygon=shape(sr.shape.__geo_interface__)
        if not polygon.is_valid:polygon=make_valid(polygon)
        if polygon.is_empty:continue
        candidates+=1
        for idx in indexes:
            i=int(idx)
            point=p[i]
            if polygon.covers(point):
                onland[i]=True
                continue
            d=coast_distance_km(point,polygon)
            # 10 km protects predeclared distance sensitivity; don't include
            # distant coast as a false candidate for the 5 km primary.
            if d>10:continue
            if cls=="island":islands[i].append((ident,d))
            elif cls=="mainland":mainlands[i].append(d)
            else:small[i].append(d)
    if candidates<=0:raise ValueError("No GSHHG land polygons intersect original reef physical region envelopes")
    classified=[]
    for rec,ins,isl,main,tiny in zip(points,onland,islands,mainlands,small):
        status,ident=nearest_island_assignment(
            is_inside_land=ins,island_distances=isl,
            mainland_distance=min(main,default=None),
            small_islet_distance=min(tiny,default=None))
        classified.append({
            "group":rec["group"],"site_key":rec["site_key"],"strict_pairs":rec["strict_pairs"],
            "assignment":status,"island_id":ident
        })
    return classified,{"publisher_polygon_count":len(reader),
                       "candidate_shoreline_polygons":candidates,
                       "site_points_input":len(p),
                       "site_points_output":len(classified)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--method1",type=Path,required=True)
    parser.add_argument("--source-frame",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding="utf-8"))
    method1=json.loads(args.method1.read_text(encoding="utf-8"))
    frame=json.loads(args.source_frame.read_text(encoding="utf-8"))
    if (protocol.get("schema")!=PROTOCOL_SCHEMA or
        method1.get("schema")!="structural.nrmn_rls_method1_physical_protocol.v1_261" or
        frame.get("schema")!="structural.nrmn_marine_event_frame_contract.v1_260" or
        frame["source"]["survey_metadata_sidecar_sha256"] != protocol["source"]["survey_sidecar_sha256"] or
        protocol["source"]["GSHHG_sha256"]!=GSHHG_SHA):
        raise ValueError("Original survey/geography source authority changed")
    points,frame_info=strict_RLS_repeat_sites(source_rows(frame),protocol,method1)
    with tempfile.TemporaryDirectory(prefix="structural-nrmn-offshore-islands-") as tmp:
        root=Path(tmp);archive=root/"gshhg-v2.3.7.zip"
        geometry_source=download_gshhg(archive)
        land=extract_original_land(archive,root)
        geo,geo_detail=coastline_assignments(points,land)
    original_order=[
        ("RLS",item["country"],item["area"],item["location"]) for
        item in method1["frozen_RLS_geographic_groups"]]
    region_results=summarize_regions(geo,group_order=original_order)
    if len(region_results)!=10 or sum(r["strict_site_month_year_pair_count"]
                                     for r in region_results)!=442:
        raise ValueError("Unexpected 10-region survey denominator after island proximity classification")
    out={
        "schema":RESULT_SCHEMA,"status":"SOURCE_ONLY_OFFSHORE_ISLAND_PROXIMITY_AUDIT",
        "source_frame":frame_info,"GSHHG_source":geometry_source,
        "GSHHG_polygon_metadata":geo_detail,
        "region_results":region_results,
        "primary_multi_island_RLS_region_count":sum(r["qualified_archipelago_sampling_network"] for r in region_results),
        "precise_geological_oceanic_origin_known":False,
        "natal_reef_fish_dispersal_measured":False,
        "biological_fish_species_or_total_accesses":0,
        "new_confirmatory_systems_admitted":0,
        "eBird_used":False,"GEB_scientific_HOLD":True
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
                        encoding="utf-8")
    print(json.dumps({"status":out["status"],
        "Method1_eligible_site_count":geo_detail["site_points_input"],
        "ten_regions":len(region_results),
        "strict_method1_survey_pairs":frame_info["ten_fixed_group_strict_method1_pairs"],
        "multi_island_RLS_regions":out["primary_multi_island_RLS_region_count"],
        "species_observations_accessed":0},sort_keys=True))


if __name__=="__main__":main()
