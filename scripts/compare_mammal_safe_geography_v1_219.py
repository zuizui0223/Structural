#!/usr/bin/env python3
"""Geographic reference rows only; no mammal species outcomes or prediction files."""
import argparse,csv,hashlib,json,math
from pathlib import Path
ALL_SHA="ebb4b54cc9b056a1ea61fcae3a53bf578c0e47488e4a496d40fceaeca4f4b8af"
SUB_SHA="5a04e8b64682979ee708f281418c017ff34c930bc8e51d7eff3d3437929b74b0"
FIELDS=["area","dist","slmp","gmmc","elev","temp","vart","ccvt","prec","varp"]
def check(path,digest):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise ValueError("Input artifact fingerprint mismatch")
def ident(x):
    if not x or any(c not in "0123456789" for c in x):raise ValueError("Unsafe island ID")
    return str(int(x))
def q(x,p):
    v=sorted(x);t=(len(v)-1)*p;i=int(t);j=min(i+1,len(v)-1)
    return v[i]*(j-t)+v[j]*(t-i)
def describe(x):
    return {"n":len(x),"q25":q(x,.25),"median":q(x,.5),"q75":q(x,.75)}
def calc(all_rows,selected_ids):
    ids=[ident(r["id"]) for r in all_rows]
    if len(ids)!=17883 or len(set(ids))!=17883 or len(selected_ids)!=5401:
        raise ValueError("Incorrect island universe size")
    if not selected_ids.issubset(set(ids)):
        raise ValueError("Selected IDs not present in safer reference")
    yes=[r for r,i in zip(all_rows,ids) if i in selected_ids]
    no=[r for r,i in zip(all_rows,ids) if i not in selected_ids]
    if len(yes)!=5401 or len(no)!=12482:raise ValueError("Selected counts differ")
    values={}
    for field in FIELDS:
        def num(r):
            s=r[field]
            if s is None or not s.strip():raise ValueError("Missing safe numeric field: "+field)
            v=float(s)
            if not math.isfinite(v):raise ValueError("Nonfinite field: "+field)
            return v
        a=[num(r) for r in yes];b=[num(r) for r in no]
        if field=="area" and min(a+b)<=0:raise ValueError("Nonpositive island area")
        if field=="dist" and min(a+b)<0:raise ValueError("Negative mainland distance")
        values[field]={"selected":describe(a),"nonselected":describe(b),"full":describe(a+b)}
    effects={}
    for label,f,fun in [("ln_area","area",math.log),("ln1p_mainland_distance","dist",math.log1p)]:
        a=[fun(float(r[f])) for r in yes];b=[fun(float(r[f])) for r in no];v=a+b
        mu=sum(v)/len(v);sd=math.sqrt(sum((u-mu)**2 for u in v)/len(v))
        if sd==0:raise ValueError("Zero geography variance")
        effects[label]={"selected_minus_nonselected_mean_sd_units":(sum(a)/len(a)-sum(b)/len(b))/sd}
    def present(group,key):
        return sum(bool((r.get(key) or "").strip()) for r in group)/len(group)
    return {
        "schema":"structural.response_cell_free_geography_selection_result.v1_219",
        "status":"PASS_MATCHED_SAFE_ISLAND_GEOGRAPHY",
        "full_reference_islands":17883,"selected_islands":len(yes),"nonselected_reference_islands":len(no),
        "selected_fraction":len(yes)/len(all_rows),
        "summaries":values,"descriptive_imbalances":effects,
        "safe_location_fields_nonempty":{key:{"selected":present(yes,key),"nonselected":present(no,key)} for key in ("archip","name_lat","name_long")},
        "nonselected_is_not_equal_to_mammal_zero":True,
        "species_by_island_labels_read":0,"network_recomputed":False,"prediction_scores_calculated":False
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("all",type=Path);p.add_argument("selected",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();out=a.out;out.parent.mkdir(parents=True,exist_ok=True)
    try:
        check(a.all,ALL_SHA);check(a.selected,SUB_SHA)
        with a.selected.open(newline="",encoding="utf-8") as f:
            ids=[ident(r["ID"]) for r in csv.DictReader(f)]
        if len(set(ids))!=5401:raise ValueError("Repeated selected ID")
        with a.all.open(newline="",encoding="utf-8") as f:
            rd=csv.DictReader(f)
            if not {"id","name_lat","name_long","archip",*FIELDS}.issubset(rd.fieldnames or []):
                raise ValueError("Missing frozen safe geography fields")
            rows=list(rd)
        result=calc(rows,set(ids))
    except Exception as ex:
        result={"schema":"structural.response_cell_free_geography_selection_result.v1_219",
                "status":"STOP_SAFE_ARTIFACT_OR_ID_MATCH","reason_type":type(ex).__name__,
                "species_by_island_labels_read":0,"prediction_scores_calculated":False}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
