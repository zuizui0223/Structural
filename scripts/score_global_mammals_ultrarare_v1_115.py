#!/usr/bin/env python3
"""Score the preregistered 529-species ultrarare heldout layer once."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,struct
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_ultrarare_scoring_contract_v1_115.json"
ACTUAL_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_PRED_V1\n"
NULL_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_NULL_PRED_V1\n"
MASK_MAGIC=b"STRUCTURAL_MAMMAL_ULTRARARE_GRAPH_EMPTY_V1\n"
class Stop(RuntimeError): pass

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def load_csv(p:Path):
    with p.open("r",encoding="utf-8",newline="") as h: return list(csv.DictReader(h))

def type7(values,p):
    xs=sorted(float(x) for x in values)
    if not xs: raise Stop("empty quantile input")
    if len(xs)==1:return xs[0]
    h=(len(xs)-1)*p;lo=int(math.floor(h));hi=int(math.ceil(h))
    if lo==hi:return xs[lo]
    f=h-lo;return xs[lo]*(1-f)+xs[hi]*f

def bootstrap(block_values:dict[str,float],reps:int,seed:int):
    names=sorted(block_values)
    if not names: raise Stop("empty bootstrap")
    point=math.fsum(block_values[b] for b in names)/len(names)
    rng=random.Random(seed);boot=[]
    for _ in range(reps):
        vals=[block_values[names[rng.randrange(len(names))]] for _ in names]
        boot.append(math.fsum(vals)/len(vals))
    return point,type7(boot,0.025),type7(boot,0.975)

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
    if len(x)!=len(y) or len(x)<2: raise Stop("invalid correlation input")
    mx=math.fsum(x)/len(x);my=math.fsum(y)/len(y)
    dx=[v-mx for v in x];dy=[v-my for v in y]
    sx=math.sqrt(math.fsum(v*v for v in dx));sy=math.sqrt(math.fsum(v*v for v in dy))
    if sx<=0 or sy<=0:return None
    return math.fsum(a*b for a,b in zip(dx,dy))/(sx*sy)

def spearman(x,y):
    return pearson(average_ranks(x),average_ranks(y))

def bootstrap_rho(pairs:dict[str,tuple[float,float]],reps:int,seed:int,min_valid:int):
    names=sorted(pairs)
    x=[pairs[b][0] for b in names];y=[pairs[b][1] for b in names]
    point=spearman(x,y)
    if point is None: raise Stop("observed Spearman not estimable")
    rng=random.Random(seed);boot=[]
    for _ in range(reps):
        chosen=[names[rng.randrange(len(names))] for _ in names]
        bx=[pairs[b][0] for b in chosen];by=[pairs[b][1] for b in chosen]
        r=spearman(bx,by)
        if r is not None:boot.append(r)
    if len(boot)<min_valid: raise Stop("too few valid Spearman bootstrap replicates")
    return point,type7(boot,0.025),type7(boot,0.975),len(boot)

def parse_actual(path:Path):
    with path.open("rb") as h:
        magic=h.read(len(ACTUAL_MAGIC))
        if magic!=ACTUAL_MAGIC:raise Stop("actual magic drift")
        ne,ns=struct.unpack("<II",h.read(8))
    if (ne,ns)!=(4126,529):raise Stop("actual shape drift")
    off=len(ACTUAL_MAGIC)+8
    arr=np.memmap(path,dtype="<f8",mode="r",offset=off,shape=(ne,ns,2))
    return arr

def parse_null(path:Path):
    with path.open("rb") as h:
        magic=h.read(len(NULL_MAGIC))
        if magic!=NULL_MAGIC:raise Stop("null magic drift")
        K,ne,ns=struct.unpack("<III",h.read(12))
    if (K,ne,ns)!=(20,4126,529):raise Stop("null shape drift")
    off=len(NULL_MAGIC)+12
    arr=np.memmap(path,dtype="<f8",mode="r",offset=off,shape=(K,ne,ns))
    return arr

def parse_mask(path:Path):
    raw=path.read_bytes()
    if not raw.startswith(MASK_MAGIC):raise Stop("mask magic drift")
    off=len(MASK_MAGIC);ne,ns=struct.unpack_from("<II",raw,off);off+=8
    if (ne,ns)!=(4126,529) or len(raw)!=off+ne*ns:raise Stop("mask shape drift")
    arr=np.frombuffer(raw,dtype=np.uint8,offset=off).reshape(ne,ns)
    if np.any((arr!=0)&(arr!=1)):raise Stop("mask domain drift")
    return arr

def logloss(p,y):
    if np.any(p<=0) or np.any(p>=1):raise Stop("probability outside unit interval")
    return -(y*np.log(p)+(1-y)*np.log1p(-p))

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("actual_predictions",type=Path)
    ap.add_argument("null_predictions",type=Path)
    ap.add_argument("entity_order",type=Path)
    ap.add_argument("graph_empty_mask",type=Path)
    ap.add_argument("block_context",type=Path)
    ap.add_argument("actual_preconfirm_receipt",type=Path)
    ap.add_argument("null_receipt",type=Path)
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
        if c.get("schema")!="structural.global_mammals_ultrarare_scoring_contract.v1_115":raise Stop("contract schema drift")
        pre=json.loads(a.actual_preconfirm_receipt.read_text())
        nul=json.loads(a.null_receipt.read_text())
        if pre.get("status")!="ULTRARARE_R3_C_PREDICTIONS_FROZEN_BEFORE_HELDOUT_ACCESS":raise Stop("actual preconfirm did not qualify")
        if nul.get("status")!="ULTRARARE_MATCHED_TOPOLOGY_NULLS_FROZEN_BEFORE_HELDOUT_ACCESS":raise Stop("null preconfirm did not qualify")
        if pre.get("heldout_response_opened") is not False or nul.get("heldout_response_opened") is not False:raise Stop("pre-response boundary drift")
        if sha(a.actual_predictions)!=pre.get("prediction_sha256"):raise Stop("actual prediction SHA drift")
        if sha(a.entity_order)!=pre.get("entity_order_sha256"):raise Stop("entity order SHA drift")
        if sha(a.graph_empty_mask)!=pre.get("graph_empty_mask_sha256"):raise Stop("graph mask SHA drift")
        if sha(a.block_context)!=pre.get("block_context_sha256"):raise Stop("block context SHA drift")
        if sha(a.null_predictions)!=nul.get("null_prediction_sha256"):raise Stop("null prediction SHA drift")
        if sha(a.universe)!=c["species_layer"]["species_universe_sha256"]:raise Stop("universe SHA drift")

        rr=json.loads(a.response_receipt.read_text())
        if rr.get("status")!="ULTRARARE_HELDOUT_RESPONSE_CONSUMED_ONCE":raise Stop("heldout response did not qualify")
        if rr.get("heldout_ultrarare_response_consumed") is not True or rr.get("rerun_authorized") is not False:raise Stop("response terminality drift")
        if rr.get("heldout_non_ultrarare_values_decoded")!=0:raise Stop("non-ultrarare heldout values decoded")
        if rr.get("pilot_occurrence_values_decoded_during_run")!=0 or rr.get("excluded_occurrence_values_decoded")!=0:raise Stop("pilot/excluded values decoded")
        if sha(a.matrix)!=rr.get("matrix_sha256"):raise Stop("matrix SHA drift")

        order=load_csv(a.entity_order);matrix=load_csv(a.matrix);context=load_csv(a.block_context)
        if len(order)!=4126 or len(matrix)!=4126 or len(context)!=168:raise Stop("row count drift")
        labels=[f"S{j:05d}" for j in range(529)]
        if list(matrix[0].keys())!=["ID","block_id","bioregion"]+labels:raise Stop("matrix schema drift")
        if [r["ID"] for r in order]!=[r["ID"] for r in matrix]:raise Stop("entity order mismatch")
        for e,m in zip(order,matrix):
            if e["block_id"]!=m["block_id"] or e["bioregion"]!=m["bioregion"]:raise Stop("routing metadata mismatch")

        Y=np.empty((4126,529),dtype=np.int8)
        for i,r in enumerate(matrix):
            for j,l in enumerate(labels):
                y=int(r[l])
                if y not in (0,1):raise Stop("target domain drift")
                Y[i,j]=y

        actual=parse_actual(a.actual_predictions);nulls=parse_null(a.null_predictions);empty=parse_mask(a.graph_empty_mask)
        p3=np.asarray(actual[:,:,0]);pc=np.asarray(actual[:,:,1]);yf=Y.astype(np.float64)
        l3=logloss(p3,yf);lc=logloss(pc,yf);delta=lc-l3

        byblock=defaultdict(list)
        for i,r in enumerate(order):byblock[r["block_id"]].append(i)
        if len(byblock)!=168:raise Stop("block count drift")
        ctx={r["block_id"]:float(r["mean_z_Current_isolation"]) for r in context}
        if set(ctx)!=set(byblock):raise Stop("block context mismatch")

        all_blocks={};presence_blocks={};absence_blocks={};support_blocks={}
        block_rows=[]
        # First pass actual C/R3.
        for b,ii in sorted(byblock.items()):
            inds=np.asarray(ii,dtype=int);d=delta[inds,:];yy=Y[inds,:];ee=empty[inds,:]
            all_blocks[b]=float(np.mean(d,dtype=np.float64))
            ad=d[yy==0];absence_blocks[b]=float(np.mean(ad,dtype=np.float64))
            pd=d[yy==1]
            pp=float(np.mean(pd,dtype=np.float64)) if pd.size else None
            if pp is not None:presence_blocks[b]=pp
            non=d[(yy==1)&(ee==0)];emp=d[(yy==1)&(ee==1)]
            sc=None
            if non.size and emp.size:
                sc=float(np.mean(non,dtype=np.float64)-np.mean(emp,dtype=np.float64));support_blocks[b]=sc
            block_rows.append({
              "block_id":b,"bioregion":order[ii[0]]["bioregion"],"islands":len(ii),
              "targets":int(d.size),"presence_cells":int(np.sum(yy==1)),"absence_cells":int(np.sum(yy==0)),
              "presence_graph_nonempty_cells":int(np.sum((yy==1)&(ee==0))),
              "presence_graph_empty_cells":int(np.sum((yy==1)&(ee==1))),
              "mean_all_C_minus_R3":all_blocks[b],"mean_presence_C_minus_R3":pp,
              "mean_absence_C_minus_R3":absence_blocks[b],
              "mean_presence_nonempty_minus_empty_C_minus_R3":sc,
              "mean_z_Current_isolation":ctx[b]
            })

        p1=c["primary_presence_opportunity"]
        if len(presence_blocks)<int(p1["minimum_presence_blocks"]):raise Stop("primary presence blocks below minimum")
        p1_point,p1_low,p1_high=bootstrap(presence_blocks,int(p1["bootstrap_replicates"]),int(p1["bootstrap_seed"]))
        p1_support=p1_point<0 and p1_high<0

        sa=c["secondary_absence_signature"]
        a_point,a_low,a_high=bootstrap(absence_blocks,int(sa["bootstrap_replicates"]),int(sa["bootstrap_seed"]))
        absence_direction_supported=a_point>=0

        iso=c["secondary_external_isolation_attenuation"]
        pairs={b:(ctx[b],presence_blocks[b]) for b in presence_blocks}
        rho,rho_low,rho_high,rho_n=bootstrap_rho(pairs,int(iso["bootstrap_replicates"]),int(iso["bootstrap_seed"]),int(iso["minimum_valid_bootstrap_replicates"]))
        iso_support=rho>0 and rho_low>0

        ss=c["secondary_source_support"]
        if len(support_blocks)>=int(ss["minimum_paired_blocks"]):
            ss_point,ss_low,ss_high=bootstrap(support_blocks,int(ss["bootstrap_replicates"]),int(ss["bootstrap_seed"]))
            ss_estimable=True;ss_support=ss_point<0 and ss_high<0
        else:
            ss_point=ss_low=ss_high=None;ss_estimable=False;ss_support=False

        # Null topology: compute null loss only on realized-presence cells, one null at a time.
        pres_mask=Y==1
        null_presence_effects=[];mean_null_presence_loss=np.zeros_like(lc)
        for k in range(20):
            pn=np.asarray(nulls[k,:,:])
            # y=1 log loss only; fill zeros elsewhere to keep array arithmetic simple.
            lp=np.zeros_like(lc)
            lp[pres_mask]=-np.log(pn[pres_mask])
            mean_null_presence_loss+=lp/20.0
            nb={}
            for b,ii in byblock.items():
                inds=np.asarray(ii,dtype=int);m=pres_mask[inds,:]
                if np.any(m):nb[b]=float(np.mean((lp[inds,:]-l3[inds,:])[m],dtype=np.float64))
            null_presence_effects.append(math.fsum(nb.values())/len(nb))

        topo_blocks={}
        for b,ii in byblock.items():
            inds=np.asarray(ii,dtype=int);m=pres_mask[inds,:]
            if np.any(m):
                topo_blocks[b]=float(np.mean((lc[inds,:]-mean_null_presence_loss[inds,:])[m],dtype=np.float64))
        st=c["secondary_topology_specificity"]
        if len(topo_blocks)<int(st["minimum_presence_blocks"]):raise Stop("topology presence blocks below minimum")
        topo_point,topo_low,topo_high=bootstrap(topo_blocks,int(st["bootstrap_replicates"]),int(st["bootstrap_seed"]))
        topo_support=topo_point<0 and topo_high<0
        actual_better=sum(p1_point<z for z in null_presence_effects)

        overall=math.fsum(all_blocks.values())/len(all_blocks)
        balanced={b:(presence_blocks[b]+absence_blocks[b])/2 for b in presence_blocks}
        balanced_point=math.fsum(balanced.values())/len(balanced)
        pooled_non=delta[(Y==1)&(empty==0)];pooled_emp=delta[(Y==1)&(empty==1)]

        a.block_output.parent.mkdir(parents=True,exist_ok=True)
        fields=list(block_rows[0].keys())
        with a.block_output.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(block_rows)
        with a.null_output.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["null_index","block_weighted_presence_C_rewired_minus_R3"])
            for k,v in enumerate(null_presence_effects,1):w.writerow([k,repr(v)])

        out={
          "schema":"structural.global_mammals_ultrarare_scoring_result.v1_115",
          "status":"PROSPECTIVE_ULTRARARE_LAYER_SCORED_ONCE",
          "species_layer":{
            "species":529,"heldout_islands":4126,"heldout_blocks":168,
            "target_cells":2182654,"positive_cells":int(np.sum(Y==1)),
            "negative_cells":int(np.sum(Y==0)),"heldout_prevalence":float(np.mean(Y))
          },
          "primary_presence_opportunity":{
            "presence_blocks":len(presence_blocks),"point_C_minus_R3":p1_point,
            "bootstrap_ci95_low":p1_low,"bootstrap_ci95_high":p1_high,
            "bootstrap_replicates":int(p1["bootstrap_replicates"]),"bootstrap_seed":int(p1["bootstrap_seed"]),
            "supported":p1_support
          },
          "secondary_absence_signature":{
            "point_C_minus_R3":a_point,"bootstrap_ci95_low":a_low,"bootstrap_ci95_high":a_high,
            "predicted_nonnegative_direction_supported":absence_direction_supported
          },
          "secondary_external_isolation_attenuation":{
            "presence_blocks":len(presence_blocks),"spearman_rho":rho,
            "bootstrap_ci95_low":rho_low,"bootstrap_ci95_high":rho_high,
            "valid_bootstrap_replicates":rho_n,"supported":iso_support
          },
          "secondary_source_support":{
            "paired_blocks":len(support_blocks),"estimable":ss_estimable,
            "point_nonempty_minus_empty":ss_point,"bootstrap_ci95_low":ss_low,
            "bootstrap_ci95_high":ss_high,"supported":ss_support,
            "pooled_presence_nonempty_C_minus_R3":float(np.mean(pooled_non)) if pooled_non.size else None,
            "pooled_presence_empty_C_minus_R3":float(np.mean(pooled_emp)) if pooled_emp.size else None
          },
          "secondary_topology_specificity":{
            "presence_blocks":len(topo_blocks),"point_actualC_minus_mean_rewiredC":topo_point,
            "bootstrap_ci95_low":topo_low,"bootstrap_ci95_high":topo_high,
            "actual_C_better_than_n_of_20_nulls_on_presence_metric":actual_better,
            "null_presence_C_minus_R3_min":min(null_presence_effects),
            "null_presence_C_minus_R3_max":max(null_presence_effects),
            "null_presence_C_minus_R3_mean":math.fsum(null_presence_effects)/len(null_presence_effects),
            "supported":topo_support
          },
          "descriptive":{
            "natural_prevalence_all_cell_C_minus_R3":overall,
            "class_balanced_equal_block_C_minus_R3":balanced_point,
            "graph_empty_fraction":float(np.mean(empty))
          },
          "interpretation":{
            "presence_opportunity_primary_supported":p1_support,
            "secondary_absence_direction_supported":absence_direction_supported,
            "secondary_external_isolation_attenuation_supported":iso_support,
            "secondary_source_support_supported":ss_support,
            "secondary_topology_specificity_supported":topo_support,
            "secondary_results_may_rescue_primary":False,
            "geographically_independent_replication":False,
            "causal_colonization_or_rescue_claimed":False
          },
          "block_scores_sha256":sha(a.block_output),"null_scores_sha256":sha(a.null_output),
          "heldout_matrix_sha256":sha(a.matrix),"heldout_ultrarare_response_consumed":True,
          "rerun_authorized":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={
          "schema":"structural.global_mammals_ultrarare_scoring_result.v1_115",
          "status":"TERMINAL_SCORING_FAILURE_AFTER_ULTRARARE_RESPONSE",
          "reason":str(e),"heldout_ultrarare_response_consumed":True,"rerun_authorized":False
        };code=2
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
