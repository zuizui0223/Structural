#!/usr/bin/env python3
"""Exact four-donor counterexample; no biological data or confirmatory evidence."""
import argparse
import itertools
import json
from fractions import Fraction as F
from pathlib import Path

DONORS=(1,2,3,4)
RECIPIENTS={"A":(1,2,3),"B":(1,2,4)}
STATES=tuple(itertools.product((0,1),repeat=4))

def perturbation(x):
    if len(x)!=4 or any(y not in (0,1) for y in x):raise ValueError("Four binary donor states required")
    return (-1)**(x[0]+x[1]+x[2])-(-1)**(x[0]+x[1]+x[3])

def distribution(sign):
    if sign not in (-1,1):raise ValueError("Only predeclared two viability laws")
    d={x:F(1,16)+sign*F(perturbation(x),32) for x in STATES}
    if min(d.values())<0 or sum(d.values())!=1:raise ValueError("Invalid state distribution")
    return d

def moment(d,selected):
    idx=tuple(DONORS.index(i) for i in selected)
    return sum(p for x,p in d.items() if all(x[i]==1 for i in idx))

def no_local_donor(d,eligible):
    if not eligible or any(i not in DONORS for i in eligible):raise ValueError("Invalid donor eligibility")
    idx=tuple(DONORS.index(i) for i in eligible)
    return sum(p for x,p in d.items() if all(x[i]==0 for i in idx))

def count_law(d):
    return {k:sum(p for x,p in d.items() if sum(x)==k) for k in range(5)}

def render(f):
    return {"exact":str(f),"decimal":float(f)}

def analyze():
    dminus,dplus=distribution(-1),distribution(+1)
    ds={"minus":dminus,"plus":dplus}
    expected={k:F(n,16) for k,n in enumerate((1,4,6,4,1))}
    for d in ds.values():
        assert all(moment(d,[i])==F(1,2) for i in DONORS)
        assert all(moment(d,[i,j])==F(1,4) for i,j in itertools.combinations(DONORS,2))
        assert count_law(d)==expected
        assert no_local_donor(d,DONORS)==F(1,16)
    risks={w:{name:no_local_donor(d,elig) for name,elig in RECIPIENTS.items()} for w,d in ds.items()}
    assert risks["minus"]=={"A":F(1,16),"B":F(3,16)}
    assert risks["plus"]=={"A":F(3,16),"B":F(1,16)}
    assert sum(risks["minus"].values())==sum(risks["plus"].values())==F(1,4)
    return {
        "schema":"structural.exact_higher_order_donor_cutset_known_truth.v1_246",
        "status":"KNOWN_TRUTH_ONLY_NO_ECOLOGICAL_RESPONSE_OBSERVED",
        "donors":list(DONORS),
        "receiver_donor_sets":{name:list(elig) for name,elig in RECIPIENTS.items()},
        "joint_viability_laws":{w:{"states":[{"viability":"".join(map(str,x)),
                          "probability":str(d[x])} for x in STATES],
            "marginal_donor_viability":{str(i):render(moment(d,[i])) for i in DONORS},
            "all_six_pairwise_joint_viability":{f"{i}-{j}":render(moment(d,[i,j]))
                 for i,j in itertools.combinations(DONORS,2)},
            "full_global_live_count_distribution":{str(k):render(p) for k,p in count_law(d).items()},
            "local_recipient_all_accessible_donors_unavailable":{name:render(p) for name,p in risks[w].items()},
            "potentially_at_least_one_donor":{name:render(1-p) for name,p in risks[w].items()},
            "both_receivers_no_donor":render(no_local_donor(d,DONORS))}
            for w,d in ds.items()},
        "exact_A_cutset_plus_minus_difference":render(risks["plus"]["A"]-risks["minus"]["A"]),
        "exact_B_cutset_plus_minus_difference":render(risks["plus"]["B"]-risks["minus"]["B"]),
        "exact_higher_to_lower_cutset_risk_ratio":render(F(3)),
        "global_total_donor_count_distributions_are_identical":True,
        "all_marginal_and_pairwise_source_moments_are_identical":True,
        "recipients_have_equal_three_potential_sources":True,
        "aggregate_two_recipient_cutset_risk_is_identical":True,
        "actual_source_loss_migration_colonization_or_fitness_observations":0,
        "higher_order_cutset_is_not_a_realized_movement_or_rescue_outcome":True,
        "new_confirmatory_systems":0,
        "original_global_mammal_heldout_unopened":True,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    receipt=analyze()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":receipt["schema"],"status":receipt["status"],
        "minus_A":receipt["joint_viability_laws"]["minus"]["local_recipient_all_accessible_donors_unavailable"]["A"],
        "plus_A":receipt["joint_viability_laws"]["plus"]["local_recipient_all_accessible_donors_unavailable"]["A"],
        "minus_B":receipt["joint_viability_laws"]["minus"]["local_recipient_all_accessible_donors_unavailable"]["B"],
        "plus_B":receipt["joint_viability_laws"]["plus"]["local_recipient_all_accessible_donors_unavailable"]["B"],
        "GEB_scientific_HOLD":True
    },sort_keys=True))
if __name__=="__main__":main()
