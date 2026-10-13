#!/usr/bin/env python3
"""v1.241: stronger published habitat-conditioned destination reference.

ONLY original frozen v1.231 documented natal immigrant origin→destination
edges. Historical 1994–2013 train; 2014 bridge excluded; later 2015–2021
are scored as an explicitly RETROSPECTIVE temporal comparison.

R0: source-independent historical recipient attractiveness, minus self.
H: R0 plus known farm-vs-nonfarm same-habitat likelihood coefficient fitted
   ONLY on 259 historical movements, fixed deterministic penalized grid.
R2: historical symmetric pair counts shrunk to H (no direction).
C2: historical directed count shrunk to R2.
Primary R2-H: predictive value of pair-specific mobility beyond habitat,
but still NOT distance-adjusted R3 or source rescue.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from helgeland_directional_route_portability_v1_240 import (
    git_blob_sha,matrix_by_era,route_distributions,normalize,
    SOURCE_BLOB_SHA,COHORT_TOTALS)

FARM=frozenset((20,26,27,28,33,38))
NON_FARM=frozenset((22,23,24,34,35))
TAUS=(5,10,20)
PRIMARY_TAU=10
BETA_GRID=tuple(x/100 for x in range(-400,401))

def same_habitat(i,j):
    if i==j:
        raise ValueError("No natal-origin==immigrant destination pairs")
    if (i not in FARM and i not in NON_FARM) or (j not in FARM and j not in NON_FARM):
        raise ValueError("Undefined historically published farm/nonfarm island class")
    return (i in FARM)==(j in FARM)

def habitat_destination(source,P0,beta):
    if not math.isfinite(beta):
        raise ValueError("Nonfinite habitat coefficient")
    return normalize({j:p*math.exp(beta*int(same_habitat(source,j)))
                      for j,p in P0.items()})

def historical_background(ids,history):
    # Formula exactly matches old v1.240 R0 for any tau; no later records read.
    return {i:route_distributions(ids,history,10)[i]["P0"] for i in ids}

def historical_habitat_coef(ids,history,P0):
    """Fixed 801-point historical-only ridge grid, penalty beta^2 / 2."""
    def criterion(beta):
        value=-beta*beta/2
        for i in ids:
            H=habitat_destination(i,P0[i],beta)
            for j,p in H.items():
                n=history[(i,j)]
                if n: value+=n*math.log(p)
        return value
    # If exact grid tie, prefer beta closest to zero, then smaller beta.
    best=max(BETA_GRID,key=lambda b:(criterion(b),-abs(b),-b))
    return best,criterion(best)

def predict(ids,history,P0,beta,tau):
    if tau not in TAUS:
        raise ValueError("Scoring with unregistered smoothing strength")
    H={}
    R2={}
    C2={}
    for i in ids:
        H[i]=habitat_destination(i,P0[i],beta)
        link={j:history[(i,j)]+history[(j,i)]+tau*H[i][j]
              for j in ids if j!=i}
        R2[i]=normalize(link)
        direction={j:history[(i,j)]+tau*R2[i][j]
                   for j in ids if j!=i}
        C2[i]=normalize(direction)
    return {i:{"P0":P0[i],"H":H[i],"R2":R2[i],"C2":C2[i]} for i in ids}

def evaluate(ids,test,models):
    N=sum(test.values())
    if N!=173:raise ValueError("Frozen independent later-birth-cohort size changed")
    scores={m:0.0 for m in ("P0","H","R2","C2")}
    source_folds=[]
    for i in ids:
        n=sum(test[(i,j)] for j in ids if j!=i)
        subtotals={m:0.0 for m in scores}
        for j in ids:
            if i==j:continue
            v=test[(i,j)]
            for m in scores:
                p=models[i][m][j]
                if not math.isfinite(p) or p<=0:
                    raise ValueError("Undefined source-conditional route probability")
                subtotal=-v*math.log(p)
                subtotals[m]+=subtotal
                scores[m]+=subtotal
        source_folds.append({
            "natal_origin_id":i,"observed_test_movers":n,
            "loss_per_test_migrant":{k:subtotals[k]/n if n else None for k in scores},
            "R2_minus_H":(subtotals["R2"]-subtotals["H"])/n if n else None,
            "H_minus_P0":(subtotals["H"]-subtotals["P0"])/n if n else None,
            "C2_minus_R2":(subtotals["C2"]-subtotals["R2"])/n if n else None,
            "_aggregate_unscaled_logloss":subtotals
        })
    avg={k:v/N for k,v in scores.items()}
    nonzero=[x for x in source_folds if x["observed_test_movers"]>0]
    exclusion=[]
    for f in nonzero:
        denom=N-f["observed_test_movers"]
        v=f["_aggregate_unscaled_logloss"]
        exclusion.append({
            "excluded_natal_origin_id":f["natal_origin_id"],
            "removed_test_movers":f["observed_test_movers"],
            "R2_minus_H":((scores["R2"]-v["R2"])-(scores["H"]-v["H"]))/denom,
            "C2_minus_R2":((scores["C2"]-v["C2"])-(scores["R2"]-v["R2"]))/denom
        })
    for x in source_folds:
        del x["_aggregate_unscaled_logloss"]
    return {
        "test_mover_count":N,
        "mean_test_logloss":avg,
        "primary_R2_minus_H":avg["R2"]-avg["H"],
        "secondary_H_minus_P0":avg["H"]-avg["P0"],
        "tertiary_C2_minus_R2":avg["C2"]-avg["R2"],
        "n_origins_with_test_movers":len(nonzero),
        "n_origins_where_pair_improves_H":sum(x["R2_minus_H"]<0 for x in nonzero),
        "n_origins_where_direction_improves_R2":sum(x["C2_minus_R2"]<0 for x in nonzero),
        "equal_origin_average_pair_minus_H":
            sum(x["R2_minus_H"] for x in nonzero)/len(nonzero),
        "all_11_source_island_folds":source_folds,
        "leave_one_origin_out":exclusion,
        "LOO_pair_delta_min_max":[min(x["R2_minus_H"] for x in exclusion),
                                   max(x["R2_minus_H"] for x in exclusion)]
    }

def run(doc):
    ids,eras=matrix_by_era(doc)
    if set(ids)!=FARM|NON_FARM or FARM&NON_FARM or len(ids)!=11:
        raise ValueError("Source island IDs do not match the original published farm classification")
    hist=eras["historical"]
    test=eras["later"]
    if sum(eras["bridge"].values())!=28:
        raise ValueError("2014 bridge cohort must stay excluded")
    P0=historical_background(ids,hist)
    beta,training_posterior=historical_habitat_coef(ids,hist,P0)
    results={}
    for tau in TAUS:
        models=predict(ids,hist,P0,beta,tau)
        results[str(tau)]=evaluate(ids,test,models)
    main=results[str(PRIMARY_TAU)]
    return {
        "schema":"structural.helgeland_habitat_conditioned_pair_route_v1_241",
        "status":"RETROSPECTIVE_CHRONOLOGICAL_HABITAT_REFERENCE_TEST_NO_RESCUE",
        "source_frozen_v231_git_blob":SOURCE_BLOB_SHA,
        "training_historical_n":259,"excluded_bridge_n":28,
        "testing_later_n":173,
        "source_classification":{"farm":sorted(FARM),"nonfarm":sorted(NON_FARM)},
        "historical_only_habitat_beta_grid_801":beta,
        "habitat_training_penalized_loglik":training_posterior,
        "base_P0":"destination popularity+1, exclude self",
        "habitat_H":"P0×exp(beta×same farm/nonfarm), normalized",
        "pair_R2":"undirected historical pair + tau H prior, normalized",
        "direction_C2":"historical directed pair + tau R2 prior, normalized",
        "tau_primary":PRIMARY_TAU,
        "all_precommitted_tau_results":results,
        "primary_R2_minus_H":main["primary_R2_minus_H"],
        "secondary_H_minus_P0":main["secondary_H_minus_P0"],
        "tertiary_C2_minus_R2":main["tertiary_C2_minus_R2"],
        "reference_excludes_geographical_distance_and_timevarying_observation_effort":True,
        "higher_quality_than_destination_popularity_not_full_R3":True,
        "no_new_original_individual_bird_rows_opened":True,
        "published_Ranke_2021_habitat_and_isolation_prior_art":True,
        "one_helgeland_archipelago_already_published":True,
        "no_true_donor_loss_0to1_colonization_immigrant_fitness_or_causal_rescue":True,
        "no_confirmatory_pvalue":True,
        "GEB_scientific_HOLD":True,
        "original_mammal_heldout_not_opened":True,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    raw=a.source.read_bytes()
    if git_blob_sha(raw)!=SOURCE_BLOB_SHA:
        raise ValueError("Frozen v1.231 Git source SHA drift")
    result=run(json.loads(raw))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":result["schema"],
        "historical_only_same_habitat_coef":result["historical_only_habitat_beta_grid_801"],
        "primary_pair_minus_habitat_tau10":result["primary_R2_minus_H"],
        "secondary_habitat_minus_destination":result["secondary_H_minus_P0"],
        "tertiary_direction_minus_pair":result["tertiary_C2_minus_R2"],
        "all_tau_pair_minus_H":{t:r["primary_R2_minus_H"] for t,r in result["all_precommitted_tau_results"].items()}
    },sort_keys=True))
if __name__=="__main__":
    main()
