#!/usr/bin/env python3
"""Audit whether external-isolation attenuation is redundant with graph-source emptiness.

Uses only already-frozen 168-block summaries. No species-level response or
prediction surface is opened here.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_isolation_empty_support_audit_contract_v1_87.json"
class Stop(RuntimeError): pass

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def load(p:Path):
    with p.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def f(x):
    v=float(str(x))
    if not math.isfinite(v):raise Stop("nonfinite value")
    return v

def mean(xs):
    return math.fsum(xs)/len(xs)

def average_ranks(xs):
    order=sorted(range(len(xs)),key=lambda i:(xs[i],i))
    ranks=[0.0]*len(xs);j=0
    while j<len(order):
        k=j+1
        while k<len(order) and xs[order[k]]==xs[order[j]]:k+=1
        r=((j+1)+k)/2.0
        for i in order[j:k]:ranks[i]=r
        j=k
    return ranks

def pearson(x,y):
    if len(x)!=len(y) or len(x)<2:raise Stop("invalid correlation input")
    mx,my=mean(x),mean(y)
    dx=[v-mx for v in x];dy=[v-my for v in y]
    sx=math.sqrt(math.fsum(v*v for v in dx));sy=math.sqrt(math.fsum(v*v for v in dy))
    if not sx>0 or not sy>0:raise Stop("zero variance")
    return math.fsum(a*b for a,b in zip(dx,dy))/(sx*sy)

def spearman(x,y):
    return pearson(average_ranks(x),average_ranks(y))

def partial(rxy,rxz,ryz):
    den=(1-rxz*rxz)*(1-ryz*ryz)
    if den<=0:raise Stop("invalid partial-correlation denominator")
    return (rxy-rxz*ryz)/math.sqrt(den)

def corrset(rows,xkey,ykey,zkey):
    x=[r[xkey] for r in rows];y=[r[ykey] for r in rows];z=[r[zkey] for r in rows]
    rxy=spearman(x,y);rxz=spearman(x,z);ryz=spearman(y,z)
    return {
      "rho_isolation_vs_C_minus_R3":rxy,
      "rho_isolation_vs_graph_empty_fraction":rxz,
      "rho_graph_empty_fraction_vs_C_minus_R3":ryz,
      "partial_rho_isolation_vs_C_minus_R3_given_graph_empty_fraction":partial(rxy,rxz,ryz)
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("block_context",type=Path)
    ap.add_argument("block_prediction_behavior",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_isolation_empty_support_audit_contract.v1_87":
            raise Stop("contract schema drift")
        if sha(a.block_context)!=c["inputs"]["block_context"]["sha256"]:raise Stop("block-context SHA drift")
        if sha(a.block_prediction_behavior)!=c["inputs"]["block_prediction_behavior"]["sha256"]:raise Stop("prediction-behavior SHA drift")
        bc=load(a.block_context);bp=load(a.block_prediction_behavior)
        if len(bc)!=168 or len(bp)!=168:raise Stop("block count drift")
        bmap={r["block_id"]:r for r in bp}
        if len(bmap)!=168:raise Stop("duplicate behavior block")
        rows=[]
        for r in bc:
            bid=r["block_id"]
            if bid not in bmap:raise Stop("block identity mismatch")
            b=bmap[bid]
            delta=f(r["delta"])
            if abs(delta-f(b["mean_C_minus_R3"]))>1e-15:raise Stop("C-minus-R3 block value drift")
            rows.append({
              "block_id":bid,
              "bioregion":r["bioregion"],
              "isolation":f(r["mean_z_Current_isolation"]),
              "delta":delta,
              "empty":f(b["graph_empty_fraction"])
            })
        raw=corrset(rows,"isolation","delta","empty")

        by=defaultdict(list)
        for r in rows:by[r["bioregion"]].append(r)
        centered=[]
        for bio in sorted(by):
            rs=by[bio]
            mi=mean([r["isolation"] for r in rs])
            md=mean([r["delta"] for r in rs])
            me=mean([r["empty"] for r in rs])
            for r in rs:
                centered.append({
                  "isolation":r["isolation"]-mi,
                  "delta":r["delta"]-md,
                  "empty":r["empty"]-me
                })
        within=corrset(centered,"isolation","delta","empty")

        out={
          "schema":"structural.global_mammals_isolation_empty_support_audit_result.v1_87",
          "status":"POSTHOC_ISOLATION_EMPTY_SUPPORT_AUDIT_COMPLETE",
          "blocks":168,
          "bioregions":len(by),
          "raw":raw,
          "within_bioregion_centered":within,
          "interpretation":"graph-source emptiness does not explain the observed external-isolation attenuation if the partial correlations remain close to the corresponding unadjusted isolation correlations",
          "posthoc":True,
          "causal_mediation_claimed":False,
          "may_change_primary_status":False,
          "counts_as_confirmatory_evidence":False,
          "new_response_accessed":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={"schema":"structural.global_mammals_isolation_empty_support_audit_result.v1_87","status":"STOP","reason":str(e),"posthoc":True,"may_change_primary_status":False,"counts_as_confirmatory_evidence":False,"new_response_accessed":False};code=2
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
