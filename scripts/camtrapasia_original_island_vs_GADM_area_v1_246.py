#!/usr/bin/env python3
"""Check source-island Area against nearest original-vintage GADM polygon area, no species data."""
import argparse,csv,hashlib,json,sys
from collections import Counter
from pathlib import Path
import pyproj
from shapely.geometry import Point
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from check_camtrapasia_gadm36_landmass_v1_243 import public_polygon_source,read_geo,SOURCE
from camtrapasia_gadm36_nearest_land_v1_245 import point_component,nearest_country_component
GEOD=pyproj.Geod(ellps="WGS84")
SHA="b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8"
def source_area_map(path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=SHA:raise ValueError("Response-safe source area changed")
    with path.open(encoding="utf-8",newline="") as f:
        rdr=csv.DictReader(f)
        if not {"ID","Area"}.issubset(rdr.fieldnames or []):raise ValueError("Frozen island area column missing")
        rows=list(rdr)
    if len(rows)!=5592:raise ValueError("Original island source universe changed")
    def num(v):return float.fromhex(v) if "0x" in v.lower() else float(v)
    d={r["ID"]:num(r["Area"]) for r in rows}
    if len(d)!=5592 or any(a<=0 for a in d.values()):raise ValueError("Invalid original island areas")
    return d
def geodetic_polygon_area_km2(geom):
    area,perimeter=GEOD.geometry_area_perimeter(geom)
    val=abs(area)/1000000.
    if not val>0:raise ValueError("Invalid GADM36 component area")
    return val
def inspect(candidates,coords,areas):
    if candidates.get("status")!="PASS_FROZEN_15_CENTROID_NEAR_CANDIDATES_METADATA_ONLY":
        raise ValueError("Frozen v241 candidates not PASS")
    rows=candidates["candidate_site_metadata"]
    if len(rows)!=15 or len({r["nearest_original_heldout_island_ID"] for r in rows})!=10:
        raise ValueError("Frozen 10 island candidates changed")
    countries={k:(polys,STRtree(polys)) for k,(polys,meta) in
      {c:public_polygon_source(c) for c in SOURCE}.items()}
    out=[];IDmemo={}
    for r in rows:
        island=r["nearest_original_heldout_island_ID"]
        polys,tree=countries[r["country"]]
        center=coords[island]
        comp=point_component(center,polys,tree)
        centroid_off=comp is None
        if centroid_off:comp=nearest_country_component(center,polys,tree)
        if comp is None:raise ValueError("No unique nearest country polygon candidate")
        polyarea=geodetic_polygon_area_km2(polys[comp])
        origarea=areas[island]
        ratio=max(polyarea/origarea,origarea/polyarea)
        studycomp=point_component((r["X_long"],r["Y_lat"]),polys,tree)
        same=(studycomp==comp)
        record={"source_survey_id":r["survey_id"],"source_region":r["landscape"],
            "original_island_ID":island,"source_island_area_km2":origarea,
            "GADM36_component_area_km2":polyarea,"area_ratio_max_min":ratio,
            "heldout_centroid_was_outside_source_country_land":centroid_off,
            "study_is_on_selected_or_nearest_component":same,
            "within_2fold_area_ratio":ratio<=2,
            "within_1p5fold_area_ratio":ratio<=1.5,
            "within_5fold_area_ratio":ratio<=5}
        if island in IDmemo and (IDmemo[island]["GADM36_component_area_km2"]!=polyarea or IDmemo[island]["source_island_area_km2"]!=origarea):
            raise ValueError("Source island mapped to inconsistent source polygons")
        IDmemo[island]=record
        out.append(record)
    counts={
        "study_same_component_including_offland_source_nearest":sum(r["study_is_on_selected_or_nearest_component"] for r in out),
        "study_same_component_and_area_ratio_le_2":sum(r["study_is_on_selected_or_nearest_component"] and r["within_2fold_area_ratio"] for r in out),
        "strict_original_centroid_inside_same_component_and_area_ratio_le_2":sum(r["study_is_on_selected_or_nearest_component"] and not r["heldout_centroid_was_outside_source_country_land"] and r["within_2fold_area_ratio"] for r in out),
        "offland_source_nearest_component_same_and_area_ratio_le_2":sum(r["study_is_on_selected_or_nearest_component"] and r["heldout_centroid_was_outside_source_country_land"] and r["within_2fold_area_ratio"] for r in out)
    }
    return {"schema":"structural.camtrapasia_original_island_area_polygon_source_screen.v1_246",
     "status":"PASS_FROZEN_GADM36_ISLAND_AREA_CONSISTENCY_CHECK",
     "source_survey_centers":15,"original_nearest_island_IDs":10,
     "area_geodetic_ellipsoid":"WGS84",
     "summary":counts,"individual_study_geography_only":out,
     "no_original_polygon_ID_verified":True,
     "source_camera_detection_rows_read":0,
     "original_mammal_heldout_response_read":0,
     "original_predictions_scored":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("candidates",type=Path);p.add_argument("source",type=Path);p.add_argument("--out",type=Path,required=True)
    x=p.parse_args();x.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=inspect(json.loads(x.candidates.read_text()),read_geo(x.source),source_area_map(x.source))
    except Exception as e:
        result={"schema":"structural.camtrapasia_original_island_area_polygon_source_screen.v1_246",
         "status":"STOP_GEOGRAPHIC_SOURCE_AREA_OR_COMPONENT","reason_class":type(e).__name__,
         "source_camera_detection_rows_read":0,"original_mammal_heldout_response_read":0}
    x.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
