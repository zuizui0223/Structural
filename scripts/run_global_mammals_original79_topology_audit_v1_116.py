#!/usr/bin/env python3
"""Post-hoc actual-vs-rewired topology audit for the frozen 79-species layer."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,struct
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np

from scripts.freeze_global_mammals_exploratory_preconfirmatory_v1_72 import (
    Stop, fit_ridge, load_csv, parse_num, predict, sha, type7,
)
from scripts.freeze_global_mammals_sealed_species_predictions_v1_94 import (
    adjacency, assign_bins, build_base, build_common_raw, build_graph_raw,
    graph_distance_to_sources, haversine_matrix, rewire_region, standardize,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_original79_topology_audit_contract_v1_116.json"
NULL_CONTRACT=ROOT/"development/global_mammals_ultrarare_topology_null_contract_v1_114.json"
MAGIC=b"STRUCTURAL_MAMMAL_PRED_V1\n"
class AuditStop(RuntimeError):pass

def load_parent_predictions(path:Path):
    raw=path.read_bytes()
    if not raw.startswith(MAGIC):raise AuditStop("prediction magic drift")
    off=len(MAGIC);ne,ns=struct.unpack_from("<II",raw,off);off+=8
    if (ne,ns)!=(4126,79):raise AuditStop("prediction shape drift")
    arr=np.frombuffer(raw,dtype="<f8",offset=off).reshape(ne,ns,2)
    return arr[:,:,0].copy(),arr[:,:,1].copy()

def logloss(p,y):
    if np.any(p<=0) or np.any(p>=1):raise AuditStop("probability domain drift")
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def bootstrap(vals:dict[str,float],reps:int,seed:int):
    names=sorted(vals);point=math.fsum(vals.values())/len(vals)
    rng=random.Random(seed);boot=[]
    for _ in range(reps):
        x=[vals[names[rng.randrange(len(names))]] for _ in names]
        boot.append(math.fsum(x)/len(x))
    return point,type7(boot,0.025),type7(boot,0.975)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("pilot_universe",type=Path);ap.add_argument("pilot_matrix",type=Path)
    ap.add_argument("state_reference",type=Path);ap.add_argument("graph_edges",type=Path)
    ap.add_argument("reference_receipt",type=Path);ap.add_argument("safe_appendix2",type=Path)
    ap.add_argument("pilot_routing",type=Path);ap.add_argument("heldout_routing",type=Path)
    ap.add_argument("actual_predictions",type=Path);ap.add_argument("entity_order",type=Path)
    ap.add_argument("heldout_matrix",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--null-output",type=Path,required=True);ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text());nc=json.loads(NULL_CONTRACT.read_text())
        if c.get("schema")!="structural.global_mammals_original79_topology_audit_contract.v1_116":raise AuditStop("contract drift")
        if np.__version__!="2.3.3":raise AuditStop("NumPy drift")
        fi=c["frozen_inputs"]
        for p,key in [(a.pilot_universe,"pilot_species_universe_sha256"),(a.pilot_matrix,"pilot_matrix_sha256"),
                      (a.actual_predictions,"actual_predictions_sha256"),(a.entity_order,"entity_order_sha256"),
                      (a.heldout_matrix,"heldout_matrix_sha256")]:
            if sha(p)!=fi[key]:raise AuditStop(f"frozen input SHA drift: {key}")

        pilot=load_csv(a.pilot_routing);held=load_csv(a.heldout_routing)
        pilot_ids=[r["ID"] for r in pilot];held_ids=[r["ID"] for r in held]
        if len(pilot_ids)!=1275 or len(held_ids)!=4126:raise AuditStop("routing drift")
        order=load_csv(a.entity_order)
        if [r["ID"] for r in order]!=held_ids:raise AuditStop("entity order drift")
        universe=load_csv(a.pilot_universe);S=79
        if len(universe)!=S:raise AuditStop("species count drift")
        labels=[f"S{j:05d}" for j in range(S)]
        pm=load_csv(a.pilot_matrix)
        if len(pm)!=1275 or list(pm[0].keys())!=["ID","block_id","bioregion"]+labels:raise AuditStop("pilot matrix drift")
        Yp=np.array([[int(r[l]) for l in labels] for r in pm],dtype=np.int8)
        if np.any((Yp!=0)&(Yp!=1)):raise AuditStop("pilot target domain drift")

        hm=load_csv(a.heldout_matrix)
        if len(hm)!=4126 or list(hm[0].keys())!=["ID","block_id","bioregion"]+labels:raise AuditStop("heldout matrix drift")
        if [r["ID"] for r in hm]!=held_ids:raise AuditStop("heldout response order drift")
        Y=np.array([[int(r[l]) for l in labels] for r in hm],dtype=np.int8)

        state=load_csv(a.state_reference);pool_levels=sorted({r["bioregion"] for r in state})
        Xbase_train,Xbase_held,smap=build_base(state,pilot_ids,held_ids,pool_levels,S)
        all_ids=pilot_ids+held_ids;id_to_idx={x:i for i,x in enumerate(all_ids)}
        all_pool=np.array([smap[i]["bioregion"] for i in all_ids],dtype=object)
        pilot_block=np.array([r["block_id"] for r in pilot],dtype=object)
        pilot_pool=np.array([r["bioregion"] for r in pilot],dtype=object);node_count=Counter(all_pool)
        safe=load_csv(a.safe_appendix2);safemap={r["ID"]:r for r in safe}
        coords=np.array([[parse_num(safemap[i]["Latitude_centroid"]),parse_num(safemap[i]["Longitude_centroid"])] for i in all_ids])
        rr=json.loads(a.reference_receipt.read_text());scales={k:float.fromhex(v) for k,v in rr["bioregion_edge_scale_hex"].items()}

        region_raw=defaultdict(list);max_edge={p:0.0 for p in pool_levels}
        for r in load_csv(a.graph_edges):
            reg=r["bioregion"];u=id_to_idx[r["from_ID"]];v=id_to_idx[r["to_ID"]];d=float.fromhex(r["distance_km_hex"])
            region_raw[reg].append((min(u,v),max(u,v),d));max_edge[reg]=max(max_edge[reg],d)
        region_nodes={reg:sorted(i for i,p in enumerate(all_pool) if p==reg) for reg in pool_levels}
        actual_regions={}
        for reg in pool_levels:
            lengths=[e[2] for e in region_raw[reg]]
            bounds=[type7(lengths,q) for q in (0.2,0.4,0.6,0.8)]
            actual_regions[reg]=assign_bins(region_raw[reg],bounds)

        source_pos=np.flatnonzero(Yp.sum(axis=1)>0)
        De=haversine_matrix(coords,coords[source_pos])
        common_train,common_held=build_common_raw(Yp,pilot_ids,all_ids,smap,pilot_block,pilot_pool,all_pool,source_pos,De,scales)
        cz_train,cz_held,_,_=standardize(common_train,common_held,"common")
        ypilot=Yp.reshape(-1).astype(float)
        cols_base=["intercept"]+[f"bioregion::{p}" for p in pool_levels]+[
          "z_Climate_velocity","z_Temperature_mean","z_Temperature_sd","z_Precipitation_mean","z_Precipitation_sd","z_Elevation_sd",
          "z_log_Area","z_Current_isolation","z_Past_isolation","z_log1p_nearest_island_km","z_generic_neighbor_pressure"]
        common_names=["z_global_occupancy_jeffreys_logit","z_bioregion_prevalence_jeffreys_logit",
          "z_log1p_nearest_euclidean_source_km","z_log1p_euclidean_source_pressure"]
        graph_names=["z_log1p_nearest_graph_source_km","z_log1p_graph_source_pressure"]
        X3t=np.column_stack([Xbase_train,cz_train]);X3h=np.column_stack([Xbase_held,cz_held])

        # Exact replay of the frozen actual surface.
        aadj=adjacency(len(all_ids),actual_regions)
        Dg=graph_distance_to_sources(len(all_ids),[int(i) for i in source_pos],aadj)
        gt,gh,_=build_graph_raw(Yp,pilot_ids,all_ids,smap,pilot_block,all_pool,source_pos,Dg,scales,node_count,max_edge)
        gzt,gzh,_,_=standardize(gt,gh,"actual")
        f3=fit_ridge(X3t,ypilot,cols_base+common_names)
        fc=fit_ridge(np.column_stack([X3t,gzt]),ypilot,cols_base+common_names+graph_names)
        p3r=predict(X3h,f3);pcr=predict(np.column_stack([X3h,gzh]),fc)
        p3,pc=load_parent_predictions(a.actual_predictions)
        max_replay=max(float(np.max(np.abs(p3r-p3.reshape(-1)))),float(np.max(np.abs(pcr-pc.reshape(-1)))))
        if max_replay>1e-12:raise AuditStop("actual prediction replay mismatch")

        yy=Y.astype(float);l3=logloss(p3,yy);lc=logloss(pc,yy);actual_delta=lc-l3
        byblock=defaultdict(list)
        for i,r in enumerate(order):byblock[r["block_id"]].append(i)
        actual_all={};actual_pre={};actual_abs={}
        for b,ii in byblock.items():
            ix=np.asarray(ii);d=actual_delta[ix,:];y=Y[ix,:]
            actual_all[b]=float(np.mean(d))
            if np.any(y==1):actual_pre[b]=float(np.mean(d[y==1]))
            actual_abs[b]=float(np.mean(d[y==0]))
        actual_all_point=math.fsum(actual_all.values())/len(actual_all)
        actual_pre_point=math.fsum(actual_pre.values())/len(actual_pre)

        fp_expected=nc["null_ensemble"]["expected_combined_graph_fingerprints"];base_seed=2026100300
        contrast_all=defaultdict(float);contrast_pre=defaultdict(float);contrast_abs=defaultdict(float)
        null_rows=[]
        for k in range(1,21):
            nregions={};metas=[];seed=base_seed+k
            for ri,reg in enumerate(pool_levels):
                orig=actual_regions[reg];E=len(orig)
                rew,meta=rewire_region(reg,region_nodes[reg],orig,coords,seed+1000*ri,2*E,400*E,all_ids)
                nregions[reg]=rew;metas.append(meta)
            h=hashlib.sha256()
            for m in metas:h.update(m["fingerprint"].encode())
            if h.hexdigest()!=fp_expected[k-1]:raise AuditStop(f"null fingerprint drift {k}")
            nadj=adjacency(len(all_ids),nregions);nmax={reg:max(e[2] for e in nregions[reg]) for reg in pool_levels}
            ndg=graph_distance_to_sources(len(all_ids),[int(i) for i in source_pos],nadj)
            nt,nh,_=build_graph_raw(Yp,pilot_ids,all_ids,smap,pilot_block,all_pool,source_pos,ndg,scales,node_count,nmax)
            nzt,nzh,_,_=standardize(nt,nh,f"null{k}")
            nf=fit_ridge(np.column_stack([X3t,nzt]),ypilot,cols_base+common_names+graph_names)
            pn=predict(np.column_stack([X3h,nzh]),nf).reshape(4126,S)
            ln=logloss(pn,yy);nd=ln-l3
            nall={};npre={};nabs={}
            for b,ii in byblock.items():
                ix=np.asarray(ii);d=nd[ix,:];y=Y[ix,:]
                nall[b]=float(np.mean(d));nabs[b]=float(np.mean(d[y==0]))
                if np.any(y==1):npre[b]=float(np.mean(d[y==1]))
                contrast_all[b]+=actual_all[b]-nall[b]
                contrast_abs[b]+=actual_abs[b]-nabs[b]
                if b in actual_pre:contrast_pre[b]+=actual_pre[b]-npre[b]
            pt_all=math.fsum(nall.values())/len(nall);pt_pre=math.fsum(npre.values())/len(npre)
            null_rows.append({"null_index":k,"block_weighted_all_C_minus_R3":pt_all,"block_weighted_presence_C_minus_R3":pt_pre})

        for d in (contrast_all,contrast_pre,contrast_abs):
            for b in d:d[b]/=20.0
        reps=int(c["uncertainty"]["bootstrap_replicates"])
        all_pt,all_lo,all_hi=bootstrap(contrast_all,reps,int(c["uncertainty"]["bootstrap_seed_all"]))
        pre_pt,pre_lo,pre_hi=bootstrap(contrast_pre,reps,int(c["uncertainty"]["bootstrap_seed_presence"]))
        abs_pt,abs_lo,abs_hi=bootstrap(contrast_abs,reps,int(c["uncertainty"]["bootstrap_seed_absence"]))
        actual_better_all=sum(actual_all_point<r["block_weighted_all_C_minus_R3"] for r in null_rows)
        actual_better_pre=sum(actual_pre_point<r["block_weighted_presence_C_minus_R3"] for r in null_rows)

        a.null_output.parent.mkdir(parents=True,exist_ok=True)
        with a.null_output.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=list(null_rows[0].keys()),lineterminator="\n");w.writeheader();w.writerows(null_rows)
        out={
          "schema":"structural.global_mammals_original79_topology_audit_result.v1_116",
          "status":"POSTHOC_ORIGINAL79_ACTUAL_VS_REWIRED_AUDIT_COMPLETE",
          "actual_surface_replay_max_abs_probability_difference":max_replay,
          "all_cells":{"actual_minus_mean_rewired":all_pt,"bootstrap_ci95_low":all_lo,"bootstrap_ci95_high":all_hi,
            "actual_better_than_n_of_20_nulls":actual_better_all},
          "presence_cells":{"presence_blocks":len(actual_pre),"actual_minus_mean_rewired":pre_pt,"bootstrap_ci95_low":pre_lo,
            "bootstrap_ci95_high":pre_hi,"actual_better_than_n_of_20_nulls":actual_better_pre},
          "absence_cells":{"actual_minus_mean_rewired":abs_pt,"bootstrap_ci95_low":abs_lo,"bootstrap_ci95_high":abs_hi},
          "null_scores_sha256":sha(a.null_output),
          "posthoc":True,"may_change_original_exploratory_status":False,"counts_as_confirmatory_evidence":False,
          "new_response_accessed":False
        };code=0
    except (Exception,) as e:
        out={"schema":"structural.global_mammals_original79_topology_audit_result.v1_116","status":"STOP",
             "reason":str(e),"posthoc":True,"may_change_original_exploratory_status":False,
             "counts_as_confirmatory_evidence":False,"new_response_accessed":False};code=2
    a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
