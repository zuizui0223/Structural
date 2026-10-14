#!/usr/bin/env python3
"""v1.245: does temporal ALIGNMENT of marked nestling source volume matter?

Entire 2026 author source byte-identical; repeat published v1.244 fit then
evaluate all 7! possible reassignments of seven source-volume years across
observed next-year recipient outcomes. The permutation percentile is ONLY a
postoutcome descriptive diagnostic, not a randomization p value.
"""
import argparse,hashlib,itertools,json,math,statistics
from pathlib import Path

from helgeland_annual_natal_supply_v1_244 import (
    compute,predict_receiving,blob,SHA_V231_FREEZE,SHA_PRESENCE,SHA_POPULATION)
from helgeland_directional_route_portability_v1_240 import matrix_by_era
from helgeland_habitat_pair_portability_v1_241 import (
    historical_background,historical_habitat_coef,predict)

ROUTES=("P0","H","R2","C2")
YEARS=(2015,2016,2017,2018,2019,2020,2021)
EXPECTED_TEST_COUNTS=(15,27,34,12,27,41,17)
PERMS=5040
PRIMARY="R2"
MAIN_V244_DELTA=-0.045237920688274036

def conditional_loss(observations,probabilities):
    value=0.0
    for dest,count in observations.items():
        if count<0 or type(count) is not int:
            raise ValueError("Noninteger or negative future recorded migrants")
        if count:
            p=probabilities.get(dest,0)
            if p<=0 or not math.isfinite(p):
                raise ValueError("Zero or nonfinite assigned probability")
            value-=count*math.log(p)
    return value

def permutation_diagnostic(cost):
    n=len(cost)
    if any(len(row)!=n for row in cost):
        raise ValueError("Must have complete n by n source-year alignment cost")
    values=[]
    observed=sum(cost[i][i] for i in range(n))
    for permutation in itertools.permutations(range(n)):
        values.append(sum(cost[i][permutation[i]] for i in range(n)))
    if len(values)!=math.factorial(n):
        raise AssertionError("Did not enumerate every assignment")
    ordered=sorted(values)
    below=sum(v<observed-1e-12 for v in values)
    tied=sum(abs(v-observed)<=1e-12 for v in values)
    return {
       "assignments":len(values),
       "observed_identity_alignment_total_logloss":observed,
       "more_favorable_assignments":below,
       "exact_tied_assignments":tied,
       "fraction_at_least_as_favorable_including_ties":(below+tied)/len(values),
       "observed_alignment_midrank_ascending":below+(tied+1)/2,
       "minimum_total_logloss":ordered[0],
       "median_total_logloss":statistics.median(ordered),
       "maximum_total_logloss":ordered[-1],
       "descriptive_2_5_to_97_5_total_loss_quantiles":[
           ordered[int(.025*(len(values)-1))],ordered[int(.975*(len(values)-1))]
       ],
       "exchangeability_or_permutation_pvalue_NOT_claimed":True
    }

def omission_deltas(per_year):
    n=sum(v["n"] for v in per_year)
    S=sum(v["n"]*v["delta"] for v in per_year)
    if n!=173:
        raise ValueError("Original later migrating cohort count drift")
    output=[]
    for k in (1,2):
        for omit in itertools.combinations(per_year,k):
            n_rem=sum(x["n"] for x in omit)
            S_rem=sum(x["n"]*x["delta"] for x in omit)
            output.append({"omitted_years":[x["year"] for x in omit],
                           "remaining_documented_migrants":n-n_rem,
                           "dynamic_minus_static":(S-S_rem)/(n-n_rem)})
    if len(output)!=28:
        raise ValueError("Expected all 7+21 omissions")
    return output

def analyze(author_presence,author_pop,v231):
    prior=compute(author_presence,author_pop,v231)
    yrs=prior["all_seven_test_birth_years"]
    if [r["birth_year"] for r in yrs]!=list(YEARS):
        raise ValueError("Out-of-order later natal cohort years")
    if tuple(r["test_documented_nextyear_immigrants"] for r in yrs)!=EXPECTED_TEST_COUNTS:
        raise ValueError("Future original observed immigrant counts differ")
    if abs(prior["main_primary_dynamic_minus_static"]-MAIN_V244_DELTA)>1e-10:
        raise ValueError("Original frozen v1.244 primary result changed")
    ids,eras=matrix_by_era(v231)
    background=historical_background(ids,eras["historical"])
    beta,_=historical_habitat_coef(ids,eras["historical"],background)
    if beta!=1.85:
        raise ValueError("Original v1.241 beta frozen historic-only mismatch")
    models=predict(ids,eras["historical"],background,beta,10)
    route={name:{i:models[i][name] for i in ids} for name in ROUTES}
    h={int(k):v for k,v in prior["historical_emigration_yields_of_marked_cohorts"].items()}
    static_source={int(k):v for k,v in prior["historical_annual_mean_marked_by_natal_island"].items()}
    source_marked=[{int(k):v for k,v in r["known_at_birth_natal_marked_by_island"].items()}
                   for r in yrs]
    obs_dest=[{int(k):v for k,v in r["test_documented_immigrants_by_recipient"].items()}
              for r in yrs]
    all_results={}
    for route_name in ROUTES:
        original_route=route[route_name]
        static_p=predict_receiving(ids,original_route,static_source,h)
        static_total=sum(conditional_loss(record,static_p) for record in obs_dest)
        static_mean=static_total/173
        if abs(static_mean-prior["all_predeclared_route_sensitivities"][route_name]["test_static_logloss"])>1e-10:
            raise ValueError("Frozen original static-route prediction changed")
        source_pattern_predictions=[
            predict_receiving(ids,original_route,source,h) for source in source_marked
        ]
        costs=[
            [conditional_loss(obs,probability) for probability in source_pattern_predictions]
            for obs in obs_dest
        ]
        aligned=sum(costs[i][i] for i in range(len(YEARS)))/173
        main_delta=aligned-static_mean
        if abs(main_delta-prior["all_predeclared_route_sensitivities"][route_name]["dynamic_minus_static"])>1e-10:
            raise ValueError("Frozen original dynamic-route prediction changed")
        diag=permutation_diagnostic(costs)
        for key in ("observed_identity_alignment_total_logloss","minimum_total_logloss",
                    "median_total_logloss","maximum_total_logloss"):
            diag[key+"_per_observed_immigrant"]=diag[key]/173
        per_year=[{"year":r["birth_year"],
                   "n":r["test_documented_nextyear_immigrants"],
                   "delta":r["all_routes"][route_name]["dynamic_minus_static"]}
                  for r in yrs]
        omissions=omission_deltas(per_year)
        ablation=[]
        for origin in ids:
            no_origin_total=0.0
            for obs,source in zip(obs_dest,source_marked):
                marked=dict(source)
                marked[origin]=static_source[origin]
                predicted=predict_receiving(ids,original_route,marked,h)
                no_origin_total+=conditional_loss(obs,predicted)
            ablated=no_origin_total/173
            ablation.append({
                "origin":origin,
                "original_annual_marks_replaced_by_20_year_training_mean":True,
                "loss_after_replacing_origin_annual_activity":ablated,
                "loss_replacing_minus_all_dynamic":ablated-aligned
            })
        all_results[route_name]={
            "static_loss":static_mean,"matched_dynamic_loss":aligned,
            "matched_dynamic_minus_static":main_delta,
            "all_5040_year_alignment_assignments":diag,
            "all_single_and_double_year_omissions":omissions,
            "all_11_source_annual_volume_ablations":ablation,
            "n_years_with_aligned_dynamic_benefit":
                sum(r["delta"]<0 for r in per_year),
            "yearly_original_signed_results":per_year
        }
    return {
        "schema":"structural.helgeland_source_supply_alignment_and_ablation.v1_245",
        "status":"POSTOUTCOME_EXACT_YEAR_ALIGNMENT_DESCRIPTIVE_DIAGNOSTICS",
        "input_2026_original_presence_git_sha":SHA_PRESENCE,
        "input_2026_original_population_git_sha":SHA_POPULATION,
        "input_frozen_v231_git_sha":SHA_V231_FREEZE,
        "original_v244_pooled_R2_delta":MAIN_V244_DELTA,
        "observed_years":list(YEARS),
        "all_four_predeclared_routes":all_results,
        "primary_route_R2_observed_percentile_among_all_5040_assignments":
             all_results[PRIMARY]["all_5040_year_alignment_assignments"][
               "fraction_at_least_as_favorable_including_ties"],
        "primary_R2_2019_and_2020_omission_as_one_of_all_21_diagnostics":
             next(x for x in all_results[PRIMARY]["all_single_and_double_year_omissions"]
                  if x["omitted_years"]==[2019,2020]),
        "year_permutations_not_randomly_assigned":True,
        "already_published_and_postoutcome_audit":True,
        "annual_marked_nestlings_not_true_source_viability":True,
        "no_causal_source_extinction_or_recipient_demographic_rescue_estimated":True,
        "original_mammal_heldout_data_unopened":True,
        "GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("author",type=Path)
    p.add_argument("frozen_v231",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    raw=a.frozen_v231.read_bytes()
    if blob(raw)!=SHA_V231_FREEZE:
        raise ValueError("Original v1.231 frozen source Git blob drift")
    base=a.author/"Data"
    out=analyze((base/"presence_data_1994_2022.txt").read_bytes(),
                (base/"estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy.txt").read_bytes(),
                json.loads(raw))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
       "schema":out["schema"],
       "R2_percentile":out["primary_route_R2_observed_percentile_among_all_5040_assignments"],
       "R2_ranking":out["all_four_predeclared_routes"]["R2"]["all_5040_year_alignment_assignments"],
       "R2_two_year_2019_2020_omitted":out["primary_R2_2019_and_2020_omission_as_one_of_all_21_diagnostics"],
       "route_year_alignment_percentiles":{name:rr["all_5040_year_alignment_assignments"]["fraction_at_least_as_favorable_including_ties"]
         for name,rr in out["all_four_predeclared_routes"].items()}
       },sort_keys=True))
if __name__=="__main__":main()
