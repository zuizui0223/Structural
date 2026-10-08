#!/usr/bin/env python3
"""Only already-authorized response-safe island geography, no mammal outcomes."""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

EXPECTED={
 "barreto":"b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8",
 "weigelt":"ebb4b54cc9b056a1ea61fcae3a53bf578c0e47488e4a496d40fceaeca4f4b8af",
 "selected":"5a04e8b64682979ee708f281418c017ff34c930bc8e51d7eff3d3437929b74b0"
}
R=6371.0088
MAX_KM=5.0
AREA_RATIO=1.5
def sha_file(path,sha):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    if h.hexdigest()!=sha:raise ValueError("Frozen safe artifact fingerprint mismatch")
def id_text(x):
    if not x or any(c not in "0123456789" for c in x):raise ValueError("Invalid pre-existing island ID")
    return str(int(x))
def num(x):
    if x is None or not x.strip():raise ValueError("Missing required number")
    v=float.fromhex(x) if "0x" in x.lower() else float(x)
    if not math.isfinite(v):raise ValueError("Nonfinite geography")
    return v
def xyz(lat,lon):
    p=math.radians(lat);l=math.radians(lon)
    return (math.cos(p)*math.cos(l),math.cos(p)*math.sin(l),math.sin(p))
def hav(a,b):
    lat1,lon1=a;lat2,lon2=b
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=p2-p1;dl=math.radians(lon2-lon1)
    v=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1.,math.sqrt(v)))
def quant(a,prob):
    if not a: return None
    x=sorted(a);t=(len(x)-1)*prob;i=int(t);j=min(len(x)-1,i+1)
    return x[i]*(j-t)+x[j]*(t-i)
def sizebin(area):
    return "<10" if area<10 else "10-100" if area<100 else ">=100"
def build(barreto,weigelt,selected):
    with selected.open(newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f)
        if "ID" not in (rd.fieldnames or []):raise ValueError("selected ID missing")
        sel=[id_text(r["ID"]) for r in rd]
    if len(sel)!=5401 or len(set(sel))!=5401:raise ValueError("selected ID contract fail")
    sel=set(sel)
    with barreto.open(newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f)
        if not {"ID","Longitude_centroid","Latitude_centroid","Area"}.issubset(rd.fieldnames or []):
            raise ValueError("safe Barreto geography wrong schema")
        rows=list(rd)
    if len(rows)!=5592:raise ValueError("Barreto safe universe mismatch")
    b=[];ids=set()
    for r in rows:
        id=id_text(r["ID"])
        if id in ids:raise ValueError("duplicate Barreto ID")
        ids.add(id)
        lat=num(r["Latitude_centroid"]);lon=num(r["Longitude_centroid"]);area=num(r["Area"])
        if not (-90<=lat<=90 and -180<=lon<=180 and area>0):raise ValueError("Bad Barreto geography")
        b.append({"id":id,"lat":lat,"lon":lon,"area":area,"selected":id in sel})
    if sum(r["selected"] for r in b)!=5401:raise ValueError("selected is not a strict source subset")
    with weigelt.open(newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f)
        if not {"id","name_lat","name_long","area"}.issubset(rd.fieldnames or []):
            raise ValueError("safe Weigelt schema missing")
        rows=list(rd)
    if len(rows)!=17883:raise ValueError("Weigelt safe universe mismatch")
    w=[];weid=set();coordinate_missing=0
    for r in rows:
        key=id_text(r["id"])
        if key in weid:raise ValueError("Duplicate Weigelt ID")
        weid.add(key)
        area=num(r["area"])
        if area<=0:raise ValueError("Bad Weigelt area")
        lt=r["name_lat"];ln=r["name_long"]
        if not lt or not lt.strip() or not ln or not ln.strip():
            coordinate_missing+=1
            continue
        lat=num(lt);lon=num(ln)
        if not (-90<=lat<=90 and -180<=lon<=180):raise ValueError("Bad Weigelt name point")
        w.append({"id":key,"lat":lat,"lon":lon,"area":area})
    if coordinate_missing!=6337:raise ValueError("Unexpected archived namepoint availability")
    return b,w,coordinate_missing
def strict_matches(b,w):
    arr=np.array([xyz(z["lat"],z["lon"]) for z in w],dtype=float)
    tree=cKDTree(arr)
    rad=2*math.sin(MAX_KM/(2*R))
    eligible=[]
    reverse=[[] for _ in w]
    ambiguous_B=0
    for i,z in enumerate(b):
        point=xyz(z["lat"],z["lon"])
        nearby=tree.query_ball_point(point,rad)
        accepted=[]
        for j in nearby:
            other=w[j]
            ratio=max(z["area"]/other["area"],other["area"]/z["area"])
            if ratio>AREA_RATIO:continue
            dist=hav((z["lat"],z["lon"]),(other["lat"],other["lon"]))
            if dist>MAX_KM:continue
            accepted.append((j,dist,ratio))
        eligible.append(accepted)
        for j,d,ratio in accepted:reverse[j].append(i)
        if len(accepted)>1:ambiguous_B+=1
    matched=[]
    for i,candidates in enumerate(eligible):
        if len(candidates)!=1:continue
        j,d,r=candidates[0]
        if len(reverse[j])!=1:continue
        matched.append((i,j,d,r))
    # every accepted pair is bidirectionally unique under fixed quality constraints
    if len(set(i for i,_,_,_ in matched))!=len(matched) or len(set(j for _,j,_,_ in matched))!=len(matched):
        raise ValueError("Non-one-to-one spatial match")
    return matched,ambiguous_B,sum(len(x)>1 for x in reverse)
def summarize(b,w,matched,missing):
    sel_ids={i for i,z in enumerate(b) if z["selected"]}
    matchedB={i for i,_,_,_ in matched}
    subset=[(i,j,d,r) for i,j,d,r in matched if i in sel_ids]
    sizes_sel=[b[i]["area"] for i in sel_ids]
    sizes_hit=[b[i]["area"] for i,_,_,_ in subset]
    sizes_nohit=[b[i]["area"] for i in sel_ids if i not in matchedB]
    def dist(a):
        return {"n":len(a),"q25":quant(a,.25),"median":quant(a,.5),"q75":quant(a,.75)}
    bins={}
    for binname in ("<10","10-100",">=100"):
        denominator=sum(sizebin(b[i]["area"])==binname for i in sel_ids)
        numerator=sum(sizebin(b[i]["area"])==binname for i,_,_,_ in subset)
        bins[binname]={"matched":numerator,"selected":denominator,"coverage":numerator/denominator if denominator else None}
    return {
        "schema":"structural.response_safe_spatial_island_crosswalk_result.v1_221",
        "status":"PASS_PREDECLARED_RECIPROCAL_SPATIAL_GEOGRAPHY_MATCH",
        "source_Barreto_rows":len(b),"selected_Structural_nodes":len(sel_ids),
        "source_Weigelt_coordinate_available":len(w),"Weigelt_missing_namepoints":missing,
        "matched_source_Barreto_islands":len(matched),"matched_selected_Structural_islands":len(subset),
        "fraction_selected_with_high_confidence_match":len(subset)/len(sel_ids),
        "match_distance_km":dist([d for _,_,d,_ in subset]),
        "match_area_larger_to_smaller_ratio":dist([r for _,_,_,r in subset]),
        "selected_area_km2":dist(sizes_sel),"matched_selected_area_km2":dist(sizes_hit),
        "unmatched_selected_area_km2":dist(sizes_nohit),
        "selected_match_coverage_by_area_bin":bins,
        "high_confidence_pairs_are_field_verified":False,
        "comparison_is_mammal_zero_v_nonzero":False,
        "all_island_network_rebuilt":False,
        "source_species_outcome_rows_opened":0,
        "mammal_model_predictions_rerun":False
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("barreto",type=Path);p.add_argument("weigelt",type=Path);p.add_argument("selected",type=Path)
    p.add_argument("--out",required=True,type=Path);args=p.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        for role,f in (("barreto",args.barreto),("weigelt",args.weigelt),("selected",args.selected)):
            sha_file(f,EXPECTED[role])
        b,w,missing=build(args.barreto,args.weigelt,args.selected)
        matches,ambiguous_b,ambiguous_w=strict_matches(b,w)
        result=summarize(b,w,matches,missing)
        result["ambiguous_Barreto_with_multiple_candidate_Weigelt"]=ambiguous_b
        result["ambiguous_Weigelt_with_multiple_candidate_Barreto"]=ambiguous_w
    except Exception as ex:
        result={"schema":"structural.response_safe_spatial_island_crosswalk_result.v1_221",
                "status":"STOP_GEO_SOURCE_SCHEMA_OR_IDENTITY","reason_type":type(ex).__name__,
                "source_species_outcome_rows_opened":0,"mammal_model_predictions_rerun":False}
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
