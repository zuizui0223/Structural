#!/usr/bin/env python3
"""Freeze and preflight the fresh GIFT community-richness topology protocol."""
from __future__ import annotations

import argparse, hashlib, json, math
from pathlib import Path

import numpy as np

CLADES=("Angiospermae","Pteridophyta","Gymnospermae")
REFERENCE_COLS=(
    "bio1","bio5","bio6","bio12","bio15",
    "log_area","log1p_dist","SLMP","GMMC",
    "log1p_nearest_other","surrounding_island_pressure","surrounding_landmass_pressure",
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
        "bio1":clim["wc2.0_bio_30s_01"],
        "bio5":clim["wc2.0_bio_30s_05"],
        "bio6":clim["wc2.0_bio_30s_06"],
        "bio12":clim["wc2.0_bio_30s_12"],
        "bio15":clim["wc2.0_bio_30s_15"],
        "log_area":math.log(max(float(island["area_km2"]),1e-12)),
        "log1p_dist":math.log1p(float(island["dist_km"])),
        "SLMP":float(island["SLMP"]),
        "GMMC":float(island["GMMC"]),
        "log1p_nearest_other":math.log1p(float(island["nearest_other_island_km"])),
        "surrounding_island_pressure":float(island["surrounding_island_pressure"]),
        "surrounding_landmass_pressure":float(island["surrounding_landmass_pressure"]),
    }

def within_transform(rows, columns):
    arr=np.asarray([[row[c] for c in columns] for row in rows],dtype=float)
    groups=default_groups(rows)
    out=arr.copy()
    for idxs in groups.values():
        idx=np.asarray(idxs,dtype=int)
        out[idx,:]-=arr[idx,:].mean(axis=0,keepdims=True)
    return out

def default_groups(rows):
    groups={}
    for i,row in enumerate(rows):
        groups.setdefault((row["archipelago_id"],row["clade"]),[]).append(i)
    return groups

def matrix_audit(rows, columns):
    X=within_transform(rows,columns)
    keep=np.std(X,axis=0)>1e-12
    kept=[c for c,k in zip(columns,keep) if k]
    dropped=[c for c,k in zip(columns,keep) if not k]
    X=X[:,keep]
    if X.shape[1]==0:
        return {"rows":len(rows),"columns":[],"dropped_constant":dropped,"rank":0,"condition":None,"full_rank":False}
    rank=int(np.linalg.matrix_rank(X,tol=1e-10))
    sv=np.linalg.svd(X,compute_uv=False)
    condition=float(sv[0]/sv[-1]) if sv[-1]>1e-15 else float("inf")
    return {
        "rows":len(rows),"columns":kept,"dropped_constant":dropped,
        "rank":rank,"n_columns":X.shape[1],"condition":condition,
        "full_rank":rank==X.shape[1],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--prior-exclusions",type=Path,required=True)
    a=ap.parse_args()
    panel=load(a.panel); prior=load(a.prior_exclusions)

    if panel.get("status")!="FROZEN_PREDICTOR_PANEL_RESPONSE_SEALED":
        raise RuntimeError("panel not frozen")
    if panel.get("response_values_accessed") is not False or panel.get("species_composition_endpoint_called") is not False:
        raise RuntimeError("response already opened")
    if tuple(panel.get("targets",()))!=CLADES:
        raise RuntimeError("clade set drift")
    if prior.get("response_values_used") is not False:
        raise RuntimeError("prior pilot response values entered protocol design")
    if any(v.get("opened") for v in panel["response_surfaces"].values()):
        raise RuntimeError("response surface already opened")

    # Freeze predictor scaling on unique islands before clade replication.
    unique=[]
    for g in panel["groups"]:
        for island in g["islands"]:
            p=raw_predictors(island)
            unique.append({
                "archipelago_id":g["archipelago_id"],
                "entity_ID":island["entity_ID"],
                **p,
                "topology_gain":float(island["topology_gain"]),
                "extreme":float(bool(island["extreme_q75"])),
            })

    continuous=[
        "bio1","bio5","bio6","bio12","bio15",
        "log_area","log1p_dist","SLMP",
        "log1p_nearest_other","surrounding_island_pressure",
        "surrounding_landmass_pressure","topology_gain",
    ]
    scaling={}
    for col in continuous:
        values=np.asarray([row[col] for row in unique],dtype=float)
        mu=float(values.mean()); sd=float(values.std(ddof=0))
        if sd<=1e-12:
            raise RuntimeError(f"predictor is globally constant before response: {col}")
        scaling[col]={"mean":mu,"sd":sd}
        for row in unique:
            row[col]=(row[col]-mu)/sd

    # Construct interactions only after the frozen z transform. Binary GMMC,
    # extreme and fern indicators remain unscaled.
    island_rows=[]
    for base in unique:
        for clade in CLADES:
            row={
                **base,
                "clade":clade,
                "fern":1.0 if clade=="Pteridophyta" else 0.0,
            }
            row["topology_x_extreme"]=row["topology_gain"]*row["extreme"]
            row["topology_x_GMMC"]=row["topology_gain"]*row["GMMC"]
            row["extreme_x_GMMC"]=row["extreme"]*row["GMMC"]
            row["topology_x_extreme_x_GMMC"]=row["topology_x_extreme"]*row["GMMC"]
            row["topology_x_fern"]=row["topology_gain"]*row["fern"]
            row["extreme_x_fern"]=row["extreme"]*row["fern"]
            row["topology_x_extreme_x_fern"]=row["topology_x_extreme"]*row["fern"]
            island_rows.append(row)

    h1_cols=list(REFERENCE_COLS)+["topology_gain","extreme","topology_x_extreme"]
    h2_cols=h1_cols+[
        "topology_x_GMMC","extreme_x_GMMC","topology_x_extreme_x_GMMC"
    ]
    h3_cols=h1_cols+[
        "topology_x_fern","extreme_x_fern","topology_x_extreme_x_fern"
    ]
    audits={
        "H1":matrix_audit(island_rows,h1_cols),
        "H2":matrix_audit(island_rows,h2_cols),
        "H3":matrix_audit(island_rows,h3_cols),
    }

    support=panel["support"]
    gates={
        "minimum_archipelagos":support["archipelagos"]>=10,
        "minimum_extreme_archipelagos":support["archipelagos_with_extreme"]>=5,
        "minimum_nonextreme_archipelagos":support["archipelagos_with_nonextreme"]>=5,
        "topology_support_extreme":support["extreme_topology_gain_nonzero_islands"]>=20,
        "topology_support_nonextreme":support["nonextreme_topology_gain_nonzero_islands"]>=20,
        "H1_full_rank":audits["H1"]["full_rank"] and audits["H1"]["condition"]<=MAX_CONDITION,
        "H2_full_rank":audits["H2"]["full_rank"] and audits["H2"]["condition"]<=MAX_CONDITION,
        "H3_full_rank":audits["H3"]["full_rank"] and audits["H3"]["condition"]<=MAX_CONDITION,
    }
    qualified=all(gates.values())

    protocol={
        "schema":"structural.gift_community_topology_protocol.v0_1",
        "status":"QUALIFIED_TO_OPEN_COMMUNITY_RESPONSE" if qualified else "STOP_PRE_RESPONSE_NON_ESTIMABLE",
        "study_family":"fresh community-level island-biogeography study; not a continuation or rescue of species-wise Structural confirmatory lanes",
        "gift_version":"3.2",
        "clades":list(CLADES),
        "panel_fingerprint":panel["panel_fingerprint"],
        "prior_response_exclusion_receipt_sha256":sha(prior),
        "response_values_accessed":False,
        "response_surfaces":panel["response_surfaces"],
        "response_semantics":{
            "unit":"island x clade",
            "response":"native species richness = number of unique work_IDs with at least one unambiguous native occurrence across the frozen eligible list_ID union for the island and clade",
            "unambiguous_native":"native=1 AND questionable!=1 AND quest_native!=1",
            "uncertain_records":"native rows with questionable=1 or quest_native=1 do not contribute to richness",
            "duplicate_work_ID_across_lists":"count once per island x clade",
            "zero_richness":"permitted only when frozen eligible list surfaces return no unambiguous native work_ID for the clade",
        },
        "predictor_semantics":{
            "reference_predictors":list(REFERENCE_COLS),
            "frozen_continuous_scaling":scaling,
            "topology_gain":panel["topology_gain_definition"],
            "extreme_isolation":panel["extreme_rule"],
            "fixed_effect_absorption":"demean outcome and every design column within each archipelago x clade group before OLS",
            "continuous_scaling":"z-standardize continuous base predictors across unique islands using the frozen means/SD above; construct topology interactions after scaling; GMMC/extreme/fern remain 0/1; then demean every final design column within archipelago x clade",
        },
        "model":{
            "family":"ordinary least squares on log1p(native richness)",
            "hyperparameter_tuning":"none",
            "archipelago_clade_fixed_intercepts":"absorbed by within-group demeaning",
            "inference_unit":"archipelago",
            "bootstrap":"resample whole archipelagos with replacement, retain all islands and all three clades, refit exact frozen model",
            "bootstrap_replicates":BOOTSTRAP_REPS,
            "bootstrap_seed":BOOTSTRAP_SEED,
            "two_sided_interval":[0.025,0.975],
        },
        "H1_primary":{
            "model_columns":h1_cols,
            "estimand":"coefficient of topology_gain x global-extreme-isolation after the declared reference and archipelago x clade fixed effects",
            "prediction":"positive: stepping-stone topology buffers richness loss more strongly under extreme mainland isolation",
            "success_rule":"95% archipelago-bootstrap interval for topology_x_extreme excludes 0 on the positive side",
        },
        "H2_primary":{
            "model_columns":h2_cols,
            "estimand":"coefficient of topology_gain x extreme x GMMC in a hierarchical interaction model that also contains topology_gain x GMMC and extreme x GMMC",
            "prediction":"negative: the extreme-isolation topology benefit is weaker on islands connected to mainland at the Last Glacial Maximum",
            "success_rule":"95% archipelago-bootstrap interval excludes 0 on the negative side",
            "claim_ceiling":"historical connection moderator, not direct colonization/extinction mechanism",
        },
        "H3_primary":{
            "model_columns":h3_cols,
            "fern_indicator":"Pteridophyta=1; Angiospermae/Gymnospermae=0",
            "estimand":"coefficient of topology_gain x extreme x fern in a hierarchical interaction model that also contains topology_gain x fern and extreme x fern",
            "prediction":"negative: high-dispersal ferns show weaker dependence on stepping-stone topology than seed plants",
            "success_rule":"95% archipelago-bootstrap interval excludes 0 on the negative side",
            "secondary":"fit exact H1 separately by all three clades; no separate-clade result can rescue H3",
        },
        "pre_response_matrix_audits":audits,
        "pre_response_gates":gates,
        "max_condition_number":MAX_CONDITION,
        "forbidden_after_response":[
            "change common island panel","reintroduce any prior-pilot archipelago",
            "change global q75 isolation threshold","change 25/50/125/250 km graph radii",
            "change topology_gain definition","drop reference covariates after seeing richness",
            "change fixed-effect absorption","switch response transformation",
            "select clades by outcome direction","change H1/H2/H3 signs or estimands",
        ],
        "response_open_authorized":qualified,
    }
    protocol["protocol_fingerprint"]=sha(protocol)
    print(json.dumps(protocol,indent=2,sort_keys=True))
    return 0 if qualified else 2

if __name__=="__main__":
    raise SystemExit(main())
