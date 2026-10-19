#!/usr/bin/env python3
"""Exact calibration-only non-identification witness from frozen mammal score summaries.

Mathematical sufficiency check, NOT a refit to heldout species records.
Do not read any occurrence matrix or prediction rows; all three outputs are
retrospective didactic examples with zero site-specific discriminatory signal.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path


def constant_probabilities(presence_delta:float,absence_delta:float):
    """Exact constant-pair witness for classwise C−R loss differences."""
    if not (math.isfinite(presence_delta) and math.isfinite(absence_delta)):
        raise ValueError("Non-finite loss contrast")
    if presence_delta*absence_delta>=0:
        raise ValueError("Requires strict opposite-sign classwise contrasts")
    r,s=math.exp(presence_delta),math.exp(absence_delta)
    c=(1-s)/(r-s)
    baseline=r*c
    if not (0<baseline<1 and 0<c<1):
        raise ValueError("No admissible probability pair")
    if not math.isclose(math.log(baseline/c),presence_delta,abs_tol=5e-13):
        raise AssertionError("Positive-class score failed exact reconstruction")
    if not math.isclose(math.log((1-baseline)/(1-c)),absence_delta,abs_tol=5e-13):
        raise AssertionError("Negative-class score failed exact reconstruction")
    return {
      "R3_constant_probability":baseline,
      "C_constant_probability":c,
      "C_over_R3_probability_ratio":c/baseline,
      "reconstructed_presence_C_minus_R3":math.log(baseline/c),
      "reconstructed_absence_C_minus_R3":math.log((1-baseline)/(1-c)),
      "AUC_of_both_hypothetical_constant_classifiers":"0.5 when both outcome classes exist",
      "site_specific_source_discrimination":False,
    }


def analyze(original79,rare,ultrarare):
    # Every number is read from frozen summary files only; no outcomes/predictions.
    if "outcome_asymmetry" not in original79 or "ranking_context" not in original79:
        raise ValueError("Exploratory v1.85 source mismatch")
    if rare.get("status")!="PROSPECTIVE_SPECIES_LAYER_NONREPLICATION_FROZEN":
        raise ValueError("Rare frozen source status changed")
    if ultrarare.get("status")!="PROSPECTIVE_ULTRARARE_PRESENCE_OPPORTUNITY_RESULT_FROZEN":
        raise ValueError("Ultrarare frozen source status changed")

    ds=[
      ("higher_occupancy_exploratory_79",
       original79["outcome_asymmetry"]["presence"]["C_minus_R3"],
       original79["outcome_asymmetry"]["absence"]["C_minus_R3"]),
      ("rare_preregistered_96",
       rare["P2_constraint_signature"]["presence_point"],
       rare["P2_constraint_signature"]["absence_point"]),
      ("ultrarare_preregistered_529",
       ultrarare["primary_presence_opportunity"]["point_C_minus_R3"],
       ultrarare["secondary_absence_signature"]["point_C_minus_R3"]),
    ]
    result={}
    for key,dpos,dneg in ds:
        result[key]={
         "original_pooled_presence_loss_contrast":dpos,
         "original_pooled_absence_loss_contrast":dneg,
         "calibration_only_witness":constant_probabilities(dpos,dneg),
        }
    ranking=original79.get("ranking_context",{})
    if ranking:
        result["higher_occupancy_exploratory_79"]["actual_full_model_ranking_metadata"]={
          "ROC_AUC_R3":ranking.get("R3_ROC_AUC"),
          "ROC_AUC_C":ranking.get("C_ROC_AUC"),
          "average_precision_R3":ranking.get("R3_average_precision"),
          "average_precision_C":ranking.get("C_average_precision"),
          "important_caveat":"Actual full models have ranking information and are not these constant witnesses"
        }
    return {
       "schema":"structural.occupancy_role_calibration_nonidentifiability.v1_250",
       "status":"EXACT_POOLED_CLASS_SCORE_COUNTEREXAMPLE_NOT_ECOLOGICAL_INVALIDATION",
       "source_paths":[
        "development/global_mammals_prediction_behavior_freeze_v1_85.json",
        "development/global_mammals_sealed_species_result_freeze_v1_97.json",
        "development/global_mammals_ultrarare_result_freeze_v1_119.json",
       ],
       "strata":result,
       "interpretation":"Opposite signs of pooled presence-vs-absence log-loss alone cannot prove a spatial constraint-to-opportunity mechanism; a probability intercept change reproduces those two summaries even if it carries zero within-stratum spatial discrimination.",
       "nonclaims":[
          "These synthetic constant probabilities are NOT actual R3/C model forecasts",
          "Does not reproduce actual ROC/AUC, source-support gradients or kNN-versus-rewire tests",
          "Does not refute original preregistered heldout results",
          "Does not estimate whether actual graph incremental gain is entirely calibration",
          "Does not reopen any original mammal response or prediction rows",
       ],
       "next_independent_discriminator":"New time-ahead same-species surveys with effort and CAL intercept-only reference, evaluating 0-to-1 detections and within-study discrimination.",
       "original_mammal_heldout_rows_opened":0,
       "new_confirmatory_systems":0,
       "eBird_used":False,
       "GEB_scientific_HOLD":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    src=[
      "development/global_mammals_prediction_behavior_freeze_v1_85.json",
      "development/global_mammals_sealed_species_result_freeze_v1_97.json",
      "development/global_mammals_ultrarare_result_freeze_v1_119.json",
    ]
    objs=[json.loads((root/s).read_text(encoding="utf-8")) for s in src]
    result=analyze(*objs)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:{
      "R3":v["calibration_only_witness"]["R3_constant_probability"],
      "C":v["calibration_only_witness"]["C_constant_probability"]}
      for key,v in result["strata"].items()},sort_keys=True))


if __name__=="__main__":main()
