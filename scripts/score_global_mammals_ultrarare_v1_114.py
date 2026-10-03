#!/usr/bin/env python3
"""Score the preregistered ultrarare presence-opportunity test once."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,struct
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_ultrarare_scoring_contract_v1_114.json"
MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_PRED_V1\n"
MASK_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_GRAPH_EMPTY_V1\n"
class Stop(RuntimeError):pass

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

def bootstrap_mean(vals:dict[str,float],reps:int,seed:int):
    names=sorted(vals)
    if not names:raise Stop("empty bootstrap")
    point=math.fsum(vals[b] for b in names)/len(names)
    rng=random.Random(seed);boot=[]
    for _ in range(reps):
        x=[vals[names[rng.randrange(len(names))]] for _ in names]
        boot.append(math.fsum(x)/len(x))
    return point,type7(boot,0.025),type7(boot,0.975)

def ranks(xs):
    order=sorted(range(len(xs)),key=lambda i:(xs[i],i))
    out=[0.0]*len(xs);j=0
    while j<len(order):
        k=j+1
        while k<len(order) and xs[order[k]]==xs[order[j]]:k+=1
        r=((j+1)+k)/2.0
        for i in order[j:k]:out[i]=r
        j=k
    return out

def pearson(x,y):
    mx=sum(x)/len(x);my=sum(y)/len(y)
    dx=[v-mx for v in x];dy=[v-my for v in y]
    sx=math.sqrt(sum(v*v for v in dx));sy=math.sqrt(sum(v*v for v in dy))
    if sx==0 or sy==0:raise Stop("zero variance correlation")
    return sum(a*b for a,b in zip(dx,dy))/(sx*sy)

def spearman(x,y):return pearson(ranks(x),ranks(y))

def bootstrap_rho(rows:list[tuple[float,float]],reps:int,seed:int):
    if len(rows)<2:raise Stop("too few correlation rows")
    point=spearman([x for x,_ in rows],[y for _,y in rows])
    rng=random.Random(seed);boot=[];invalid=0;n=len(rows)
    for _ in range(reps):
        samp=[rows[rng.randrange(n)] for _ in range(n)]
        try:boot.append(spearman([x for x,_ in samp],[y for _,y in samp]))
        except Stop:invalid+=1
    if len(boot)<int(0.95*reps):raise Stop("too many invalid correlation bootstrap replicates")
    return point,type7(boot,0.025),type7(boot,0.975),len(boot),invalid

def parse_predictions(p:Path):
    raw=p.read_bytes()
    if not raw.startswith(MAGIC):raise Stop("prediction magic drift")
    off=len(MAGIC);ne,ns=struct.unpack_from("<II",raw,off);off+=8
    if len(raw)!=off+ne*ns*2*8:raise Stop("prediction byte-size drift")
    return ne,ns,np.frombuffer(raw,dtype="<f8",offset=off).reshape(ne,ns,2)

def parse_mask(p:Path):
    raw=p.read_bytes()
    if not raw.startswith(MASK_MAGIC):raise Stop("mask magic drift")
    off=len(MASK_MAGIC);ne,ns=struct.unpack_from("<II",raw,off);off+=8
    if len(raw)!=off+ne*ns:raise Stop("mask size drift")
    arr=np.frombuffer(raw,dtype=np.uint8,offset=off).reshape(ne,ns)
    if np.any((arr!=0)&(arr!=1)):raise Stop("mask domain drift")
    return ne,ns,arr

def logloss(p,y):
    if np.any(p<=0) or np.any(p>=1):raise Stop("probability boundary")
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("predictions",type=Path)
    ap.add_argument("entity_order",type=Path)
    ap.add_argument("graph_empty_mask",type=Path)
    ap.add_argument("block_context",type=Path)
    ap.add_argument("preconfirm_receipt",type=Path)
    ap.add_argument("universe",type=Path)
    ap.add_argument("matrix",type=Path)
    ap.add_argument("response_receipt",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--block-output",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_ultrarare_scoring_contract.v1_114":
            raise Stop("contract schema drift")
        pre=json.loads(a.preconfirm_receipt.read_text())
        if pre.get("status")!="ULTRARARE_R3_C_PREDICTIONS_FROZEN_BEFORE_HELDOUT_ACCESS":
            raise Stop("preconfirm status drift")
        if pre.get("heldout_response_opened") is not False:raise Stop("preconfirm boundary drift")
        if sha(a.predictions)!=pre["prediction_sha256"]:raise Stop("prediction SHA drift")
        if sha(a.entity_order)!=pre["entity_order_sha256"]:raise Stop("entity-order SHA drift")
        if sha(a.graph_empty_mask)!=pre["graph_empty_mask_sha256"]:raise Stop("mask SHA drift")
        if sha(a.block_context)!=pre["block_context_sha256"]:raise Stop("block context SHA drift")
        if sha(a.universe)!=c["species_layer"]["species_universe_sha256"]:raise Stop("universe SHA drift")

        rr=json.loads(a.response_receipt.read_text())
        if rr.get("status")!="ULTRARARE_HELDOUT_RESPONSE_CONSUMED_ONCE":raise Stop("response status drift")
        if rr.get("heldout_non_ultrarare_values_decoded")!=0:raise Stop("non-ultrarare response decoded")
        if rr.get("pilot_occurrence_values_decoded_during_run")!=0 or rr.get("excluded_occurrence_values_decoded")!=0:
            raise Stop("pilot/excluded decode drift")
        if sha(a.matrix)!=rr["matrix_sha256"]:raise Stop("matrix SHA drift")

        er=load_csv(a.entity_order);mr=load_csv(a.matrix);ur=load_csv(a.universe);bc=load_csv(a.block_context)
        S=int(c["species_layer"]["species"])
        if len(er)!=4126 or len(mr)!=4126 or len(ur)!=S or len(bc)!=168:raise Stop("dimension drift")
        labels=[f"S{j:05d}" for j in range(S)]
        if list(mr[0].keys())!=["ID","block_id","bioregion"]+labels:raise Stop("matrix schema drift")
        if [r["ID"] for r in er]!=[r["ID"] for r in mr]:raise Stop("entity order drift")

        Y=np.empty((4126,S),dtype=np.int8)
        for i,r in enumerate(mr):
            if r["block_id"]!=er[i]["block_id"] or r["bioregion"]!=er[i]["bioregion"]:raise Stop("routing metadata drift")
            for j,l in enumerate(labels):
                y=int(r[l])
                if y not in (0,1):raise Stop("target domain drift")
                Y[i,j]=y

        ne,ns,pred=parse_predictions(a.predictions);me,ms,empty=parse_mask(a.graph_empty_mask)
        if (ne,ns)!=(4126,S) or (me,ms)!=(4126,S):raise Stop("prediction/mask shape drift")
        p3=pred[:,:,0];pc=pred[:,:,1];y=Y.astype(np.float64)
        delta=logloss(pc,y)-logloss(p3,y)

        ctx={r["block_id"]:float(r["mean_z_Current_isolation"]) for r in bc}
        byblock=defaultdict(list)
        for i,r in enumerate(er):byblock[r["block_id"]].append(i)
        if len(byblock)!=168 or set(byblock)!=set(ctx):raise Stop("block context mismatch")

        presence_blocks={};absence_blocks={};overall_blocks={};support_blocks={}
        rows=[]
        for b,inds0 in sorted(byblock.items()):
            inds=np.asarray(inds0,dtype=int);d=delta[inds];yy=Y[inds];ee=empty[inds]
            overall=float(np.mean(d));overall_blocks[b]=overall
            ad=d[yy==0]
            if ad.size==0:raise Stop("block without absence cells")
            absence=float(np.mean(ad));absence_blocks[b]=absence
            pd=d[yy==1]
            presence=float(np.mean(pd)) if pd.size else None
            if presence is not None:presence_blocks[b]=presence

            pmask=(yy==1)
            non=d[pmask & (ee==0)];emp=d[pmask & (ee==1)]
            contrast=None
            if non.size and emp.size:
                contrast=float(np.mean(non)-np.mean(emp));support_blocks[b]=contrast
            rows.append({
              "block_id":b,"bioregion":er[inds0[0]]["bioregion"],"islands":len(inds0),
              "presence_cells":int(np.sum(yy==1)),"absence_cells":int(np.sum(yy==0)),
              "presence_graph_nonempty":int(np.sum(pmask & (ee==0))),
              "presence_graph_empty":int(np.sum(pmask & (ee==1))),
              "mean_overall_C_minus_R3":overall,
              "mean_presence_C_minus_R3":presence,
              "mean_absence_C_minus_R3":absence,
              "mean_presence_nonempty_minus_empty":contrast,
              "mean_z_Current_isolation":ctx[b],
            })

        P1=c["P1_presence_opportunity"]
        if len(presence_blocks)<int(P1["minimum_presence_blocks"]):
            p1_estimable=False;p1_point=p1_low=p1_high=None;p1_support=False
        else:
            p1_estimable=True
            p1_point,p1_low,p1_high=bootstrap_mean(presence_blocks,int(P1["bootstrap_replicates"]),int(P1["bootstrap_seed"]))
            p1_support=p1_point<0 and p1_high<0

        P2=c["P2_absence_signature"]
        p2_point,p2_low,p2_high=bootstrap_mean(absence_blocks,int(P2["bootstrap_replicates"]),int(P2["bootstrap_seed"]))
        p2_support=p2_point>=0

        P3=c["P3_external_isolation_attenuation"]
        iso_rows=[(ctx[b],presence_blocks[b]) for b in sorted(presence_blocks)]
        if len(iso_rows)<int(P3["minimum_presence_blocks"]):
            p3_estimable=False;p3_point=p3_low=p3_high=None;p3_acc=p3_inv=0;p3_support=False
        else:
            p3_estimable=True
            p3_point,p3_low,p3_high,p3_acc,p3_inv=bootstrap_rho(iso_rows,int(P3["bootstrap_replicates"]),int(P3["bootstrap_seed"]))
            p3_support=p3_point>0 and p3_low>0

        P4=c["P4_source_support"]
        if len(support_blocks)<int(P4["minimum_paired_blocks"]):
            p4_estimable=False;p4_point=p4_low=p4_high=None;p4_support=False
        else:
            p4_estimable=True
            p4_point,p4_low,p4_high=bootstrap_mean(support_blocks,int(P4["bootstrap_replicates"]),int(P4["bootstrap_seed"]))
            p4_support=p4_point<0 and p4_high<0

        overall_point,overall_low,overall_high=bootstrap_mean(overall_blocks,10000,20261014)

        a.block_output.parent.mkdir(parents=True,exist_ok=True)
        fields=list(rows[0].keys())
        with a.block_output.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

        out={
          "schema":"structural.global_mammals_ultrarare_scoring_result.v1_114",
          "status":"PROSPECTIVE_ULTRARARE_SPECIES_LAYER_SCORED_ONCE",
          "species_layer":{
            "species":S,"heldout_islands":4126,"heldout_blocks":168,"target_cells":int(Y.size),
            "positive_cells":int(np.sum(Y==1)),"negative_cells":int(np.sum(Y==0)),
            "heldout_prevalence":float(np.mean(Y))
          },
          "P1_presence_opportunity":{
            "estimable":p1_estimable,"presence_blocks":len(presence_blocks),
            "point":p1_point,"ci95_low":p1_low,"ci95_high":p1_high,"supported":p1_support
          },
          "P2_absence_signature":{
            "point":p2_point,"ci95_low":p2_low,"ci95_high":p2_high,"supported":p2_support
          },
          "P3_external_isolation_attenuation":{
            "estimable":p3_estimable,"presence_blocks":len(presence_blocks),
            "spearman_rho":p3_point,"ci95_low":p3_low,"ci95_high":p3_high,
            "bootstrap_accepted":p3_acc,"bootstrap_invalid":p3_inv,"supported":p3_support
          },
          "P4_source_support":{
            "estimable":p4_estimable,"paired_blocks":len(support_blocks),
            "point_nonempty_minus_empty":p4_point,"ci95_low":p4_low,"ci95_high":p4_high,
            "supported":p4_support
          },
          "descriptive_overall":{
            "point_C_minus_R3":overall_point,"ci95_low":overall_low,"ci95_high":overall_high,
            "graph_empty_fraction":float(np.mean(empty))
          },
          "interpretation":{
            "presence_opportunity_replication_supported":p1_support,
            "external_isolation_attenuation_supported":p3_support,
            "source_support_signature_supported":p4_support,
            "absence_nonimprovement_direction_supported":p2_support,
            "geographically_independent_replication":False,
            "fresh_system_confirmation":False,
            "secondaries_can_rescue_failed_primary":False
          },
          "block_scores_sha256":sha(a.block_output),
          "heldout_matrix_sha256":sha(a.matrix),
          "prediction_sha256":sha(a.predictions),
          "heldout_ultrarare_response_consumed":True,
          "rerun_authorized":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={
          "schema":"structural.global_mammals_ultrarare_scoring_result.v1_114",
          "status":"TERMINAL_SCORING_FAILURE_AFTER_ULTRARARE_RESPONSE",
          "reason":str(e),
          "heldout_ultrarare_response_consumed":True,
          "rerun_authorized":False
        };code=2
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
