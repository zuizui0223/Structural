#!/usr/bin/env python3
"""v1.226: retrospective LOSO ring-neighborhood forecast of *sample* redetection.

No prey variable (original dilution method not yet verified), no individual
movement observation, no true colonization, no confirmatory inference.
"""
import argparse
import json
import math
import random
from collections import defaultdict,Counter
from pathlib import Path
from hopson_temporal_detection_audit_v1_222 import (
    download_locked,layout_index,rows_locked,OBS_HEADER,intish,optional_count
)

FEATURE_REFERENCE=(
    "log_zero_run","day_over_81","metapop_positive_fraction",
    "log1p_other_source_counts","nearest_positive_ring_distance_over_8",
    "sample_volume","assigned_small_world","time_block_2")
FEATURE_ADDITIONS=("ring_one_step_positive_count","ring_two_step_positive_count")
SCHEMA="structural.hopson_ring_geometric_increment.v1_226"
SEED=20261010
BOOT=2000

def ring_distance(a,b,n=15):
    if not(1<=a<=n and 1<=b<=n):raise ValueError("Bad ring patch index")
    delta=abs(a-b)
    return min(delta,n-delta)

def neighbors(positive,target,n=15):
    others=[k for k,v in positive.items() if k!=target and v]
    return {
        "nearest":min((ring_distance(target,k,n) for k in others),default=8),
        "one":sum(ring_distance(target,k,n)==1 for k in others),
        "two":sum(ring_distance(target,k,n)==2 for k in others),
        "total":len(others)
    }

def rows_from_pinned(raw_obs,raw_layout):
    layout=layout_index(raw_layout)
    day_table=defaultdict(dict)
    count_rows=0
    for row in rows_locked(raw_obs,OBS_HEADER):
        jar=intish(row["jar.no"],"jar")
        if jar not in layout:raise ValueError("Source jar absent from pinned layout")
        meta,patch,trt,block=layout[jar]
        day=intish(row["day"],"day")
        vol=float(row["samp.vol"])
        count=optional_count(row["eupl"],"eupl")
        if not math.isfinite(vol) or vol<=0 or count is None:
            raise ValueError("Unexpected unusable sample; never impute zero")
        if patch in day_table[(meta,day)]:
            raise ValueError("duplicate metapop/patch/day")
        day_table[(meta,day)][patch]=(count,vol,trt,block)
        count_rows+=1
    if count_rows!=4830 or len(day_table)!=14*23:
        raise ValueError("Original 14x15x23 sample support changed")
    for panel in day_table.values():
        if set(panel)!=set(range(1,16)):
            raise ValueError("A complete contemporaneous source map is required")
    result=[]
    for meta in range(1,15):
        dates=sorted(day for m,day in day_table if m==meta)
        if len(dates)!=23:raise ValueError("Missing visit")
        streak={p:0 for p in range(1,16)}
        for i,day in enumerate(dates):
            state=day_table[(meta,day)]
            positive={p:int(state[p][0]>0) for p in range(1,16)}
            if i<22:
                nextday=dates[i+1]
                future=day_table[(meta,nextday)]
                for patch in range(1,16):
                    count,volume,trt,block=state[patch]
                    if count>0: continue
                    n=neighbors(positive,patch)
                    other_sum=sum(state[p][0] for p in range(1,16) if p!=patch)
                    vec=[
                        math.log1p(streak[patch]+1),
                        day/81.0,
                        n["total"]/14,
                        math.log1p(other_sum),
                        n["nearest"]/8,
                        volume,
                        int(trt=="sw"),
                        int(block==2)
                    ]
                    add=[n["one"],n["two"]]
                    result.append({
                        "meta":meta,"day":day,"nextday":nextday,
                        "y":int(future[patch][0]>0),
                        "reference":vec,
                        "candidate":vec+add,
                        "streak_before_prediction":streak[patch]+1,
                    })
            for p in range(1,16):
                streak[p]=streak[p]+1 if state[p][0]==0 else 0
    if len(result)!=sum(1 for rec in result if rec["y"] in (0,1)):
        raise ValueError("unscorable target labels")
    return result

def score(data):
    try:
        import numpy as np
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
    except ImportError as e:
        raise RuntimeError("Requires pinned sklearn and numpy runtime") from e
    folds=[]
    for m in range(1,15):
        tr=[r for r in data if r["meta"]!=m]
        te=[r for r in data if r["meta"]==m]
        if not tr or not te or {x["y"] for x in tr}!={0,1}:
            raise ValueError("Insufficient heldout metapop support")
        fold={"metapopulation":m,"test_rows":len(te),
              "test_redetections":sum(x["y"] for x in te)}
        for name in ("reference","candidate"):
            X=np.asarray([x[name] for x in tr],dtype=float)
            y=np.asarray([x["y"] for x in tr],dtype=int)
            XT=np.asarray([x[name] for x in te],dtype=float)
            if not(np.isfinite(X).all() and np.isfinite(XT).all()):
                raise ValueError("Invalid predictor")
            model=make_pipeline(StandardScaler(),LogisticRegression(
                C=1.0,solver="liblinear",max_iter=2000,random_state=SEED))
            model.fit(X,y)
            prob=np.clip(model.predict_proba(XT)[:,1],1e-12,1-1e-12)
            yt=np.asarray([x["y"] for x in te],dtype=int)
            loss=float(np.mean(-yt*np.log(prob)-(1-yt)*np.log(1-prob)))
            fold[f"{name}_test_logloss"]=loss
        fold["increment_candidate_minus_reference"]=(
            fold["candidate_test_logloss"]-fold["reference_test_logloss"])
        folds.append(fold)
    point=sum(x["increment_candidate_minus_reference"] for x in folds)/len(folds)
    rng=random.Random(SEED)
    null=[]
    for i in range(BOOT):
        sample=rng.choices(range(len(folds)),k=len(folds))
        null.append(sum(folds[k]["increment_candidate_minus_reference"] for k in sample)/len(sample))
    null.sort()
    return {
        "schema":SCHEMA,
        "status":"POSTPUBLICATION_RETROSPECTIVE_LOSO_REDETECTION_PREDICTIVE_AUDIT",
        "n_source_metapopulations":14,
        "n_zero_start_transition_rows":len(data),
        "n_zero_to_positive_redetections":sum(x["y"] for x in data),
        "reference_columns":list(FEATURE_REFERENCE),
        "candidate_only_columns":list(FEATURE_ADDITIONS),
        "model":"StandardScaler (training only) then L2 LogisticRegression(C=1.0,liblinear), fixed, no tune",
        "unit_of_out_of_sample_heldout":"entire metapopulation, 14 disjoint folds",
        "folds":folds,
        "equal_metapopulation_C_minus_R_loss":point,
        "descriptive_2000_cluster_bootstrap_2_5_97_5":[null[int(.025*(BOOT-1))],null[int(.975*(BOOT-1))]],
        "bootstrap_is_posthoc_descriptive_not_confirmatory":True,
        "forecast_target":"observed sample zero at visit t, positive sample next visit, NOT true colonization",
        "predictors_are_all_at_t_or_earlier":True,
        "no_lookahead_tplus1_other_patch_labels":True,
        "source_network_semantics":"observed 15-patch ring-nearest geometry, NOT realized migrants/transport",
        "original_prey_not_used_unverified_dilution":True,
        "not_reference_R3_ecological_adequacy_claim":True,
        "no_cross_system_replication":True,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    ans=score(rows_from_pinned(download_locked("observations"),
                               download_locked("layout")))
    if ans["n_zero_to_positive_redetections"]!=554:
        raise ValueError("v1.222 event count source drift")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(ans,indent=2,sort_keys=True)+"\n")
    print(json.dumps(ans,sort_keys=True))

if __name__=="__main__":main()
