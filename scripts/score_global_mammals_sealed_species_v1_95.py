#!/usr/bin/env python3
"""Score the preregistered 96-species heldout replication once."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,struct
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_sealed_species_scoring_contract_v1_95.json"
MAGIC=b"STRUCTURAL_MAMMAL_SECOND_LAYER_PRED_V1\n"
MASK_MAGIC=b"STRUCTURAL_MAMMAL_SECOND_LAYER_GRAPH_EMPTY_V1\n"

class Stop(RuntimeError): pass

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def load_csv(p:Path):
    with p.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def type7(values,p):
    xs=sorted(float(x) for x in values)
    if not xs:raise Stop("empty quantile input")
    if len(xs)==1:return xs[0]
    h=(len(xs)-1)*p;lo=int(math.floor(h));hi=int(math.ceil(h))
    if lo==hi:return xs[lo]
    f=h-lo;return xs[lo]*(1-f)+xs[hi]*f

def bootstrap(block_values:dict[str,float],reps:int,seed:int):
    names=sorted(block_values)
    if not names:raise Stop("empty bootstrap blocks")
    point=math.fsum(block_values[b] for b in names)/len(names)
    rng=random.Random(seed);boot=[]
    for _ in range(reps):
        vals=[block_values[names[rng.randrange(len(names))]] for _ in names]
        boot.append(math.fsum(vals)/len(vals))
    return point,type7(boot,0.025),type7(boot,0.975)

def parse_predictions(path:Path):
    raw=path.read_bytes()
    if not raw.startswith(MAGIC):raise Stop("prediction magic drift")
    off=len(MAGIC)
    if len(raw)<off+12:raise Stop("prediction binary truncated")
    ne,ns,k=struct.unpack_from("<III",raw,off);off+=12
    nfields=2+k
    expected=off+ne*ns*nfields*8
    if len(raw)!=expected:raise Stop("prediction byte-size drift")
    arr=np.frombuffer(raw,dtype="<f8",offset=off).reshape(ne,ns,nfields)
    return ne,ns,k,arr

def parse_mask(path:Path):
    raw=path.read_bytes()
    if not raw.startswith(MASK_MAGIC):raise Stop("mask magic drift")
    off=len(MASK_MAGIC)
    if len(raw)<off+8:raise Stop("mask truncated")
    ne,ns=struct.unpack_from("<II",raw,off);off+=8
    if len(raw)!=off+ne*ns:raise Stop("mask byte-size drift")
    arr=np.frombuffer(raw,dtype=np.uint8,offset=off).reshape(ne,ns)
    if np.any((arr!=0)&(arr!=1)):raise Stop("mask domain drift")
    return ne,ns,arr

def binary_logloss(p:np.ndarray,y:np.ndarray):
    if np.any(p<=0) or np.any(p>=1):raise Stop("probability outside open unit interval")
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("predictions",type=Path)
    ap.add_argument("entity_order",type=Path)
    ap.add_argument("graph_empty_mask",type=Path)
    ap.add_argument("preconfirm_receipt",type=Path)
    ap.add_argument("universe",type=Path)
    ap.add_argument("matrix",type=Path)
    ap.add_argument("response_receipt",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--block-output",type=Path,required=True)
    ap.add_argument("--null-output",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_sealed_species_scoring_contract.v1_95":raise Stop("contract schema drift")
        pre=json.loads(a.preconfirm_receipt.read_text())
        if pre.get("status")!="SECOND_LAYER_R3_C_AND_REWIRED_PREDICTIONS_FROZEN_BEFORE_HELDOUT_ACCESS":raise Stop("preconfirm freeze did not qualify")
        if pre.get("heldout_second_layer_response_opened") is not False:raise Stop("preconfirm response boundary drift")
        if sha(a.predictions)!=pre.get("prediction_sha256"):raise Stop("prediction SHA drift")
        if sha(a.entity_order)!=pre.get("entity_order_sha256"):raise Stop("entity-order SHA drift")
        if sha(a.graph_empty_mask)!=pre.get("graph_empty_mask_sha256"):raise Stop("graph-empty mask SHA drift")
        if sha(a.universe)!=c["species_layer"]["species_universe_sha256"]:raise Stop("universe SHA drift")

        rr=json.loads(a.response_receipt.read_text())
        if rr.get("status")!="SECOND_LAYER_HELDOUT_RESPONSE_CONSUMED_ONCE":raise Stop("heldout response did not qualify")
        if rr.get("heldout_second_layer_response_consumed") is not True or rr.get("rerun_authorized") is not False:raise Stop("response terminality drift")
        if rr.get("heldout_non_second_layer_values_decoded")!=0:raise Stop("non-second-layer heldout values decoded")
        if rr.get("pilot_occurrence_values_decoded_during_run")!=0 or rr.get("excluded_occurrence_values_decoded")!=0:raise Stop("pilot/excluded values decoded")
        if sha(a.matrix)!=rr.get("matrix_sha256"):raise Stop("matrix SHA drift")

        erows=load_csv(a.entity_order);urows=load_csv(a.universe);mrows=load_csv(a.matrix)
        if len(erows)!=4126 or len(urows)!=96 or len(mrows)!=4126:raise Stop("scoring dimension drift")
        labels=[f"S{j:05d}" for j in range(96)]
        if list(mrows[0].keys())!=["ID","block_id","bioregion"]+labels:raise Stop("matrix schema drift")
        if [r["ID"] for r in erows]!=[r["ID"] for r in mrows]:raise Stop("entity order drift")
        for er,mr in zip(erows,mrows):
            if er["block_id"]!=mr["block_id"] or er["bioregion"]!=mr["bioregion"]:raise Stop("routing metadata drift")

        Y=np.empty((4126,96),dtype=np.int8)
        for i,r in enumerate(mrows):
            for j,l in enumerate(labels):
                y=int(r[l])
                if y not in (0,1):raise Stop("target domain drift")
                Y[i,j]=y

        ne,ns,K,pred=parse_predictions(a.predictions)
        me,ms,empty=parse_mask(a.graph_empty_mask)
        if (ne,ns,K)!=(4126,96,20) or (me,ms)!=(4126,96):raise Stop("prediction/mask shape drift")
        p3=pred[:,:,0];pc=pred[:,:,1];pnull=pred[:,:,2:]
        y=Y.astype(np.float64)
        l3=binary_logloss(p3,y);lc=binary_logloss(pc,y)
        lnull=-(y[:,:,None]*np.log(pnull)+(1-y[:,:,None])*np.log1p(-pnull))
        delta=lc-l3
        topo=lc-np.mean(lnull,axis=2,dtype=np.float64)
        null_delta=lnull-l3[:,:,None]

        byblock=defaultdict(list)
        for i,r in enumerate(erows):byblock[r["block_id"]].append(i)
        if len(byblock)!=168:raise Stop("block count drift")

        primary_blocks={};absence_blocks={};presence_blocks={};p3_blocks={};p4_blocks={}
        block_rows=[]
        for b,inds_list in sorted(byblock.items()):
            inds=np.asarray(inds_list,dtype=int)
            d=delta[inds,:];yy=Y[inds,:];ee=empty[inds,:];tt=topo[inds,:]
            primary=float(np.mean(d,dtype=np.float64));primary_blocks[b]=primary
            ad=d[yy==0]
            if ad.size==0:raise Stop("block with no absence cell")
            absence=float(np.mean(ad,dtype=np.float64));absence_blocks[b]=absence
            pd=d[yy==1]
            presence=float(np.mean(pd,dtype=np.float64)) if pd.size else None
            if presence is not None:presence_blocks[b]=presence
            non=d[ee==0];emp=d[ee==1]
            support_contrast=None
            if non.size and emp.size:
                support_contrast=float(np.mean(non,dtype=np.float64)-np.mean(emp,dtype=np.float64))
                p3_blocks[b]=support_contrast
            topology=float(np.mean(tt,dtype=np.float64));p4_blocks[b]=topology
            block_rows.append({
              "block_id":b,
              "bioregion":erows[inds_list[0]]["bioregion"],
              "islands":len(inds_list),
              "targets":int(d.size),
              "presence_cells":int(np.sum(yy==1)),
              "absence_cells":int(np.sum(yy==0)),
              "graph_nonempty_cells":int(np.sum(ee==0)),
              "graph_empty_cells":int(np.sum(ee==1)),
              "mean_C_minus_R3":primary,
              "mean_absence_C_minus_R3":absence,
              "mean_presence_C_minus_R3":presence,
              "mean_nonempty_minus_empty_C_minus_R3":support_contrast,
              "mean_actualC_minus_mean_rewiredC":topology,
            })

        p1=c["P1"];p1_point,p1_low,p1_high=bootstrap(primary_blocks,int(p1["bootstrap_replicates"]),int(p1["bootstrap_seed"]))
        p1_support=p1_point<0 and p1_high<0

        p2=c["P2"]
        a_point,a_low,a_high=bootstrap(absence_blocks,int(p2["absence_bootstrap_replicates"]),int(p2["absence_bootstrap_seed"]))
        if len(presence_blocks)>=int(p2["minimum_presence_blocks"]):
            pr_point,pr_low,pr_high=bootstrap(presence_blocks,int(p2["presence_bootstrap_replicates"]),int(p2["presence_bootstrap_seed"]))
            p2_estimable=True
            p2_support=a_point<0 and a_high<0 and pr_point>=0
            balanced={b:(absence_blocks[b]+presence_blocks[b])/2 for b in presence_blocks}
            balanced_point=math.fsum(balanced.values())/len(balanced)
        else:
            pr_point=pr_low=pr_high=balanced_point=None;p2_estimable=False;p2_support=False

        p3=c["P3"]
        if len(p3_blocks)>=int(p3["minimum_paired_blocks"]):
            p3_point,p3_low,p3_high=bootstrap(p3_blocks,int(p3["bootstrap_replicates"]),int(p3["bootstrap_seed"]))
            p3_estimable=True;p3_support=p3_point<0 and p3_high<0
        else:
            p3_point=p3_low=p3_high=None;p3_estimable=False;p3_support=False

        p4=c["P4"]
        p4_point,p4_low,p4_high=bootstrap(p4_blocks,int(p4["bootstrap_replicates"]),int(p4["bootstrap_seed"]))
        p4_support=p4_point<0 and p4_high<0

        null_effects=[]
        for k in range(K):
            nb={}
            for b,inds_list in byblock.items():
                inds=np.asarray(inds_list,dtype=int)
                nb[b]=float(np.mean(null_delta[inds,:,k],dtype=np.float64))
            pt=math.fsum(nb.values())/len(nb)
            null_effects.append(pt)
        actual_better=sum(p1_point < z for z in null_effects)

        # Pooled support diagnostics are descriptive only.
        empty_delta=delta[empty==1];nonempty_delta=delta[empty==0]
        pooled_empty=float(np.mean(empty_delta,dtype=np.float64)) if empty_delta.size else None
        pooled_nonempty=float(np.mean(nonempty_delta,dtype=np.float64)) if nonempty_delta.size else None

        a.block_output.parent.mkdir(parents=True,exist_ok=True)
        fields=["block_id","bioregion","islands","targets","presence_cells","absence_cells","graph_nonempty_cells","graph_empty_cells",
                "mean_C_minus_R3","mean_absence_C_minus_R3","mean_presence_C_minus_R3",
                "mean_nonempty_minus_empty_C_minus_R3","mean_actualC_minus_mean_rewiredC"]
        with a.block_output.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(block_rows)
        with a.null_output.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["null_index","block_weighted_C_rewired_minus_R3"])
            for k,v in enumerate(null_effects,1):w.writerow([k,repr(v)])

        out={
          "schema":"structural.global_mammals_sealed_species_scoring_result.v1_95",
          "status":"PROSPECTIVE_SECOND_SPECIES_LAYER_SCORED_ONCE",
          "candidate_id":c["candidate_id"],
          "species_layer":{
            "species":96,"heldout_islands":4126,"heldout_blocks":168,"target_cells":396096,
            "positive_cells":int(np.sum(Y==1)),"negative_cells":int(np.sum(Y==0)),
          },
          "P1_primary":{
            "point_C_minus_R3":p1_point,"bootstrap_ci95_low":p1_low,"bootstrap_ci95_high":p1_high,
            "bootstrap_replicates":int(p1["bootstrap_replicates"]),"bootstrap_seed":int(p1["bootstrap_seed"]),
            "supported":p1_support,
          },
          "P2_constraint_signature":{
            "estimable":p2_estimable,"presence_blocks":len(presence_blocks),
            "absence_point":a_point,"absence_ci95_low":a_low,"absence_ci95_high":a_high,
            "presence_point":pr_point,"presence_ci95_low":pr_low,"presence_ci95_high":pr_high,
            "class_balanced_equal_block":balanced_point,
            "supported":p2_support,
          },
          "P3_source_support_signature":{
            "estimable":p3_estimable,"paired_blocks":len(p3_blocks),
            "point_nonempty_minus_empty_delta":p3_point,"bootstrap_ci95_low":p3_low,"bootstrap_ci95_high":p3_high,
            "pooled_graph_nonempty_C_minus_R3":pooled_nonempty,
            "pooled_graph_empty_C_minus_R3":pooled_empty,
            "supported":p3_support,
          },
          "P4_topology_specificity":{
            "point_actualC_minus_mean_rewiredC":p4_point,"bootstrap_ci95_low":p4_low,"bootstrap_ci95_high":p4_high,
            "null_graphs":20,"actual_C_better_than_n_of_20_nulls_on_block_weighted_C_minus_R3":actual_better,
            "null_block_weighted_C_minus_R3_min":min(null_effects),
            "null_block_weighted_C_minus_R3_max":max(null_effects),
            "null_block_weighted_C_minus_R3_mean":math.fsum(null_effects)/len(null_effects),
            "supported":p4_support,
          },
          "interpretation":{
            "primary_species_layer_replication_supported":p1_support,
            "all_three_secondary_signatures_supported":p2_support and p3_support and p4_support,
            "all_four_predictions_supported":p1_support and p2_support and p3_support and p4_support,
            "allowed_primary_wording":"prospective preregistered species-layer replication within the same geographic system" if p1_support else "prospective species-layer non-replication within the same geographic system",
            "geographically_independent_replication":False,
            "fresh_system_confirmation":False,
            "secondary_signatures_can_rescue_failed_P1":False,
          },
          "block_scores_sha256":sha(a.block_output),
          "null_scores_sha256":sha(a.null_output),
          "prediction_sha256":sha(a.predictions),
          "heldout_matrix_sha256":sha(a.matrix),
          "heldout_second_layer_response_consumed":True,
          "rerun_authorized":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={
          "schema":"structural.global_mammals_sealed_species_scoring_result.v1_95",
          "status":"TERMINAL_SCORING_FAILURE_AFTER_SECOND_LAYER_RESPONSE",
          "reason":str(e),
          "heldout_second_layer_response_consumed":True,
          "rerun_authorized":False
        };code=2
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
