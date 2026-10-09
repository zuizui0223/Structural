#!/usr/bin/env python3
"""Independent Natural Earth land-component preflight of 15 previously frozen candidate pairs."""
import argparse,csv,hashlib,io,json,math,tempfile,zipfile
from collections import Counter
from pathlib import Path
from urllib.request import Request,urlopen
import geopandas as gpd
from shapely.geometry import Point,box
from shapely.ops import unary_union

URL="https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip"
SAFE_SHA="b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8"
REQUIRED=("ne_10m_land.shp","ne_10m_land.shx","ne_10m_land.dbf","ne_10m_land.prj")
def frozen_geo(path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=SAFE_SHA:raise ValueError("Frozen physical coordinates changed")
    with path.open(encoding="utf-8",newline="") as f:
        rd=csv.DictReader(f)
        if not {"ID","Latitude_centroid","Longitude_centroid"}.issubset(rd.fieldnames or []):
            raise ValueError("Frozen source geographic schema changed")
        rows=list(rd)
    if len(rows)!=5592:raise ValueError("Original geography row count drift")
    d={}
    for r in rows:
        if r["ID"] in d:raise ValueError("Duplicate source island ID")
        def num(x):return float.fromhex(x) if "0x" in x.lower() else float(x)
        lat=num(r["Latitude_centroid"]);lon=num(r["Longitude_centroid"])
        if not (-90<=lat<=90 and -180<=lon<=180):raise ValueError("Source coordinates invalid")
        d[r["ID"]]=(lon,lat)
    return d
def candidates(path):
    d=json.loads(path.read_text())
    if d.get("status")!="PASS_FROZEN_15_CENTROID_NEAR_CANDIDATES_METADATA_ONLY":
        raise ValueError("Prior geographic candidates were not frozen PASS")
    rows=d.get("candidate_site_metadata")
    if not isinstance(rows,list) or len(rows)!=15:raise ValueError("Incorrect candidate count")
    if len({r["nearest_original_heldout_island_ID"] for r in rows})!=10 or len({r["nearest_heldout_block_id"] for r in rows})!=7:
        raise ValueError("Original 10-island/7-block candidate identities drift")
    if sorted(set(r["country"] for r in rows))!=["Indonesia","Malaysia","Vietnam"]:
        raise ValueError("Candidate countries changed")
    if any(not (0<=r["distance_km"]<25) for r in rows):
        raise ValueError("A previously unselected source candidate was added")
    return rows
def fetch_land():
    with urlopen(Request(URL,headers={"User-Agent":"Structural-land-identity-v1.242"}),timeout=90) as f:
        if f.url!="https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip":
            raise ValueError("Unfrozen natural-earth source redirect")
        blob=f.read(12000001)
    if len(blob)>12000000 or not blob.startswith(b"PK\x03\x04"):
        raise ValueError("Official land ZIP is missing or too large")
    sha=hashlib.sha256(blob).hexdigest()
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            contents={z.filename:z for z in archive.infolist()}
            if any(x not in contents for x in REQUIRED):raise ValueError("Natural Earth required shape members missing")
            for name in REQUIRED:
                item=contents[name]
                if item.file_size>45000000 or item.flag_bits&1 or "/" in name or ".." in name:
                    raise ValueError("Unexpected GIS source ZIP metadata")
                Path(tmp,name).write_bytes(archive.read(item))
        frame=gpd.read_file(str(Path(tmp,"ne_10m_land.shp")))
        if frame.crs is None or frame.crs.to_epsg()!=4326:raise ValueError("Different land polygon CRS")
        polygons=[g for g in frame.geometry if g is not None and not g.is_empty]
    if not 100<=len(polygons)<=100000:raise ValueError("Unexpected Natural Earth polygon feature count")
    return polygons,sha,len(polygons)
def land_component(site,held,polygons):
    # Uses a generous SOURCE-INDEPENDENT 0.5° bbox around the two points, no response-dependent tuning.
    lo=min(site[0],held[0])-.5;hi=max(site[0],held[0])+.5
    la=min(site[1],held[1])-.5;ha=max(site[1],held[1])+.5
    local=box(lo,la,hi,ha)
    clipped=[]
    for geom in polygons:
        if geom.intersects(local):
            g=geom.intersection(local)
            if not g.is_empty:clipped.append(g)
    if not clipped:return "one_or_both_points_outside_mapped_land"
    merged=unary_union(clipped)
    sitepoint,heldpoint=Point(site),Point(held)
    components=list(merged.geoms) if hasattr(merged,"geoms") else [merged]
    a=[i for i,p in enumerate(components) if p.covers(sitepoint)]
    b=[i for i,p in enumerate(components) if p.covers(heldpoint)]
    if len(a)!=1 or len(b)!=1:
        return ("one_or_both_points_outside_mapped_land" if not a or not b else "geometry_ambiguous")
    return "same_land_component" if a[0]==b[0] else "distinct_land_components_in_local_clip"
def main():
    p=argparse.ArgumentParser()
    p.add_argument("source_geography",type=Path);p.add_argument("candidate_source",type=Path)
    p.add_argument("--out",required=True,type=Path);a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        geo=frozen_geo(a.source_geography);sites=candidates(a.candidate_source)
        land,sha,n=fetch_land()
        records=[]
        for r in sites:
            held=geo[r["nearest_original_heldout_island_ID"]]
            point=(float(r["X_long"]),float(r["Y_lat"]))
            records.append({"survey_id":r["survey_id"],"country":r["country"],"landscape":r["landscape"],
               "site":r["site"],"original_nearest_heldout_ID":r["nearest_original_heldout_island_ID"],
               "distance_km":r["distance_km"],"landmass_test":land_component(point,held,land)})
        count=Counter(r["landmass_test"] for r in records)
        out={"schema":"structural.camtrapasia_land_component_candidates_result.v1_242",
           "status":"PASS_INDEPENDENT_COASTLINE_COMPONENT_PREFLIGHT",
           "coastline_source":"Natural Earth 10m land v5.1.1",
           "source_zip_sha256":sha,"original_shape_feature_count":n,
           "screened_source_surveys":15,"class_counts":dict(count),"candidate_study_records":records,
           "GADM_3_6_original_vintage_polygon_identity_verified":False,
           "same_land_mass_is_not_independent_survey_prediction_result":True,
           "source_camera_detection_values_read":0,"original_mammal_heldout_cells_opened":0,
           "original_model_predictions_opened":0}
    except Exception as e:
        out={"schema":"structural.camtrapasia_land_component_candidates_result.v1_242",
            "status":"STOP_COASTLINE_SOURCE_OR_COMPONENT_IDENTITY",
            "reason_class":type(e).__name__,"source_camera_detection_values_read":0,
            "original_mammal_heldout_cells_opened":0}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    if out["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
