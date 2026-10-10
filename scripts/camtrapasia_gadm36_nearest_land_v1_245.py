#!/usr/bin/env python3
"""Sensitivity: nearest country-land polygon for OFF-LAND original centroids, no biological data."""
import argparse,json,sys
from collections import Counter
from pathlib import Path
from shapely.geometry import Point
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"scripts"))
from check_camtrapasia_gadm36_landmass_v1_243 import public_polygon_source,read_geo,SOURCE,classify
from camtrapasia_gadm36_outside_diagnostic_v1_244 import point_status

def point_component(point,parts,tree):
    idx=[int(k) for k in tree.query(Point(*point)) if parts[int(k)].covers(Point(*point))]
    if len(idx)!=1:return None
    return idx[0]
def nearest_country_component(point,parts,tree):
    p=Point(*point)
    k=tree.query_nearest(p,all_matches=True)
    unique=set(int(j) for j in k)
    return next(iter(unique)) if len(unique)==1 else None
def process(candidates,geo):
    if candidates.get("status")!="PASS_FROZEN_15_CENTROID_NEAR_CANDIDATES_METADATA_ONLY":
        raise ValueError("Unfrozen source candidate set")
    rows=candidates["candidate_site_metadata"]
    if len(rows)!=15:raise ValueError("Source candidates changed")
    countries={name:(parts,STRtree(parts)) for name,(parts,meta) in
         {c:public_polygon_source(c) for c in SOURCE}.items()}
    out=[]
    for r in rows:
        parts,tree=countries[r["country"]]
        s=(r["X_long"],r["Y_lat"])
        target=geo[r["nearest_original_heldout_island_ID"]]
        old=classify(s,target,parts)
        a=point_component(s,parts,tree)
        if a is None:raise ValueError("Earlier v244 all source sites inside geometry not reproduced")
        b=point_component(target,parts,tree)
        if b is not None:
            cls="both_inside_same" if a==b else "both_inside_different"
        else:
            nearest=nearest_country_component(target,parts,tree)
            if nearest is None:cls="unresolved_ambiguous"
            else:cls=("original_offland_nearest_polygon_same_as_study"
                if a==nearest else "original_offland_nearest_polygon_differs_from_study")
        out.append({"survey_id":r["survey_id"],"region":r["landscape"],
           "source_country":r["country"],"original_nearest_heldout_ID":r["nearest_original_heldout_island_ID"],
           "old_v243_class":old,"nearest_polygon_sensitivity_class":cls,
           "source_original_heldout_centroid_outside_land":b is None})
    ct=Counter(x["nearest_polygon_sensitivity_class"] for x in out)
    old=Counter(x["old_v243_class"] for x in out)
    if dict(old)!={"same_component":2,"different_component":3,"one_or_both_outside":10}:
        raise ValueError("Original GADM v1.243 boundary classifications changed")
    return {"schema":"structural.camtrapasia_gadm36_nearest_land_sensitivity_result.v1_245",
       "status":"PASS_NEAREST_LAND_COMPONENT_RESPONSES_OPAQUE",
       "source_studies":15,"geo_sensitivity_classes":dict(ct),
       "previous_v243_classes":dict(old),"individual_geography_only_cases":out,
       "geographic_nearest_polygon_heurstic_not_true_island_ID":True,
       "matched_mammal_taxon_site_detected_values_read":0,
       "IUCN_heldout_mammal_response_cells_opened":0,
       "original_network_scores_computed":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("candidates",type=Path);p.add_argument("original",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    try:result=process(json.loads(a.candidates.read_text()),read_geo(a.original))
    except Exception as e:result={"schema":"structural.camtrapasia_gadm36_nearest_land_sensitivity_result.v1_245",
       "status":"STOP_NEAREST_SOURCE_LAND_GEOMETRY_IDENTITY",
       "reason_type":type(e).__name__,
       "matched_mammal_taxon_site_detected_values_read":0,"IUCN_heldout_mammal_response_cells_opened":0}
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
