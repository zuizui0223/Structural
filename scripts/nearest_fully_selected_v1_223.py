#!/usr/bin/env python3
"""Physical geography proximity against all 5401 original selected centroids, no outcomes."""
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from strict_safe_geospatial_crosswalk_v1_221 import EXPECTED,sha_file,build,strict_matches,xyz,quant,hav,R

def summaries(x):
    return {"n":len(x),"median":quant(x,.5),"q25":quant(x,.25),"q75":quant(x,.75)}
def analyze(b,w,matches):
    selected=[(i,rec) for i,rec in enumerate(b) if rec["selected"]]
    if len(selected)!=5401 or len(w)!=11546:raise ValueError("Source node universe inconsistent")
    matched=[(i,j) for i,j,_,_ in matches if b[i]["selected"]]
    if len(matched)!=3878:raise ValueError("Strict geographic focal matching changed")
    selected_idx=[i for i,r in selected];bxyz=np.array([xyz(r["lat"],r["lon"]) for _,r in selected])
    wxyz=np.array([xyz(r["lat"],r["lon"]) for r in w])
    btree=cKDTree(bxyz);wtree=cKDTree(wxyz)
    srclookup={i:k for k,i in enumerate(selected_idx)}
    rad=2*math.sin(5/(2*R))
    data=[];nearby5=0;ambiguous=0
    for i,j in matched:
        focal=b[i];pt=np.array(xyz(focal["lat"],focal["lon"]))
        selected_knn_ids=btree.query(pt,k=6)[1]
        neighbour_b=None
        for cand in np.atleast_1d(selected_knn_ids):
            k=int(cand)
            if selected_idx[k]!=i:
                neighbour_b=selected[selected_idx.index(selected_idx[k])][1]
                break
        if neighbour_b is None:raise ValueError("Failed original selected nearest")
        distance_selected=hav((focal["lat"],focal["lon"]),(neighbour_b["lat"],neighbour_b["lon"]))
        nearestW=wtree.query(pt,k=8)[1]
        otherW=None
        for k in np.atleast_1d(nearestW):
            if int(k)!=j:
                otherW=w[int(k)]
                break
        if otherW is None:raise ValueError("Failed excluded-same-island neighbor")
        distance_w=hav((focal["lat"],focal["lon"]),(otherW["lat"],otherW["lon"]))
        if distance_w<0.2:
            ambiguous+=1
            continue
        # Check whether the selected frame contains ANOTHER geographically/area compatible node
        otherXYZ=xyz(otherW["lat"],otherW["lon"])
        eligible=False
        for k in btree.query_ball_point(otherXYZ,rad):
            key=selected_idx[k]
            if key==i:continue
            z=b[key]
            ratio=max(z["area"]/otherW["area"],otherW["area"]/z["area"])
            if ratio<=1.5 and hav((z["lat"],z["lon"]),(otherW["lat"],otherW["lon"]))<=5:
                eligible=True;break
        binname="<10" if focal["area"]<10 else "10-100" if focal["area"]<100 else ">=100"
        data.append({"area_bin":binname,"original_selected_nearest_km":distance_selected,
          "full_named_nearest_km":distance_w,"other_named_had_selected_compatible_centroid":eligible,
          "other_named_at_least_5km_closer":distance_selected-distance_w>=5})
    if len(data)+ambiguous!=3878:raise ValueError("Focal count drift")
    def describe(rows):
        if not rows:return {"n":0}
        return {"n":len(rows),
          "fraction_other_namepoint_without_original_selected_geographic_match":sum(not z["other_named_had_selected_compatible_centroid"] for z in rows)/len(rows),
          "fraction_other_namepoint_at_least_5km_closer":sum(z["other_named_at_least_5km_closer"] for z in rows)/len(rows),
          "selected_nearest_km":summaries([z["original_selected_nearest_km"] for z in rows]),
          "Weigelt_other_nearest_km":summaries([z["full_named_nearest_km"] for z in rows])}
    return {
      "schema":"structural.full_selected_centroid_vs_named_physical_neighbour_result.v1_223",
      "status":"PASS_RESPONSE_SAFE_SELECTED_VS_NAMEPOINT_GEOMETRY",
      "full_original_selected_centroid_reference":5401,
      "focal_confidently_corresponded_islands":3878,
      "ambiguous_alternate_namepoints_lt_200m_from_focal":ambiguous,
      "valid_focals":len(data),
      "overall":describe(data),
      "area_bin":{key:describe([z for z in data if z["area_bin"]==key]) for key in ("<10","10-100",">=100")},
      "source_neighbours_absent_from_original_graph_identified":False,
      "unknown_mammal_zero_labels_identified":False,
      "modelled_network_inference_recomputed":False,"mammal_response_access_count":0
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("barreto",type=Path);p.add_argument("weigelt",type=Path);p.add_argument("selected",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        for name,path in (("barreto",a.barreto),("weigelt",a.weigelt),("selected",a.selected)):
            sha_file(path,EXPECTED[name])
        b,w,nmissing=build(a.barreto,a.weigelt,a.selected)
        matches,_,_=strict_matches(b,w)
        result=analyze(b,w,matches)
    except Exception as e:
        result={"schema":"structural.full_selected_centroid_vs_named_physical_neighbour_result.v1_223",
          "status":"STOP_SAFE_GEOGRAPHIC_NEAREST_CONTRACT",
          "reason_type":type(e).__name__,"mammal_response_access_count":0}
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
