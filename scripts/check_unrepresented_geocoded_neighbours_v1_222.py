#!/usr/bin/env python3
"""v1.222 response-independent proximity of matched and nonmatched geocoded islands."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from strict_safe_geospatial_crosswalk_v1_221 import (
    EXPECTED,sha_file,build,strict_matches,xyz,quant,R)
def hav_from_dot(dot):
    return 2*R*math.asin(min(1.0,math.sqrt(max(0.0,(1-min(1.0,max(-1.0,dot)))/2))))
def quantiles(vals):
    return {"q25":quant(vals,.25),"median":quant(vals,.5),"q75":quant(vals,.75)}
def analyze(b,w,match):
    represented=[j for i,j,dist,ratio in match if b[i]["selected"]]
    if len(represented)!=3878 or len(set(represented))!=3878 or len(w)!=11546:
        raise ValueError("Frozen spatial crosswalk identity not reproduced")
    pts=np.asarray([xyz(q["lat"],q["lon"]) for q in w])
    if not np.isfinite(pts).all():raise ValueError("NaN coordinates")
    alltree=cKDTree(pts)
    repreetree=cKDTree(pts[represented])
    represented_set=set(represented)
    kmin={"<10":[],"10-100":[],">=100":[]}
    all_d,sub_d,inflation,nearest_unrepresented=[],[],[],0
    nr_10,nr_25=[],[]
    for i,j,d,r in match:
        if not b[i]["selected"]:continue
        # query 2 excludes the focal geography ID: no ID matching across datasets
        full_dist,full_idx=alltree.query(pts[j],k=2)
        if int(full_idx[0])!=j or full_dist[0]>1e-9:
            raise ValueError("Coordinate self lookup failed")
        # equal coordinates at other islands are genuine ties; terminate rather than divide by zero
        full_j=int(full_idx[1])
        fullkm=hav_from_dot(float(np.dot(pts[j],pts[full_j])))
        if fullkm<1e-6:raise ValueError("Duplicated physical named coordinates; ratio undefined")
        sd,si=repreetree.query(pts[j],k=2)
        if int(represented[int(si[0])])!=j or sd[0]>1e-9:raise ValueError("Represented self lookup failed")
        selected_neigh=int(represented[int(si[1])])
        subkm=hav_from_dot(float(np.dot(pts[j],pts[selected_neigh])))
        if subkm<1e-6:raise ValueError("Duplicate confidently represented coordinates")
        if subkm+1e-5<fullkm:raise ValueError("Subset nearest should never be closer")
        all_d.append(fullkm);sub_d.append(subkm)
        inflation.append(subkm/fullkm)
        missing=(full_j not in represented_set)
        if missing:nearest_unrepresented+=1
        # source all-tree radius uses 3-D chord length; subtract represented points, including focal
        for radius,out in ((10,nr_10),(25,nr_25)):
            close=alltree.query_ball_point(pts[j],r=2*math.sin(radius/(2*R)))
            out.append(sum((k not in represented_set) for k in close))
        area=b[i]["area"]
        binname="<10" if area<10 else "10-100" if area<100 else ">=100"
        kmin[binname].append({"missing":missing,"fullkm":fullkm,"matchedkm":subkm})
    if len(all_d)!=3878:raise ValueError("Wrong focal count")
    def substats(rows):
        return {"n":len(rows),"fraction_nearest_outside_matched":sum(v["missing"] for v in rows)/len(rows),
                "median_full_nearest_km":quant([v["fullkm"] for v in rows],.5),
                "median_matched_nearest_km":quant([v["matchedkm"] for v in rows],.5)}
    return {
        "schema":"structural.unrepresented_geocoded_neighbourhood_result.v1_222",
        "status":"PASS_RESPONSE_SAFE_GEOGRAPHIC_NEIGHBOR_SENSITIVITY",
        "Weigelt_geocoded_namepoints":11546,
        "focal_high_confidence_selected_matches":3878,
        "nearest_full_namepoint_km":quantiles(all_d),
        "nearest_confidently_matched_namepoint_km":quantiles(sub_d),
        "nearest_distance_ratio_matched_over_full":quantiles(inflation),
        "fraction_nearest_full_node_not_confidently_matched":nearest_unrepresented/len(all_d),
        "fraction_matched_nearest_at_least_5km_farther":sum(b-a>=5 for a,b in zip(all_d,sub_d))/len(all_d),
        "unrepresented_named_islands_within_10km":quantiles(nr_10),
        "unrepresented_named_islands_within_25km":quantiles(nr_25),
        "by_selected_island_area_bin":{k:substats(v) for k,v in kmin.items()},
        "nonmatched_does_not_imply_mammal_zero":True,
        "namepoints_do_not_define_all_island_centroids":True,
        "graph_or_predictions_recomputed":False,"mammal_response_values_opened":0,
        "status_not_an_external_mammal_field_validation":True
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("barreto",type=Path);p.add_argument("weigelt",type=Path);p.add_argument("selected",type=Path)
    p.add_argument("--out",required=True,type=Path);a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        for name,src in (("barreto",a.barreto),("weigelt",a.weigelt),("selected",a.selected)):
            sha_file(src,EXPECTED[name])
        b,w,missing=build(a.barreto,a.weigelt,a.selected)
        matched,am,aw=strict_matches(b,w)
        out=analyze(b,w,matched)
    except Exception as e:
        out={"schema":"structural.unrepresented_geocoded_neighbourhood_result.v1_222",
             "status":"STOP_PHYSICAL_NEIGHBOUR_IDENTITY_OR_DISTANCE",
             "reason_type":type(e).__name__,"mammal_response_values_opened":0}
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps(out,sort_keys=True))
    if out["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
