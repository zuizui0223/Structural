#!/usr/bin/env python3
"""v1.227 retrospective prey-adjusted geometry comparison (observation endpoint only).

Original author density conversion confirmed in v1.225. All predictor values at
sampling visit t; future sample (t+1) is used solely as the binary scoring target.
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from hopson_temporal_detection_audit_v1_222 import (
    download_locked,layout_index,rows_locked,OBS_HEADER,intish,optional_count
)
from hopson_ring_reappearance_loso_v1_226 import rows_from_pinned,score

def tet_per_ml(tet,samp,dil,sub):
    """Match MD5-locked author R lines 14–15 exactly, with fail-closed schema."""
    if tet is None or not all(math.isfinite(v) for v in (samp,dil,sub)):
        raise ValueError("Prey assay not available")
    if samp<=0 or dil<0 or sub<0:
        raise ValueError("Invalid sample/dilution/subsample volumes")
    if dil==0 and sub==0:
        return tet/samp
    if dil>0 and sub>0:
        return (tet/sub)*(dil+samp)/samp
    raise ValueError("Inconsistent dilution and subsample flags")

def build_predictor_rows(raw_obs,raw_layout):
    layout=layout_index(raw_layout)
    taxon_data={}
    table=defaultdict(dict)
    for row in rows_locked(raw_obs,OBS_HEADER):
        jar=intish(row["jar.no"],"jar")
        if jar not in layout:raise ValueError("Unknown source jar")
        meta,patch,trt,block=layout[jar]
        day=intish(row["day"],"day")
        count=optional_count(row["eupl"],"eupl")
        tet=optional_count(row["tet"],"tet")
        v=float(row["samp.vol"])
        dil=float(row["dil.vol"])
        sub=float(row["sub.samp.vol"])
        if count is None:
            raise ValueError("Missing predator count")
        prey_density=tet_per_ml(tet,v,dil,sub)
        if not math.isfinite(prey_density) or prey_density<0:
            raise ValueError("Invalid prey density")
        key=(meta,day,patch)
        if key in taxon_data:raise ValueError("Duplicate patch/day")
        taxon_data[key]=(count,prey_density)
        table[(meta,day)][patch]=prey_density
    if len(taxon_data)!=4830:
        raise ValueError("4,830 sample identity drift")
    if any(len(x)!=15 for x in table.values()):
        raise ValueError("Missing metapop prey patch count")
    prior=rows_from_pinned(raw_obs,raw_layout)
    # Prior v1.226 constructs its samples in sorted metapop, time, ring-patch order.
    keys=[]
    for meta in range(1,15):
        dates=sorted(day for m,day in table if m==meta)
        for day in dates[:-1]:
            for patch in range(1,16):
                if taxon_data[(meta,day,patch)][0]==0:
                    keys.append((meta,day,patch))
    if len(prior)!=len(keys):
        raise ValueError("Baseline zero-start rows do not align")
    data=[]
    for old,(meta,day,patch) in zip(prior,keys):
        if (old["meta"],old["day"])!=(meta,day):
            raise ValueError("Source order drift")
        # t+1 biological target is already part of old['y'] and is not
        # consulted to construct any covariate.
        d=taxon_data[(meta,day,patch)][1]
        others=[table[(meta,day)][k] for k in range(1,16)]
        mean_prey=sum(others)/15
        extra=[math.log1p(d),math.log1p(mean_prey)]
        base=list(old["reference"])
        adjacency=list(old["candidate"])[len(base):]
        if len(adjacency)!=2:raise ValueError("Ring feature layout drift")
        data.append({
            "meta":meta,"y":old["y"],
            "reference":base+extra,
            "candidate":base+extra+adjacency
        })
    return prior,data

def evaluate(raw_obs,raw_layout):
    prior,with_prey=build_predictor_rows(raw_obs,raw_layout)
    first=score(prior)
    second=score(with_prey)
    if len(first["folds"])!=len(second["folds"])!=14:
        raise ValueError("Missing independent metapopulation folds")
    if first["n_zero_start_transition_rows"]!=second["n_zero_start_transition_rows"]:
        raise ValueError("Different comparison denominators")
    fold=[]
    for a,b in zip(first["folds"],second["folds"]):
        if (a["metapopulation"],a["test_rows"],a["test_redetections"])!=(
            b["metapopulation"],b["test_rows"],b["test_redetections"]):
            raise ValueError("Prey feature introduced outcome selection")
        fold.append({
            "metapopulation":a["metapopulation"],"test_rows":a["test_rows"],
            "test_redetections":a["test_redetections"],
            "R_without_prey":a["reference_test_logloss"],
            "C_without_prey":a["candidate_test_logloss"],
            "R_with_prey":b["reference_test_logloss"],
            "C_with_prey":b["candidate_test_logloss"],
            "ring_increment_after_prey":b["increment_candidate_minus_reference"],
            "prey_increment_to_reference":(
                b["reference_test_logloss"]-a["reference_test_logloss"])
        })
    ring=sum(x["ring_increment_after_prey"] for x in fold)/14
    prey=sum(x["prey_increment_to_reference"] for x in fold)/14
    return {
      "schema":"structural.hopson_prey_conditioned_ring_prediction.v1_227",
      "status":"RETROSPECTIVE_POSTOUTCOME_LOSO_NO_RESCUE",
      "source_MD5s":{
        "obs":"76de51cecdee69e87138c469a93b35a9",
        "layout":"6957db366d97aa5a15fd7107b2429ac3"
      },
      "assay_author_R_MD5":"dadab72ec94583cdbf7197cc3eb09ea0",
      "density_formula":"if dil=0 and sub=0: tet/samp; else (tet/sub)*(dil+samp)/samp",
      "prey_variables_at_t":["log1p(own_tet_ml)","log1p(mean_15_patch_tet_ml)"],
      "n_independent_metapopulations":14,
      "n_zero_start_transition_rows":len(prior),
      "n_zero_to_positive_redetections":sum(x["y"] for x in prior),
      "folds":fold,
      "primary_equal_metapopulation_Cprey_minus_Rprey_logloss":ring,
      "secondary_equal_metapopulation_Rprey_minus_Rno_prey_logloss":prey,
      "source_unadjusted_v226_C_minus_R_logloss":first["equal_metapopulation_C_minus_R_loss"],
      "prey_conditioned_candidate_descriptive_cluster_bootstrap_2_5_97_5":second["descriptive_2000_cluster_bootstrap_2_5_97_5"],
      "primary_direction_claimed_before_replay":"Cprey-Rprey<0 favorable, else non-support, no subgroup rescue",
      "prediction_target":"sample Euplotes 0 at t -> positive sample at t+1, NOT true colonization",
      "future_time_prey_used":False,
      "realized_source_target_migrations_observed":False,
      "ecological_R3_reference_is_satisfied":False,
      "new_fresh_confirmatory_evidence":False,
      "GEB_scientific_HOLD":True,
      "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=evaluate(download_locked("observations"),download_locked("layout"))
    if result["n_zero_to_positive_redetections"]!=554:
        raise ValueError("Source event anchor changed")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":main()
