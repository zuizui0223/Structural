#!/usr/bin/env python3
"""Post-hoc nonrescuing diagnostics of frozen mammal R3/C prediction behavior."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,struct
from collections import defaultdict
from pathlib import Path

MAGIC=b"STRUCTURAL_MAMMAL_PRED_V1\n"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_csv(path:Path):
    with path.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def mean(xs):
    if not xs: raise Stop("empty mean")
    return math.fsum(xs)/len(xs)

def median(xs):
    if not xs: raise Stop("empty median")
    x=sorted(xs);n=len(x)
    return x[n//2] if n%2 else (x[n//2-1]+x[n//2])/2.0

def logloss(p,y):
    p=float(p)
    if not 0.0<p<1.0 or y not in (0,1):raise Stop("invalid prediction/target")
    return -math.log(p) if y==1 else -math.log1p(-p)

def parse_predictions(path:Path):
    raw=path.read_bytes()
    if not raw.startswith(MAGIC):raise Stop("prediction magic drift")
    off=len(MAGIC)
    ne,ns=struct.unpack_from("<II",raw,off);off+=8
    expected=off+ne*ns*16
    if len(raw)!=expected:raise Stop("prediction byte length drift")
    vals=list(struct.iter_unpack("<dd",memoryview(raw)[off:]))
    return ne,ns,vals

def average_ranks(vals):
    order=sorted(range(len(vals)),key=lambda i:(vals[i],i))
    ranks=[0.0]*len(vals);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and vals[order[j]]==vals[order[i]]:j+=1
        r=((i+1)+j)/2.0
        for k in order[i:j]:ranks[k]=r
        i=j
    return ranks

def pearson(x,y):
    mx,my=mean(x),mean(y)
    dx=[v-mx for v in x];dy=[v-my for v in y]
    den=math.sqrt(math.fsum(v*v for v in dx)*math.fsum(v*v for v in dy))
    if not den>0:raise Stop("zero correlation variance")
    return math.fsum(a*b for a,b in zip(dx,dy))/den

def spearman(x,y):
    return pearson(average_ranks(x),average_ranks(y))

def roc_auc(y,score):
    ranks=average_ranks(score)
    pos=[i for i,v in enumerate(y) if v==1]
    npos=len(pos);nneg=len(y)-npos
    if npos==0 or nneg==0:raise Stop("ROC-AUC class missing")
    return (math.fsum(ranks[i] for i in pos)-npos*(npos+1)/2.0)/(npos*nneg)

def average_precision(y,score):
    order=sorted(range(len(y)),key=lambda i:(-score[i],i))
    tp=0;vals=[]
    for rank,i in enumerate(order,start=1):
        if y[i]==1:
            tp+=1
            vals.append(tp/rank)
    if not vals:raise Stop("average precision no positives")
    return mean(vals)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pilot_matrix",type=Path)
    ap.add_argument("predictions",type=Path)
    ap.add_argument("entity_order",type=Path)
    ap.add_argument("model_receipt",type=Path)
    ap.add_argument("confirmatory_matrix",type=Path)
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--block-output",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c["schema"]!="structural.global_mammals_prediction_behavior_contract.v1_84":raise Stop("contract schema drift")
        exp=c["inputs"]
        for path,key in [
          (a.pilot_matrix,"pilot_matrix_sha256"),
          (a.predictions,"prediction_sha256"),
          (a.entity_order,"entity_order_sha256"),
          (a.model_receipt,"model_receipt_sha256"),
          (a.confirmatory_matrix,"confirmatory_matrix_sha256")
        ]:
            if sha(path)!=exp[key]:raise Stop(f"input SHA drift: {key}")

        pilot=load_csv(a.pilot_matrix)
        order=load_csv(a.entity_order)
        conf=load_csv(a.confirmatory_matrix)
        if len(pilot)!=1275 or len(order)!=4126 or len(conf)!=4126:raise Stop("island count drift")
        labels=[k for k in pilot[0] if k.startswith("S")]
        if len(labels)!=79:raise Stop("species count drift")
        if [r["ID"] for r in conf] != [r["ID"] for r in order]:raise Stop("confirmatory order drift")

        # Pilot occupancy counts within bioregion. The v1.40 frozen graph is connected
        # within each bioregion, so zero occupied pilot sources in-region is exactly
        # the v1.72 graph-source-empty condition for held-out rows.
        counts=defaultdict(lambda:[0]*79)
        for r in pilot:
            bio=r["bioregion"]
            for j,s in enumerate(labels):counts[bio][j]+=int(r[s])

        ne,ns,pairs=parse_predictions(a.predictions)
        if (ne,ns)!=(4126,79):raise Stop("prediction shape drift")
        if len(pairs)!=4126*79:raise Stop("prediction cell count drift")

        model=json.loads(a.model_receipt.read_text())
        expected_empty=int(model["confirmatory_empty_graph_source_rows"])

        block=defaultdict(lambda:{"delta":[],"r3":[],"c":[],"positive_delta":[],"negative_delta":[],"empty":0,"cells":0})
        y_all=[];p3_all=[];pc_all=[];delta_all=[]
        empty_delta=[];nonempty_delta=[];positive_delta=[];negative_delta=[]
        positive_r3=[];positive_c=[];negative_r3=[];negative_c=[]
        empty_count=0
        idx=0
        for i,(r,o) in enumerate(zip(conf,order)):
            if r["block_id"]!=o["block_id"] or r["bioregion"]!=o["bioregion"]:raise Stop("routing metadata drift")
            bio=r["bioregion"];b=r["block_id"]
            for j,s in enumerate(labels):
                y=int(r[s])
                if y not in (0,1):raise Stop("target domain drift")
                p3,pc=pairs[idx];idx+=1
                l3=logloss(p3,y);lc=logloss(pc,y);d=lc-l3
                empty=counts[bio][j]==0
                if empty:
                    empty_count+=1;empty_delta.append(d)
                else:nonempty_delta.append(d)
                if y==1:
                    positive_delta.append(d);positive_r3.append(l3);positive_c.append(lc)
                    block[b]["positive_delta"].append(d)
                else:
                    negative_delta.append(d);negative_r3.append(l3);negative_c.append(lc)
                    block[b]["negative_delta"].append(d)
                block[b]["delta"].append(d);block[b]["r3"].append(l3);block[b]["c"].append(lc)
                block[b]["empty"]+=int(empty);block[b]["cells"]+=1
                y_all.append(y);p3_all.append(p3);pc_all.append(pc);delta_all.append(d)

        if idx!=325954 or empty_count!=expected_empty:raise Stop("cell or graph-empty count drift")
        if len(block)!=168:raise Stop("block count drift")

        block_rows=[]
        presence_block_means=[];absence_block_means=[];balanced_block_means=[]
        for b in sorted(block):
            z=block[b]
            d=mean(z["delta"]);r3=mean(z["r3"]);cc=mean(z["c"])
            pos=mean(z["positive_delta"]) if z["positive_delta"] else None
            neg=mean(z["negative_delta"])
            if pos is not None:
                presence_block_means.append(pos)
                balanced_block_means.append((pos+neg)/2.0)
            absence_block_means.append(neg)
            block_rows.append({
              "block_id":b,
              "cells":z["cells"],
              "graph_empty_fraction":z["empty"]/z["cells"],
              "mean_R3_logloss":r3,
              "mean_C_logloss":cc,
              "mean_C_minus_R3":d,
              "presence_C_minus_R3":"" if pos is None else pos,
              "absence_C_minus_R3":neg
            })

        bw_r3=mean([r["mean_R3_logloss"] for r in block_rows])
        bw_c=mean([r["mean_C_logloss"] for r in block_rows])
        bw_delta=mean([r["mean_C_minus_R3"] for r in block_rows])

        # Four equal-rank groups of 42 blocks by graph-empty fraction.
        ranked=sorted(block_rows,key=lambda r:(r["graph_empty_fraction"],r["block_id"]))
        empty_quartiles=[]
        for q in range(4):
            chunk=ranked[q*42:(q+1)*42]
            empty_quartiles.append({
              "quartile":q+1,
              "blocks":42,
              "mean_graph_empty_fraction":mean([r["graph_empty_fraction"] for r in chunk]),
              "mean_C_minus_R3":mean([r["mean_C_minus_R3"] for r in chunk]),
              "median_C_minus_R3":median([r["mean_C_minus_R3"] for r in chunk]),
              "negative_blocks":sum(r["mean_C_minus_R3"]<0 for r in chunk)
            })

        empty_rho=spearman([r["graph_empty_fraction"] for r in block_rows],[r["mean_C_minus_R3"] for r in block_rows])
        cell_r3=mean([logloss(p,y) for p,y in zip(p3_all,y_all)])
        cell_c=mean([logloss(p,y) for p,y in zip(pc_all,y_all)])
        result={
          "schema":"structural.global_mammals_prediction_behavior_result.v1_84",
          "status":"POSTHOC_NONRESCUING_PREDICTION_BEHAVIOR_COMPLETE",
          "cells":325954,
          "positive_cells":sum(y_all),
          "negative_cells":len(y_all)-sum(y_all),
          "block_weighted":{
            "R3_logloss":bw_r3,
            "C_logloss":bw_c,
            "C_minus_R3":bw_delta,
            "relative_logloss_reduction":(bw_r3-bw_c)/bw_r3
          },
          "cell_weighted":{
            "R3_logloss":cell_r3,
            "C_logloss":cell_c,
            "C_minus_R3":mean(delta_all),
            "relative_logloss_reduction":(cell_r3-cell_c)/cell_r3
          },
          "outcome_stratified":{
            "presence":{
              "cells":len(positive_delta),
              "R3_logloss":mean(positive_r3),
              "C_logloss":mean(positive_c),
              "C_minus_R3":mean(positive_delta),
              "blocks_with_presence":len(presence_block_means),
              "equal_block_C_minus_R3":mean(presence_block_means),
              "blocks_where_C_better":sum(x<0 for x in presence_block_means)
            },
            "absence":{
              "cells":len(negative_delta),
              "R3_logloss":mean(negative_r3),
              "C_logloss":mean(negative_c),
              "C_minus_R3":mean(negative_delta),
              "blocks":len(absence_block_means),
              "equal_block_C_minus_R3":mean(absence_block_means),
              "blocks_where_C_better":sum(x<0 for x in absence_block_means)
            },
            "class_balanced_equal_block_C_minus_R3":mean(balanced_block_means),
            "class_balanced_blocks":len(balanced_block_means)
          },
          "ranking_context":{
            "R3_ROC_AUC":roc_auc(y_all,p3_all),
            "C_ROC_AUC":roc_auc(y_all,pc_all),
            "R3_average_precision":average_precision(y_all,p3_all),
            "C_average_precision":average_precision(y_all,pc_all)
          },
          "graph_empty_support":{
            "empty_cells":empty_count,
            "empty_fraction":empty_count/325954,
            "nonempty_cells":325954-empty_count,
            "empty_cell_mean_C_minus_R3":mean(empty_delta),
            "nonempty_cell_mean_C_minus_R3":mean(nonempty_delta),
            "block_empty_fraction_vs_C_minus_R3_spearman_rho":empty_rho,
            "empty_fraction_quartiles":empty_quartiles
          },
          "interpretation":{
            "primary_status_changed":False,
            "main_behavior":"C improves the prevalence-weighted primary mainly by lowering loss for true absences; true-presence log loss is worse under C",
            "sentinel_artifact_interpretation":"the gain is not created by graph-empty sentinel rows: C-minus-R3 is much more negative in graph-source-nonempty cells, and blocks with more graph-empty cells show weaker C advantage",
            "ecological_wording":"graph-path source topology acts primarily as an exclusion or occupancy-constraint filter in this sparse occurrence matrix, reducing overprediction of nonoccurrence-prone island-species cells rather than increasing probability assigned to realized presences"
          },
          "posthoc":True,
          "may_change_primary_status":False,
          "counts_as_confirmatory_evidence":False,
          "fresh_system_denominator_contribution":0
        }

        a.block_output.parent.mkdir(parents=True,exist_ok=True)
        with a.block_output.open("w",encoding="utf-8",newline="") as h:
            fields=list(block_rows[0])
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(block_rows)
        result["block_table_sha256"]=sha(a.block_output)
        a.result.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True));return 0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        out={"schema":"structural.global_mammals_prediction_behavior_result.v1_84","status":"STOP","reason":str(e),"posthoc":True,"may_change_primary_status":False,"counts_as_confirmatory_evidence":False}
        a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print(json.dumps(out,indent=2,sort_keys=True));return 2

if __name__=="__main__":raise SystemExit(main())
