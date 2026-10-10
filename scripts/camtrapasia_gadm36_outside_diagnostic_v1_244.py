#!/usr/bin/env python3
"""Why GADM36 says outside: candidate point or original centroid? Only geometry."""
import argparse,json,math,sys
from pathlib import Path
from collections import Counter
from shapely.geometry import Point
from shapely.strtree import STRtree
from shapely.ops import nearest_points
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from check_camtrapasia_gadm36_landmass_v1_243 import public_polygon_source,read_geo,SOURCE,classify

R=6371.0088
def hav(lonlat_a,lonlat_b):
    lon1,lat1=lonlat_a;lon2,lat2=lonlat_b
    dp=math.radians(lat2-lat1);dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dl/2)**2
    return 2*R*math.asin(min(1.,math.sqrt(a)))
def point_status(point,parts,tree):
    p=Point(*point)
    ids=tree.query(p)
    covered=[int(k) for k in ids if parts[int(k)].covers(p)]
    if len(covered)>1:return {"inside":False,"ambiguous":True,"distance_to_land_km":None}
    if covered:return {"inside":True,"ambiguous":False,"distance_to_land_km":0.}
    nearest=parts[int(tree.nearest(p))]
    nearest_on_land=nearest_points(p,nearest)[1]
    d=hav(point,(nearest_on_land.x,nearest_on_land.y))
    return {"inside":False,"ambiguous":False,"distance_to_land_km":d}
def main():
    p=argparse.ArgumentParser();p.add_argument("candidates",type=Path);p.add_argument("original",type=Path)
    p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        d=json.loads(a.candidates.read_text())
        if d.get("status")!="PASS_FROZEN_15_CENTROID_NEAR_CANDIDATES_METADATA_ONLY" or len(d["candidate_site_metadata"])!=15:
            raise ValueError("Candidate geography replaced")
        geom=read_geo(a.original)
        countries={name:(parts,STRtree(parts)) for name,(parts,meta) in
          {c:public_polygon_source(c) for c in SOURCE}.items()}
        rows=[]
        for site in d["candidate_site_metadata"]:
            parts,tree=countries[site["country"]]
            study=(site["X_long"],site["Y_lat"])
            target=geom[site["nearest_original_heldout_island_ID"]]
            A=point_status(study,parts,tree);B=point_status(target,parts,tree)
            rows.append({"study":site["survey_id"],"country":site["country"],
                "study_inside_source_country_land":A["inside"],
                "original_heldout_centroid_inside_country_land":B["inside"],
                "study_distance_to_mapped_land_km":A["distance_to_land_km"],
                "heldout_centroid_distance_to_mapped_land_km":B["distance_to_land_km"],
                "original_v243_class":classify(study,target,parts)})
        counts={
            "both_inside":sum(x["study_inside_source_country_land"] and x["original_heldout_centroid_inside_country_land"] for x in rows),
            "study_inside_only":sum(x["study_inside_source_country_land"] and not x["original_heldout_centroid_inside_country_land"] for x in rows),
            "heldout_centroid_inside_only":sum(not x["study_inside_source_country_land"] and x["original_heldout_centroid_inside_country_land"] for x in rows),
            "neither_inside":sum(not x["study_inside_source_country_land"] and not x["original_heldout_centroid_inside_country_land"] for x in rows)
        }
        if sum(counts.values())!=15:raise ValueError("GIS source category totals differ")
        current=Counter(x["original_v243_class"] for x in rows)
        if dict(current)!={"same_component":2,"different_component":3,"one_or_both_outside":10}:
            raise ValueError("Earlier GADM v1.243 classes changed")
        out={"schema":"structural.camtrapasia_gadm36_outside_diagnostic_result.v1_244",
           "status":"PASS_DIAGNOSED_SOURCE_LAND_GEOMETRY_OUTSIDE_CLASS",
           "input_study_count":15,"status_count":counts,"previous_v243_count":dict(current),
           "candidate_point_status":rows,
           "outside_land_distance_is_not_distance_from_true_island_nor_buffer_reassignment":True,
           "source_species_detection_rows_read":0,
           "original_mammal_heldout_labels_read":0,
           "original_predictions_scored":False}
    except Exception as e:
        out={"schema":"structural.camtrapasia_gadm36_outside_diagnostic_result.v1_244",
           "status":"STOP_GADM36_POINT_SOURCE_IDENTITY","reason_type":type(e).__name__,
           "source_species_detection_rows_read":0,
           "original_mammal_heldout_labels_read":0}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    if out["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
