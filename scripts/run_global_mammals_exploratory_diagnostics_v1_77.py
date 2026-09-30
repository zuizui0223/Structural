#!/usr/bin/env python3
"""Post-hoc nonrescuing diagnostics for the frozen global mammal block scores.

This script never re-scores species-level response. It joins the already-frozen
168 block C-minus-R3 scores to response-independent block means from the frozen
state reference, then reports descriptive geographic breadth and Spearman
associations. These diagnostics cannot alter confirmatory status.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_exploratory_diagnostics_contract_v1_77.json"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def parse_float(x:str)->float:
    s=str(x).strip()
    try:
        v=float.fromhex(s) if s.lower().startswith(("0x","+0x","-0x")) else float(s)
    except Exception as e:
        raise Stop(f"invalid numeric value: {s!r}") from e
    if not math.isfinite(v): raise Stop("nonfinite numeric value")
    return v

def mean(xs):
    if not xs: raise Stop("empty mean")
    return math.fsum(xs)/len(xs)

def median(xs):
    if not xs: raise Stop("empty median")
    ys=sorted(xs); n=len(ys)
    return ys[n//2] if n%2 else (ys[n//2-1]+ys[n//2])/2

def average_ranks(xs):
    order=sorted(range(len(xs)),key=lambda i:(xs[i],i))
    ranks=[0.0]*len(xs); j=0
    while j<len(order):
        k=j+1
        while k<len(order) and xs[order[k]]==xs[order[j]]: k+=1
        r=((j+1)+k)/2.0
        for pos in order[j:k]: ranks[pos]=r
        j=k
    return ranks

def pearson(x,y):
    if len(x)!=len(y) or len(x)<2: raise Stop("invalid correlation input")
    mx,my=mean(x),mean(y)
    dx=[v-mx for v in x]; dy=[v-my for v in y]
    sx=math.sqrt(math.fsum(v*v for v in dx)); sy=math.sqrt(math.fsum(v*v for v in dy))
    if not sx>0 or not sy>0: raise Stop("zero variance correlation input")
    return math.fsum(a*b for a,b in zip(dx,dy))/(sx*sy)

def spearman(x,y):
    return pearson(average_ranks(x),average_ranks(y))

def load_block_scores(path,expected_sha,expected_n):
    if sha(path)!=expected_sha: raise Stop("block-score SHA mismatch")
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    if len(rows)!=expected_n: raise Stop("block-score row-count drift")
    out=[]
    seen=set()
    for r in rows:
        bid=str(r["block_id"])
        if bid in seen: raise Stop("duplicate block score")
        seen.add(bid)
        out.append({
          "block_id":bid,
          "bioregion":str(r["bioregion"]),
          "islands":int(r["islands"]),
          "delta":parse_float(r["mean_C_minus_R3_logloss"])
        })
    return out

def load_state(path,expected_sha,expected_islands):
    if sha(path)!=expected_sha: raise Stop("state-reference SHA mismatch")
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    rows=[r for r in rows if str(r["split"])=="confirmatory"]
    if len(rows)!=expected_islands: raise Stop("confirmatory island-count drift")
    needed=("z_Current_isolation","z_Past_isolation","z_log_Area")
    by=defaultdict(list)
    for r in rows:
        by[(str(r["block_id"]),str(r["bioregion"]))].append({
          "z_Current_isolation":parse_float(r["z_Current_isolation"]),
          "z_Past_isolation":parse_float(r["z_Past_isolation"]),
          "z_log_Area":parse_float(r["z_log_Area"])
        })
    return by

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("block_scores",type=Path)
    ap.add_argument("state_reference",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--block-output",type=Path,required=True)
    ap.add_argument("--bioregion-output",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_exploratory_diagnostics_contract.v1_77":
            raise Stop("contract schema drift")
        scores=load_block_scores(a.block_scores,c["inputs"]["block_scores"]["sha256"],c["inputs"]["block_scores"]["blocks"])
        state=load_state(a.state_reference,c["inputs"]["state_reference"]["sha256"],c["inputs"]["state_reference"]["confirmatory_islands"])
        variables=["z_Current_isolation","z_Past_isolation","z_log_Area"]
        enriched=[]
        for r in scores:
            key=(r["block_id"],r["bioregion"])
            xs=state.get(key)
            if xs is None: raise Stop(f"missing state block: {key}")
            if len(xs)!=r["islands"]: raise Stop(f"block island-count mismatch: {key}")
            row=dict(r)
            for v in variables: row["mean_"+v]=mean([x[v] for x in xs])
            enriched.append(row)

        bybio=defaultdict(list)
        for r in enriched: bybio[r["bioregion"]].append(r)
        bio_rows=[]
        for bio in sorted(bybio):
            rs=bybio[bio]; ds=[r["delta"] for r in rs]
            bio_rows.append({
              "bioregion":bio,
              "blocks":len(rs),
              "islands":sum(r["islands"] for r in rs),
              "mean_delta":mean(ds),
              "median_delta":median(ds),
              "negative_blocks":sum(d<0 for d in ds),
              "positive_blocks":sum(d>0 for d in ds),
              "fraction_negative":sum(d<0 for d in ds)/len(ds)
            })

        deltas=[r["delta"] for r in enriched]
        associations={}
        for v in variables:
            x=[r["mean_"+v] for r in enriched]
            rho=spearman(x,deltas)
            # within-bioregion centering, keeping equal block weight
            xwc=[]; ywc=[]
            for bio in sorted(bybio):
                rs=bybio[bio]
                bx=[r["mean_"+v] for r in rs]; by=[r["delta"] for r in rs]
                mx,my=mean(bx),mean(by)
                xwc.extend(z-mx for z in bx); ywc.extend(z-my for z in by)
            associations[v]={
              "spearman_rho_equal_block":rho,
              "spearman_rho_within_bioregion_centered":spearman(xwc,ywc)
            }

        a.block_output.parent.mkdir(parents=True,exist_ok=True)
        with a.block_output.open("w",encoding="utf-8",newline="") as h:
            fields=["block_id","bioregion","islands","delta"]+["mean_"+v for v in variables]
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n"); w.writeheader()
            for r in sorted(enriched,key=lambda z:z["block_id"]): w.writerow(r)
        with a.bioregion_output.open("w",encoding="utf-8",newline="") as h:
            fields=["bioregion","blocks","islands","mean_delta","median_delta","negative_blocks","positive_blocks","fraction_negative"]
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(bio_rows)

        result={
          "schema":"structural.global_mammals_exploratory_diagnostics_result.v1_77",
          "status":"POSTHOC_NONRESCUING_DIAGNOSTICS_COMPLETE",
          "candidate_id":c["candidate_id"],
          "analysis_route":c["analysis_route"],
          "blocks":len(enriched),
          "islands":sum(r["islands"] for r in enriched),
          "geographic_breadth":{
            "negative_blocks":sum(d<0 for d in deltas),
            "positive_blocks":sum(d>0 for d in deltas),
            "zero_blocks":sum(d==0 for d in deltas),
            "fraction_negative_blocks":sum(d<0 for d in deltas)/len(deltas),
            "bioregions":len(bio_rows),
            "bioregions_with_negative_mean":sum(r["mean_delta"]<0 for r in bio_rows),
            "bioregions_with_positive_mean":sum(r["mean_delta"]>0 for r in bio_rows)
          },
          "external_isolation_context":associations,
          "interpretation_key":"positive isolation rho means the incremental C advantage weakens as external isolation increases",
          "block_context_sha256":sha(a.block_output),
          "bioregion_summary_sha256":sha(a.bioregion_output),
          "posthoc":True,
          "may_change_primary_status":False,
          "counts_as_confirmatory_evidence":False,
          "fresh_system_denominator_contribution":0
        }
        a.result.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={"schema":"structural.global_mammals_exploratory_diagnostics_result.v1_77","status":"STOP","reason":str(e),"posthoc":True,"may_change_primary_status":False,"counts_as_confirmatory_evidence":False,"fresh_system_denominator_contribution":0}
        a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print(json.dumps(out,indent=2,sort_keys=True));return 2

if __name__=="__main__": raise SystemExit(main())
