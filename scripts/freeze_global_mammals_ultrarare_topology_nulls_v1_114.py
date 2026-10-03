#!/usr/bin/env python3
"""Freeze 20 matched rewired-C prediction surfaces for the ultrarare layer.

No ultrarare heldout response value is opened. The graph-null ensemble is
identical to the one frozen for the 5-12-presence layer.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,struct
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np

from scripts.freeze_global_mammals_exploratory_preconfirmatory_v1_72 import (
    Stop, fit_ridge, load_csv, model_mapping, parse_num, predict, sha, type7,
)
from scripts.freeze_global_mammals_sealed_species_predictions_v1_94 import (
    adjacency, assign_bins, build_base, build_common_raw, build_graph_raw,
    graph_distance_to_sources, haversine_matrix, rewire_region, standardize,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_ultrarare_topology_null_contract_v1_114.json"
PARENT_CONTRACT=ROOT/"development/global_mammals_ultrarare_preconfirm_contract_v1_113.json"
ACTUAL_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_PRED_V1\n"
NULL_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_NULL_PRED_V1\n"

def read_actual(path:Path,S:int):
    raw=path.read_bytes()
    if not raw.startswith(ACTUAL_MAGIC): raise Stop("actual prediction magic drift")
    off=len(ACTUAL_MAGIC)
    ne,ns=struct.unpack_from("<II",raw,off); off+=8
    if (ne,ns)!=(4126,S): raise Stop("actual prediction shape drift")
    vals=np.frombuffer(raw,dtype="<f8",offset=off)
    if vals.size!=ne*ns*2: raise Stop("actual prediction payload drift")
    vals=vals.reshape(ne*ns,2)
    return vals[:,0].copy(),vals[:,1].copy()

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
    ap.add_argument("actual_predictions",type=Path)
    ap.add_argument("actual_entity_order",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--null-predictions",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_ultrarare_topology_null_contract.v1_114":
            raise Stop("contract schema drift")
        pc=json.loads(PARENT_CONTRACT.read_text())
        if np.__version__!=pc["model"]["numpy_version"]: raise Stop("NumPy version drift")

        # Bind exact already-frozen actual surface.
        par=c["actual_preconfirm_parent"]
        if sha(a.actual_predictions)!=par["prediction_sha256"]: raise Stop("actual prediction SHA drift")
        if sha(a.actual_entity_order)!=par["entity_order_sha256"]: raise Stop("actual entity-order SHA drift")

        exp=pc["required_inputs"]
        for p,k in [
          (a.pilot_universe,"pilot_species_universe_sha256"),
          (a.pilot_matrix,"pilot_matrix_sha256"),
          (a.state_reference,"state_reference_sha256"),
          (a.graph_edges,"source_graph_edges_sha256"),
          (a.reference_receipt,"reference_receipt_sha256"),
          (a.safe_appendix2,"safe_appendix2_sha256"),
          (a.pilot_routing,"pilot_routing_sha256"),
          (a.heldout_routing,"heldout_routing_sha256"),
        ]:
            if sha(p)!=exp[k]: raise Stop(f"input SHA drift: {k}")

        universe=load_csv(a.pilot_universe); S=529
        if len(universe)!=S: raise Stop("species count drift")
        labels=[]
        for j,r in enumerate(universe):
            if int(r["species_index"])!=j or not 1<=int(r["pilot_presence"])<=4:
                raise Stop("ultrarare universe drift")
            labels.append(f"S{j:05d}")

        pilot=load_csv(a.pilot_routing); held=load_csv(a.heldout_routing)
        pilot_ids=[str(r["ID"]) for r in pilot]; held_ids=[str(r["ID"]) for r in held]
        if len(pilot_ids)!=1275 or len(held_ids)!=4126: raise Stop("routing count drift")
        all_ids=pilot_ids+held_ids; id_to_idx={x:i for i,x in enumerate(all_ids)}

        # Parent entity order must equal the frozen heldout routing byte-for-byte by rows.
        order=load_csv(a.actual_entity_order)
        if [r["ID"] for r in order]!=held_ids: raise Stop("actual entity order routing drift")

        mrows=load_csv(a.pilot_matrix)
        if len(mrows)!=1275 or [r["ID"] for r in mrows]!=pilot_ids: raise Stop("pilot matrix routing drift")
        if list(mrows[0].keys())!=["ID","block_id","bioregion"]+labels: raise Stop("pilot matrix schema drift")
        Y=np.empty((1275,S),dtype=np.int8)
        for i,r in enumerate(mrows):
            for j,l in enumerate(labels):
                y=int(r[l])
                if y not in (0,1): raise Stop("pilot target domain drift")
                Y[i,j]=y
        counts=Y.sum(axis=0)
        if np.any(counts<1) or np.any(counts>4): raise Stop("pilot prevalence drift")

        state=load_csv(a.state_reference)
        pool_levels=sorted({r["bioregion"] for r in state})
        Xbase_train,Xbase_held,smap=build_base(state,pilot_ids,held_ids,pool_levels,S)
        all_pool=np.array([smap[i]["bioregion"] for i in all_ids],dtype=object)
        pilot_block=np.array([r["block_id"] for r in pilot],dtype=object)
        pilot_pool=np.array([r["bioregion"] for r in pilot],dtype=object)
        node_count=Counter(all_pool)

        safe=load_csv(a.safe_appendix2); safemap={str(r["ID"]):r for r in safe}
        coords=np.array([[parse_num(safemap[i]["Latitude_centroid"]),parse_num(safemap[i]["Longitude_centroid"])] for i in all_ids],dtype=np.float64)
        rr=json.loads(a.reference_receipt.read_text())
        scales={k:float.fromhex(v) for k,v in rr["bioregion_edge_scale_hex"].items()}

        region_raw=defaultdict(list); max_edge={p:0.0 for p in pool_levels}
        for r in load_csv(a.graph_edges):
            reg=r["bioregion"]; u=id_to_idx[str(r["from_ID"])]; v=id_to_idx[str(r["to_ID"])]
            d=float.fromhex(r["distance_km_hex"])
            region_raw[reg].append((min(u,v),max(u,v),d)); max_edge[reg]=max(max_edge[reg],d)
        region_nodes={reg:sorted(i for i,p in enumerate(all_pool) if p==reg) for reg in pool_levels}
        actual_regions={}
        for reg in pool_levels:
            lengths=[e[2] for e in region_raw[reg]]
            bounds=[type7(lengths,q) for q in (0.2,0.4,0.6,0.8)]
            actual_regions[reg]=assign_bins(region_raw[reg],bounds)

        source_pos=np.flatnonzero(Y.sum(axis=1)>0)
        De_src=haversine_matrix(coords,coords[source_pos])
        common_train,common_held=build_common_raw(
            Y,pilot_ids,all_ids,smap,pilot_block,pilot_pool,all_pool,source_pos,De_src,scales
        )
        common_z_train,common_z_held,_,_=standardize(common_train,common_held,"common")
        y=Y.reshape(-1).astype(np.float64)

        cols_base=["intercept"]+[f"bioregion::{p}" for p in pool_levels]+[
          "z_Climate_velocity","z_Temperature_mean","z_Temperature_sd","z_Precipitation_mean",
          "z_Precipitation_sd","z_Elevation_sd","z_log_Area","z_Current_isolation",
          "z_Past_isolation","z_log1p_nearest_island_km","z_generic_neighbor_pressure"
        ]
        common_names=["z_global_occupancy_jeffreys_logit","z_bioregion_prevalence_jeffreys_logit",
          "z_log1p_nearest_euclidean_source_km","z_log1p_euclidean_source_pressure"]
        graph_names=["z_log1p_nearest_graph_source_km","z_log1p_graph_source_pressure"]
        X3_train=np.column_stack([Xbase_train,common_z_train])
        X3_held=np.column_stack([Xbase_held,common_z_held])

        # Replay actual R3/C first; response is still sealed.
        actual_adj=adjacency(len(all_ids),actual_regions)
        Dg=graph_distance_to_sources(len(all_ids),[int(i) for i in source_pos],actual_adj)
        gtrain,gheld,_=build_graph_raw(Y,pilot_ids,all_ids,smap,pilot_block,all_pool,source_pos,Dg,scales,node_count,max_edge)
        gz_train,gz_held,_,_=standardize(gtrain,gheld,"actual")
        fit3=fit_ridge(X3_train,y,cols_base+common_names)
        fitC=fit_ridge(np.column_stack([X3_train,gz_train]),y,cols_base+common_names+graph_names)
        p3_replay=predict(X3_held,fit3)
        pc_replay=predict(np.column_stack([X3_held,gz_held]),fitC)
        p3_parent,pc_parent=read_actual(a.actual_predictions,S)
        max_r3=float(np.max(np.abs(p3_replay-p3_parent)))
        max_c=float(np.max(np.abs(pc_replay-pc_parent)))
        tol=float(c["pre_response_requirements"]["actual_R3_C_surface_must_replay_with_max_abs_probability_difference_lte"])
        if max(max_r3,max_c)>tol: raise Stop("actual R3/C replay exceeded tolerance")

        expected_fps=c["null_ensemble"]["expected_combined_graph_fingerprints"]
        K=int(c["null_ensemble"]["null_graphs"])
        base_seed=int(c["null_ensemble"]["base_seed"])
        sum_null=np.zeros_like(pc_parent)
        null_meta=[]
        a.null_predictions.parent.mkdir(parents=True,exist_ok=True)
        with a.null_predictions.open("wb") as out:
            out.write(NULL_MAGIC); out.write(struct.pack("<III",K,4126,S))
            for k in range(1,K+1):
                null_regions={}; regions_meta=[]; null_seed=base_seed+k
                for ri,reg in enumerate(pool_levels):
                    original=actual_regions[reg]; E=len(original)
                    rew,meta=rewire_region(
                        reg,region_nodes[reg],original,coords,
                        null_seed+1000*ri,2*E,200*(2*E),all_ids
                    )
                    null_regions[reg]=rew; regions_meta.append(meta)
                h=hashlib.sha256()
                for m in regions_meta: h.update(m["fingerprint"].encode())
                fp=h.hexdigest()
                if fp!=expected_fps[k-1]: raise Stop(f"null graph fingerprint drift: {k}")
                nadj=adjacency(len(all_ids),null_regions)
                nmax={reg:max(e[2] for e in null_regions[reg]) for reg in pool_levels}
                ndg=graph_distance_to_sources(len(all_ids),[int(i) for i in source_pos],nadj)
                ngtrain,ngheld,_=build_graph_raw(Y,pilot_ids,all_ids,smap,pilot_block,all_pool,source_pos,ndg,scales,node_count,nmax)
                ngz_train,ngz_held,nmu,nsd=standardize(ngtrain,ngheld,f"null{k}")
                nfit=fit_ridge(np.column_stack([X3_train,ngz_train]),y,cols_base+common_names+graph_names)
                npred=predict(np.column_stack([X3_held,ngz_held]),nfit)
                out.write(np.asarray(npred,dtype="<f8").tobytes(order="C"))
                sum_null+=npred
                null_meta.append({
                  "null_index":k,"combined_graph_fingerprint":fp,
                  "model":model_mapping(nfit),
                  "graph_source_standardization":{
                    "mean_hex":[float(v).hex() for v in nmu],
                    "sd_hex":[float(v).hex() for v in nsd]
                  }
                })

        mean_null=sum_null/K
        d=np.abs(pc_parent-mean_null)
        threshold=1e-12
        # heldout order rows carry block IDs, repeated across species below.
        block_abs=defaultdict(list)
        for ci,r in enumerate(order):
            sl=slice(ci*S,(ci+1)*S)
            block_abs[r["block_id"]].append(float(np.mean(d[sl])))
        blocks_diff=sum((math.fsum(v)/len(v))>threshold for v in block_abs.values())
        if int(np.sum(d>threshold))<c["pre_response_requirements"]["minimum_cells_with_abs_actualC_minus_mean_nullC_gt_1e_12"]:
            raise Stop("actual C and null mean are numerically identical")
        if blocks_diff<c["pre_response_requirements"]["minimum_blocks_with_mean_abs_actualC_minus_mean_nullC_gt_1e_12"]:
            raise Stop("too few blocks differ from null mean")

        result={
          "schema":"structural.global_mammals_ultrarare_topology_null_result.v1_114",
          "status":"ULTRARARE_MATCHED_TOPOLOGY_NULLS_FROZEN_BEFORE_HELDOUT_ACCESS",
          "species":S,"heldout_islands":4126,"heldout_blocks":168,
          "heldout_target_cells":4126*S,"null_graphs":K,
          "actual_R3_replay_max_abs_difference":max_r3,
          "actual_C_replay_max_abs_difference":max_c,
          "null_graph_fingerprints":[x["combined_graph_fingerprint"] for x in null_meta],
          "null_models":null_meta,
          "null_prediction_magic":"STRUCTURAL_MAMMAL_ULTRARARE_NULL_PRED_V1\\n",
          "null_prediction_shape":[K,4126,S],
          "null_prediction_sha256":sha(a.null_predictions),
          "cells_with_abs_actualC_minus_mean_nullC_gt_1e_12":int(np.sum(d>threshold)),
          "blocks_with_mean_abs_actualC_minus_mean_nullC_gt_1e_12":blocks_diff,
          "mean_abs_actualC_minus_mean_nullC":float(np.mean(d)),
          "heldout_target_values_used":False,
          "heldout_response_opened":False,
          "heldout_response_authorized":False,
          "counts_as_current_empirical_result":False
        }; code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.global_mammals_ultrarare_topology_null_result.v1_114",
          "status":"STOP_BEFORE_ULTRARARE_HELDOUT_ACCESS","reason":str(e),
          "heldout_target_values_used":False,"heldout_response_opened":False,
          "heldout_response_authorized":False,"counts_as_current_empirical_result":False
        }; code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__": raise SystemExit(main())
