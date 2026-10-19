#!/usr/bin/env python3
"""Geo-only source-locked GSHHG 2.3.7 island crosswalk of 33 BioTIME study frames.

This NEVER touches BioTIME taxon, species abundance, biomass or heldout response.
Original GIS binary and sample coordinates are not written to public artifacts.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import tempfile
import urllib.request
import zipfile

import shapefile
from shapely.geometry import Point, box, shape
from shapely.ops import nearest_points
from shapely.strtree import STRtree
from pyproj import Geod

GIS_SOURCE="https://github.com/GenericMappingTools/gshhg-gmt/releases/download/2.3.7/gshhg-shp-2.3.7.zip"
GIS_BYTES=149_157_845
GIS_LAYER="GSHHS_shp/h/GSHHS_h_L1"
MIN_MAINLAND_AREA=7_000_000.0
SOURCE_MAX_BYTES=GIS_BYTES+1
GEOD=Geod(ellps="WGS84")


def site_class(poly_area_km2:float,interior_shore_distance_km:float,threshold:float=5.0,buffer:float=1.0):
    """Landmass type; GSHHG polygon is NOT an oceanic-origin classifier."""
    if not 0 <= poly_area_km2 or not 0 <= interior_shore_distance_km:
        raise ValueError("Invalid polygon area or land-interior distance")
    if poly_area_km2>=MIN_MAINLAND_AREA:
        return "mainland"
    if poly_area_km2<threshold:
        return "small_landmass_below_threshold"
    if interior_shore_distance_km<buffer:
        return "shoreline_ambiguity"
    return "island_polygon_interior"


def distance_to_polygon_boundary_km(poly,point):
    nearest=nearest_points(poly.boundary,point)[0]
    _,_,meters=GEOD.inv(point.x,point.y,nearest.x,nearest.y)
    return max(0.0,float(meters)/1000.0)


def source_archive(dest:Path):
    req=urllib.request.Request(GIS_SOURCE,headers={"User-Agent":"Structural-GSHHG-research/1.0","Accept":"application/zip"})
    h=hashlib.sha256()
    size=0
    with urllib.request.urlopen(req,timeout=180) as source,dest.open("wb") as out:
        while True:
            chunk=source.read(1_048_576)
            if not chunk: break
            size+=len(chunk)
            if size>SOURCE_MAX_BYTES:
                raise ValueError("GIS archive exceeds frozen publisher release size")
            h.update(chunk);out.write(chunk)
    if size!=GIS_BYTES:
        raise ValueError(f"GIS source file size mismatch {size} vs {GIS_BYTES}")
    return {"original_url":GIS_SOURCE,"bytes":size,"sha256":h.hexdigest(),"tag":"2.3.7"}


def extract_layer(zip_path:Path,root:Path):
    with zipfile.ZipFile(zip_path) as z:
        files={}
        for ext in (".shp",".shx",".dbf"):
            target=GIS_LAYER+ext
            matches=[name for name in z.namelist() if name.endswith(target)]
            if len(matches)!=1:
                raise ValueError(f"Original GSHHG h L1 polygon layer missing or duplicated: {target}")
            files[ext]=matches[0]
        layer_dir=root/"GSHHS_shp"/"h"
        layer_dir.mkdir(parents=True,exist_ok=True)
        for ext,member in files.items():
            (layer_dir/("GSHHS_h_L1"+ext)).write_bytes(z.read(member))
    return layer_dir/"GSHHS_h_L1.shp"


def read_sites(csv_file:Path,allowed_ids:set[str]):
    with csv_file.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    required={"study","realm","latitude","longitude","strict_matched_pair_n","distinct_matched_years"}
    if not rows or set(rows[0])!=required:
        raise ValueError("Six-field output differs from fixed physical-only R schema")
    studies={r["study"] for r in rows}
    if len(studies)!=33 or studies!=allowed_ids:
        raise ValueError("Physical GIS input not exactly the 33 frozen study-network representatives")
    observed=set()
    for r in rows:
        key=(r["study"],float(r["latitude"]),float(r["longitude"]))
        if key in observed:raise ValueError("Duplicated physical site in GIS export")
        observed.add(key)
        if not -90<=key[1]<=90 or not -180<=key[2]<=180:
            raise ValueError("Invalid site coordinate")
        if int(r["strict_matched_pair_n"])<1 or int(r["distinct_matched_years"])<1:
            raise ValueError("Unsampled physical site unexpectedly exported")
    return rows


def classify_points_with_polygons(rows:list[dict],polygon_records):
    """Pure geometry engine. polygon_records has (id, area, geometry) tuples."""
    pts=[Point(float(r["longitude"]),float(r["latitude"])) for r in rows]
    point_index=STRtree(pts)
    members=[[] for _ in rows]
    for poly_id,area,poly in polygon_records:
        if poly is None or poly.is_empty:continue
        possible=point_index.query(box(*poly.bounds))
        for idx in possible:
            idx=int(idx)
            if poly.covers(pts[idx]):
                members[idx].append((str(poly_id),float(area),poly))
    classified=[]
    for record,point,found in zip(rows,pts,members):
        if len(found)>1:
            raise ValueError(f"Multiple original GSHHG L1 polygon memberships, study={record['study']}; ambiguous")
        if not found:
            kind="water_or_no_land_polygon"
            area=None;ident=None;interior=None
        else:
            ident,area,poly=found[0]
            interior=distance_to_polygon_boundary_km(poly,point) if area<MIN_MAINLAND_AREA else 99_999.0
            kind=site_class(area,interior)
        classified.append({
            "study":record["study"],"realm":record["realm"],
            "polygon_id":ident,"polygon_area_km2":area,
            "interior_shore_distance_km":interior,
            "class":kind,
            "sensitivity_025km_1km2":bool(area is not None and area>=1 and area<MIN_MAINLAND_AREA and interior>=.25),
            "sensitivity_1km_20km2":bool(area is not None and area>=20 and area<MIN_MAINLAND_AREA and interior>=1),
            "strict_matched_pair_n":int(record["strict_matched_pair_n"])
        })
    return classified


def load_original_geography(shp_file:Path,rows):
    source=shapefile.Reader(str(shp_file))
    fields={str(descriptor[0]).casefold() for descriptor in source.fields[1:]}
    if "area" not in fields or "id" not in fields:
        raise ValueError("GSHHG original polygon 'area' or 'id' attribute missing; do not improvise")
    points=[Point(float(x["longitude"]),float(x["latitude"])) for x in rows]
    tree=STRtree(points)
    records=[]
    candidates=0
    for sr in source.iterShapeRecords():
        bbox=sr.shape.bbox
        if not bbox:continue
        possible=tree.query(box(*bbox))
        if len(possible)==0:continue
        attrs={k.casefold():v for k,v in sr.record.as_dict().items()}
        area=float(attrs["area"])
        if area<0:raise ValueError("Negative GSHHG area")
        poly=shape(sr.shape.__geo_interface__)
        if not poly.is_valid:
            # Do not repair a source geometry after inspecting biological outcomes.
            from shapely import make_valid
            poly=make_valid(poly)
        records.append((str(attrs["id"]),area,poly))
        candidates+=1
    if not records:raise ValueError("No source GSHHG polygons overlap eligible physical survey bounding boxes")
    return records,{"candidate_polygon_count":candidates,"source_total_polygons":len(source)}


def summarize(classified:list[dict],cohort:dict, gis:dict,meta:dict):
    reps=cohort["selected_study_ids_by_realm"]
    out=[]
    for realm,studies in reps.items():
        for study in studies:
            rec=[r for r in classified if r["study"]==study]
            if not rec: raise ValueError(f"Missing frozen study geometry {study}")
            counts=Counter(r["class"] for r in rec)
            good=[r for r in rec if r["class"]=="island_polygon_interior"]
            island_sites=Counter(r["polygon_id"] for r in good)
            n_islands_3plus=sum(n>=3 for n in island_sites.values())
            flags={
                "study":str(study),"realm":realm,
                "physical_strict_sites":len(rec),
                "island_polygon_sites_primary":len(good),
                "island_polygon_count_primary":len(island_sites),
                "island_polygons_with_3plus_strict_sites":n_islands_3plus,
                "inter_island_network_primary":realm in ("Terrestrial","Freshwater") and n_islands_3plus>=2,
                "mainland_sites":counts["mainland"],
                "coastal_ambiguous_sites":counts["shoreline_ambiguity"],
                "small_landmass_sites":counts["small_landmass_below_threshold"],
                "water_or_unclassified_sites":counts["water_or_no_land_polygon"],
                "sensitivity_025km_1km2_sites":sum(x["sensitivity_025km_1km2"] for x in rec),
                "sensitivity_1km_20km2_sites":sum(x["sensitivity_1km_20km2"] for x in rec),
                "original_strict_matched_pairs":sum(x["strict_matched_pair_n"] for x in rec)
            }
            out.append(flags)
    by_realm=[]
    for realm in ("Freshwater","Marine","Terrestrial"):
        r=[x for x in out if x["realm"]==realm]
        by_realm.append({
            "realm":realm,
            "network_proxies":len(r),
            "study_proxies_with_1plus_interior_island_site":sum(x["island_polygon_sites_primary"]>0 for x in r),
            "study_proxies_with_2plus_separate_island_polygons":sum(x["island_polygon_count_primary"]>=2 for x in r),
            "strict_multi_island_sampling_networks":sum(x["inter_island_network_primary"] for x in r)
        })
    report={
        "schema":"structural.biotime_gshhg_island_crosswalk.v1_256",
        "evidence_class":"GEOGRAPHY_ONLY_NO_TAXON_OR_ECOLOGICAL_RESPONSE",
        "biotime_source_doi":"10.5281/zenodo.15222193",
        "gshhg_source":gis,
        "original_gshhg_candidate_polygon_counts":meta,
        "study_network_candidates":33,
        "n_site_points":len(classified),
        "study_counts_by_realm":by_realm,
        "strict_multi_island_study_network_total":sum(x["strict_multi_island_sampling_networks"] for x in by_realm),
        "global_oceanic_vs_continental_island_origin_verified":False,
        "mainland_and_coastline_uncertainty_reported":True,
        "marine_sampling_sites_never_relabelled_as_island_land_studies":True,
        "future_33_study_species_responses_opened":0,
        "original_mammal_heldout_reopened":False,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }
    return report,out


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sites",required=True,type=Path)
    p.add_argument("--cohort",required=True,type=Path)
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--summary-out",required=True,type=Path)
    p.add_argument("--studies-out",required=True,type=Path)
    args=p.parse_args()
    cohort=json.loads(args.cohort.read_text())
    proto=json.loads(args.protocol.read_text())
    if proto.get("schema")!="structural.biotime_gshhg_island_crosswalk_protocol.v1_256":
        raise ValueError("Not frozen GSHHG source protocol")
    if proto["gshhg_source"]["exact_url"]!=GIS_SOURCE or proto["gshhg_source"]["github_asset_bytes"]!=GIS_BYTES:
        raise ValueError("GSHHG original tagged source identity changed")
    if proto["selected_studies"]!="development/biotime_v2_conservative_network_cohort_v1_255.json":
        raise ValueError("Study identifiers not frozen before GIS access")
    ids={str(x) for members in cohort["selected_study_ids_by_realm"].values() for x in members}
    rows=read_sites(args.sites,ids)
    with tempfile.TemporaryDirectory(prefix="structural-gshhg-") as td:
        root=Path(td)
        zipfile_path=root/"gshhg-shp-2.3.7.zip"
        gis=source_archive(zipfile_path)
        shp=extract_layer(zipfile_path,root)
        records,poly_info=load_original_geography(shp,rows)
        classified=classify_points_with_polygons(rows,records)
    summary,studies=summarize(classified,cohort,gis,poly_info)
    args.summary_out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    with args.studies_out.open("w",encoding="utf-8",newline="") as f:
        if not studies:raise ValueError("No study summaries")
        w=csv.DictWriter(f,fieldnames=list(studies[0]))
        w.writeheader();w.writerows(studies)
    print(json.dumps({"network_count":33,
                      "sites":len(classified),
                      "strict_multi_island":summary["strict_multi_island_study_network_total"],
                      "source_sha256":gis["sha256"],
                      "no_species_labels":True},sort_keys=True))

if __name__=="__main__":main()
