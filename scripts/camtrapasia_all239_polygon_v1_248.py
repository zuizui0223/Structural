#!/usr/bin/env python3
"""All CamTrapAsia 239 camera-study centers versus original heldout islands; geography ONLY."""
import argparse,csv,io,json,math,sys,hashlib
from collections import defaultdict,Counter
from pathlib import Path
from shapely.geometry import Point
from shapely.strtree import STRtree
from shapely.ops import nearest_points

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from check_camtrapasia_gadm36_landmass_v1_243 import SOURCE,public_polygon_source,read_geo
from camtrapasia_original_island_vs_GADM_area_v1_246 import source_area_map,geodetic_polygon_area_km2
from camtrapasia_sites_vs_mammal_heldout_grid_v1_239 import get_source

ROUTING_SHA="afda05287599110c7248c5cb0c1931689a2aee40f8ff4ff5b76509aff5350715"
R=6371.0088
def hav(a,b):
    lo1,la1=a;lo2,la2=b
    dp=math.radians(la2-la1);dl=math.radians(lo2-lo1)
    v=math.sin(dp/2)**2+math.cos(math.radians(la1))*math.cos(math.radians(la2))*math.sin(dl/2)**2
    return 2*R*math.asin(min(1,math.sqrt(v)))
def routing(path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=ROUTING_SHA:raise ValueError("Original heldout SHA mismatch")
    with path.open(newline="",encoding="utf-8") as f:
        r=csv.DictReader(f)
        if not {"ID","block_id"}.issubset(r.fieldnames or []):raise ValueError("Heldout ID fields missing")
        rows=list(r)
    d={r["ID"]:r["block_id"] for r in rows}
    if len(rows)!=4126 or len(d)!=4126 or not all(d.values()):raise ValueError("Invalid frozen heldout records")
    return d
def sites(raw):
    with io.StringIO(raw.decode("utf-8-sig")) as f:
        rd=csv.DictReader(f)
        required={"survey_id","country","landscape","site","Y_lat","X_long"}
        if not required.issubset(rd.fieldnames or []):raise ValueError("Source study metadata changed")
        rows=[{k:r[k] for k in required} for r in rd]
    if len(rows)!=239 or len({r["survey_id"] for r in rows})!=239:raise ValueError("239 source study universe drift")
    out=[]
    for r in rows:
        lon=float(r["X_long"]);lat=float(r["Y_lat"])
        if not all(map(math.isfinite,(lon,lat))) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError("Invalid study center")
        out.append({"survey_id":r["survey_id"],"country":r["country"],"landscape":r["landscape"],
                    "site":r["site"],"lon":lon,"lat":lat})
    return out
def eligible(poly,area,original):
    result=[]
    minx,miny,maxx,maxy=poly.bounds
    for iid,r in original.items():
        ratio=max(area/r["area"],r["area"]/area)
        if ratio>2:continue
        lon,lat=r["point"]
        if not (minx-.12<=lon<=maxx+.12 and miny-.12<=lat<=maxy+.12):continue
        pt=Point(lon,lat)
        if poly.covers(pt):d=0.
        else:
            q=nearest_points(pt,poly)[1]
            d=hav((lon,lat),(q.x,q.y))
        if d<=5:result.append((iid,r,d,ratio))
    return result
def analyze(studies,original,polygons):
    countries={c:(polys,STRtree(polys)) for c,polys in polygons.items()}
    groups=defaultdict(list);uncovered=Counter();offland=0;ambiguous=0
    for r in studies:
        if r["country"] not in countries:
            uncovered[r["country"]]+=1;continue
        poly,tree=countries[r["country"]]
        point=Point(r["lon"],r["lat"])
        indices=[int(i) for i in tree.query(point) if poly[int(i)].covers(point)]
        if len(indices)==0:offland+=1;continue
        if len(indices)>1:ambiguous+=1;continue
        groups[(r["country"],indices[0])].append(r)
    found={};none=0;multiple=0
    for key,items in groups.items():
        country,ix=key;polygon=countries[country][0][ix]
        polygon_area=geodetic_polygon_area_km2(polygon)
        hits=eligible(polygon,polygon_area,original)
        found[key]={"hits":hits,"polygon_area_km2":polygon_area,"studies":items}
        if len(hits)==0:none+=1
        elif len(hits)>1:multiple+=1
    # Reverse uniqueness across surveyed polygons, not against unexamined components.
    reverse=Counter(v["hits"][0][0] for v in found.values() if len(v["hits"])==1)
    matches=[];nonreciprocal=0
    for key,v in found.items():
        if len(v["hits"])!=1:continue
        iid,original_rec,distance,ratio=v["hits"][0]
        if reverse[iid]!=1:
            nonreciprocal+=1;continue
        for study in v["studies"]:
            matches.append({
              "survey_id":study["survey_id"],"country":study["country"],"landscape":study["landscape"],
              "site":study["site"],"candidate_original_heldout_ID":iid,
              "original_heldout_block_id":original_rec["block"],
              "original_island_area_km2":original_rec["area"],
              "study_polygon_area_km2":v["polygon_area_km2"],
              "area_ratio":ratio,
              "original_centroid_in_polygon":distance==0,
              "original_centroid_to_polygon_km":distance,
              "camera_center_to_original_centroid_km":hav((study["lon"],study["lat"]),original_rec["point"])
            })
    matches.sort(key=lambda z:(z["original_heldout_block_id"],z["candidate_original_heldout_ID"],z["survey_id"]))
    return {
      "schema":"structural.camtrapasia_all239_GADM36_polygon_support_result.v1_248",
      "status":"PASS_RESPONSE_SAFE_FULL239_POLYGON_IDENTITY_PRESCREEN",
      "source_studies_total":len(studies),
      "source_study_countries_outside_three_pinned_GADM_countries":dict(sorted(uncovered.items())),
      "study_centers_off_mapped_country_land":offland,
      "study_centers_on_multiple_source_polygons":ambiguous,
      "distinct_GADM36_country_polygon_components_with_studies":len(groups),
      "polygons_without_original_heldout_island_candidate":none,
      "polygons_with_multiple_area_and_position_compatible_heldout_islands":multiple,
      "nonreciprocal_one_to_one_polygon_candidate_count":nonreciprocal,
      "retained_geography_candidate_study_count":len(matches),
      "distinct_candidate_original_heldout_islands":len({x["candidate_original_heldout_ID"] for x in matches}),
      "distinct_candidate_original_heldout_blocks":len({x["original_heldout_block_id"] for x in matches}),
      "geography_only_candidate_studies":matches,
      "prior_25km_centroid_filter_not_used":True,
      "source_camera_detection_rows_read":0,
      "original_mammal_heldout_species_values_read":0,
      "original_model_predictions_read":0,
      "field_confirmed_original_island_identifications":0,
      "external_mammal_predictive_score_allowed":False
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("original",type=Path);p.add_argument("heldout",type=Path);p.add_argument("--out",required=True,type=Path)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    stage="source_identity"
    try:
        route=routing(a.heldout)
        points=read_geo(a.original)
        areas=source_area_map(a.original)
        if not set(route).issubset(points) or not set(route).issubset(areas):raise ValueError("Original source coverage incomplete")
        original={iid:{"point":points[iid],"area":areas[iid],"block":block} for iid,block in route.items()}
        src=sites(get_source())
        stage="country_geometry"
        polygons={c:public_polygon_source(c)[0] for c in SOURCE}
        stage="all_study_polygon_candidate_matching"
        result=analyze(src,original,polygons)
    except Exception as e:
        result={"schema":"structural.camtrapasia_all239_GADM36_polygon_support_result.v1_248",
          "status":"STOP_OFFICIAL_GEOGRAPHIC_SOURCE_OR_UNIQUE_MATCH",
          "failure_stage":stage,"error_type":type(e).__name__,"safe_reason":str(e)[:160],
          "source_camera_detection_rows_read":0,"original_mammal_heldout_species_values_read":0}
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
