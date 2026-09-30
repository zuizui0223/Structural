#!/usr/bin/env python3
"""Freeze exploratory mammal R0-R3-C models and confirmatory R3/C predictions.

This is a separate nonconfirmatory lineage after the terminal v1.65 parser
failure. The scientific model is exactly v1.67. Confirmatory occurrence values
are never downloaded, decoded, or used here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_exploratory_preconfirmatory_contract_v1_72.json"
EARTH_RADIUS_KM=6371.0088
MAGIC=b"STRUCTURAL_MAMMAL_PRED_V1\n"

class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def load_csv(path:Path)->list[dict]:
    with path.open("r",encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

def parse_num(x)->float:
    s=str(x).strip()
    try:
        v=float.fromhex(s) if s.lower().startswith(("0x","+0x","-0x")) else float(s)
    except Exception as e:
        raise Stop(f"invalid numeric value: {s!r}") from e
    if not math.isfinite(v): raise Stop("nonfinite numeric value")
    return v

def sigmoid(x):
    out=np.empty_like(x,dtype=np.float64)
    pos=x>=0
    out[pos]=1.0/(1.0+np.exp(-x[pos]))
    ex=np.exp(x[~pos]);out[~pos]=ex/(1.0+ex)
    return out

def fit_ridge(X,y,columns):
    X=np.asarray(X,dtype=np.float64,order="C")
    y=np.asarray(y,dtype=np.float64)
    p=X.shape[1]
    if X.ndim!=2 or y.shape!=(X.shape[0],) or p!=len(columns):
        raise Stop("fit dimension drift")
    beta=np.zeros(p,dtype=np.float64)
    penalty=np.ones(p,dtype=np.float64);penalty[0]=0.0
    final=math.inf
    for iteration in range(1,101):
        eta=X@beta
        mu=sigmoid(eta)
        w=mu*(1.0-mu)
        grad=X.T@(y-mu)-penalty*beta
        H=X.T@(X*w[:,None])
        H.flat[::p+1]+=penalty
        try:
            delta=np.linalg.solve(H,grad)
        except np.linalg.LinAlgError as e:
            raise Stop("ridge IRLS linear solve failed") from e
        if not np.all(np.isfinite(delta)): raise Stop("nonfinite IRLS delta")
        beta+=delta
        final=float(np.max(np.abs(delta)))
        if final<=1e-8:
            return {"columns":list(columns),"coefficients":beta,"iterations":iteration,"final_delta":final}
    raise Stop("ridge IRLS did not converge within 100 iterations")

def predict(X,fit):
    p=sigmoid(np.asarray(X,dtype=np.float64)@fit["coefficients"])
    return np.clip(p,1e-12,0.999999999999)

def model_mapping(fit):
    return {
      "columns":fit["columns"],
      "coefficients_hex":[float(x).hex() for x in fit["coefficients"]],
      "iterations":fit["iterations"],
      "final_max_abs_delta_hex":float(fit["final_delta"]).hex(),
      "ridge_lambda_hex":float(1.0).hex(),
    }

def vector_logit(successes,trials):
    s=np.asarray(successes,dtype=np.float64)
    p=(s+0.5)/(float(trials)+1.0)
    return np.log(p/(1.0-p))

def haversine_matrix(target_coords,pilot_coords):
    lat=np.radians(target_coords[:,0])[:,None]
    lon=np.radians(target_coords[:,1])[:,None]
    plat=np.radians(pilot_coords[:,0])[None,:]
    plon=np.radians(pilot_coords[:,1])[None,:]
    dp=plat-lat;dl=plon-lon
    a=np.sin(dp/2.0)**2+np.cos(lat)*np.cos(plat)*np.sin(dl/2.0)**2
    return 2.0*EARTH_RADIUS_KM*np.arcsin(np.minimum(1.0,np.sqrt(a)))

def dijkstra_array(source_idx,adj,n):
    dist=np.full(n,np.inf,dtype=np.float64)
    dist[source_idx]=0.0
    q=[(0.0,source_idx)]
    while q:
        d,u=heapq.heappop(q)
        if d!=dist[u]: continue
        for v,w in adj[u]:
            nd=d+w
            if nd<dist[v]:
                dist[v]=nd
                heapq.heappush(q,(nd,v))
    return dist

def type7(values,p):
    xs=np.sort(np.asarray(values,dtype=np.float64))
    if xs.size==0: raise Stop("empty quantile input")
    if xs.size==1:return float(xs[0])
    h=(xs.size-1)*p
    lo=int(math.floor(h));hi=int(math.ceil(h))
    if lo==hi:return float(xs[lo])
    frac=h-lo
    return float(xs[lo]*(1-frac)+xs[hi]*frac)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("pilot_universe",type=Path)
    ap.add_argument("pilot_matrix",type=Path)
    ap.add_argument("state_reference",type=Path)
    ap.add_argument("graph_edges",type=Path)
    ap.add_argument("reference_receipt",type=Path)
    ap.add_argument("safe_appendix2",type=Path)
    ap.add_argument("pilot_routing",type=Path)
    ap.add_argument("confirmatory_routing",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--predictions",type=Path,required=True)
    ap.add_argument("--entity-order",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_exploratory_preconfirmatory_contract.v1_72":
            raise Stop("contract schema drift")
        if np.__version__!=c["numerics"]["numpy_version"]:
            raise Stop(f"NumPy version drift: {np.__version__}")
        exp=c["required_inputs"]
        for path,key in [
          (a.pilot_universe,"pilot_species_universe_sha256"),
          (a.pilot_matrix,"pilot_matrix_sha256"),
          (a.state_reference,"state_reference_sha256"),
          (a.graph_edges,"source_graph_edges_sha256"),
          (a.reference_receipt,"reference_receipt_sha256"),
          (a.safe_appendix2,"safe_appendix2_sha256"),
          (a.pilot_routing,"pilot_routing_sha256"),
          (a.confirmatory_routing,"confirmatory_routing_sha256"),
        ]:
            if sha(path)!=exp[key]: raise Stop(f"input SHA drift: {key}")

        universe=load_csv(a.pilot_universe)
        if len(universe)!=c["dimensions"]["focal_species"]: raise Stop("focal species count drift")
        if tuple(universe[0].keys())!=("species_index","source_data_column_index","species_name","pilot_presence","pilot_absence"):
            raise Stop("pilot universe schema drift")
        species_names=[]
        for j,r in enumerate(universe):
            if int(r["species_index"])!=j: raise Stop("species index drift")
            if int(r["source_data_column_index"])<2: raise Stop("invalid source data column")
            if int(r["pilot_presence"])<13 or int(r["pilot_absence"])<13: raise Stop("species threshold drift")
            species_names.append(str(r["species_name"]))
        if len(set(species_names))!=len(species_names): raise Stop("duplicate focal species")
        S=len(species_names)
        labels=[f"S{j:05d}" for j in range(S)]

        pilot_route=load_csv(a.pilot_routing)
        conf_route=load_csv(a.confirmatory_routing)
        if len(pilot_route)!=1275 or len(conf_route)!=4126: raise Stop("routing count drift")
        if tuple(pilot_route[0].keys())!=("ID","block_id","bioregion") or tuple(conf_route[0].keys())!=("ID","block_id","bioregion"):
            raise Stop("routing schema drift")
        pilot_ids=[str(r["ID"]) for r in pilot_route]
        confirm_ids=[str(r["ID"]) for r in conf_route]
        if len(set(pilot_ids))!=1275 or len(set(confirm_ids))!=4126 or set(pilot_ids)&set(confirm_ids):
            raise Stop("routing identity drift")
        all_ids=pilot_ids+confirm_ids
        id_to_idx={iid:i for i,iid in enumerate(all_ids)}

        matrix_rows=load_csv(a.pilot_matrix)
        if len(matrix_rows)!=1275: raise Stop("pilot matrix island-row count drift")
        if [str(r["ID"]) for r in matrix_rows]!=pilot_ids: raise Stop("pilot matrix routing order drift")
        expected_matrix_header=["ID","block_id","bioregion"]+labels
        if list(matrix_rows[0].keys())!=expected_matrix_header: raise Stop("pilot matrix column drift")
        Y=np.empty((1275,S),dtype=np.int8)
        for i,r in enumerate(matrix_rows):
            if r["block_id"]!=pilot_route[i]["block_id"] or r["bioregion"]!=pilot_route[i]["bioregion"]:
                raise Stop("pilot matrix routing metadata drift")
            for j,label in enumerate(labels):
                y=int(r[label])
                if y not in (0,1): raise Stop("pilot target domain drift")
                Y[i,j]=y
        if np.any(Y.sum(axis=0)<13) or np.any((1275-Y.sum(axis=0))<13):
            raise Stop("realized species universe violates frozen m=13")

        state_rows=load_csv(a.state_reference)
        if len(state_rows)!=5401: raise Stop("state population drift")
        smap={str(r["ID"]):r for r in state_rows}
        if set(smap)!=set(all_ids): raise Stop("state/routing population mismatch")
        for r in pilot_route+conf_route:
            s=smap[r["ID"]]
            if s["block_id"]!=r["block_id"] or s["bioregion"]!=r["bioregion"]:
                raise Stop("state/routing block or region mismatch")

        safe_rows=load_csv(a.safe_appendix2)
        safemap={str(r["ID"]):r for r in safe_rows}
        if len(safe_rows)!=5592 or not set(all_ids)<=set(safemap):
            raise Stop("safe-coordinate support drift")
        coords=np.array([
          [parse_num(safemap[iid]["Latitude_centroid"]),parse_num(safemap[iid]["Longitude_centroid"])]
          for iid in all_ids
        ],dtype=np.float64)
        if np.any(~np.isfinite(coords)): raise Stop("nonfinite coordinates")

        rr=json.loads(a.reference_receipt.read_text())
        if rr.get("schema")!="structural.global_mammals_reference_operator_result.v1_40":
            raise Stop("reference receipt schema drift")
        scales={k:float.fromhex(v) for k,v in rr["bioregion_edge_scale_hex"].items()}
        pool_levels=sorted({smap[i]["bioregion"] for i in all_ids})
        if pool_levels!=sorted(scales): raise Stop("bioregion scale level drift")
        if len(pool_levels)!=12: raise Stop("bioregion count drift")
        pool_index={p:i for i,p in enumerate(pool_levels)}

        adj=[[] for _ in all_ids]
        max_edge={p:0.0 for p in pool_levels}
        edge_rows=load_csv(a.graph_edges)
        if len(edge_rows)!=73162: raise Stop("graph edge count drift")
        for r in edge_rows:
            p=r["bioregion"];u=str(r["from_ID"]);v=str(r["to_ID"]);d=float.fromhex(r["distance_km_hex"])
            if p not in scales or u not in id_to_idx or v not in id_to_idx or d<=0:
                raise Stop("graph edge outside frozen support")
            if smap[u]["bioregion"]!=p or smap[v]["bioregion"]!=p:
                raise Stop("cross-bioregion graph edge")
            ui=id_to_idx[u];vi=id_to_idx[v]
            adj[ui].append((vi,d));adj[vi].append((ui,d))
            max_edge[p]=max(max_edge[p],d)
        node_count=Counter(smap[i]["bioregion"] for i in all_ids)
        if any(node_count[p]<2 or max_edge[p]<=0 for p in pool_levels):
            raise Stop("invalid graph sentinel context")

        # Response-independent distance matrices. Dg is computed from each pilot
        # source, which is mathematically identical to target-to-source shortest
        # paths in the undirected frozen graph and scales better than 5,401 Dijkstra runs.
        De=haversine_matrix(coords,coords[:1275])
        Dg=np.empty((5401,1275),dtype=np.float64)
        for j,pid in enumerate(pilot_ids):
            Dg[:,j]=dijkstra_array(id_to_idx[pid],adj,5401)

        pilot_block=np.array([r["block_id"] for r in pilot_route],dtype=object)
        pilot_pool=np.array([r["bioregion"] for r in pilot_route],dtype=object)
        all_pool=np.array([smap[i]["bioregion"] for i in all_ids],dtype=object)

        def source_raw(target_index:int,training:bool):
            target_id=all_ids[target_index]
            pool=all_pool[target_index]
            scale=scales[pool]
            allowed=np.ones(1275,dtype=bool)
            if training:
                allowed=(pilot_block!=smap[target_id]["block_id"])
            trials=int(allowed.sum())
            if trials<1: raise Stop("cross-fit left zero global pilot trials")
            successes=Y[allowed].sum(axis=0)
            global_logit=vector_logit(successes,trials)

            rallowed=allowed & (pilot_pool==pool)
            rtrials=int(rallowed.sum())
            rsuccess=Y[rallowed].sum(axis=0) if rtrials else np.zeros(S,dtype=np.int64)
            regional_logit=vector_logit(rsuccess,rtrials)

            occ=(Y==1)&allowed[:,None]
            ed=De[target_index]
            nearest_e=np.min(np.where(occ,ed[:,None],np.inf),axis=0)
            empty_e=~np.isfinite(nearest_e)
            nearest_e[empty_e]=math.pi*EARTH_RADIUS_KM+scale
            pressure_e=np.sum(occ*np.exp(-ed/scale)[:,None],axis=0,dtype=np.float64)

            gd=Dg[target_index]
            reachable=np.isfinite(gd)
            gocc=occ & reachable[:,None]
            nearest_g=np.min(np.where(gocc,gd[:,None],np.inf),axis=0)
            empty_g=~np.isfinite(nearest_g)
            nearest_g[empty_g]=(node_count[pool]-1)*max_edge[pool]+scale
            gw=np.zeros(1275,dtype=np.float64)
            gw[reachable]=np.exp(-gd[reachable]/scale)
            pressure_g=np.sum(gocc*gw[:,None],axis=0,dtype=np.float64)

            raw=np.column_stack([
              global_logit,
              regional_logit,
              np.log1p(nearest_e),
              np.log1p(pressure_e),
              np.log1p(nearest_g),
              np.log1p(pressure_g),
            ])
            return raw,int(empty_e.sum()),int(empty_g.sum())

        training_rows=1275*S
        source_train=np.empty((training_rows,6),dtype=np.float64)
        y=np.empty(training_rows,dtype=np.float64)
        train_empty_e=train_empty_g=0
        for i in range(1275):
            raw,ee,eg=source_raw(i,True)
            sl=slice(i*S,(i+1)*S)
            source_train[sl]=raw
            y[sl]=Y[i]
            train_empty_e+=ee;train_empty_g+=eg

        src_mean=np.mean(source_train,axis=0,dtype=np.float64)
        src_var=np.mean((source_train-src_mean)**2,axis=0,dtype=np.float64)
        src_sd=np.sqrt(src_var)
        if np.any(~np.isfinite(src_sd)) or np.any(src_sd<=0):
            raise Stop("zero/nonfinite source-feature SD")
        source_z=(source_train-src_mean)/src_sd

        r0_cont=[
          "z_Climate_velocity","z_Temperature_mean","z_Temperature_sd",
          "z_Precipitation_mean","z_Precipitation_sd","z_Elevation_sd",
        ]
        r1_cont=["z_log_Area","z_Current_isolation","z_Past_isolation"]
        r2_cont=["z_log1p_nearest_island_km","z_generic_neighbor_pressure"]
        source_names=[
          "global_occupancy_jeffreys_logit","bioregion_prevalence_jeffreys_logit",
          "log1p_nearest_euclidean_source_km","log1p_euclidean_source_pressure",
          "log1p_nearest_graph_source_km","log1p_graph_source_pressure",
        ]
        columns=["intercept"]+[f"bioregion::{p}" for p in pool_levels]+r0_cont+r1_cont+r2_cont+[
          f"z_{x}" for x in source_names
        ]
        if len(columns)!=30: raise Stop("full model column count drift")

        X=np.empty((training_rows,30),dtype=np.float64)
        for i,eid in enumerate(pilot_ids):
            sl=slice(i*S,(i+1)*S)
            row=smap[eid]
            X[sl,0]=1.0
            one=np.zeros(12,dtype=np.float64);one[pool_index[row["bioregion"]]]=1.0
            X[sl,1:13]=one
            X[sl,13:19]=[parse_num(row[x]) for x in r0_cont]
            X[sl,19:22]=[parse_num(row[x]) for x in r1_cont]
            X[sl,22:24]=[parse_num(row[x]) for x in r2_cont]
        X[:,24:30]=source_z

        bounds={"R0":19,"R1":22,"R2":24,"R3":28,"C":30}
        fits={}
        for name in ("R0","R1","R2","R3","C"):
            k=bounds[name]
            fits[name]=fit_ridge(X[:,:k],y,columns[:k])

        a.entity_order.parent.mkdir(parents=True,exist_ok=True)
        with a.entity_order.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n")
            w.writerow(["ID","block_id","bioregion"])
            for r in conf_route:
                w.writerow([r["ID"],r["block_id"],r["bioregion"]])

        confirm_empty_e=confirm_empty_g=0
        absdiff=np.empty(4126*S,dtype=np.float64)
        block_sum=defaultdict(float);block_n=defaultdict(int)
        a.predictions.parent.mkdir(parents=True,exist_ok=True)
        with a.predictions.open("wb") as h:
            h.write(MAGIC)
            h.write(struct.pack("<II",4126,S))
            offset=0
            for ci,eid in enumerate(confirm_ids):
                target_index=1275+ci
                raw,ee,eg=source_raw(target_index,False)
                confirm_empty_e+=ee;confirm_empty_g+=eg
                z=(raw-src_mean)/src_sd
                row=smap[eid]
                base=np.empty((S,30),dtype=np.float64)
                base[:,0]=1.0
                one=np.zeros(12,dtype=np.float64);one[pool_index[row["bioregion"]]]=1.0
                base[:,1:13]=one
                base[:,13:19]=[parse_num(row[x]) for x in r0_cont]
                base[:,19:22]=[parse_num(row[x]) for x in r1_cont]
                base[:,22:24]=[parse_num(row[x]) for x in r2_cont]
                base[:,24:30]=z
                p3=predict(base[:,:28],fits["R3"])
                pc=predict(base[:,:30],fits["C"])
                pair=np.empty((S,2),dtype="<f8")
                pair[:,0]=p3;pair[:,1]=pc
                h.write(pair.tobytes(order="C"))
                d=np.abs(pc-p3)
                absdiff[offset:offset+S]=d;offset+=S
                b=row["block_id"]
                block_sum[b]+=float(np.sum(d,dtype=np.float64));block_n[b]+=S

        threshold=float(c["response_independent_estimability_audit"]["threshold_abs_pC_minus_pR3"])
        blocks={b:block_sum[b]/block_n[b] for b in sorted(block_sum)}
        if len(blocks)!=168: raise Stop("confirmatory block count drift")
        cells_above=int(np.sum(absdiff>threshold))
        blocks_above=sum(v>threshold for v in blocks.values())

        result={
          "schema":"structural.global_mammals_exploratory_preconfirmatory_result.v1_72",
          "status":"NONCONFIRMATORY_EXPLORATORY_R3_C_PREDICTIONS_FROZEN_BEFORE_CONFIRMATORY_RESPONSE",
          "candidate_id":c["candidate_id"],
          "analysis_route":c["analysis_route"],
          "focal_species":S,
          "training_rows":training_rows,
          "confirmatory_entities":4126,
          "confirmatory_blocks":168,
          "prediction_cells":4126*S,
          "bioregion_levels":pool_levels,
          "source_standardization":{
            name:{"mean_hex":float(src_mean[i]).hex(),"sd_hex":float(src_sd[i]).hex()}
            for i,name in enumerate(source_names)
          },
          "training_empty_global_source_rows":train_empty_e,
          "training_empty_graph_source_rows":train_empty_g,
          "confirmatory_empty_global_source_rows":confirm_empty_e,
          "confirmatory_empty_graph_source_rows":confirm_empty_g,
          "models":{name:model_mapping(fits[name]) for name in ("R0","R1","R2","R3","C")},
          "pilot_species_universe_sha256":sha(a.pilot_universe),
          "pilot_matrix_sha256":sha(a.pilot_matrix),
          "entity_order_sha256":sha(a.entity_order),
          "prediction_binary_sha256":sha(a.predictions),
          "prediction_binary_magic":"STRUCTURAL_MAMMAL_PRED_V1\\n",
          "prediction_binary_shape":[4126,S,2],
          "prediction_binary_fields":["p_R3","p_C"],
          "response_independent_prediction_estimability_audit":{
            "threshold_abs_pC_minus_pR3":threshold,
            "cells_with_abs_pC_minus_pR3_gt_threshold":cells_above,
            "total_cells":int(absdiff.size),
            "fraction":float(cells_above/absdiff.size),
            "median_abs_probability_difference":float(np.median(absdiff)),
            "mean_abs_probability_difference":float(np.mean(absdiff,dtype=np.float64)),
            "max_abs_probability_difference":float(np.max(absdiff)),
            "confirmatory_blocks":168,
            "blocks_with_nonzero_mean_abs_probability_difference_gt_threshold":blocks_above,
          },
          "pilot_response_used":True,
          "confirmatory_target_values_used":False,
          "confirmatory_occurrence_opened":False,
          "confirmatory_response_authorized":False,
          "fresh_status_restored":False,
          "counts_as_fresh_confirmation":False,
          "counts_as_primary_confirmatory_evidence":False,
          "next_action":"freeze this exploratory prediction artifact; only a separately labelled nonconfirmatory one-shot scorer may open confirmatory occurrence values"
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.global_mammals_exploratory_preconfirmatory_result.v1_72",
          "status":"STOP",
          "reason":str(e),
          "confirmatory_target_values_used":False,
          "confirmatory_occurrence_opened":False,
          "confirmatory_response_authorized":False,
          "fresh_status_restored":False,
          "counts_as_fresh_confirmation":False,
          "counts_as_primary_confirmatory_evidence":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__": raise SystemExit(main())
