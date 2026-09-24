#!/usr/bin/env python3
"""Freeze the final H1/H3-only GIFT community protocol before response access.

H2 is terminally non-estimable from response-blind design checks and is not
tested in this dataset. H1 and H3 are unchanged from the first scale-free
step-isolation protocol that made them estimable.
"""
from __future__ import annotations

import argparse, hashlib, json, math
from pathlib import Path
import numpy as np

CLADES=("Angiospermae","Pteridophyta","Gymnospermae")
REFERENCE_COLS=(
    "bio1","bio5","bio6","bio12","bio15",
    "log_area","log1p_dist","SLMP","GMMC",
    "log1p_nearest_other","surrounding_island_pressure","surrounding_landmass_pressure",
    "log1p_list_count",
)
MAX_CONDITION=1e8
BOOTSTRAP_REPS=10000
BOOTSTRAP_SEED=20260924

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path):
    x=json.loads(Path(path).read_text())
    if not isinstance(x,dict):raise RuntimeError(f"{path} must contain object")
    return x

def raw_predictors(island):
    clim=island["climate"]
    return {
        "bio1":float(clim["wc2.0_bio_30s_01"]),
        "bio5":float(clim["wc2.0_bio_30s_05"]),
        "bio6":float(clim["wc2.0_bio_30s_06"]),
        "bio12":float(clim["wc2.0_bio_30s_12"]),
        "bio15":float(clim["wc2.0_bio_30s_15"]),
        "log_area":math.log(max(float(island["area_km2"]),1e-12)),
        "log1p_dist":math.log1p(float(island["dist_km"])),
        "SLMP":float(island["SLMP"]),
        "GMMC":float(island["GMMC"]),
        "log1p_nearest_other":math.log1p(float(island["nearest_other_island_km"])),
        "surrounding_island_pressure":float(island["surrounding_island_pressure"]),
        "surrounding_landmass_pressure":float(island["surrounding_landmass_pressure"]),
    }

def group_indices(rows):
    groups={}
    for i,row in enumerate(rows):
        groups.setdefault((row["archipelago_id"],row["clade"]),[]).append(i)
    return groups

def matrix_audit(rows,columns):
    arr=np.asarray([[row[c] for c in columns] for row in rows],dtype=float)
    out=arr.copy()
    groups=group_indices(rows)
    weights=np.zeros(len(rows),dtype=float)
    for idxs in groups.values():
        idx=np.asarray(idxs,dtype=int)
        out[idx,:]-=arr[idx,:].mean(axis=0,keepdims=True)
        weights[idx]=1.0/len(idxs)
    keep=np.std(out,axis=0)>1e-12
    kept=[c for c,k in zip(columns,keep) if k]
    dropped=[c for c,k in zip(columns,keep) if not k]
    X=out[:,keep]
    Xw=X*np.sqrt(weights)[:,None]
    if Xw.shape[1]==0:
        return {"rows":len(rows),"columns":[],"dropped_constant":dropped,"rank":0,"n_columns":0,"condition":None,"full_rank":False}
    rank=int(np.linalg.matrix_rank(Xw,tol=1e-10))
    sv=np.linalg.svd(Xw,compute_uv=False)
    condition=float(sv[0]/sv[-1]) if sv[-1]>1e-15 else float("inf")
    return {
        "rows":len(rows),"columns":kept,"dropped_constant":dropped,
        "rank":rank,"n_columns":int(Xw.shape[1]),"condition":condition,
        "full_rank":rank==Xw.shape[1],
        "archipelago_total_weight":"1.0 per archipelago within clade",
    }

def demeaned_design(rows,columns):
    arr=np.asarray([[row[c] for c in columns] for row in rows],dtype=float)
    out=arr.copy()
    groups=group_indices(rows)
    weights=np.zeros(len(rows),dtype=float)
    for idxs in groups.values():
        idx=np.asarray(idxs,dtype=int)
        out[idx,:]-=arr[idx,:].mean(axis=0,keepdims=True)
        weights[idx]=1.0/len(idxs)
    keep=np.std(out,axis=0)>1e-12
    kept=[c for c,k in zip(columns,keep) if k]
    weighted=out[:,keep]*np.sqrt(weights)[:,None]
    return weighted, kept, [row["archipelago_id"] for row in rows]

def freeze_bootstrap_draws(rows,h1_cols,clade_audits):
    archipelagos=sorted({row["archipelago_id"] for row in rows})
    by_clade={}
    for clade in CLADES:
        sub=[row for row in rows if row["clade"]==clade]
        X,kept,labels=demeaned_design(sub,h1_cols)
        if kept!=clade_audits[clade]["columns"]:
            raise RuntimeError(f"design-column replay drift for {clade}")
        blocks={}
        for arch in archipelagos:
            idx=[i for i,label in enumerate(labels) if label==arch]
            blocks[arch]=X[np.asarray(idx,dtype=int),:]
        by_clade[clade]=blocks

    rng=np.random.default_rng(BOOTSTRAP_SEED)
    accepted=[]
    attempted=0
    max_attempts=BOOTSTRAP_REPS*10
    while len(accepted)<BOOTSTRAP_REPS and attempted<max_attempts:
        attempted+=1
        draw=[archipelagos[int(i)] for i in rng.integers(0,len(archipelagos),size=len(archipelagos))]
        valid=True
        for clade in CLADES:
            X=np.vstack([by_clade[clade][arch] for arch in draw])
            if np.linalg.matrix_rank(X,tol=1e-10)!=X.shape[1]:
                valid=False
                break
        if valid:
            accepted.append(draw)
    if len(accepted)!=BOOTSTRAP_REPS:
        raise RuntimeError(
            f"could freeze only {len(accepted)} full-rank bootstrap draws after {attempted} attempts"
        )
    return {
        "archipelagos":archipelagos,
        "requested_replicates":BOOTSTRAP_REPS,
        "accepted_replicates":len(accepted),
        "candidate_draws_attempted":attempted,
        "rank_filter":"accept a response-independent whole-archipelago resample only when the frozen H1 design is full column rank for all three clade-specific models",
        "rng":"numpy.default_rng(PCG64)",
        "seed":BOOTSTRAP_SEED,
        "accepted_draws_sha256":sha(accepted),
        "accepted_draws_replay_rule":"re-run the exact candidate-draw sequence from the frozen seed and predictor-only rank filter; use the first 10,000 accepted draws in order",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--prior-exclusions",type=Path,required=True)
    ap.add_argument("--h2-terminal",type=Path,required=True)
    a=ap.parse_args()

    panel=load(a.panel); prior=load(a.prior_exclusions); h2=load(a.h2_terminal)

    if panel.get("schema")!="structural.gift_community_topology_panel.v0_2":
        raise RuntimeError("unexpected panel schema")
    if panel.get("response_values_accessed") is not False or panel.get("species_composition_endpoint_called") is not False:
        raise RuntimeError("community response already opened")
    if tuple(panel.get("targets",()))!=CLADES:
        raise RuntimeError("clade set drift")
    if any(v.get("opened") for v in panel["response_surfaces"].values()):
        raise RuntimeError("a response surface is already marked opened")
    if prior.get("response_values_used") is not False:
        raise RuntimeError("prior pilot responses entered predictor design")
    if h2.get("status")!="H2_TERMINAL_PRE_RESPONSE_NON_ESTIMABLE":
        raise RuntimeError("H2 terminal boundary missing")
    if h2.get("response_values_accessed") is not False:
        raise RuntimeError("H2 boundary is post-response")
    if h2.get("panel_fingerprint")!=panel["panel_fingerprint"]:
        raise RuntimeError("H2 boundary panel drift")
    if h2["terminal_boundary"].get("H1_H3_may_proceed_under_unchanged_pre_response_definitions") is not True:
        raise RuntimeError("H1/H3 continuation not authorized by H2 terminal boundary")

    unique=[]
    for g in panel["groups"]:
        for island in g["islands"]:
            p=raw_predictors(island)
            unique.append({
                "archipelago_id":g["archipelago_id"],
                "entity_ID":str(island["entity_ID"]),
                **p,
                "step_isolation_gain_log":float(island["step_isolation_gain_log"]),
                "extreme":float(bool(island["extreme_q75"])),
            })

    continuous=[
        "bio1","bio5","bio6","bio12","bio15",
        "log_area","log1p_dist","SLMP",
        "log1p_nearest_other","surrounding_island_pressure",
        "surrounding_landmass_pressure","step_isolation_gain_log",
    ]
    scaling={}
    for col in continuous:
        vals=np.asarray([row[col] for row in unique],dtype=float)
        mu=float(vals.mean()); sd=float(vals.std(ddof=0))
        if sd<=1e-12:raise RuntimeError(f"globally constant predictor: {col}")
        scaling[col]={"mean":mu,"sd":sd}
        for row in unique:row[col]=(row[col]-mu)/sd

    rows=[]
    for base in unique:
        for clade in CLADES:
            island_source=next(
                island for g in panel["groups"]
                if g["archipelago_id"]==base["archipelago_id"]
                for island in g["islands"]
                if str(island["entity_ID"])==base["entity_ID"]
            )
            list_count=len(island_source["list_ids"][clade])
            if list_count < 1:
                raise RuntimeError(f"empty frozen list surface for {base['entity_ID']} {clade}")
            row={
                **base,
                "clade":clade,
                "log1p_list_count":math.log1p(list_count),
            }
            row["step_gain_x_extreme"]=row["step_isolation_gain_log"]*row["extreme"]
            rows.append(row)

    # Checklist union effort is response-independent but clade-specific.
    list_scaling={}
    for clade in CLADES:
        subset=[row for row in rows if row["clade"]==clade]
        vals=np.asarray([row["log1p_list_count"] for row in subset],dtype=float)
        mu=float(vals.mean()); sd=float(vals.std(ddof=0))
        if sd<=1e-12:
            raise RuntimeError(f"log1p_list_count is constant within {clade}")
        list_scaling[clade]={"mean":mu,"sd":sd}
        for row in subset:
            row["log1p_list_count"]=(row["log1p_list_count"]-mu)/sd
    scaling["log1p_list_count_by_clade"]=list_scaling

    h1_cols=list(REFERENCE_COLS)+[
        "step_isolation_gain_log","extreme","step_gain_x_extreme"
    ]
    clade_audits={
        clade:matrix_audit([row for row in rows if row["clade"]==clade],h1_cols)
        for clade in CLADES
    }
    audits={"H1_by_clade":clade_audits}
    bootstrap_design=freeze_bootstrap_draws(rows,h1_cols,clade_audits)

    support=panel["support"]
    gates={
        "minimum_archipelagos":support["archipelagos"]>=10,
        "minimum_extreme_archipelagos":support["archipelagos_with_extreme"]>=5,
        "minimum_nonextreme_archipelagos":support["archipelagos_with_nonextreme"]>=5,
        "step_support_extreme":support["extreme_step_isolation_gain_nonzero_islands"]>=20,
        "step_support_nonextreme":support["nonextreme_step_isolation_gain_nonzero_islands"]>=20,
        "all_clade_H1_models_full_rank":all(
            audit["full_rank"] and audit["condition"]<=MAX_CONDITION
            for audit in clade_audits.values()
        ),
        "all_clade_H1_targets_retained":all(
            "step_gain_x_extreme" in audit["columns"]
            for audit in clade_audits.values()
        ),
        "bootstrap_draw_set_complete":bootstrap_design["accepted_replicates"]==BOOTSTRAP_REPS,
    }
    qualified=all(gates.values())

    protocol={
        "schema":"structural.gift_community_topology_protocol.v0_5",
        "status":"QUALIFIED_TO_OPEN_COMMUNITY_RESPONSE" if qualified else "STOP_PRE_RESPONSE_NON_ESTIMABLE",
        "study_family":"fresh community-level global island-biogeography study",
        "gift_version":"3.2",
        "clades":list(CLADES),
        "panel_fingerprint":panel["panel_fingerprint"],
        "prior_response_exclusion_receipt_sha256":sha(prior),
        "h2_terminal_receipt_sha256":sha(h2),
        "response_values_accessed":False,
        "response_surfaces":panel["response_surfaces"],
        "response_semantics":{
            "unit":"island x clade",
            "response":"native species richness = unique work_ID count with >=1 unambiguous native record across the frozen eligible list union",
            "unambiguous_native":"native=1 AND questionable!=1 AND quest_native!=1",
            "uncertain_records":"native rows with questionable=1 or quest_native=1 are excluded from richness",
            "duplicate_work_ID_across_lists":"count once per island x clade",
            "zero_richness":"allowed only when all frozen lists for that island x clade return zero unambiguous native work_IDs",
        },
        "predictor_semantics":{
            "reference_predictors":list(REFERENCE_COLS),
            "checklist_effort_control":"z-scored log1p number of frozen eligible list_IDs for each island x clade; metadata-only and fixed before response",
            "frozen_continuous_scaling":scaling,
            "step_isolation_gain_log":panel["step_isolation_gain_definition"],
            "extreme_isolation":panel["extreme_rule"],
            "fixed_effect_absorption":"demean outcome and each final design column within archipelago x clade",
            "interaction_order":"construct interactions after frozen continuous z-scaling, before fixed-effect demeaning",
        },
        "model":{
            "family":"archipelago-equal weighted least squares on log1p(native richness)",
            "hyperparameter_tuning":"none",
            "archipelago_fixed_intercepts":"within each clade model, absorbed by exact within-archipelago demeaning",
            "observation_weights":"within each clade, every island in archipelago g has weight 1/n_g so every archipelago contributes total weight 1 to the point estimate",
            "inference_unit":"archipelago",
            "bootstrap":"use the exact response-independent whole-archipelago draw sequence frozen below; every sampled archipelago copy retains total WLS weight 1 and is full-rank for all three clade models",
            "bootstrap_replicates":BOOTSTRAP_REPS,
            "bootstrap_seed":BOOTSTRAP_SEED,
            "bootstrap_design":bootstrap_design,
            "interval_quantiles":[0.025,0.975],
            "quantile_method":"numpy.quantile method=linear",
        },
        "H1_primary":{
            "per_clade_model_columns":{
                clade:clade_audits[clade]["columns"] for clade in CLADES
            },
            "per_clade_dropped_constant_columns":{
                clade:clade_audits[clade]["dropped_constant"] for clade in CLADES
            },
            "per_clade_target_column":"step_gain_x_extreme",
            "per_clade_estimand":"change in the richness association with standardized step-isolation gain in the global upper-25% mainland-isolation regime versus remaining islands, estimated separately with clade-specific reference slopes and archipelago fixed effects",
            "pooled_estimand":"equal-weight mean of the Angiospermae, Pteridophyta, and Gymnospermae per-clade target coefficients within each whole-archipelago bootstrap replicate",
            "prediction":"positive",
            "success_rule":"whole-archipelago bootstrap 95% interval for the equal-clade mean excludes 0 on the positive side",
            "clade_specific_coefficients":"reported as secondary components; none alone can rescue a failed equal-clade H1",
        },
        "H2":{
            "status":"TERMINAL_PRE_RESPONSE_NON_ESTIMABLE_NOT_TESTED",
            "terminal_receipt":"research/gift_community_topology/pre_response_h2_stop_v0_4.json",
            "claim":"none; geological-history moderation is not estimated from this dataset",
            "cannot_be_reintroduced_after_response":True,
        },
        "H3_primary":{
            "uses_same_per_clade_H1_models":True,
            "estimand":"Pteridophyta step_gain_x_extreme coefficient minus the equal-weight mean of Angiospermae and Gymnospermae coefficients within the same whole-archipelago bootstrap replicate",
            "prediction":"negative",
            "success_rule":"whole-archipelago bootstrap 95% interval excludes 0 on the negative side",
            "rationale":"clade-specific H1 fits allow climate, area, checklist effort and all other reference slopes to differ freely among clades; H3 compares only the frozen topology-by-extreme coefficient",
            "cannot_rescue_H1":True,
        },
        "pre_response_matrix_audits":audits,
        "pre_response_gates":gates,
        "max_condition_number":MAX_CONDITION,
        "pre_response_history":[
            {"version":"v0.1","result":"STOP","reason":"fixed-radius topology gain had zero support in all global-extreme islands","response_opened":False},
            {"version":"v0.2","result":"H1/H3 estimable; H2 STOP","reason":"GMMC H2 target constant","response_opened":False},
            {"version":"v0.3","result":"H1/H3 estimable; H2 STOP","reason":"direct island-type H2 aliased","response_opened":False},
            {"version":"v0.4","result":"H1/H3 estimable; H2 terminal STOP","reason":"cleaned-archipelago geology H2 remained non-estimable","response_opened":False},
            {"version":"v0.5-final","result":"H1/H3 reparameterized before response","reason":"fit identical H1 model separately by clade so all reference slopes are clade-specific; H1 is equal-clade mean and H3 is fern minus mean seed-plants coefficient","response_opened":False},
        ],
        "forbidden_after_response":[
            "change common island panel","reintroduce any prior-pilot archipelago",
            "change global q75 isolation threshold","change scale-free step-isolation definition",
            "change response-independent per-clade retained/dropped design columns","change reference predictor set or checklist-effort control","change frozen continuous scaling",
            "change log1p richness response","change fixed-effect absorption",
            "change per-archipelago total weight=1 rule","change bootstrap unit/repetitions/seed/rank filter or accepted draw set","change clade-specific fitting or equal-clade weighting","change H1 or H3 estimand/sign",
            "reintroduce H2 or any geology moderator","select clades by outcome direction",
        ],
        "response_open_authorized":qualified,
    }
    protocol["protocol_fingerprint"]=sha(protocol)
    print(json.dumps(protocol,indent=2,sort_keys=True))
    return 0 if qualified else 2

if __name__=="__main__":
    raise SystemExit(main())
