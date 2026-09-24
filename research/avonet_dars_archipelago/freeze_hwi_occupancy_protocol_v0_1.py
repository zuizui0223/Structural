#!/usr/bin/env python3
"""Freeze the AVONET/DARs bird archipelago protocol before any PA matrix opens."""
from __future__ import annotations

import argparse, hashlib, json, math
from pathlib import Path
import numpy as np

BOOTSTRAP_REPS=10000
BOOTSTRAP_SEED=20260924
MIN_ISLANDS=8
MIN_HWI_MATCHED_SPECIES=20
MIN_HWI_COVERAGE=0.80
MIN_VARIABLE_OCCUPANCY_SPECIES=15
MIN_DISTINCT_OCCUPANCY_FRACTIONS=4
MIN_UNIQUE_HWI=10

def load(path):
    x=json.loads(Path(path).read_text())
    if not isinstance(x,dict): raise RuntimeError(f"{path} must contain object")
    return x

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def design(rows,use_continuous_iso=False):
    mean_dist=np.log1p(np.asarray([float(r["MeanDist"]) for r in rows],dtype=float))
    md=(mean_dist-mean_dist.mean())/mean_dist.std(ddof=0)
    if use_continuous_iso:
        iso=np.log1p(np.asarray([float(r["Iso"]) for r in rows],dtype=float))
        focal=(iso-iso.mean())/iso.std(ddof=0)
    else:
        focal=np.asarray([1.0 if r["extreme_isolation_q75"] else 0.0 for r in rows])
    oceanic=np.asarray([1.0 if r["Type_V_fine"]=="Oceanic" else 0.0 for r in rows])
    X=np.column_stack([np.ones(len(rows)),focal,oceanic,md])
    return X,md,focal,oceanic

def audit(X):
    rank=int(np.linalg.matrix_rank(X,tol=1e-12))
    sv=np.linalg.svd(X,compute_uv=False)
    cond=float(sv[0]/sv[-1]) if sv[-1]>1e-15 else float("inf")
    return {"rows":int(X.shape[0]),"columns":int(X.shape[1]),"rank":rank,"condition":cond,"full_rank":rank==X.shape[1]}

def freeze_bootstrap(rows):
    X_primary,_,_,_=design(rows,False)
    X_sens,_,_,_=design(rows,True)
    names=[r["dataset"] for r in rows]
    index={name:i for i,name in enumerate(names)}
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    accepted=[];attempted=0
    while len(accepted)<BOOTSTRAP_REPS and attempted<BOOTSTRAP_REPS*20:
        attempted+=1
        draw=[names[int(i)] for i in rng.integers(0,len(names),size=len(names))]
        idx=np.asarray([index[x] for x in draw],dtype=int)
        if np.linalg.matrix_rank(X_primary[idx,:],tol=1e-12)!=X_primary.shape[1]:
            continue
        if np.linalg.matrix_rank(X_sens[idx,:],tol=1e-12)!=X_sens.shape[1]:
            continue
        accepted.append(draw)
    if len(accepted)!=BOOTSTRAP_REPS:
        raise RuntimeError(f"could not freeze {BOOTSTRAP_REPS} full-rank draws")
    return {
      "replicates":BOOTSTRAP_REPS,
      "seed":BOOTSTRAP_SEED,
      "rng":"numpy.default_rng(PCG64)",
      "candidate_draws_attempted":attempted,
      "accepted_draws_sha256":sha(accepted),
      "replay_rule":"draw 16 confirmatory archipelago names with replacement; accept only if both frozen primary and continuous-Iso sensitivity design matrices are full column rank; use first 10,000 accepted draws",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--census",type=Path,required=True)
    ap.add_argument("--partition",type=Path,required=True)
    ap.add_argument("--trait",type=Path,required=True)
    a=ap.parse_args()
    census=load(a.census); part=load(a.partition); trait=load(a.trait)

    if census.get("status")!="RESPONSE_SEALED_METADATA_ONLY": raise RuntimeError("census not sealed")
    if part.get("status")!="RESPONSE_SEALED_PARTITIONS_FROZEN": raise RuntimeError("partition not frozen")
    if trait.get("status")!="PREDICTOR_OPEN_RESPONSE_SEALED": raise RuntimeError("trait predictor not frozen")
    if any([
        census.get("response_values_accessed") is not False,
        part.get("response_values_accessed") is not False,
        trait.get("response_values_accessed") is not False,
    ]): raise RuntimeError("response already opened")
    if part["source_fingerprint"]!=census["source_fingerprint"]: raise RuntimeError("source drift")

    confirm=part["confirmatory"]
    if len(confirm)!=16: raise RuntimeError("confirmatory panel drift")
    if sum(r["Type_V_fine"]=="Oceanic" for r in confirm)!=8: raise RuntimeError("Oceanic count drift")
    if sum(r["Type_V_fine"]=="C.Shelf" for r in confirm)!=8: raise RuntimeError("Shelf count drift")

    X,md,extreme,oceanic=design(confirm,False)
    Xs,_,ziso,_=design(confirm,True)
    primary_audit=audit(X); sensitivity_audit=audit(Xs)
    if not primary_audit["full_rank"] or primary_audit["condition"]>20:
        raise RuntimeError("primary archipelago design not estimable")
    if not sensitivity_audit["full_rank"] or sensitivity_audit["condition"]>20:
        raise RuntimeError("continuous-Iso sensitivity design not estimable")

    cells={}
    for r in confirm:
        key=f'{r["Type_V_fine"]}|{"extreme" if r["extreme_isolation_q75"] else "nonextreme"}'
        cells[key]=cells.get(key,0)+1

    bootstrap=freeze_bootstrap(confirm)
    protocol={
      "schema":"structural.avonet_dars_hwi_occupancy_protocol.v0_1",
      "status":"FROZEN_BEFORE_BURNED_PILOT_RESPONSE",
      "selection_provenance":"bird/AVONET parallel system was specified before any GIFT burned-pilot response was opened",
      "dars_commit":"8b381ff26e3d6f4da17730dda0c5ab7dbad12eed",
      "source_fingerprint":census["source_fingerprint"],
      "partition_fingerprint":part["partition_fingerprint"],
      "trait_fingerprint":trait["trait_fingerprint"],
      "response_values_accessed":False,
      "pilot_response_opened":False,
      "confirmatory_response_opened":False,
      "trait":{
        "predictor":"Hand-Wing Index",
        "source_path":trait["source"]["path"],
        "source_sha256":trait["source"]["sha256"],
        "species_name_column":"Species 2",
        "direction":"higher HWI = greater dispersal/flight morphology",
        "no_alternate_trait_after_response":True,
      },
      "matrix_contract":{
        "format":"species rows x island columns",
        "species_label_column":"first column",
        "terminal_metadata_rows":["Area (ha)","sp.r"],
        "incidence_values":"0/1 only in species rows",
        "area_and_sp_r_never_enter_primary_trait-occupancy_endpoint":True,
      },
      "archipelago_endpoint":{
        "name":"HWI-occupancy Spearman rho",
        "species_occupancy":"number of occupied islands / total islands in the DARs archipelago matrix",
        "species_inclusion":"species row with nonmissing direct HWI; all occupancy fractions retained, including occupancy=1",
        "rank_method":"average ranks for ties, then ordinary Pearson correlation of HWI ranks and occupancy-fraction ranks",
        "minimum_requirements":{
          "islands":MIN_ISLANDS,
          "HWI_matched_species":MIN_HWI_MATCHED_SPECIES,
          "HWI_match_coverage":MIN_HWI_COVERAGE,
          "variable_occupancy_species":MIN_VARIABLE_OCCUPANCY_SPECIES,
          "distinct_occupancy_fractions":MIN_DISTINCT_OCCUPANCY_FRACTIONS,
          "unique_HWI_values":MIN_UNIQUE_HWI,
        },
        "claim_ceiling":"rho is a trait-occupancy association within an archipelago, not a direct dispersal or colonization rate",
      },
      "burned_pilot_gate":{
        "response_surface":"the 5 frozen pilot matrices only",
        "pilot_datasets":[r["dataset"] for r in part["pilot"]],
        "effect_or_rho_computation_allowed":False,
        "model_fit_allowed":False,
        "audit_only":[
          "matrix schema and binary incidence",
          "island count",
          "direct HWI name-match coverage",
          "number of HWI-matched species",
          "number of species with 0<occupancy<1",
          "number of distinct occupancy fractions",
          "number of unique HWI values"
        ],
        "dataset_pass_rule":"all archipelago-endpoint minimum requirements pass",
        "study_pass_rule":"at least 4 of 5 pilot datasets pass AND at least one Oceanic pilot passes AND at least one C.Shelf pilot passes",
        "hybrid_role":"C.Shelf / Atoll pilot is schema/geometry stress only and is never confirmatory",
        "failure_rule":"terminal STOP for v0.1; do not change HWI, thresholds, endpoint, partition or confirmatory panel",
        "pilot_predictive_denominator_contribution":0,
      },
      "confirmatory_gate":{
        "datasets":[r["dataset"] for r in confirm],
        "all_16_must_satisfy_exact_endpoint_requirements_before_H1_H2_scoring":True,
        "failure_rule":"if any confirmatory dataset is non-estimable, record terminal STOP and do not score H1/H2",
      },
      "second_stage":{
        "unit":"archipelago",
        "equal_archipelago_weight":True,
        "response":"frozen HWI-occupancy Spearman rho",
        "primary_model":"OLS: rho ~ intercept + extreme_q75 + Oceanic + z(log1p MeanDist)",
        "columns":["intercept","extreme_q75","Oceanic","z_log1p_MeanDist"],
        "design_audit":primary_audit,
        "cell_counts":cells,
        "H1":{
          "target":"extreme_q75 coefficient",
          "prediction":"positive",
          "interpretation":"dispersal morphology is more strongly associated with within-archipelago occupancy under extreme mainland isolation",
          "success_rule":"frozen whole-archipelago bootstrap 95% interval excludes 0 on positive side",
        },
        "H2":{
          "target":"Oceanic coefficient",
          "prediction":"positive",
          "interpretation":"dispersal filtering is stronger in oceanic than continental-shelf archipelagos after adjusting extreme-isolation class and MeanDist",
          "success_rule":"frozen whole-archipelago bootstrap 95% interval excludes 0 on positive side",
          "not_an_interaction":"q75 x island-type interaction is not tested because the response-blind confirmatory 2x2 table has only one extreme C.Shelf archipelago",
        },
        "MeanDist_role":"response-independent control for average within-archipelago island spacing",
        "bootstrap":bootstrap,
        "quantile_method":"numpy.quantile method=linear",
      },
      "nonrescuing_sensitivity":{
        "model":"rho ~ intercept + z(log1p Iso) + Oceanic + z(log1p MeanDist)",
        "design_audit":sensitivity_audit,
        "Iso_target_prediction":"positive",
        "cannot_rescue_H1_or_H2":True,
      },
      "forbidden_after_pilot_or_confirmatory_response":[
        "change pilot or confirmatory dataset membership",
        "change q75 definition",
        "replace HWI with another AVONET trait",
        "change rho endpoint or species inclusion rule",
        "lower pilot or confirmatory estimability requirements",
        "drop MeanDist after seeing outcome",
        "add q75 x type interaction",
        "use continuous Iso sensitivity to rescue failed H1",
        "select archipelagos by rho direction",
      ],
      "pilot_response_authorized":False,
      "confirmatory_response_authorized":False,
    }
    protocol["protocol_fingerprint"]=sha(protocol)
    print(json.dumps(protocol,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
