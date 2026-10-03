#!/usr/bin/env python3
"""Freeze ultrarare-layer R3/C predictions before any heldout response access."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,struct
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np

from scripts.freeze_global_mammals_exploratory_preconfirmatory_v1_72 import (
    Stop, fit_ridge, load_csv, model_mapping, parse_num, predict, sha,
)
from scripts.freeze_global_mammals_sealed_species_predictions_v1_94 import (
    adjacency, build_base, build_common_raw, build_graph_raw,
    graph_distance_to_sources, haversine_matrix, standardize,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_ultrarare_preconfirm_contract_v1_113.json"
MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_PRED_V1\n"
MASK_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_GRAPH_EMPTY_V1\n"

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
    ap.add_argument("--block-context",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_ultrarare_preconfirm_contract.v1_113":
            raise Stop("contract schema drift")
        if np.__version__!=c["model"]["numpy_version"]:
            raise Stop(f"NumPy version drift: {np.__version__}")

        exp=c["required_inputs"]
        checks=[
          (a.pilot_universe,"pilot_species_universe_sha256"),
          (a.pilot_matrix,"pilot_matrix_sha256"),
          (a.state_reference,"state_reference_sha256"),
          (a.graph_edges,"source_graph_edges_sha256"),
          (a.reference_receipt,"reference_receipt_sha256"),
          (a.safe_appendix2,"safe_appendix2_sha256"),
          (a.pilot_routing,"pilot_routing_sha256"),
          (a.heldout_routing,"heldout_routing_sha256"),
        ]
        for p,k in checks:
            if sha(p)!=exp[k]: raise Stop(f"input SHA drift: {k}")

        universe=load_csv(a.pilot_universe)
        S=int(c["population"]["species"])
        if len(universe)!=S: raise Stop("species count drift")
        labels=[];species=[]
        for j,r in enumerate(universe):
            if int(r["species_index"])!=j: raise Stop("species index drift")
            pres=int(r["pilot_presence"]);absn=int(r["pilot_absence"])
            if not 1<=pres<=4 or absn<13: raise Stop("ultrarare membership drift")
            labels.append(f"S{j:05d}");species.append(str(r["species_name"]))
        if len(set(species))!=S: raise Stop("duplicate species")

        pilot=load_csv(a.pilot_routing);held=load_csv(a.heldout_routing)
        pilot_ids=[str(r["ID"]) for r in pilot];held_ids=[str(r["ID"]) for r in held]
        if len(pilot_ids)!=1275 or len(held_ids)!=4126: raise Stop("routing count drift")
        if set(pilot_ids)&set(held_ids): raise Stop("routing overlap")
        all_ids=pilot_ids+held_ids;id_to_idx={iid:i for i,iid in enumerate(all_ids)}

        mrows=load_csv(a.pilot_matrix)
        if len(mrows)!=1275 or [str(r["ID"]) for r in mrows]!=pilot_ids:
            raise Stop("pilot matrix routing drift")
        if list(mrows[0].keys())!=["ID","block_id","bioregion"]+labels:
            raise Stop("pilot matrix schema drift")
        Y=np.empty((1275,S),dtype=np.int8)
        for i,r in enumerate(mrows):
            if r["block_id"]!=pilot[i]["block_id"] or r["bioregion"]!=pilot[i]["bioregion"]:
                raise Stop("pilot metadata drift")
            for j,l in enumerate(labels):
                y=int(r[l])
                if y not in (0,1): raise Stop("pilot target domain drift")
                Y[i,j]=y
        pc=Y.sum(axis=0)
        if np.any(pc<1) or np.any(pc>4): raise Stop("realized pilot presence drift")

        state=load_csv(a.state_reference)
        if len(state)!=5401: raise Stop("state population drift")
        pool_levels=sorted({r["bioregion"] for r in state})
        if len(pool_levels)!=12: raise Stop("bioregion count drift")
        Xbase_train,Xbase_held,smap=build_base(state,pilot_ids,held_ids,pool_levels,S)
        if set(smap)!=set(all_ids): raise Stop("state population mismatch")

        safe=load_csv(a.safe_appendix2);safemap={str(r["ID"]):r for r in safe}
        if len(safe)!=5592 or not set(all_ids)<=set(safemap): raise Stop("safe geography drift")
        coords=np.array([
          [parse_num(safemap[i]["Latitude_centroid"]),parse_num(safemap[i]["Longitude_centroid"])]
          for i in all_ids
        ],dtype=np.float64)

        rr=json.loads(a.reference_receipt.read_text())
        scales={k:float.fromhex(v) for k,v in rr["bioregion_edge_scale_hex"].items()}
        if sorted(scales)!=pool_levels: raise Stop("scale levels drift")

        all_pool=np.array([smap[i]["bioregion"] for i in all_ids],dtype=object)
        pilot_block=np.array([r["block_id"] for r in pilot],dtype=object)
        pilot_pool=np.array([r["bioregion"] for r in pilot],dtype=object)
        node_count=Counter(all_pool)

        region_edges=defaultdict(list);max_edge={p:0.0 for p in pool_levels}
        for r in load_csv(a.graph_edges):
            reg=r["bioregion"];u=id_to_idx[str(r["from_ID"])];v=id_to_idx[str(r["to_ID"])]
            d=float.fromhex(r["distance_km_hex"])
            region_edges[reg].append((u,v,d,0));max_edge[reg]=max(max_edge[reg],d)
        if sum(len(v) for v in region_edges.values())!=73162: raise Stop("graph edge count drift")
        actual_adj=adjacency(len(all_ids),region_edges)

        source_pos=np.flatnonzero(Y.sum(axis=1)>0)
        if source_pos.size<1: raise Stop("no occupied pilot source islands")
        De_src=haversine_matrix(coords,coords[source_pos])
        Dg_src=graph_distance_to_sources(len(all_ids),[int(i) for i in source_pos],actual_adj)

        common_train,common_held=build_common_raw(
          Y,pilot_ids,all_ids,smap,pilot_block,pilot_pool,all_pool,source_pos,De_src,scales
        )
        common_z_train,common_z_held,common_mu,common_sd=standardize(common_train,common_held,"common")

        graph_train,graph_held,empty=build_graph_raw(
          Y,pilot_ids,all_ids,smap,pilot_block,all_pool,source_pos,Dg_src,scales,node_count,max_edge
        )
        graph_z_train,graph_z_held,graph_mu,graph_sd=standardize(graph_train,graph_held,"graph")

        y=Y.reshape(-1).astype(np.float64)
        cols_base=["intercept"]+[f"bioregion::{p}" for p in pool_levels]+[
          "z_Climate_velocity","z_Temperature_mean","z_Temperature_sd",
          "z_Precipitation_mean","z_Precipitation_sd","z_Elevation_sd",
          "z_log_Area","z_Current_isolation","z_Past_isolation",
          "z_log1p_nearest_island_km","z_generic_neighbor_pressure"
        ]
        common_names=[
          "z_global_occupancy_jeffreys_logit","z_bioregion_prevalence_jeffreys_logit",
          "z_log1p_nearest_euclidean_source_km","z_log1p_euclidean_source_pressure"
        ]
        graph_names=["z_log1p_nearest_graph_source_km","z_log1p_graph_source_pressure"]

        X3_train=np.column_stack([Xbase_train,common_z_train])
        XC_train=np.column_stack([X3_train,graph_z_train])
        fit3=fit_ridge(X3_train,y,cols_base+common_names)
        fitC=fit_ridge(XC_train,y,cols_base+common_names+graph_names)

        a.entity_order.parent.mkdir(parents=True,exist_ok=True)
        with a.entity_order.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["ID","block_id","bioregion"])
            for r in held:w.writerow([r["ID"],r["block_id"],r["bioregion"]])

        block_vals=defaultdict(list)
        for r in held:
            block_vals[r["block_id"]].append(parse_num(smap[r["ID"]]["z_Current_isolation"]))
        with a.block_context.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["block_id","bioregion","islands","mean_z_Current_isolation"])
            first={}
            for r in held:first.setdefault(r["block_id"],r["bioregion"])
            for b in sorted(block_vals):
                vals=block_vals[b]
                w.writerow([b,first[b],len(vals),repr(math.fsum(vals)/len(vals))])

        threshold=float(c["response_independent_estimability_gate"]["threshold_abs_pC_minus_pR3"])
        cells_diff=0;block_sum=defaultdict(float);block_n=defaultdict(int)
        with a.predictions.open("wb") as h:
            h.write(MAGIC);h.write(struct.pack("<II",4126,S))
            for ci,eid in enumerate(held_ids):
                sl=slice(ci*S,(ci+1)*S)
                p3=predict(np.column_stack([Xbase_held[sl],common_z_held[sl]]),fit3)
                pc_=predict(np.column_stack([Xbase_held[sl],common_z_held[sl],graph_z_held[sl]]),fitC)
                pair=np.column_stack([p3,pc_]).astype("<f8",copy=False)
                h.write(pair.tobytes(order="C"))
                d=np.abs(pc_-p3)
                cells_diff+=int(np.sum(d>threshold))
                b=held[ci]["block_id"];block_sum[b]+=float(np.sum(d));block_n[b]+=S

        with a.graph_empty_mask.open("wb") as h:
            h.write(MASK_MAGIC);h.write(struct.pack("<II",4126,S))
            h.write(np.asarray(empty,dtype=np.uint8,order="C").tobytes(order="C"))

        blocks_diff=sum((block_sum[b]/block_n[b])>threshold for b in block_sum)
        if cells_diff<int(c["response_independent_estimability_gate"]["minimum_cells_with_difference"]):
            raise Stop("R3/C predictions numerically identical")
        if blocks_diff<int(c["response_independent_estimability_gate"]["minimum_blocks_with_mean_difference"]):
            raise Stop("too few blocks with prediction difference")

        result={
          "schema":"structural.global_mammals_ultrarare_preconfirm_result.v1_113",
          "status":"ULTRARARE_R3_C_PREDICTIONS_FROZEN_BEFORE_HELDOUT_ACCESS",
          "species":S,
          "pilot_islands":1275,
          "heldout_islands":4126,
          "heldout_blocks":168,
          "heldout_target_cells":4126*S,
          "pilot_positive_cells":int(Y.sum()),
          "unique_occupied_pilot_source_islands":int(source_pos.size),
          "graph_empty_cells":int(np.sum(empty)),
          "graph_nonempty_cells":int(empty.size-np.sum(empty)),
          "graph_empty_fraction":float(np.mean(empty)),
          "R3_model":model_mapping(fit3),
          "C_model":model_mapping(fitC),
          "common_source_standardization":{
            "mean_hex":[float(v).hex() for v in common_mu],"sd_hex":[float(v).hex() for v in common_sd]
          },
          "graph_source_standardization":{
            "mean_hex":[float(v).hex() for v in graph_mu],"sd_hex":[float(v).hex() for v in graph_sd]
          },
          "prediction_sha256":sha(a.predictions),
          "entity_order_sha256":sha(a.entity_order),
          "graph_empty_mask_sha256":sha(a.graph_empty_mask),
          "block_context_sha256":sha(a.block_context),
          "cells_with_abs_pC_minus_pR3_gt_threshold":cells_diff,
          "blocks_with_mean_abs_difference_gt_threshold":blocks_diff,
          "heldout_target_values_used":False,
          "heldout_response_opened":False,
          "heldout_response_authorized":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.global_mammals_ultrarare_preconfirm_result.v1_113",
          "status":"STOP_BEFORE_ULTRARARE_HELDOUT_ACCESS",
          "reason":str(e),
          "heldout_target_values_used":False,
          "heldout_response_opened":False,
          "heldout_response_authorized":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__":raise SystemExit(main())
