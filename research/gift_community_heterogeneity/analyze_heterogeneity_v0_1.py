#!/usr/bin/env python3
"""Exploratory heterogeneity audit of the frozen GIFT community one-shot.

This script uses only the archived one-shot response artifact plus a replay of
the already-frozen predictor panel/protocol. It performs no GIFT checklist
request and cannot rescue or modify H1/H3.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

CLADES=("Angiospermae","Pteridophyta","Gymnospermae")
CLIMATE_MAP={
    "bio1":"wc2.0_bio_30s_01",
    "bio5":"wc2.0_bio_30s_05",
    "bio6":"wc2.0_bio_30s_06",
    "bio12":"wc2.0_bio_30s_12",
    "bio15":"wc2.0_bio_30s_15",
}
EXPECTED_PANEL="7d8c01f6dd36f479106f669f11c0c46aa0c3ff245874b99416f4ad3440393b7b"
EXPECTED_PROTOCOL="6529dbd74d845dfdbecf614177376c80d690445f4cf6f9eb8c5fb654c03f54e1"
EXPECTED_OUTCOME="939c6492748f50db80be59eb0ef112fe092479f62d8d57e5157f0c9b6edcbde5"
EXPECTED_RAW_SHA="5b5404c80da580f06f3cc21a53be7be080aebbb84d28cc46a1615119666cbf80"
EXPECTED_RICHNESS_SHA="5366f662580f17ce93861013773734816303fc18bd7298383ab13dacf5d01af6"
EXPECTED_H1_BOOT_SHA="bfebf4a229903fef83f9479c388ed3bb98ede5b47876bf42bb49ded054203fdf"
EXPECTED_H3_BOOT_SHA="9d348213e513133a91ee6efc84fc118e09cdc2f33fd87fb520a174904fb319b2"

def sha(value)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path:Path)->dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"{path} must contain JSON object")
    return value

def as01(value):
    try:
        return int(float(value))
    except (TypeError,ValueError):
        return None

def raw_predictors(island):
    climate=island["climate"]
    return {
        "bio1":float(climate[CLIMATE_MAP["bio1"]]),
        "bio5":float(climate[CLIMATE_MAP["bio5"]]),
        "bio6":float(climate[CLIMATE_MAP["bio6"]]),
        "bio12":float(climate[CLIMATE_MAP["bio12"]]),
        "bio15":float(climate[CLIMATE_MAP["bio15"]]),
        "log_area":math.log(max(float(island["area_km2"]),1e-12)),
        "log1p_dist":math.log1p(float(island["dist_km"])),
        "SLMP":float(island["SLMP"]),
        "GMMC":float(island["GMMC"]),
        "log1p_nearest_other":math.log1p(float(island["nearest_other_island_km"])),
        "surrounding_island_pressure":float(island["surrounding_island_pressure"]),
        "surrounding_landmass_pressure":float(island["surrounding_landmass_pressure"]),
        "step_isolation_gain_log":float(island["step_isolation_gain_log"]),
        "extreme":float(bool(island["extreme_q75"])),
    }

def read_archived_response(raw_path:Path,panel):
    present=defaultdict(set)
    uncertain=defaultdict(set)
    canonical=[]
    with raw_path.open(encoding="utf-8",newline="") as handle:
        rows=csv.DictReader(handle)
        expected={"clade","list_ID","entity_ID","work_ID","native","questionable","quest_native"}
        if set(rows.fieldnames or [])!=expected:
            raise RuntimeError(f"unexpected raw-response columns: {rows.fieldnames}")
        for row in rows:
            clade=row["clade"]
            if clade not in CLADES:
                raise RuntimeError(f"unexpected clade {clade}")
            lid=str(int(float(row["list_ID"])))
            eid=str(int(float(row["entity_ID"])))
            wid=str(int(float(row["work_ID"])))
            native=as01(row["native"])
            questionable=as01(row["questionable"])
            quest_native=as01(row["quest_native"])
            canonical.append((clade,lid,eid,wid,native,questionable,quest_native))
            if native==1 and questionable!=1 and quest_native!=1:
                present[(clade,eid)].add(wid)
            elif native==1:
                uncertain[(clade,eid)].add(wid)
    canonical.sort(key=lambda r:(r[0],int(r[1]),int(r[2]),int(r[3])))
    if sha(canonical)!=EXPECTED_RAW_SHA:
        raise RuntimeError("archived raw response fingerprint drift")

    island_ids={
        str(island["entity_ID"])
        for group in panel["groups"] for island in group["islands"]
    }
    richness={}
    for clade in CLADES:
        for eid in island_ids:
            p=present[(clade,eid)]
            u=uncertain[(clade,eid)]-p
            richness[(clade,eid)]={
                "richness":len(p),
                "uncertain_only_work_ids":len(u),
            }
    richness_rows=sorted(
        [
            {"clade":clade,"entity_ID":eid,**value}
            for (clade,eid),value in richness.items()
        ],
        key=lambda row:(row["clade"],int(row["entity_ID"])),
    )
    if sha(richness_rows)!=EXPECTED_RICHNESS_SHA:
        raise RuntimeError("reconstructed richness fingerprint drift")
    return richness, canonical, richness_rows

def build_model_rows(panel,protocol,richness,outcome):
    scaling=protocol["predictor_semantics"]["frozen_continuous_scaling"]
    island_scaling={k:v for k,v in scaling.items() if k!="log1p_list_count_by_clade"}
    list_scaling=scaling["log1p_list_count_by_clade"]
    expected_response_scaling=outcome["richness"]["analysis_response_scaling_by_clade"]

    rows={clade:[] for clade in CLADES}
    for group in panel["groups"]:
        arch=group["archipelago_id"]
        for island in group["islands"]:
            eid=str(island["entity_ID"])
            raw=raw_predictors(island)
            scaled=dict(raw)
            for col,spec in island_scaling.items():
                scaled[col]=(float(raw[col])-float(spec["mean"]))/float(spec["sd"])
            for clade in CLADES:
                list_count=len(island["list_ids"][clade])
                ls=list_scaling[clade]
                r=richness[(clade,eid)]["richness"]
                row={
                    "archipelago_id":arch,
                    "entity_ID":eid,
                    "clade":clade,
                    **scaled,
                    "log1p_list_count":(
                        math.log1p(list_count)-float(ls["mean"])
                    )/float(ls["sd"]),
                    "y_log":math.log1p(int(r)),
                }
                row["step_gain_x_extreme"]=row["step_isolation_gain_log"]*row["extreme"]
                rows[clade].append(row)

    for clade in CLADES:
        vals=np.asarray([r["y_log"] for r in rows[clade]],dtype=float)
        mu=float(vals.mean()); sd=float(vals.std(ddof=0))
        exp=expected_response_scaling[clade]
        if abs(mu-float(exp["log1p_mean"]))>1e-12 or abs(sd-float(exp["log1p_sd"]))>1e-12:
            raise RuntimeError(f"{clade}: response scaling drift")
        for row in rows[clade]:
            row["y"]=(row["y_log"]-mu)/sd
    return rows

def weighted_blocks(rows,columns):
    X=np.asarray([[row[c] for c in columns] for row in rows],dtype=float)
    y=np.asarray([row["y"] for row in rows],dtype=float)
    groups=defaultdict(list)
    for i,row in enumerate(rows):
        groups[row["archipelago_id"]].append(i)
    Xc=X.copy(); yc=y.copy(); weights=np.zeros(len(rows),dtype=float)
    for idxs in groups.values():
        idx=np.asarray(idxs,dtype=int)
        Xc[idx,:]-=X[idx,:].mean(axis=0,keepdims=True)
        yc[idx]-=y[idx].mean()
        weights[idx]=1.0/len(idxs)
    root=np.sqrt(weights)
    Xw=Xc*root[:,None]; yw=yc*root
    if np.linalg.matrix_rank(Xw,tol=1e-10)!=Xw.shape[1]:
        raise RuntimeError("full weighted design lost rank")
    blocks={}
    for arch,idxs in groups.items():
        idx=np.asarray(idxs,dtype=int)
        blocks[arch]=(Xw[idx,:],yw[idx])
    return blocks

def beta(X,y):
    b,_,rank,_=np.linalg.lstsq(X,y,rcond=None)
    if rank!=X.shape[1]:
        raise RuntimeError("rank failure in exploratory replay")
    return b

def fit_from_blocks(blocks,columns,target,archipelagos):
    X=np.vstack([blocks[a][0] for a in archipelagos])
    y=np.concatenate([blocks[a][1] for a in archipelagos])
    if np.linalg.matrix_rank(X,tol=1e-10)!=X.shape[1]:
        return None
    return float(beta(X,y)[columns.index(target)])

def full_estimates(protocol,blocks):
    archs=protocol["model"]["bootstrap_design"]["archipelagos"]
    cols=protocol["H1_primary"]["per_clade_model_columns"]
    target=protocol["H1_primary"]["per_clade_target_column"]
    comp={
        clade:fit_from_blocks(blocks[clade],cols[clade],target,archs)
        for clade in CLADES
    }
    if any(v is None for v in comp.values()):
        raise RuntimeError("full fit became non-estimable")
    h1=sum(comp.values())/3.0
    h3=comp["Pteridophyta"]-(comp["Angiospermae"]+comp["Gymnospermae"])/2.0
    return comp,float(h1),float(h3)

def replay_bootstrap(protocol,blocks):
    frozen=protocol["model"]["bootstrap_design"]
    archs=frozen["archipelagos"]
    reps=int(frozen["accepted_replicates"])
    rng=np.random.default_rng(int(frozen["seed"]))
    cols=protocol["H1_primary"]["per_clade_model_columns"]
    target=protocol["H1_primary"]["per_clade_target_column"]
    accepted=[]; h1=[]; h3=[]; cb={clade:[] for clade in CLADES}
    attempted=0
    while len(accepted)<reps and attempted<reps*10:
        attempted+=1
        draw=[archs[int(i)] for i in rng.integers(0,len(archs),size=len(archs))]
        values={}
        valid=True
        for clade in CLADES:
            v=fit_from_blocks(blocks[clade],cols[clade],target,draw)
            if v is None:
                valid=False; break
            values[clade]=v
        if not valid:
            continue
        accepted.append(draw)
        for clade in CLADES:
            cb[clade].append(values[clade])
        h1.append(sum(values.values())/3.0)
        h3.append(values["Pteridophyta"]-(values["Angiospermae"]+values["Gymnospermae"])/2.0)

    if len(accepted)!=reps or attempted!=int(frozen["candidate_draws_attempted"]):
        raise RuntimeError("frozen bootstrap replay count drift")
    if sha(accepted)!=frozen["accepted_draws_sha256"]:
        raise RuntimeError("frozen bootstrap draw SHA drift")
    if sha(h1)!=EXPECTED_H1_BOOT_SHA or sha(h3)!=EXPECTED_H3_BOOT_SHA:
        raise RuntimeError("frozen bootstrap estimate SHA drift")
    return cb,h1,h3

def quantiles(x,ps=(0.025,0.25,0.5,0.75,0.975)):
    a=np.asarray(x,dtype=float)
    q=np.quantile(a,ps,method="linear")
    return {str(p):float(v) for p,v in zip(ps,q)}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--lock",type=Path,required=True)
    ap.add_argument("--raw-response",type=Path,required=True)
    ap.add_argument("--outcome",type=Path,required=True)
    args=ap.parse_args()

    panel=load(args.panel); protocol=load(args.protocol); lock=load(args.lock); outcome=load(args.outcome)
    if panel["panel_fingerprint"]!=EXPECTED_PANEL or lock["panel_fingerprint"]!=EXPECTED_PANEL:
        raise RuntimeError("panel fingerprint drift")
    if protocol["protocol_fingerprint"]!=EXPECTED_PROTOCOL or lock["protocol_fingerprint"]!=EXPECTED_PROTOCOL:
        raise RuntimeError("protocol fingerprint drift")
    if outcome["outcome_fingerprint"]!=EXPECTED_OUTCOME:
        raise RuntimeError("one-shot outcome fingerprint drift")
    if outcome["panel_fingerprint"]!=EXPECTED_PANEL or outcome["protocol_fingerprint"]!=EXPECTED_PROTOCOL:
        raise RuntimeError("outcome is not from frozen final design")
    if outcome["H2"]["status"]!="NOT_TESTED_TERMINAL_PRE_RESPONSE_NON_ESTIMABLE":
        raise RuntimeError("H2 boundary drift")

    richness,raw_rows,richness_rows=read_archived_response(args.raw_response,panel)
    rows=build_model_rows(panel,protocol,richness,outcome)
    cols=protocol["H1_primary"]["per_clade_model_columns"]
    blocks={clade:weighted_blocks(rows[clade],cols[clade]) for clade in CLADES}
    comp,h1,h3=full_estimates(protocol,blocks)

    if abs(h1-float(outcome["H1_primary"]["estimate"]))>1e-12:
        raise RuntimeError("H1 point estimate failed exact replay")
    if abs(h3-float(outcome["H3_primary"]["estimate"]))>1e-12:
        raise RuntimeError("H3 point estimate failed exact replay")
    for clade in CLADES:
        if abs(comp[clade]-float(outcome["H1_primary"]["clade_component_estimates"][clade]))>1e-12:
            raise RuntimeError(f"{clade} point estimate failed exact replay")

    cb,h1boot,h3boot=replay_bootstrap(protocol,blocks)
    h1ci=np.quantile(np.asarray(h1boot),[0.025,0.975],method="linear")
    h3ci=np.quantile(np.asarray(h3boot),[0.025,0.975],method="linear")
    if max(abs(float(h1ci[i])-float(outcome["H1_primary"]["bootstrap_95_ci"][i])) for i in (0,1))>1e-12:
        raise RuntimeError("H1 interval failed exact replay")
    if max(abs(float(h3ci[i])-float(outcome["H3_primary"]["bootstrap_95_ci"][i])) for i in (0,1))>1e-12:
        raise RuntimeError("H3 interval failed exact replay")

    archs=protocol["model"]["bootstrap_design"]["archipelagos"]
    group_meta={g["archipelago_id"]:g for g in panel["groups"]}
    loo=[]
    for omitted in archs:
        keep=[a for a in archs if a!=omitted]
        c={}
        valid=True
        for clade in CLADES:
            v=fit_from_blocks(blocks[clade],cols[clade],protocol["H1_primary"]["per_clade_target_column"],keep)
            if v is None:
                valid=False; break
            c[clade]=v
        g=group_meta[omitted]
        extreme=int(g["extreme_islands"]); n=int(g["n_islands"])
        item={
            "archipelago":omitted,
            "n_islands":n,
            "extreme_islands":extreme,
            "nonextreme_islands":n-extreme,
            "regime_class":"mixed" if 0<extreme<n else "all_extreme" if extreme==n else "nonextreme_only",
            "mean_step_isolation_gain":float(np.mean([float(i["step_isolation_gain_log"]) for i in g["islands"]])),
            "estimable_after_omission":valid,
        }
        if valid:
            lh1=sum(c.values())/3.0
            lh3=c["Pteridophyta"]-(c["Angiospermae"]+c["Gymnospermae"])/2.0
            item.update({
                "H1_leave_one_out":float(lh1),
                "H1_shift_from_full":float(lh1-h1),
                "H3_leave_one_out":float(lh3),
                "H3_shift_from_full":float(lh3-h3),
                "clade_leave_one_out":{k:float(v) for k,v in c.items()},
                "clade_shift_from_full":{k:float(c[k]-comp[k]) for k in CLADES},
            })
        loo.append(item)

    valid=[x for x in loo if x["estimable_after_omission"]]
    top_h1=sorted(valid,key=lambda x:abs(x["H1_shift_from_full"]),reverse=True)
    top_h3=sorted(valid,key=lambda x:abs(x["H3_shift_from_full"]),reverse=True)
    by_regime=defaultdict(list)
    for x in valid:
        by_regime[x["regime_class"]].append(abs(x["H1_shift_from_full"]))

    richness_by_clade={}
    for clade in CLADES:
        vals=[richness[(clade,str(i["entity_ID"]))]["richness"] for g in panel["groups"] for i in g["islands"]]
        richness_by_clade[clade]={
            "zero_rows":sum(v==0 for v in vals),
            "median":float(np.median(vals)),
            "mean":float(np.mean(vals)),
            "max":int(max(vals)),
        }

    out={
        "schema":"structural.gift_community_heterogeneity.v0_1",
        "status":"EXPLORATORY_AFTER_FROZEN_ONE_SHOT",
        "source":{
            "artifact_id":10804663234,
            "workflow_run_id":35992977691,
            "artifact_zip_sha256":"c666c58a920e34ee72fae695f4a74691294dd4ed169a1e9121e95aa9a3b78ae7",
            "outcome_fingerprint":EXPECTED_OUTCOME,
            "panel_fingerprint":EXPECTED_PANEL,
            "protocol_fingerprint":EXPECTED_PROTOCOL,
        },
        "evidence_boundary":{
            "new_response_queries":0,
            "uses_archived_one_shot_only":True,
            "confirmatory_H1_H3_unchanged":True,
            "cannot_rescue_confirmatory_results":True,
            "H2_reintroduced":False,
        },
        "exact_replay":{
            "H1":float(h1),
            "H3":float(h3),
            "clade_H1":{k:float(v) for k,v in comp.items()},
            "bootstrap_H1_sha256":sha(h1boot),
            "bootstrap_H3_sha256":sha(h3boot),
        },
        "bootstrap_directional_stability":{
            "H1_fraction_gt_zero":float(np.mean(np.asarray(h1boot)>0)),
            "H1_fraction_lt_zero":float(np.mean(np.asarray(h1boot)<0)),
            "H1_quantiles":quantiles(h1boot),
            "H3_fraction_lt_zero":float(np.mean(np.asarray(h3boot)<0)),
            "H3_fraction_gt_zero":float(np.mean(np.asarray(h3boot)>0)),
            "H3_quantiles":quantiles(h3boot),
            "clade_fraction_gt_zero":{
                clade:float(np.mean(np.asarray(cb[clade])>0)) for clade in CLADES
            },
        },
        "leave_one_archipelago_out":{
            "n_archipelagos":len(archs),
            "estimable_omissions":len(valid),
            "H1_positive_omissions":sum(x["H1_leave_one_out"]>0 for x in valid),
            "H1_negative_omissions":sum(x["H1_leave_one_out"]<0 for x in valid),
            "H1_min":min(x["H1_leave_one_out"] for x in valid),
            "H1_max":max(x["H1_leave_one_out"] for x in valid),
            "H3_negative_omissions":sum(x["H3_leave_one_out"]<0 for x in valid),
            "H3_positive_omissions":sum(x["H3_leave_one_out"]>0 for x in valid),
            "H3_min":min(x["H3_leave_one_out"] for x in valid),
            "H3_max":max(x["H3_leave_one_out"] for x in valid),
            "mean_abs_H1_shift_by_regime":{
                k:float(np.mean(v)) for k,v in sorted(by_regime.items())
            },
            "top_H1_influence":top_h1[:8],
            "top_H3_influence":top_h3[:8],
            "all_archipelagos":loo,
        },
        "panel_support":{
            "all_extreme_archipelagos":sum(x["regime_class"]=="all_extreme" for x in loo),
            "mixed_archipelagos":sum(x["regime_class"]=="mixed" for x in loo),
            "nonextreme_only_archipelagos":sum(x["regime_class"]=="nonextreme_only" for x in loo),
            "richness_by_clade":richness_by_clade,
        },
    }
    out["exploratory_fingerprint"]=sha(out)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
