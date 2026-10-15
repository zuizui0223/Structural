#!/usr/bin/env python3
"""v1.247: exact hypothetical conservation decision based on v1.246 cutsets.

No actual measured cost, restoration, survival, immigration or rescue.
"""
import argparse,json
from pathlib import Path
from fractions import Fraction as F
from higher_order_donor_cutset_known_truth_v1_246 import (
    distribution,no_local_donor,RECIPIENTS)

Q_GRID=(F(1,4),F(1,2),F(1,1))
WORLDS={"minus":-1,"plus":1}
ACTIONS=("A","B")

def fmt(q):
    return {"exact":str(q),"decimal":float(q)}

def action_result(initial,chosen,q):
    """Supplemental donor is independently viable with probability q.

    If it is viable and all old sources fail, the *potential* cutset opens;
    it does not prove a propagule arrives, survives, or reproduces.
    """
    if q<0 or q>1 or chosen not in ACTIONS:
        raise ValueError("Nonexistent supplement success or target island")
    avoided={r:q*initial[r] if r==chosen else F(0) for r in ACTIONS}
    residual={r:initial[r]-avoided[r] for r in ACTIONS}
    return {"targeted_receiver":chosen,
            "expected_potential_cutset_failures_avoided":fmt(sum(avoided.values())),
            "aggregate_residual_cutset_risk_AplusB":fmt(sum(residual.values())),
            "per_receiver_residual_risk":{r:fmt(v) for r,v in residual.items()}}

def audit():
    record={}
    for world,sgn in WORLDS.items():
        law=distribution(sgn)
        initial={r:no_local_donor(law,eligible) for r,eligible in RECIPIENTS.items()}
        assert sum(initial.values())==F(1,4)
        world_record={"baseline_cutset_risk":{r:fmt(v) for r,v in initial.items()},
                      "baseline_sum_AplusB":fmt(sum(initial.values())),
                      "by_supplemental_source_viability_probability":{}}
        for q in Q_GRID:
            actions={a:action_result(initial,a,q) for a in ACTIONS}
            optimum=max(ACTIONS,key=lambda a:(F(actions[a]["expected_potential_cutset_failures_avoided"]["exact"]),
                                              -ACTIONS.index(a)))
            opposite=next(a for a in ACTIONS if a!=optimum)
            regret=(F(actions[optimum]["expected_potential_cutset_failures_avoided"]["exact"])
                    - F(actions[opposite]["expected_potential_cutset_failures_avoided"]["exact"]))
            world_record["by_supplemental_source_viability_probability"][str(q)]={
                "new_donor_potential_viability":fmt(q),
                "all_equal_cost_single_receiver_actions":actions,
                "optimal_target_under_FULL_joint_viability_law":optimum,
                "worst_target_under_full_joint_law":opposite,
                "wrong_target_expected_cutset_loss_reduction_regret":fmt(regret)}
        record[world]=world_record
    for q in Q_GRID:
        neg=record["minus"]["by_supplemental_source_viability_probability"][str(q)]
        pos=record["plus"]["by_supplemental_source_viability_probability"][str(q)]
        assert neg["optimal_target_under_FULL_joint_viability_law"]=="B"
        assert pos["optimal_target_under_FULL_joint_viability_law"]=="A"
        assert F(neg["wrong_target_expected_cutset_loss_reduction_regret"]["exact"])==q*F(1,8)
        assert F(pos["wrong_target_expected_cutset_loss_reduction_regret"]["exact"])==q*F(1,8)
    return {
        "schema":"structural.higher_order_cutset_single_island_protection_decision.v1_247",
        "status":"EXACT_RATIONAL_HYPOTHETICAL_POLICY_KNOWN_TRUTH_ONLY",
        "baseline_controlled_worlds":"Identical donor first- and second-order moments, entire global live donor count distribution, and recipient source sets",
        "action_cost_assumption":"Exactly one of receiver A/B gains an equal-cost supplemental potential donor, independently viable with given q",
        "q_grid":["1/4","1/2","1"],
        "all_worlds_and_equal_cost_actions":record,
        "when_q_is_one":{
            "minus_optimal":"B","plus_optimal":"A",
            "optimal_risk_avoided":fmt(F(3,16)),
            "suboptimal_risk_avoided":fmt(F(1,16)),
            "wrong_choice_regret":fmt(F(1,8))
        },
        "when_q_is_one_half":{
            "minus_optimal":"B","plus_optimal":"A",
            "optimal_risk_avoided":fmt(F(3,32)),
            "suboptimal_risk_avoided":fmt(F(1,32)),
            "wrong_choice_regret":fmt(F(1,16))
        },
        "summary_only_approach_cannot_resolve_recipient_priority":True,
        "does_not_estimate_true_additional_donor_survival_or_planting_cost":True,
        "does_not_estimate_colonization_or_population_fitness":True,
        "observed_biological_source_and_recipient_records":0,
        "new_confirmatory_systems":0,
        "original_GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    out=audit()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema":out["schema"],"status":out["status"],
        "q_one":out["when_q_is_one"],"q_half":out["when_q_is_one_half"],
        "GEB_scientific_HOLD":True},sort_keys=True))
if __name__=="__main__":main()
