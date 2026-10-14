#!/usr/bin/env python3
"""v1.240: temporal portability of observed natal island -> recipient direction.

Strictly uses v1.231 source-fingerprinted ALREADY PUBLISHED/EXPOSED counts.
Historical birth cohorts 1994-2013 train, later 2015-2021 are heldout;
2014 bridge is sealed OUT of comparison, not a source of tuning.
Predict recorded migrant DESTINATION given that a migrant was observed and
natal source is known. Not movement probability, fitness, true rescue, or R3.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

SOURCE_BLOB_SHA="955d58e958b2f241cda726706bec0260fea79dd5"
SCHEMA="structural.helgeland_historic_directional_transport_temporal_v1_240"
PREDECLARED_TAUS=(5,10,20)
PRIMARY_TAU=10
COHORT_TOTALS={"historical":259,"bridge":28,"later":173}

def git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

def matrix_by_era(source):
    if source.get("schema")!="structural.helgeland_nestling_origin_nextyear_resight_freeze.v1_231":
        raise ValueError("Wrong frozen source schema")
    original=source.get("data",{})
    if original.get("n_model_islands")!=11 or original.get("source_rows")!=73593:
        raise ValueError("Source island/record universe changed")
    ids=sorted({x["origin"] for x in original["per_origin"]})
    if len(ids)!=11:
        raise ValueError("Expected exactly eleven original source IDs")
    periods={}
    for era,N in COHORT_TOTALS.items():
        allowed={(i,j):0 for i in ids for j in ids if i!=j}
        for e in original["observed_cross_island_edges"]:
            if e["era"]!=era:continue
            pair=(e["origin"],e["destination"])
            n=e["observed_n"]
            if pair not in allowed or allowed[pair]!=0:
                raise ValueError("Duplicate or self-directed immigrant cell")
            if type(n) is not int or n<=0:
                raise ValueError("Documented migration count invalid")
            allowed[pair]=n
        if sum(allowed.values())!=N:
            raise ValueError("Original fixed migrant total changed")
        expected={r["origin"]:r["exported"] for r in original["per_origin"] if r["era"]==era}
        if set(expected)!=set(ids):
            raise ValueError("All 11 source cohorts required")
        for i in ids:
            if sum(allowed[(i,j)] for j in ids if j!=i)!=expected[i]:
                raise ValueError("Birth-island export totals disagree with directed rows")
        periods[era]=allowed
    return ids,periods

def normalize(weights):
    if any(not math.isfinite(float(v)) or v<0 for v in weights.values()):
        raise ValueError("Negative or invalid weight")
    denominator=sum(weights.values())
    if denominator<=0:
        raise ValueError("No allowed destination probability mass")
    return {k:v/denominator for k,v in weights.items()}

def route_distributions(ids,history,tau):
    """All predictions strictly based on historical movements. No later input."""
    if tau<=0:raise ValueError("Frozen smoothing strength must be positive")
    history_dest={j:sum(history[(i,j)] for i in ids if i!=j) for j in ids}
    out={}
    for source in ids:
        recipients=[j for j in ids if j!=source]
        P0=normalize({j:history_dest[j]+1 for j in recipients})
        undirected={j:history[(source,j)]+history[(j,source)] for j in recipients}
        R1=normalize({j:undirected[j]+tau*P0[j] for j in recipients})
        directed={j:history[(source,j)] for j in recipients}
        C=normalize({j:directed[j]+tau*R1[j] for j in recipients})
        for name,x in (("P0",P0),("R1",R1),("C",C)):
            if (len(x)!=len(ids)-1 or
                    not math.isclose(sum(x.values()),1,abs_tol=1e-12) or
                    any(not math.isfinite(p) or p<=0 for p in x.values())):
                raise AssertionError("Invalid "+name+" distribution")
        out[source]={"P0":P0,"R1":R1,"C":C}
    return out

def heldout_scores(ids,training,heldout,distributions):
    total=sum(heldout.values())
    if total!=COHORT_TOTALS["later"]:
        raise ValueError("Chronological test cohort count changed")
    total_loss={m:0.0 for m in ("P0","R1","C")}
    per_source=[]
    unseen=0
    unseen_undirected=0
    for i in ids:
        n_source=sum(heldout[(i,j)] for j in ids if i!=j)
        losses={m:0.0 for m in ("P0","R1","C")}
        for j in ids:
            if i==j:continue
            n=heldout[(i,j)]
            if n==0:continue
            if training[(i,j)]==0:unseen+=n
            if training[(i,j)]+training[(j,i)]==0:unseen_undirected+=n
            for model in losses:
                loss=-n*math.log(distributions[i][model][j])
                losses[model]+=loss
                total_loss[model]+=loss
        per_source.append({
            "natal_island_id":i,"heldout_documented_migrants":n_source,
            "heldout_logloss":{m:losses[m]/n_source if n_source else None
                               for m in losses},
            "direction_C_minus_undirected_R1":
                (losses["C"]-losses["R1"])/n_source if n_source else None,
            "undirected_R1_minus_destination_P0":
                (losses["R1"]-losses["P0"])/n_source if n_source else None
        })
    av={name:val/total for name,val in total_loss.items()}
    represented=[x for x in per_source if x["heldout_documented_migrants"]>0]
    return {
        "heldout_events":total,
        "test_movers_using_historical_direction_unseen":unseen,
        "test_movers_using_historical_undirected_pair_unseen":unseen_undirected,
        "test_logloss_mean_per_recorded_migrant":av,
        "primary_C_minus_R1":av["C"]-av["R1"],
        "secondary_R1_minus_P0":av["R1"]-av["P0"],
        "equal_source_mean_primary_C_minus_R1":
            sum(x["direction_C_minus_undirected_R1"] for x in represented)/len(represented),
        "represented_natal_islands":len(represented),
        "per_all_11_natal_islands":per_source
    }

def analyze(source):
    ids,periods=matrix_by_era(source)
    hist=periods["historical"]
    later=periods["later"]
    # 2014 cohort intentionally not used even to estimate priors.
    if sum(periods["bridge"].values())!=28:
        raise ValueError("Bridge cohort altered")
    output={}
    for tau in PREDECLARED_TAUS:
        distributions=route_distributions(ids,hist,tau)
        output[str(tau)]=heldout_scores(ids,hist,later,distributions)
    actual=output[str(PRIMARY_TAU)]
    return {
        "schema":SCHEMA,
        "status":"POSTPUBLICATION_RETROSPECTIVE_TEMPORAL_SOURCE_DIRECTIONALITY_AUDIT",
        "verified_input_git_blob_sha1":SOURCE_BLOB_SHA,
        "model_island_IDs":ids,
        "train_historical_migrant_birth_cohorts":259,
        "excluded_birth_cohort_2014":28,
        "test_later_birth_cohort_migrants":173,
        "training_predictor_information":"Historical destination frequency, historical undirected historical natal-source/recipient pair counts and historical directed pair counts only",
        "destination_popularity_ref_P0":"(historic total incoming to j +1) normalized excluding natal source",
        "undirected_pair_ref_R1":"(historic pair i->j plus j->i + tau*P0)/(sum historic pair + tau)",
        "directional_C":"(historic i->j count + tau*R1)/(total historic i exports + tau)",
        "fixed_alpha_receiver_popularity":1,
        "declared_tau_primary":PRIMARY_TAU,
        "declared_tau_sensitivities":[5,20],
        "all_precommitted_sensitivity_results":output,
        "primary_C_minus_R1_logloss":actual["primary_C_minus_R1"],
        "secondary_R1_minus_P0_logloss":actual["secondary_R1_minus_P0"],
        "no_test_label_used_in_training_features":True,
        "test_destination_conditional_on_being_OBSERVED_natal_emigrant":True,
        "no_true_emigration_probability_or_fitness_estimated":True,
        "published_natal_direction_study_precedes_this_analysis":True,
        "one_archipelago_not_independent_system_confirmation":True,
        "no_geo_distance_habitat_environment_full_R3_reference":True,
        "no_p_value_or_confirmatory_confidence_interval":True,
        "no_new_source_biological_rows_opened":True,
        "original_mammal_heldout_data_not_read":True,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("frozen_source",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    raw=args.frozen_source.read_bytes()
    if git_blob_sha(raw)!=SOURCE_BLOB_SHA:
        raise ValueError("Immutable v1.231 source Git blob fingerprint mismatch")
    result=analyze(json.loads(raw))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":result["schema"],"status":result["status"],
        "all_tau_CminusR1":{tau:r["primary_C_minus_R1"] for tau,r in
                           result["all_precommitted_sensitivity_results"].items()},
        "primary_tau_10":result["primary_C_minus_R1_logloss"],
        "secondary_tau_10":result["secondary_R1_minus_P0_logloss"],
        "n_future_movers":result["test_later_birth_cohort_migrants"]
    },sort_keys=True))
if __name__=="__main__":
    main()
