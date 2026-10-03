#!/usr/bin/env python3
"""Freeze second-layer R3/C and degree+distance-matched rewired-C predictions.

This script uses only the already-open pilot matrix plus response-independent
island state, coordinates, routing and graph structure. It does not access the
held-out second-layer occurrence response.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import random
import struct
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np

from scripts.freeze_global_mammals_exploratory_preconfirmatory_v1_72 import (
    EARTH_RADIUS_KM,
    Stop,
    dijkstra_array,
    fit_ridge,
    haversine_matrix,
    load_csv,
    model_mapping,
    parse_num,
    predict,
    sha,
    type7,
    vector_logit,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_sealed_species_replication_contract_v1_94.json"
MAGIC=b"STRUCTURAL_MAMMAL_SECOND_LAYER_PRED_V1\n"
MASK_MAGIC=b"STRUCTURAL_MAMMAL_SECOND_LAYER_GRAPH_EMPTY_V1\n"

def edge_key(u:int,v:int):
    return (u,v) if u<v else (v,u)

def hav_pair(coords:np.ndarray,u:int,v:int)->float:
    lat1,lon1=coords[u];lat2,lon2=coords[v]
    p1=math.radians(float(lat1));p2=math.radians(float(lat2))
    dp=math.radians(float(lat2-lat1));dl=math.radians(float(lon2-lon1))
    a=math.sin(dp/2.0)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2.0)**2
    return 2.0*EARTH_RADIUS_KM*math.asin(min(1.0,math.sqrt(a)))

def connected(nodes:list[int],edges:list[tuple[int,int,float,int]])->bool:
    if not nodes:return False
    adj={u:[] for u in nodes}
    for u,v,_,_ in edges:
        adj[u].append(v);adj[v].append(u)
    seen={nodes[0]};q=deque([nodes[0]])
    while q:
        u=q.popleft()
        for v in adj[u]:
            if v not in seen:
                seen.add(v);q.append(v)
    return len(seen)==len(nodes)

def degree_signature(nodes:list[int],edges:list[tuple[int,int,float,int]]):
    d=Counter()
    for u,v,_,_ in edges:
        d[u]+=1;d[v]+=1
    return tuple(sorted(d[u] for u in nodes))

def bin_counts(edges):
    c=Counter(e[3] for e in edges)
    return tuple(c[i] for i in range(5))

def region_fingerprint(region:str,edges:list[tuple[int,int,float,int]],all_ids:list[str])->str:
    h=hashlib.sha256()
    h.update(region.encode("utf-8"));h.update(b"\n")
    for u,v,d,b in sorted(edges,key=lambda e:(all_ids[e[0]],all_ids[e[1]])):
        h.update(all_ids[u].encode());h.update(b"\t")
        h.update(all_ids[v].encode());h.update(b"\t")
        h.update(float(d).hex().encode());h.update(b"\t")
        h.update(str(b).encode());h.update(b"\n")
    return h.hexdigest()

def assign_bins(raw_edges:list[tuple[int,int,float]],bounds:list[float]):
    out=[]
    for u,v,d in raw_edges:
        b=bisect.bisect_right(bounds,d)
        if not 0<=b<=4:raise Stop("distance-bin assignment drift")
        out.append((u,v,d,b))
    return out

def rewire_region(region:str,nodes:list[int],original:list[tuple[int,int,float,int]],coords:np.ndarray,
                  seed:int,target_swaps:int,max_attempts:int,all_ids:list[str]):
    if len(nodes)<4 or len(original)<2:
        raise Stop(f"region too small for preregistered rewiring: {region}")
    orig_degree=degree_signature(nodes,original);orig_bins=bin_counts(original)
    # Bounds are recoverable from the original edge bins only through the
    # original lengths, so calculate exact type-7 quintiles here.
    lengths=[e[2] for e in original]
    bounds=[type7(lengths,q) for q in (0.2,0.4,0.6,0.8)]

    for retry in range(21):
        rng=random.Random(seed+100000*retry)
        edges=[list(e) for e in original]
        eset={edge_key(e[0],e[1]) for e in edges}
        accepted=attempts=0
        while accepted<target_swaps and attempts<max_attempts:
            attempts+=1
            i,j=rng.sample(range(len(edges)),2)
            u,v,d1,b1=edges[i];x,y,d2,b2=edges[j]
            if len({u,v,x,y})<4:continue
            if rng.random()<0.5:
                pairs=[(u,y),(x,v)]
            else:
                pairs=[(u,x),(v,y)]
            n1=edge_key(*pairs[0]);n2=edge_key(*pairs[1])
            if n1==n2 or n1[0]==n1[1] or n2[0]==n2[1]:continue
            old1=edge_key(u,v);old2=edge_key(x,y)
            if n1 in eset and n1 not in (old1,old2):continue
            if n2 in eset and n2 not in (old1,old2):continue
            nd1=hav_pair(coords,*n1);nd2=hav_pair(coords,*n2)
            nb1=bisect.bisect_right(bounds,nd1);nb2=bisect.bisect_right(bounds,nd2)
            if nb1==b1 and nb2==b2:
                repl=[(n1,nd1,b1),(n2,nd2,b2)]
            elif nb1==b2 and nb2==b1:
                repl=[(n2,nd2,b1),(n1,nd1,b2)]
            else:
                continue
            eset.remove(old1);eset.remove(old2)
            (a,b),nd,bb=repl[0];edges[i]=[a,b,nd,bb]
            (a,b),nd,bb=repl[1];edges[j]=[a,b,nd,bb]
            eset.add(edge_key(edges[i][0],edges[i][1]))
            eset.add(edge_key(edges[j][0],edges[j][1]))
            accepted+=1
        final=[tuple(e) for e in edges]
        if accepted<target_swaps:
            continue
        if not connected(nodes,final):
            continue
        if degree_signature(nodes,final)!=orig_degree:raise Stop("degree sequence changed")
        if bin_counts(final)!=orig_bins:raise Stop("edge-length bin counts changed")
        return final,{
          "region":region,"seed":seed,"retry_index":retry,
          "accepted_swaps":accepted,"attempts":attempts,
          "target_swaps":target_swaps,
          "edge_count":len(final),
          "degree_signature_sha256":hashlib.sha256(repr(orig_degree).encode()).hexdigest(),
          "distance_bin_counts":list(orig_bins),
          "fingerprint":region_fingerprint(region,final,all_ids),
        }
    raise Stop(f"could not produce connected rewired graph: {region}")

def adjacency(n:int,region_edges:dict[str,list[tuple[int,int,float,int]]]):
    adj=[[] for _ in range(n)]
    for edges in region_edges.values():
        for u,v,d,_ in edges:
            adj[u].append((v,d));adj[v].append((u,d))
    return adj

def graph_distance_to_sources(n:int,source_global_idx:list[int],adj)->np.ndarray:
    out=np.empty((n,len(source_global_idx)),dtype=np.float64)
    for j,u in enumerate(source_global_idx):
        out[:,j]=dijkstra_array(u,adj,n)
    return out

def build_common_raw(Y:np.ndarray,pilot_ids:list[str],all_ids:list[str],smap:dict,
                     pilot_block:np.ndarray,pilot_pool:np.ndarray,all_pool:np.ndarray,
                     source_pos:np.ndarray,De_src:np.ndarray,scales:dict):
    n_pilot,S=Y.shape
    Ysrc=Y[source_pos]
    src_blocks=pilot_block[source_pos]
    train=np.empty((n_pilot*S,4),dtype=np.float64)
    held=np.empty(((len(all_ids)-n_pilot)*S,4),dtype=np.float64)

    def one(target_index:int,training:bool):
        pool=all_pool[target_index];scale=scales[pool]
        if training:
            allowed=(pilot_block!=smap[all_ids[target_index]]["block_id"])
        else:
            allowed=np.ones(n_pilot,dtype=bool)
        trials=int(allowed.sum())
        successes=Y[allowed].sum(axis=0)
        global_logit=vector_logit(successes,trials)
        rallowed=allowed & (pilot_pool==pool)
        rtrials=int(rallowed.sum())
        rsuccess=Y[rallowed].sum(axis=0) if rtrials else np.zeros(S,dtype=np.int64)
        regional_logit=vector_logit(rsuccess,rtrials)

        sallowed=(src_blocks!=smap[all_ids[target_index]]["block_id"]) if training else np.ones(len(source_pos),dtype=bool)
        occ=(Ysrc==1)&sallowed[:,None]
        ed=De_src[target_index]
        nearest=np.min(np.where(occ,ed[:,None],np.inf),axis=0)
        empty=~np.isfinite(nearest)
        nearest[empty]=math.pi*EARTH_RADIUS_KM+scale
        pressure=np.sum(occ*np.exp(-ed/scale)[:,None],axis=0,dtype=np.float64)
        return np.column_stack([global_logit,regional_logit,np.log1p(nearest),np.log1p(pressure)])

    for i in range(n_pilot):
        train[i*S:(i+1)*S]=one(i,True)
    for ci in range(len(all_ids)-n_pilot):
        held[ci*S:(ci+1)*S]=one(n_pilot+ci,False)
    return train,held

def build_graph_raw(Y:np.ndarray,pilot_ids:list[str],all_ids:list[str],smap:dict,
                    pilot_block:np.ndarray,all_pool:np.ndarray,source_pos:np.ndarray,
                    Dg_src:np.ndarray,scales:dict,node_count:Counter,max_edge:dict):
    n_pilot,S=Y.shape
    Ysrc=Y[source_pos];src_blocks=pilot_block[source_pos]
    train=np.empty((n_pilot*S,2),dtype=np.float64)
    held=np.empty(((len(all_ids)-n_pilot)*S,2),dtype=np.float64)
    held_empty=np.empty((len(all_ids)-n_pilot,S),dtype=np.uint8)

    def one(target_index:int,training:bool):
        pool=all_pool[target_index];scale=scales[pool]
        sallowed=(src_blocks!=smap[all_ids[target_index]]["block_id"]) if training else np.ones(len(source_pos),dtype=bool)
        gd=Dg_src[target_index]
        reachable=np.isfinite(gd)
        occ=(Ysrc==1)&sallowed[:,None]&reachable[:,None]
        nearest=np.min(np.where(occ,gd[:,None],np.inf),axis=0)
        empty=~np.isfinite(nearest)
        nearest[empty]=(node_count[pool]-1)*max_edge[pool]+scale
        weights=np.zeros(len(source_pos),dtype=np.float64)
        weights[reachable]=np.exp(-gd[reachable]/scale)
        pressure=np.sum(occ*weights[:,None],axis=0,dtype=np.float64)
        return np.column_stack([np.log1p(nearest),np.log1p(pressure)]),empty

    for i in range(n_pilot):
        raw,_=one(i,True);train[i*S:(i+1)*S]=raw
    for ci in range(len(all_ids)-n_pilot):
        raw,empty=one(n_pilot+ci,False)
        held[ci*S:(ci+1)*S]=raw;held_empty[ci]=empty.astype(np.uint8)
    return train,held,held_empty

def standardize(train:np.ndarray,held:np.ndarray,label:str):
    mu=np.mean(train,axis=0,dtype=np.float64)
    sd=np.sqrt(np.mean((train-mu)**2,axis=0,dtype=np.float64))
    if np.any(~np.isfinite(sd)) or np.any(sd<=0):raise Stop(f"zero/nonfinite SD: {label}")
    return (train-mu)/sd,(held-mu)/sd,mu,sd

def build_base(state_rows:list[dict],pilot_ids:list[str],heldout_ids:list[str],pool_levels:list[str],S:int):
    smap={str(r["ID"]):r for r in state_rows}
    pool_index={p:i for i,p in enumerate(pool_levels)}
    r0=["z_Climate_velocity","z_Temperature_mean","z_Temperature_sd","z_Precipitation_mean","z_Precipitation_sd","z_Elevation_sd"]
    r1=["z_log_Area","z_Current_isolation","z_Past_isolation"]
    r2=["z_log1p_nearest_island_km","z_generic_neighbor_pressure"]
    def rows(ids):
        X=np.empty((len(ids)*S,24),dtype=np.float64)
        for i,eid in enumerate(ids):
            r=smap[eid];sl=slice(i*S,(i+1)*S)
            X[sl,0]=1.0
            one=np.zeros(12);one[pool_index[r["bioregion"]]]=1.0
            X[sl,1:13]=one
            X[sl,13:19]=[parse_num(r[x]) for x in r0]
            X[sl,19:22]=[parse_num(r[x]) for x in r1]
            X[sl,22:24]=[parse_num(r[x]) for x in r2]
        return X
    return rows(pilot_ids),rows(heldout_ids),smap

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("pilot_universe",type=Path)
    ap.add_argument("pilot_matrix",type=Path)
    ap.add_argument("state_reference",type=Path)
    ap.add_argument("graph_edges",type=Path)
    ap.add_argument("reference_receipt",type=Path)
    ap.add_argument("safe_appendix2",type=Path)
    ap.add_argument("pilot_routing",type=Path)
    ap.add_argument("heldout_routing",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--predictions",type=Path,required=True)
    ap.add_argument("--entity-order",type=Path,required=True)
    ap.add_argument("--graph-empty-mask",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_sealed_species_replication_contract.v1_94":
            raise Stop("contract schema drift")
        if np.__version__!="2.3.3":raise Stop(f"NumPy version drift: {np.__version__}")
        expected={
          a.pilot_universe:c["population"]["species_universe_sha256"],
          a.pilot_matrix:c["population"]["pilot_matrix_sha256"],
          a.state_reference:"5a04e8b64682979ee708f281418c017ff34c930bc8e51d7eff3d3437929b74b0",
          a.graph_edges:"92e0ec3e5335233f6430b18a972235481845848796d0d7e1cd12cc6fb10d090f",
          a.reference_receipt:"55a0581c7c7d0136ecb6a025fa2a41f5ddeeb8ec674b8500bf7c37f81763954a",
          a.safe_appendix2:"b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8",
          a.pilot_routing:"ac3898162331ce4217ea63d8b9330051acaa3a39ddca425cd0b48246a11caec0",
          a.heldout_routing:"afda05287599110c7248c5cb0c1931689a2aee40f8ff4ff5b76509aff5350715",
        }
        for p,h in expected.items():
            if sha(p)!=h:raise Stop(f"input SHA drift: {p.name}")

        universe=load_csv(a.pilot_universe)
        if len(universe)!=96:raise Stop("second-layer species count drift")
        species_names=[];labels=[]
        for j,r in enumerate(universe):
            if int(r["species_index"])!=j:raise Stop("species index drift")
            if not 5<=int(r["pilot_presence"])<=12:raise Stop("pilot presence outside frozen range")
            species_names.append(str(r["species_name"]));labels.append(f"S{j:05d}")

        pilot=load_csv(a.pilot_routing);heldout=load_csv(a.heldout_routing)
        pilot_ids=[str(r["ID"]) for r in pilot];heldout_ids=[str(r["ID"]) for r in heldout]
        if len(pilot_ids)!=1275 or len(heldout_ids)!=4126:raise Stop("routing count drift")
        all_ids=pilot_ids+heldout_ids;id_to_idx={iid:i for i,iid in enumerate(all_ids)}

        mrows=load_csv(a.pilot_matrix)
        if len(mrows)!=1275 or [r["ID"] for r in mrows]!=pilot_ids:raise Stop("pilot matrix routing drift")
        if list(mrows[0].keys())!=["ID","block_id","bioregion"]+labels:raise Stop("pilot matrix schema drift")
        S=96;Y=np.empty((1275,S),dtype=np.int8)
        for i,r in enumerate(mrows):
            for j,label in enumerate(labels):
                y=int(r[label])
                if y not in (0,1):raise Stop("pilot target domain drift")
                Y[i,j]=y
        counts=Y.sum(axis=0)
        if np.any(counts<5) or np.any(counts>12):raise Stop("realized pilot counts drift")

        state=load_csv(a.state_reference)
        if len(state)!=5401:raise Stop("state population drift")
        Xbase_train,Xbase_held,smap=build_base(state,pilot_ids,heldout_ids,sorted({r["bioregion"] for r in state}),S)
        pool_levels=sorted({r["bioregion"] for r in state})
        all_pool=np.array([smap[i]["bioregion"] for i in all_ids],dtype=object)
        pilot_block=np.array([r["block_id"] for r in pilot],dtype=object)
        pilot_pool=np.array([r["bioregion"] for r in pilot],dtype=object)

        safe=load_csv(a.safe_appendix2);safemap={str(r["ID"]):r for r in safe}
        coords=np.array([[parse_num(safemap[i]["Latitude_centroid"]),parse_num(safemap[i]["Longitude_centroid"])] for i in all_ids],dtype=np.float64)

        rr=json.loads(a.reference_receipt.read_text())
        scales={k:float.fromhex(v) for k,v in rr["bioregion_edge_scale_hex"].items()}
        node_count=Counter(all_pool)

        raw_edge_rows=load_csv(a.graph_edges)
        region_raw=defaultdict(list);max_edge={p:0.0 for p in pool_levels}
        for r in raw_edge_rows:
            reg=r["bioregion"];u=id_to_idx[str(r["from_ID"])];v=id_to_idx[str(r["to_ID"])]
            d=float.fromhex(r["distance_km_hex"])
            region_raw[reg].append((min(u,v),max(u,v),d));max_edge[reg]=max(max_edge[reg],d)
        region_nodes={reg:sorted([i for i,p in enumerate(all_pool) if p==reg]) for reg in pool_levels}
        actual_regions={}
        for reg in pool_levels:
            lengths=[e[2] for e in region_raw[reg]]
            bounds=[type7(lengths,q) for q in (0.2,0.4,0.6,0.8)]
            actual_regions[reg]=assign_bins(region_raw[reg],bounds)
            if not connected(region_nodes[reg],actual_regions[reg]):raise Stop(f"actual region not connected: {reg}")

        source_pos=np.flatnonzero(Y.sum(axis=1)>0)
        if len(source_pos)>int(Y.sum()):raise Stop("source-position logic drift")
        source_global=[int(i) for i in source_pos]
        De_src=haversine_matrix(coords,coords[source_pos])
        common_train,common_held=build_common_raw(
            Y,pilot_ids,all_ids,smap,pilot_block,pilot_pool,all_pool,source_pos,De_src,scales
        )
        common_z_train,common_z_held,common_mu,common_sd=standardize(common_train,common_held,"R3 common")

        # Build R3 once.
        X3_train=np.column_stack([Xbase_train,common_z_train])
        X3_held=np.column_stack([Xbase_held,common_z_held])
        y=Y.reshape(-1).astype(np.float64)
        cols_base=["intercept"]+[f"bioregion::{p}" for p in pool_levels]+[
          "z_Climate_velocity","z_Temperature_mean","z_Temperature_sd","z_Precipitation_mean","z_Precipitation_sd","z_Elevation_sd",
          "z_log_Area","z_Current_isolation","z_Past_isolation","z_log1p_nearest_island_km","z_generic_neighbor_pressure"
        ]
        common_names=[
          "z_global_occupancy_jeffreys_logit","z_bioregion_prevalence_jeffreys_logit",
          "z_log1p_nearest_euclidean_source_km","z_log1p_euclidean_source_pressure"
        ]
        if X3_train.shape[1]!=28:raise Stop("R3 design dimension drift")
        fit3=fit_ridge(X3_train,y,cols_base+common_names)
        p3=predict(X3_held,fit3)

        # Actual C.
        actual_adj=adjacency(len(all_ids),actual_regions)
        Dg=graph_distance_to_sources(len(all_ids),source_global,actual_adj)
        gtrain,gheld,empty=build_graph_raw(Y,pilot_ids,all_ids,smap,pilot_block,all_pool,source_pos,Dg,scales,node_count,max_edge)
        gz_train,gz_held,gmu,gsd=standardize(gtrain,gheld,"actual graph")
        fitC=fit_ridge(np.column_stack([X3_train,gz_train]),y,cols_base+common_names+[
          "z_log1p_nearest_graph_source_km","z_log1p_graph_source_pressure"])
        pC=predict(np.column_stack([X3_held,gz_held]),fitC)

        K=int(c["rewired_graph_null"]["null_graphs"])
        preds=np.empty((len(heldout_ids)*S,2+K),dtype=np.float64)
        preds[:,0]=p3;preds[:,1]=pC
        null_meta=[];base_seed=int(c["rewired_graph_null"]["base_seed"])

        for k in range(1,K+1):
            null_regions={};regions_meta=[]
            null_seed=base_seed+k
            for ri,reg in enumerate(pool_levels):
                original=actual_regions[reg]
                E=len(original);target_swaps=2*E;max_attempts=200*target_swaps
                region_seed=null_seed+1000*ri
                rew,meta=rewire_region(reg,region_nodes[reg],original,coords,region_seed,target_swaps,max_attempts,all_ids)
                null_regions[reg]=rew;regions_meta.append(meta)
            nadj=adjacency(len(all_ids),null_regions)
            null_max_edge={reg:max(e[2] for e in null_regions[reg]) for reg in pool_levels}
            ndg=graph_distance_to_sources(len(all_ids),source_global,nadj)
            ngtrain,ngheld,_=build_graph_raw(Y,pilot_ids,all_ids,smap,pilot_block,all_pool,source_pos,ndg,scales,node_count,null_max_edge)
            ngz_train,ngz_held,nmu,nsd=standardize(ngtrain,ngheld,f"null{k}")
            nfit=fit_ridge(np.column_stack([X3_train,ngz_train]),y,cols_base+common_names+[
              "z_log1p_nearest_graph_source_km","z_log1p_graph_source_pressure"])
            npred=predict(np.column_stack([X3_held,ngz_held]),nfit)
            preds[:,1+k]=npred
            h=hashlib.sha256()
            for m in regions_meta:h.update(m["fingerprint"].encode())
            null_meta.append({
              "null_index":k,"null_seed":null_seed,
              "combined_graph_fingerprint":h.hexdigest(),
              "regions":regions_meta,
              "model":model_mapping(nfit),
              "graph_source_standardization":{
                "mean_hex":[float(v).hex() for v in nmu],
                "sd_hex":[float(v).hex() for v in nsd],
              }
            })

        a.entity_order.parent.mkdir(parents=True,exist_ok=True)
        with a.entity_order.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["ID","block_id","bioregion"])
            for r in heldout:w.writerow([r["ID"],r["block_id"],r["bioregion"]])

        with a.predictions.open("wb") as h:
            h.write(MAGIC);h.write(struct.pack("<III",len(heldout_ids),S,K))
            h.write(np.asarray(preds,dtype="<f8",order="C").tobytes(order="C"))

        with a.graph_empty_mask.open("wb") as h:
            h.write(MASK_MAGIC);h.write(struct.pack("<II",len(heldout_ids),S))
            h.write(np.asarray(empty,dtype=np.uint8,order="C").tobytes(order="C"))

        diff=np.abs(pC-p3)
        null_mean=np.mean(preds[:,2:],axis=1,dtype=np.float64)
        actual_null_diff=np.abs(pC-null_mean)
        threshold=float(c["preconfirmatory_freeze"]["prediction_difference_threshold"])
        result={
          "schema":"structural.global_mammals_sealed_species_preconfirm_result.v1_94",
          "status":"SECOND_LAYER_R3_C_AND_REWIRED_PREDICTIONS_FROZEN_BEFORE_HELDOUT_ACCESS",
          "candidate_id":c["candidate_id"],
          "second_layer_species":S,
          "pilot_islands":1275,
          "heldout_islands":4126,
          "heldout_blocks":168,
          "heldout_target_cells":len(heldout_ids)*S,
          "pilot_positive_cells":int(Y.sum()),
          "unique_occupied_pilot_source_islands":int(len(source_pos)),
          "actual_graph_nonempty_heldout_cells":int(np.sum(empty==0)),
          "actual_graph_empty_heldout_cells":int(np.sum(empty==1)),
          "actual_graph_empty_fraction":float(np.mean(empty,dtype=np.float64)),
          "R3_model":model_mapping(fit3),
          "actual_C_model":model_mapping(fitC),
          "common_source_standardization":{
            "mean_hex":[float(v).hex() for v in common_mu],
            "sd_hex":[float(v).hex() for v in common_sd],
          },
          "actual_graph_source_standardization":{
            "mean_hex":[float(v).hex() for v in gmu],
            "sd_hex":[float(v).hex() for v in gsd],
          },
          "null_graphs":null_meta,
          "prediction_binary_magic":"STRUCTURAL_MAMMAL_SECOND_LAYER_PRED_V1\\n",
          "prediction_binary_shape":[4126,S,2+K],
          "prediction_fields":["p_R3","p_C_actual"]+[f"p_C_rewired_{i:02d}" for i in range(1,K+1)],
          "prediction_sha256":sha(a.predictions),
          "entity_order_sha256":sha(a.entity_order),
          "graph_empty_mask_sha256":sha(a.graph_empty_mask),
          "cells_with_abs_pC_minus_pR3_gt_threshold":int(np.sum(diff>threshold)),
          "mean_abs_pC_minus_pR3":float(np.mean(diff,dtype=np.float64)),
          "cells_with_abs_actualC_minus_mean_rewiredC_gt_threshold":int(np.sum(actual_null_diff>threshold)),
          "mean_abs_actualC_minus_mean_rewiredC":float(np.mean(actual_null_diff,dtype=np.float64)),
          "heldout_second_layer_target_values_used":False,
          "heldout_second_layer_response_opened":False,
          "heldout_response_authorized":False,
          "counts_as_current_empirical_result":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.global_mammals_sealed_species_preconfirm_result.v1_94",
          "status":"STOP_BEFORE_SECOND_LAYER_HELDOUT_ACCESS",
          "reason":str(e),
          "heldout_second_layer_target_values_used":False,
          "heldout_second_layer_response_opened":False,
          "heldout_response_authorized":False,
          "counts_as_current_empirical_result":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
