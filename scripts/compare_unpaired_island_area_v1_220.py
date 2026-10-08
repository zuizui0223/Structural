#!/usr/bin/env python3
"""Two independent archived, safe island-area distributions; NO crosswalk or mammal labels."""
import argparse,csv,hashlib,json,math
from pathlib import Path
HASH_FULL="ebb4b54cc9b056a1ea61fcae3a53bf578c0e47488e4a496d40fceaeca4f4b8af"
HASH_SELECTED="5a04e8b64682979ee708f281418c017ff34c930bc8e51d7eff3d3437929b74b0"
def checksum(path,expected):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError("Frozen archive SHA mismatch")
def q(arr,p):
    a=sorted(arr);z=(len(a)-1)*p;i=int(z);j=min(i+1,len(a)-1)
    return a[i]*(j-z)+a[j]*(z-i)
def stats(arr):
    if not arr or any(not math.isfinite(v) or v<=0 for v in arr):raise ValueError("Invalid positive area")
    return {"n":len(arr),"q25_km2":q(arr,.25),"median_km2":q(arr,.5),
      "q75_km2":q(arr,.75),"fraction_lt_10km2":sum(x<10 for x in arr)/len(arr),
      "fraction_ge_100km2":sum(x>=100 for x in arr)/len(arr)}
def analyze(weigelt,state,receipt):
    check=receipt.get("standardization",{}).get("log_Area",{})
    mu=float.fromhex(check["mean_hex"]);sd=float.fromhex(check["sd_hex"])
    if not sd>0:raise ValueError("Missing positive log area scale")
    with weigelt.open(newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f)
        if "area" not in (rd.fieldnames or []):raise ValueError("Missing safe area")
        a=[float(row["area"]) for row in rd]
    with state.open(newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f)
        if "z_log_Area" not in (rd.fieldnames or []):raise ValueError("Missing archived standardized island area")
        b=[math.exp(float.fromhex(row["z_log_Area"])*sd+mu) for row in rd]
    if len(a)!=17883 or len(b)!=5401:raise ValueError("Wrong archived area denominators")
    s1,s2=stats(a),stats(b)
    return {"schema":"structural.unpaired_island_area_frame_result.v1_220",
      "status":"PASS_TWO_SOURCE_AREA_DISTRIBUTIONS_NO_ISLAND_CROSSWALK",
      "Weigelt_2013_17883_islands":s1,"Barreto_Structural_5401_islands":s2,
      "median_ratio_selected_compilation_over_full_Weigelt_frame":s2["median_km2"]/s1["median_km2"],
      "matched_individual_island_ids":False,
      "can_infer_causal_mammal_zero_selection_bias":False,
      "species_island_response_values_read":0,"model_predictions_rerun":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("weigelt",type=Path);p.add_argument("state",type=Path);p.add_argument("receipt",type=Path);p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    try:
        checksum(x.weigelt,HASH_FULL);checksum(x.state,HASH_SELECTED)
        obj=analyze(x.weigelt,x.state,json.loads(x.receipt.read_text()))
    except Exception as e:
        obj={"schema":"structural.unpaired_island_area_frame_result.v1_220","status":"STOP_UNPAIRED_AREA_SOURCE_GATE",
          "reason_type":type(e).__name__,"species_island_response_values_read":0}
    x.out.parent.mkdir(parents=True,exist_ok=True);x.out.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    print(json.dumps(obj,sort_keys=True))
    if obj["status"].startswith("STOP_"):raise SystemExit(2)
if __name__=="__main__":main()
