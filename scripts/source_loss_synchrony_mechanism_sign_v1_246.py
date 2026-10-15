#!/usr/bin/env python3
"""v1.246: exact PROSPECTIVE MECHANISM SIGN DECOMPOSITION, synthetic ONLY.

Not an empirical estimate, simulation of persistence, or confirmation.
This isolates a necessary condition for the "spatial hydra" rescue-window
possibility after loss of one source: effects on the joint state of remaining
sources MUST outweigh the nonnegative unique contribution of the removed
source. Compare independent before/after binary-source probability laws.
"""
from fractions import Fraction
import argparse
import json
from pathlib import Path

SCHEMA="structural.source_loss_synchrony_mechanism_sign.v1_246"

def law(raw,width):
    if type(width) is not int or width<1:
        raise ValueError("Expected positive source number")
    if not isinstance(raw,dict) or not raw:
        raise ValueError("Need a non-empty binary source law")
    d={}
    for state,weight in raw.items():
        if not isinstance(state,str) or len(state)!=width or set(state)-{"0","1"}:
            raise ValueError("Invalid source-state bit string")
        try:
            p=Fraction(weight)
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            raise ValueError("Invalid exact source state probability") from exc
        if p<0:
            raise ValueError("Negative source-state probability")
        d[state]=p
    if sum(d.values(),Fraction())!=1:
        raise ValueError("Source-state probabilities must sum exactly to one")
    return d

def q_all_off(d,width):
    return d.get("0"*width,Fraction(0))

def mean_active(d):
    return sum((v*sum(int(bit) for bit in state) for state,v in d.items()),
               Fraction(0))

def surviving_source_marginals(before,after,removed):
    keep=[i for i in range(len(next(iter(before)))) if i!=removed]
    baseline=[sum((p for state,p in before.items() if state[i]=="1"),Fraction(0))
              for i in keep]
    modified=[sum((p for state,p in after.items() if state[k]=="1"),Fraction(0))
              for k in range(len(keep))]
    return baseline,modified

def decompose(raw_before,raw_after,removed_index=2):
    if not isinstance(raw_before,dict) or not raw_before:
        raise ValueError("Before source law absent")
    n=len(next(iter(raw_before)))
    if type(removed_index) is not int or removed_index<0 or removed_index>=n:
        raise ValueError("Lost source not in baseline roster")
    if n<2:raise ValueError("Cannot calculate remaining network with fewer than two")
    before=law(raw_before,n)
    after=law(raw_after,n-1)
    remain=[i for i in range(n) if i!=removed_index]
    before_empty=q_all_off(before,n)
    static_empty=sum((p for state,p in before.items()
                      if all(state[i]=="0" for i in remain)),Fraction(0))
    after_empty=q_all_off(after,n-1)
    unique_loss=sum((p for state,p in before.items()
                     if state[removed_index]=="1"
                     and all(state[i]=="0" for i in remain)),Fraction(0))
    synchronization_response=after_empty-static_empty
    net=after_empty-before_empty
    if static_empty-before_empty!=unique_loss:
        raise AssertionError("Static source-set monotonicity identity violated")
    if net!=unique_loss+synchronization_response:
        raise AssertionError("Exact direct/reorganization decomposition violated")
    baseline_survivors,after_survivors=surviving_source_marginals(before,after,removed_index)
    def export(q):
        return {"exact":str(q),"decimal":float(q)}
    return {
      "pre_loss_no_viable_delivery_probability":export(before_empty),
      "counterfactual_no_feedback_after_deletion":export(static_empty),
      "post_loss_no_viable_delivery_probability":export(after_empty),
      "direct_loss_unique_delivery_term":export(unique_loss),
      "remaining_source_joint_reorganization_term":export(synchronization_response),
      "total_change_in_no_viable_delivery":export(net),
      "total_change_sign":"lower_probability_of_empty_rescue_window" if net<0 else
           "higher_probability_of_empty_rescue_window" if net>0 else
           "no_change_in_empty_rescue_window",
      "strict_hydra_window_criterion_satisfied":net<0,
      "direct_loss_without_feedback_cannot_lower_failure":unique_loss>=0,
      "same_individual_survivor_activity_marginals":
           baseline_survivors==after_survivors,
      "survivor_marginals_before":[export(x) for x in baseline_survivors],
      "survivor_marginals_after":[export(x) for x in after_survivors],
      "mean_viable_sources_before":export(mean_active(before)),
      "mean_viable_sources_after":export(mean_active(after)),
      "not_a_persistence_probability_or_colonization_estimate":True
    }

# Three exact known-truth source laws, NOT measured ecological experiments.
# Order is [surviving_A,surviving_B,deleted_C].
BEFORE_SYNC_AB_C_INDEPENDENT={
    "000":"3/10","001":"1/5","110":"3/10","111":"1/5"
}
AFTER_AB_INDEPENDENT={"00":"1/4","01":"1/4","10":"1/4","11":"1/4"}
AFTER_AB_SYNC={"00":"1/2","11":"1/2"}
BEFORE_INDEPENDENT_AB_C_INDEPENDENT={
    "000":"3/20","001":"1/10",
    "010":"3/20","011":"1/10",
    "100":"3/20","101":"1/10",
    "110":"3/20","111":"1/10"
}
SCENARIOS={
    "static_deletion_no_feedback":{
        "before":BEFORE_SYNC_AB_C_INDEPENDENT,
        "after":AFTER_AB_SYNC,
        "interpretation":"No surviving-source response: removing C cannot improve availability"},
    "hydra_like_decorrelation":{
        "before":BEFORE_SYNC_AB_C_INDEPENDENT,
        "after":AFTER_AB_INDEPENDENT,
        "interpretation":"Surviving A/B keep marginals 0.5 but lose cofailure synchrony"},
    "amplified_cofailure_after_removal":{
        "before":BEFORE_INDEPENDENT_AB_C_INDEPENDENT,
        "after":AFTER_AB_SYNC,
        "interpretation":"Remaining A/B retain marginals 0.5 but become synchronous"}
}

def run():
    result={}
    for key,scenario in SCENARIOS.items():
        result[key]={"calculation":decompose(scenario["before"],scenario["after"]),
                     "interpretation":scenario["interpretation"]}
    return {
       "schema":SCHEMA,
       "status":"EXACT_KNOWN_TRUTH_NO_EMPIRICAL_SOURCE_DATA_READ",
       "model_scope":"A single target's binary source-delivery opportunity at one specified lag",
       "causal_identity":
          "Q_after-Q_before = P(removed source uniquely viable before) + (Q_after-Q_static_remaining_before)",
       "necessary_window_hydra_inequality":
          "Q_static_remaining_before-Q_after > P(removed source uniquely viable before)",
       "examples":result,
       "no_empirical_persistence_or_source_colonization_measured":True,
       "published_prior_2017_spatial_hydra_is_not_new":True,
       "published_prior_2009_butterfly_synchrony_amplification_is_not_new":True,
       "existing_v1_203_pairwise_cofailure_known_truth_not_rebranded":True,
       "not_a_confirmatory_new_system":True,
       "GEB_scientific_HOLD":True,
       "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=run()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",
                      encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
