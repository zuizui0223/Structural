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
def dj(adj,s):
    d=np.full(len(adj),np.inf);d[s]=0.;q=[(0.,s)]
    while q:
        x,u=heapq.heappop(q)
        if x!=d[u]:continue
        for v,w in adj[u]:
            z=x+w
            if z<d[v]:d[v]=z;heapq.heappush(q,(z,v))
    return d
def write(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def source_turnover(weights):
    # weights shape: sources x heldout targets
    total=weights.sum(axis=0,dtype=np.float64)
    ok=total>0
    if not np.any(ok):raise RuntimeError("no supported heldout targets")
    p=weights[:,ok]/total[ok]
    concentration=np.sum(p*p,axis=0,dtype=np.float64)
    alpha=1.0/float(np.mean(concentration,dtype=np.float64))
    q=np.mean(p,axis=1,dtype=np.float64)
    gamma=1.0/float(np.sum(q*q,dtype=np.float64))
    beta=gamma/alpha
    dom=float(np.mean(np.max(p,axis=0),dtype=np.float64))
    return alpha,gamma,beta,dom,int(ok.sum())

def main():
    ap=argparse.ArgumentParser()
    for n in ["species_universe","pilot_matrix","graph_edges","reference_receipt","pilot_routing","heldout_routing"]:
        ap.add_argument(n,type=Path)
    ap.add_argument("--species-table",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    ap.add_argument("--null-reps",type=int,default=1000)
    ap.add_argument("--seed",type=int,default=20261007)
    ap.add_argument("--bootstrap-seed",type=int,default=2026100701)
    a=ap.parse_args()
    try:
        if np.__version__!="2.3.3":raise RuntimeError("NumPy drift")
        for p in [a.species_universe,a.pilot_matrix,a.graph_edges,a.reference_receipt,a.pilot_routing,a.heldout_routing]:
            if p.name not in H or sha(p)!=H[p.name]:raise RuntimeError("input SHA drift: "+p.name)
        if (a.null_reps,a.seed,a.bootstrap_seed)!=(1000,20261007,2026100701):raise RuntimeError("Monte Carlo drift")
        U,M,P,T=read(a.species_universe),read(a.pilot_matrix),read(a.pilot_routing),read(a.heldout_routing)
        if (len(U),len(M),len(P),len(T))!=(529,1275,1275,4126):raise RuntimeError("population drift")
        labs=[f"S{i:05d}" for i in range(529)]
        Y=np.array([[int(r[z]) for z in labs] for r in M],dtype=np.int8)
        cnt=Y.sum(0)
        if np.any(cnt<1)|np.any(cnt>4):raise RuntimeError("source count drift")
        ids=[int(r["ID"]) for r in P]+[int(r["ID"]) for r in T];ix={z:i for i,z in enumerate(ids)}
        pp=np.array([r["bioregion"] for r in P],object)
        tp=np.array([r["bioregion"] for r in T],object)
        rr=json.loads(a.reference_receipt.read_text())
        scale={k:float.fromhex(v) for k,v in rr["bioregion_edge_scale_hex"].items()}
        adj=[[] for _ in ids]
        for r in read(a.graph_edges):
            u,v=ix[int(r["from_ID"])],ix[int(r["to_ID"])];d=float.fromhex(r["distance_km_hex"])
            adj[u].append((v,d));adj[v].append((u,d))
        held_idx=np.array([ix[int(r["ID"])] for r in T],dtype=int)
        held_scale=np.array([scale[r["bioregion"]] for r in T],dtype=np.float64)

        # Response-free source x target access surface.
        W=np.zeros((1275,4126),dtype=np.float64)
        for i,r in enumerate(P):
            d=dj(adj,ix[int(r["ID"])])[held_idx]
            ok=np.isfinite(d)
            W[i,ok]=np.exp(-d[ok]/held_scale[ok])

        bypool={p:np.flatnonzero(pp==p) for p in sorted(set(pp))}
        rng=np.random.default_rng(a.seed)
        rows=[];dbeta=[];dalpha=[];dgamma=[];ddom=[]
        gt_beta=gt_q975=lt_q025=0
        for j,u in enumerate(U):
            pos=np.flatnonzero(Y[:,j]);k=len(pos)
            if k<2:continue
            comp=Counter(str(pp[z]) for z in pos)
            alpha,gamma,beta,dom,nsup=source_turnover(W[pos])
            nb=np.empty(a.null_reps);na=np.empty(a.null_reps);ng=np.empty(a.null_reps);nd=np.empty(a.null_reps)
            for b in range(a.null_reps):
                z=[]
                for pool,n in sorted(comp.items()):
                    z.extend(rng.choice(bypool[pool],n,replace=False))
                aa,gg,bb,dm,_=source_turnover(W[np.asarray(z,dtype=int)])
                na[b]=aa;ng[b]=gg;nb[b]=bb;nd[b]=dm
            bmean=float(nb.mean()); b025=qtile(nb,.025); b975=qtile(nb,.975)
            d_b=beta-bmean;d_a=alpha-float(na.mean());d_g=gamma-float(ng.mean());d_d=dom-float(nd.mean())
            dbeta.append(d_b);dalpha.append(d_a);dgamma.append(d_g);ddom.append(d_d)
            gt_beta+=beta>bmean;gt_q975+=beta>b975;lt_q025+=beta<b025
            rows.append({
              "species_index":j,"species_name":u["species_name"],"n_sources":k,
              "n_source_bioregions":len(comp),"supported_targets":nsup,
              "alpha_effective_sources":alpha,"gamma_effective_sources":gamma,
              "beta_source_turnover":beta,"mean_target_dominant_share":dom,
              "null_mean_alpha_effective_sources":float(na.mean()),
              "null_mean_gamma_effective_sources":float(ng.mean()),
              "null_mean_beta_source_turnover":bmean,
              "null_mean_target_dominant_share":float(nd.mean()),
              "actual_minus_null_alpha":d_a,"actual_minus_null_gamma":d_g,
              "actual_minus_null_beta":d_b,"actual_minus_null_dominant_share":d_d,
              "null_q025_beta":b025,"null_q975_beta":b975
            })
        if len(rows)!=212:raise RuntimeError("multi-source species count drift")
        write(a.species_table,rows)

        def boot_ci(vals,seed):
            z=np.asarray(vals,dtype=np.float64);rg=np.random.default_rng(seed)
            b=np.array([z[rg.integers(0,len(z),len(z))].mean() for _ in range(10000)])
            return [qtile(b,.025),qtile(b,.975)]

        out={
          "schema":"structural.global_mammals_distributed_irreplaceability_result.v1_181",
          "status":"POSTHOC_RESPONSE_FREE_SOURCE_TURNOVER_DIAGNOSTIC_COMPLETE",
          "species":529,"multi_source_species":212,
          "heldout_targets_geometry_only":4126,
          "heldout_occurrence_values_used":False,
          "heldout_occurrence_values_opened":False,
          "result":{
            "median_alpha_effective_sources":float(np.median([r["alpha_effective_sources"] for r in rows])),
            "median_gamma_effective_sources":float(np.median([r["gamma_effective_sources"] for r in rows])),
            "median_beta_source_turnover":float(np.median([r["beta_source_turnover"] for r in rows])),
            "median_mean_target_dominant_share":float(np.median([r["mean_target_dominant_share"] for r in rows])),
            "mean_actual_minus_null_beta":float(np.mean(dbeta)),
            "mean_actual_minus_null_beta_bootstrap_ci95":boot_ci(dbeta,a.bootstrap_seed),
            "mean_actual_minus_null_alpha":float(np.mean(dalpha)),
            "mean_actual_minus_null_gamma":float(np.mean(dgamma)),
            "mean_actual_minus_null_target_dominant_share":float(np.mean(ddom)),
            "actual_beta_gt_null_mean":int(gt_beta),
            "actual_beta_gt_null_q975":int(gt_q975),
            "actual_beta_lt_null_q025":int(lt_q025)
          },
          "interpretation":"response-free post-hoc diagnostic of spatial turnover in source influence across heldout geometry targets; not dispersal, persistence, rescue or temporal range-contraction evidence",
          "species_table_sha256":sha(a.species_table)
        }
        a.result.parent.mkdir(parents=True,exist_ok=True)
        a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print(json.dumps(out,indent=2));return 0
    except Exception as e:
        out={"schema":"structural.global_mammals_distributed_irreplaceability_result.v1_181","status":"STOP","reason":str(e),"heldout_occurrence_values_used":False}
        a.result.parent.mkdir(parents=True,exist_ok=True)
        a.result.write_text(json.dumps(out,indent=2)+"\n")
        print(json.dumps(out,indent=2));return 2

if __name__=="__main__":raise SystemExit(main())
