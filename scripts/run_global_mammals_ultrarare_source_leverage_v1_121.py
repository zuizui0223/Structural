#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,heapq,json,math
from collections import Counter
from pathlib import Path
import numpy as np

H={
"ultrarare_species_universe.csv":"4f801eac218edb00f319cd04416af3c6e7d7a90e04b68868eeed47f4d403dfd9",
"ultrarare_pilot_matrix.csv":"476c35e7e197c6b7a9daf7fc6697101add9e0bda1690de94f64efffd5468fb79",
"source_graph_edges.csv":"92e0ec3e5335233f6430b18a972235481845848796d0d7e1cd12cc6fb10d090f",
"reference_receipt.json":"55a0581c7c7d0136ecb6a025fa2a41f5ddeeb8ec674b8500bf7c37f81763954a",
"pilot_ids.csv":"ac3898162331ce4217ea63d8b9330051acaa3a39ddca425cd0b48246a11caec0",
"confirmatory_ids.csv":"afda05287599110c7248c5cb0c1931689a2aee40f8ff4ff5b76509aff5350715"}

def read(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def qtile(x,q):return float(np.quantile(np.asarray(x,float),q,method="linear"))
def effective_source_count(m):
    m=np.asarray(m,float); s=float(m.sum())
    if not math.isfinite(s) or s<=0:raise RuntimeError("nonpositive mass")
    p=m/s
    return float(1/(p@p)),float(p.max())
def dj(adj,s):
    d=np.full(len(adj),np.inf);d[s]=0;q=[(0.,s)]
    while q:
        x,u=heapq.heappop(q)
        if x!=d[u]:continue
        for v,w in adj[u]:
            z=x+w
            if z<d[v]:d[v]=z;heapq.heappush(q,(z,v))
    return d
def write(p,rs):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)

def main():
    a=argparse.ArgumentParser()
    for n in ["species_universe","pilot_matrix","graph_edges","reference_receipt","pilot_routing","heldout_routing"]:a.add_argument(n,type=Path)
    a.add_argument("--source-table",type=Path,required=True);a.add_argument("--species-table",type=Path,required=True);a.add_argument("--result",type=Path,required=True)
    a.add_argument("--null-reps",type=int,default=1000);a.add_argument("--seed",type=int,default=20261004);a.add_argument("--bootstrap-seed",type=int,default=2026100401)
    x=a.parse_args()
    try:
        if np.__version__!="2.3.3":raise RuntimeError("NumPy drift")
        ps=[x.species_universe,x.pilot_matrix,x.graph_edges,x.reference_receipt,x.pilot_routing,x.heldout_routing]
        for p in ps:
            if p.name not in H or sha(p)!=H[p.name]:raise RuntimeError("input SHA drift: "+p.name)
        if (x.null_reps,x.seed,x.bootstrap_seed)!=(1000,20261004,2026100401):raise RuntimeError("Monte Carlo drift")
        U,M,P,T=read(x.species_universe),read(x.pilot_matrix),read(x.pilot_routing),read(x.heldout_routing)
        if (len(U),len(M),len(P),len(T))!=(529,1275,1275,4126):raise RuntimeError("population drift")
        labs=[f"S{i:05d}" for i in range(529)]
        ids=[int(r["ID"]) for r in P]+[int(r["ID"]) for r in T];ix={z:i for i,z in enumerate(ids)}
        pp=np.array([r["bioregion"] for r in P],object);tp=np.array([r["bioregion"] for r in T],object)
        Y=np.array([[int(r[z]) for z in labs] for r in M],np.int8)
        cnt=Y.sum(0)
        if np.any(cnt<1)|np.any(cnt>4):raise RuntimeError("source-count drift")
        rr=json.loads(x.reference_receipt.read_text());scale={k:float.fromhex(v) for k,v in rr["bioregion_edge_scale_hex"].items()}
        adj=[[] for _ in ids]
        for r in read(x.graph_edges):
            u,v=ix[int(r["from_ID"])],ix[int(r["to_ID"])];d=float.fromhex(r["distance_km_hex"])
            adj[u].append((v,d));adj[v].append((u,d))
        hi=np.array([ix[int(r["ID"])] for r in T]);hs=np.array([scale[r["bioregion"]] for r in T])
        mass=np.empty(1275)
        for i,r in enumerate(P):
            d=dj(adj,ix[int(r["ID"])])[hi];ok=np.isfinite(d)
            mass[i]=np.exp(-d[ok]/hs[ok]).sum()
        bypool={p:np.flatnonzero(pp==p) for p in sorted(set(pp))}
        heldn=Counter(tp);rng=np.random.default_rng(x.seed);sr=[];sp=[];delta=[]
        gt=lo=hi95=0
        for j,u in enumerate(U):
            pos=np.flatnonzero(Y[:,j]);k=len(pos);pools=[str(pp[z]) for z in pos]
            ne,dom=effective_source_count(mass[pos]);shares=mass[pos]/mass[pos].sum();comp=Counter(pools)
            for z,sh in zip(pos,shares):
                empty=heldn[str(pp[z])] if comp[str(pp[z])]==1 else 0
                sr.append({"species_index":j,"species_name":u["species_name"],"n_sources":k,"source_ID":int(P[z]["ID"]),
                           "source_bioregion":str(pp[z]),"graph_pressure_mass_share":float(sh),
                           "source_removal_graph_empty_count":int(empty)})
            nm=n025=n975=dd=None
            if k>1:
                vv=np.empty(x.null_reps)
                for b in range(x.null_reps):
                    z=[]
                    for p,c in sorted(comp.items()):z.extend(rng.choice(bypool[p],c,replace=False))
                    vv[b]=effective_source_count(mass[np.array(z,int)])[0]
                nm=float(vv.mean());n025=qtile(vv,.025);n975=qtile(vv,.975);dd=ne-nm;delta.append(dd)
                gt+=ne>nm;lo+=ne<n025;hi95+=ne>n975
            sp.append({"species_index":j,"species_name":u["species_name"],"n_sources":k,"n_source_bioregions":len(comp),
                       "pressure_effective_source_count":ne,"effective_over_nominal":ne/k,"dominant_source_pressure_share":dom,
                       "any_source_removal_creates_graph_empty":any(comp[p]==1 and heldn[p]>0 for p in comp),
                       "null_mean_effective_source_count":nm,"actual_minus_null_mean_effective_count":dd,
                       "null_q025_effective_source_count":n025,"null_q975_effective_source_count":n975})
        write(x.source_table,sr);write(x.species_table,sp)
        groups={}
        for k in range(1,5):
            z=[r for r in sp if r["n_sources"]==k]
            groups[str(k)]={"species":len(z),"median_effective_source_count":float(np.median([r["pressure_effective_source_count"] for r in z])),
                            "median_effective_over_nominal":float(np.median([r["effective_over_nominal"] for r in z])),
                            "median_dominant_source_pressure_share":float(np.median([r["dominant_source_pressure_share"] for r in z])),
                            "species_where_any_removal_creates_graph_empty":sum(r["any_source_removal_creates_graph_empty"] for r in z)}
            if k>1:
                groups[str(k)].update(mean_actual_effective_source_count=float(np.mean([r["pressure_effective_source_count"] for r in z])),
                                      mean_null_effective_source_count=float(np.mean([r["null_mean_effective_source_count"] for r in z])),
                                      mean_actual_minus_null=float(np.mean([r["actual_minus_null_mean_effective_count"] for r in z])))
        d=np.array(delta);br=np.random.default_rng(x.bootstrap_seed);boot=np.array([d[br.integers(0,len(d),len(d))].mean() for _ in range(10000)])
        multi=[r for r in sp if r["n_sources"]>1]
        out={"schema":"structural.global_mammals_ultrarare_source_leverage_result.v1_121",
             "status":"POSTHOC_PILOT_PLUS_GEOMETRY_SOURCE_LEVERAGE_DIAGNOSTIC_COMPLETE",
             "heldout_occurrence_values_used":False,"heldout_occurrence_values_opened":False,"species":529,
             "pilot_sources_total":int(cnt.sum()),"heldout_islands_geometry_only":4126,"groups_by_nominal_source_count":groups,
             "multi_source_summary":{"species":len(multi),"median_dominant_source_pressure_share":float(np.median([r["dominant_source_pressure_share"] for r in multi])),
             "median_effective_over_nominal":float(np.median([r["effective_over_nominal"] for r in multi])),
             "multi_bioregion_species":sum(r["n_source_bioregions"]>1 for r in multi),
             "species_where_any_removal_creates_graph_empty":sum(r["any_source_removal_creates_graph_empty"] for r in multi),
             "actual_effective_count_gt_matched_null_mean":int(gt),"actual_effective_count_lt_null_q025":int(lo),"actual_effective_count_gt_null_q975":int(hi95),
             "paired_mean_actual_minus_null_effective_count":float(d.mean()),"paired_mean_bootstrap_ci95":[qtile(boot,.025),qtile(boot,.975)]},
             "interpretation":"response-free post-hoc mechanism diagnostic only; graph paths are not occupied-source chains; no causal dispersal or rescue inference",
             "source_table_sha256":sha(x.source_table),"species_table_sha256":sha(x.species_table)}
        x.result.parent.mkdir(parents=True,exist_ok=True);x.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2));return 0
    except Exception as e:
        out={"schema":"structural.global_mammals_ultrarare_source_leverage_result.v1_121","status":"STOP","reason":str(e),"heldout_occurrence_values_used":False}
        x.result.parent.mkdir(parents=True,exist_ok=True);x.result.write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2));return 2
if __name__=="__main__":raise SystemExit(main())
