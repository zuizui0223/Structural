#!/usr/bin/env python3
"""v1.229 source-locked retrospective TWO-RULE prey-assay sensitivity.

The frozen v1.227 run remains terminal STOP. This is a DISTINCT,
postoutcome exploratory audit of the SINGLE assay flag discrepancy identified
in v1.228, not silent repairing/renaming the prior failed protocol.
All rows and both interpretations are predeclared and always reported.
"""
import argparse
import json
import math
from pathlib import Path

import hopson_prey_conditioned_ring_v1_227 as original
from hopson_temporal_detection_audit_v1_222 import download_locked
from hopson_prey_volume_schema_v1_228 import audit as metadata_audit

EXPECTED_V226=-0.000571276180789163
EXACT_V228_COUNTS={
    "both_zero_undiluted":3591,
    "both_positive_diluted":1238,
    "dilution_zero_subsample_positive":1,
}

def prey_density(tet,samp,dil,sub,rule):
    if tet is None or not isinstance(tet,int) or tet<0:
        raise ValueError("Missing or invalid prey count")
    if any(not math.isfinite(v) for v in (samp,dil,sub)):
        raise ValueError("Nonfinite assay volume")
    if samp<=0 or dil<0 or sub<0:
        raise ValueError("Impossible source assay volume")
    if rule=="author_R_literal":
        # R line 14 then 15 nonfinite fallback, implemented algebraically.
        if sub>0:
            return (tet/sub)*(dil+samp)/samp
        return tet/samp
    if rule=="README_no_dilution":
        if dil==0:return tet/samp
        if sub>0:return (tet/sub)*(dil+samp)/samp
        raise ValueError("Diluted sample has no subsample")
    raise ValueError("Rule not frozen")

def assess(observation,layout):
    meta=metadata_audit(observation)
    if (meta["n_published_rows"]!=4830 or
        meta["assay_flag_category_counts"]!=EXACT_V228_COUNTS or
        meta["status"]!="STOP_V227_ASSAY_DOMAIN_MISMATCH"):
        raise ValueError("Source v1.228 schema changed; cannot compare rules")
    f=original.tet_per_ml
    variants={}
    try:
        for rule in ("author_R_literal","README_no_dilution"):
            original.tet_per_ml=lambda tet,samp,dil,sub,rule=rule:prey_density(
                tet,samp,dil,sub,rule)
            ans=original.evaluate(observation,layout)
            if (ans["n_zero_start_transition_rows"]!=1085
                or ans["n_zero_to_positive_redetections"]!=554
                or ans["n_independent_metapopulations"]!=14
                or len(ans["folds"])!=14):
                raise ValueError("Prediction rows/folds not original")
            if abs(ans["source_unadjusted_v226_C_minus_R_logloss"]-EXPECTED_V226)>1e-10:
                raise ValueError("Baseline v226 model drift")
            variants[rule]={
                "n_prediction_rows":ans["n_zero_start_transition_rows"],
                "n_sample_redetections":ans["n_zero_to_positive_redetections"],
                "prey_adjusted_R_mean":sum(x["R_with_prey"] for x in ans["folds"])/14,
                "prey_adjusted_C_mean":sum(x["C_with_prey"] for x in ans["folds"])/14,
                "primary_ring_increment_C_minus_R":ans["primary_equal_metapopulation_Cprey_minus_Rprey_logloss"],
                "secondary_prey_reference_increment_Rprey_minus_Rwithoutprey":ans["secondary_equal_metapopulation_Rprey_minus_Rno_prey_logloss"],
                "original_preypoor_v226_increment":ans["source_unadjusted_v226_C_minus_R_logloss"],
                "descriptive_bootstrap_2_5_97_5":ans["prey_conditioned_candidate_descriptive_cluster_bootstrap_2_5_97_5"],
                "per_independent_metapopulation":[
                    {"id":x["metapopulation"],
                     "test_rows":x["test_rows"],
                     "redetections":x["test_redetections"],
                     "prey_increment":x["prey_increment_to_reference"],
                     "ring_after_prey_increment":x["ring_increment_after_prey"]}
                    for x in ans["folds"]
                ],
            }
    finally:
        original.tet_per_ml=f
    a=variants["author_R_literal"];b=variants["README_no_dilution"]
    return {
        "schema":"structural.hopson_two_assay_rules_ring_preydensity.v1_229",
        "status":"RETROSPECTIVE_POSTHOC_ASSAY_RULE_SENSITIVITY_TWO_FIXED_INTERPRETATIONS",
        "single_discordant_source_row":1,
        "v227_frozen_scoring_terminal_STOP":True,
        "v228_assay_metadata_status":meta["status"],
        "source_observation_MD5":"76de51cecdee69e87138c469a93b35a9",
        "source_layout_MD5":"6957db366d97aa5a15fd7107b2429ac3",
        "original_R_source_MD5":"dadab72ec94583cdbf7197cc3eb09ea0",
        "all_14_metapopulation_folds_with_no_tuning":True,
        "two_fixed_assay_rule_results":variants,
        "absolute_difference_between_rule_primary_ring_C_minus_R":abs(
            a["primary_ring_increment_C_minus_R"]-b["primary_ring_increment_C_minus_R"]),
        "absolute_difference_between_rule_secondary_prey_R_increment":abs(
            a["secondary_prey_reference_increment_Rprey_minus_Rwithoutprey"]-
            b["secondary_prey_reference_increment_Rprey_minus_Rwithoutprey"]),
        "prediction_target":"Euplotes sampled zero at t to count-positive at next visit, not true colonization",
        "no_realized_donor_migration_or_true_occupancy":True,
        "no_original_mammal_holdout_reopened":True,
        "nonfresh_published_outcome_exposure":True,
        "zero_new_confirmatory_systems":True,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    ans=assess(download_locked("observations"),download_locked("layout"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(ans,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(ans,sort_keys=True))

if __name__=="__main__":main()
