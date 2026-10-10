#!/usr/bin/env python3
"""v1.218 retrospective 6-patch guild-marginal/co-presence decomposition by corridor."""
import argparse
import json
from itertools import product
from pathlib import Path
from run_wolfe_ambiguous_row_bounds_v1_212 import load_source

MATRIX = ("none", "low", "high")
TREAT = ("homogeneous", "heterogeneous")
CORRIDORS = ("low", "high")
STATES = ((0, 0), (0, 1), (1, 0), (1, 1))
MISSING_KEYS = (
    (6, "heterogeneous", "none", "high"),
    (6, "homogeneous", "high", "high"),
)
KEYS = tuple((6, h, m, c) for h in TREAT for m in MATRIX for c in CORRIDORS)
METRICS = ("G", "S", "J", "marginal_product", "association_remainder")

def summarize(source):
    """Each completed arm has 12 independent microcosms, 4 in each matrix stratum."""
    metrics = {}
    for h in TREAT:
        for c in CORRIDORS:
            total = dict.fromkeys(METRICS, 0.0)
            for m in MATRIX:
                xs = source[(6, h, m, c)]
                if len(xs) != 4:
                    raise ValueError("Incomplete four-replicate matrix stratum")
                g = sum(x[0] for x in xs)
                s = sum(x[1] for x in xs)
                j = sum(x[2] for x in xs)
                if any((len(x) != 3 or x[0] not in (0, 1) or x[1] not in (0, 1)
                        or x[2] != x[0]*x[1]) for x in xs):
                    raise ValueError("Invalid binary joint guild state")
                # Number of joints predicted by the empirical independent marginals.
                expected = g*s/4
                for k,val in (("G",g),("S",s),("J",j),
                              ("marginal_product",expected),
                              ("association_remainder",j-expected)):
                    total[k] += val/12
            metrics[(h,c)] = total
            if abs(total["J"]-total["marginal_product"]-total["association_remainder"])>1e-12:
                raise AssertionError("Decomposition mismatch")
    hetero = {k:metrics[("heterogeneous","low")][k] -
                 metrics[("heterogeneous","high")][k] for k in METRICS}
    het_advantage = {k:(metrics[("heterogeneous","low")][k] -
                        metrics[("homogeneous","low")][k]) -
                       (metrics[("heterogeneous","high")][k] -
                        metrics[("homogeneous","high")][k])
                     for k in METRICS}
    return hetero,het_advantage,metrics

def compute(groups):
    """Exactly enumerate all 4^2 missing G,S states in two 6-patch high corridor cells."""
    if any(k not in groups for k in KEYS):
        raise ValueError("Missing focal source cells")
    base = {k: list(groups[k]) for k in KEYS}
    for k in KEYS:
        expected = 3 if k in MISSING_KEYS else 4
        if len(base[k]) != expected:
            raise ValueError("Original focal missingness layout changed")
    observed = {}
    for h in TREAT:
        for c in CORRIDORS:
            xs = [x for m in MATRIX for x in base[(6,h,m,c)]]
            if any(x[2] != x[0]*x[1] for x in xs):
                raise ValueError("Invalid input joint state")
            observed[h+"_"+c] = {
                "observed_microcosms":len(xs),
                "G_present":sum(x[0] for x in xs),
                "S_present":sum(x[1] for x in xs),
                "both_present":sum(x[2] for x in xs),
                "G_only":sum(x[0] and not x[1] for x in xs),
                "S_only":sum(x[1] and not x[0] for x in xs),
                "neither":sum(not x[0] and not x[1] for x in xs)
            }
    permutations=[]
    for completion in product(STATES, repeat=len(MISSING_KEYS)):
        cells={k:list(v) for k,v in base.items()}
        for k,(g,s) in zip(MISSING_KEYS,completion):
            cells[k].append((g,s,g*s))
        hetero,advantage,metrics=summarize(cells)
        permutations.append({"hetero":hetero,"advantage":advantage,"metrics":metrics})
    if len(permutations)!=16:
        raise AssertionError("Unexpected number of joint missing-state completions")
    def envelope(field):
        return {
            k:[min(x[field][k] for x in permutations),
               max(x[field][k] for x in permutations)]
            for k in METRICS
        }
    return {
        "schema":"structural.wolfe_six_patch_guild_remainder_v1_218",
        "status":"EXPLORATORY_EXPOSED_OUTCOME_SHARP_MISSING_STATE_BOUNDS",
        "source":"Wolfe 2022 exact blob e78003d425b646b390ae02e36c007892c1c70926",
        "observed_source_microcosms":observed,
        "focal_missing_original_groups":[list(k) for k in MISSING_KEYS],
        "joint_missing_state_completions":len(permutations),
        "units":"proportions of 12 intended independent metacommunity microcosms; matrix strata equally weighted",
        "six_heterogeneous_low_minus_high_corridor":envelope("hetero"),
        "heterogeneity_advantage_low_minus_high_corridor":envelope("advantage"),
        "decomposition":"J = mean_matrix(P(G)*P(S)) + mean_matrix(Cov(G,S)), within each corridor/heterogeneity arm",
        "interpretation":"statistical binary co-presence; covariance may reflect stochastic outcomes/day/shared conditions, NOT causal guild interaction or segregation",
        "source_treatment_reassigned":False,
        "confidence_intervals_or_p_values":False,
        "postoutcome_and_posthoc":True,
        "original_mammal_predictions_or_holdout_opened":False,
        "eBird_used":False,
        "GEB_scientific_HOLD":True,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source_csv",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=compute(load_source(a.source_csv.read_bytes()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":
    main()
