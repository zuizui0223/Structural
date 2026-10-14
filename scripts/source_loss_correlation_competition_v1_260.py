#!/usr/bin/env python3
"""v1.260: known-truth sign boundary for source-loss vs correlated failure.

This is a transparent MODEL COUNTEREXAMPLE, NOT a reanalysis of published Fox
or Matter data, a measured extinction effect, rescue, or confirmatory finding.

Donors have fixed marginal failure q. A shared catastrophe has probability c.
Otherwise each donor fails independently with probability p=(q-c)/(1-c).
Each viable donor supplies the target independently with success probability a.
We compare n=4 / c=.22 versus n=3 / c=.01, holding q=.35.
The shared-correlation change is an explicit HYPOTHETICAL intervention, not a
demonstrated consequence of removing a biological source island.
"""
import argparse
import itertools
import json
import math
from pathlib import Path

PRIMARY={
    "q":0.35,
    "before":{"n_donors":4,"shared_catastrophe":0.22},
    "after":{"n_donors":3,"shared_catastrophe":0.01},
    "after_loss_without_decoupling":{"n_donors":3,"shared_catastrophe":0.22},
}
REGISTERED_ARRIVALS=(0.25,0.30,0.45,0.50,0.60,0.75,0.90,1.0)

def validate(n,q,c,a):
    if not isinstance(n,int) or isinstance(n,bool) or n<1:
        raise ValueError("number of donor patches must be a positive integer")
    if any(not isinstance(x,(int,float)) or not math.isfinite(x)
           for x in (q,c,a)):
        raise ValueError("All underlying probabilities must be finite")
    if not 0<q<1 or not 0<=c<=q or not 0<=a<=1:
        raise ValueError("Require 0<q<1, 0<=c<=q and 0<=a<=1")

def individual_fail_given_no_common(q,c):
    return (q-c)/(1-c)

def no_delivery(n,q,c,a):
    """P(no viable donor makes a successful arrival), not extinction risk."""
    validate(n,q,c,a)
    p=individual_fail_given_no_common(q,c)
    return c+(1-c)*(1-(1-p)*a)**n

def exact_small_enumeration(n,q,c,a):
    """Independent exact known-truth combinatoric check, n<=10."""
    validate(n,q,c,a)
    if n>10:raise ValueError("Only a small-fixture enumerator")
    p=individual_fail_given_no_common(q,c)
    result=c
    for indicators in itertools.product((0,1),repeat=n):
        # indicator==1 denotes source failure in NO common-catastrophe case.
        failed=sum(indicators)
        viable=n-failed
        result+=(1-c)*p**failed*(1-p)**viable*(1-a)**viable
    return result

def pair_failure_correlation(q,c):
    """Correlation of two donor failure indicators under mixture."""
    validate(2,q,c,0.5)
    return c*(1-q)/(q*(1-c))

def expected_successful_arrivals(n,q,a):
    """Mean viable source deliveries; correlations do not affect mean."""
    validate(n,q,0,a)
    return n*(1-q)*a

def local_state(n,q,c,a):
    return {
        "donors":n,
        "marginal_local_failure_probability":q,
        "shared_event_probability":c,
        "conditional_independent_local_failure_probability":
            individual_fail_given_no_common(q,c),
        "pairwise_source_failure_correlation":pair_failure_correlation(q,c)
             if n>=2 else None,
        "expected_successful_donor_arrivals":expected_successful_arrivals(n,q,a),
        "probability_no_deliveries":no_delivery(n,q,c,a),
        "probability_one_or_more_deliveries":1-no_delivery(n,q,c,a),
    }

def nonzero_sign_threshold(n_before,c_before,n_after,c_after,q):
    """Return interior a* with equal delivery-shortage risks, not the a=0 root."""
    def difference(a):
        return no_delivery(n_after,q,c_after,a)-no_delivery(
            n_before,q,c_before,a)
    if difference(.10)<=0 or difference(1)>=0:
        raise ValueError("Scenario does not establish the registered interior sign flip")
    left,right=.10,1.0
    for _ in range(90):
        middle=(left+right)/2
        if difference(middle)>0:left=middle
        else:right=middle
    root=(left+right)/2
    if abs(difference(root))>2e-13:
        raise AssertionError("Root not found")
    return root

def run():
    q=PRIMARY["q"]
    before=PRIMARY["before"]
    after=PRIMARY["after"]
    no_decouple=PRIMARY["after_loss_without_decoupling"]
    n0=before["n_donors"]
    n1=after["n_donors"]
    c0=before["shared_catastrophe"]
    c1=after["shared_catastrophe"]
    boundary=nonzero_sign_threshold(n0,c0,n1,c1,q)
    rows=[]
    for a in REGISTERED_ARRIVALS:
        old=local_state(n0,q,c0,a)
        new=local_state(n1,q,c1,a)
        same_corr=local_state(n1,q,no_decouple["shared_catastrophe"],a)
        for x in (old,new,same_corr):
            if not math.isclose(x["probability_no_deliveries"],
                                exact_small_enumeration(x["donors"],q,
                                    x["shared_event_probability"],a),
                                abs_tol=1e-13):
                raise AssertionError("Closed-form and enumeration differ")
        rows.append({
            "per_donor_viable_arrival_probability":a,
            "before":old,
            "after_source_loss_plus_hypothetical_decoupling":new,
            "after_source_loss_but_NO_decoupling":same_corr,
            "delivery_shortage_delta_with_decoupling":
                new["probability_no_deliveries"]-old["probability_no_deliveries"],
            "delivery_shortage_delta_without_decoupling":
                same_corr["probability_no_deliveries"]-old["probability_no_deliveries"],
            "expected_arrival_difference":
                new["expected_successful_donor_arrivals"]-
                    old["expected_successful_donor_arrivals"],
        })
    for x in rows:
        if x["expected_arrival_difference"]>=0:
            raise AssertionError("Fixture fails source-number loss condition")
        if x["delivery_shortage_delta_without_decoupling"]<=0:
            raise AssertionError("Loss without correlation change unexpectedly helps")
    if not (rows[1]["delivery_shortage_delta_with_decoupling"]>0
            and rows[5]["delivery_shortage_delta_with_decoupling"]<0):
        raise AssertionError("Expected qualitative sign reversal absent")
    return {
        "schema":"structural.known_truth_source_loss_cofailure_arrival.v1_260",
        "status":"MODEL_KNOWN_TRUTH_COMPETING_SOURCE_NUMBER_AND_SYNCHRONY_CHANNELS",
        "single_timepoint_target_endpoint":"zero successful donor arrivals to one target",
        "not_endpoint":"not metapopulation extinction time, survival, realized recolonization or actual immigration",
        "mixture_model":{
            "common_extinction_shock_probability":"c",
            "marginal_donor_failure_probability":"q fixed per surviving donor",
            "given_no_common_shock_independent_failure_probability":
                "(q-c)/(1-c)",
            "arrival_conditional_on_local_survival":"independent Bernoulli(a)",
            "exact_no_delivery_probability":
                "c + (1-c)*(1-a*(1-q)/(1-c))**n",
            "failure_correlation":"c*(1-q)/(q*(1-c))",
            "expected_successful_arrivals":"n*(1-q)*a",
        },
        "registered_example":{
            "q":q,
            "before_source_count":n0,
            "after_source_count":n1,
            "before_c":c0,
            "after_c_hypothetical_decoupling":c1,
            "after_c_if_no_decoupling":no_decouple["shared_catastrophe"],
        },
        "nontrivial_arrival_success_threshold_a":boundary,
        "examples":rows,
        "biological_intervention_caution":
            "Fox 2017 transient local extinction with patch habitat intact differs from permanent physical donor loss; Matter & Roland 2010 temporary whole subpopulation removal differs again. Changing c is hypothetical and not proven by deleting a source.",
        "published_precedence":{
            "Fox_2017_DOI":"10.1038/s41559-017-0271-y",
            "Matter_Roland_2010_DOI":"10.1098/rspb.2009.1520",
            "both_opposing_mechanisms_already_published":True
        },
        "no_real_observation_rows_used":True,
        "no_causal_biological_effect_estimated":True,
        "not_confirmatory_data_or_validation":True,
        "original_global_mammal_heldout_untouched":True,
        "eBird_used":False,
        "GEB_scientific_HOLD":True,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    ans=run()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(ans,sort_keys=True,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
        "schema":ans["schema"],
        "interior_arrival_threshold_a":ans["nontrivial_arrival_success_threshold_a"],
        "at_0_30_delta_no_delivery":
            next(x["delivery_shortage_delta_with_decoupling"] for x
                 in ans["examples"] if x["per_donor_viable_arrival_probability"]==.3),
        "at_0_75_delta_no_delivery":
            next(x["delivery_shortage_delta_with_decoupling"] for x
                 in ans["examples"] if x["per_donor_viable_arrival_probability"]==.75),
        "closed_form_and_exact_enumeration_all_agree":True,
        "GEB_scientific_HOLD":True
    },sort_keys=True))
if __name__=="__main__":
    main()
