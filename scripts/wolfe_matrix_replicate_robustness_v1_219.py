#!/usr/bin/env python3
"""v1.219 source-locked posthoc Wolfe six-patch matrix jackknife and replicate audit.

Only already-exposed 2022 outcomes; strictly no new causal or confirmatory claim.
"""
import argparse
import csv
import io
import json
import math
from pathlib import Path

from run_wolfe_ambiguous_row_bounds_v1_212 import load_source

MATRIX = ("none", "low", "high")
HET = ("heterogeneous", "homogeneous")
COR = ("low", "high")
N = (4, 6)

def interval(groups,n,h,m,c,endpoint=2):
    v=groups[(n,h,m,c)]
    if len(v) not in (3,4):
        raise ValueError("Expected 3/4 independent microcosms per treatment arm")
    count=sum(x[endpoint] for x in v)
    if not all(x[endpoint] in (0,1) for x in v):
        raise ValueError("Invalid binary endpoint")
    return [count/4,(count+4-len(v))/4]

def add(x,y): return [x[0]+y[0],x[1]+y[1]]
def negate(x): return [-x[1],-x[0]]
def sub(x,y): return add(x,negate(y))
def mean(xs): return [sum(x[i] for x in xs)/len(xs) for i in (0,1)]

def matrix_contrasts(groups,n,endpoint=2):
    # Each source interval is exactly the set of possible complete 4-replicate means.
    by_matrix={}
    for m in MATRIX:
        l_het=interval(groups,n,"heterogeneous",m,"low",endpoint)
        h_het=interval(groups,n,"heterogeneous",m,"high",endpoint)
        l_hom=interval(groups,n,"homogeneous",m,"low",endpoint)
        h_hom=interval(groups,n,"homogeneous",m,"high",endpoint)
        he=sub(l_het,h_het)
        ho=sub(l_hom,h_hom)
        by_matrix[m]={"heterogeneous_low_minus_high":he,
                      "homogeneous_low_minus_high":ho,
                      "difference_in_differences":sub(he,ho)}
    out={}
    for k in by_matrix[MATRIX[0]]:
        out[k]={
            "all_three_equal_weight":mean([by_matrix[m][k] for m in MATRIX]),
            "leave_one_matrix_out":{
                removed:mean([by_matrix[m][k] for m in MATRIX if m!=removed])
                for removed in MATRIX
            }
        }
    return {"matrix_cells":by_matrix,"summaries":out}

def paired_replicates_verified_raw(raw):
    # Content fingerprint, layout, and ambiguous excluded metadata are checked by
    # load_source BEFORE parsing any outcomes, even though raw is already exposed.
    load_source(raw)
    rows=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    indexed={}
    for r in rows:
        if r[""]=="6HoLM1": continue
        n=int(r["patch_number"])
        if n not in N or r["corridor_dispersal"] not in COR:continue
        key=(n,r["heterogeneity"],r["matrix_dispersal"],
             r["corridor_dispersal"],int(r["replicate"]))
        if key in indexed:raise ValueError("Duplicate replicate identity")
        g=int(float(r["stentor_coeruleus"])>0)
        s=int(float(r["didinium_nasutum"])>0 or float(r["dileptus_anser"])>0)
        indexed[key]=(g,s,g*s)
    return indexed

def paired_summary(rows,n,h,endpoint=2,missing_high_state=None):
    seen=[]
    missing=[]
    for m in MATRIX:
        for replicate in range(1,5):
            lk=(n,h,m,"low",replicate)
            hk=(n,h,m,"high",replicate)
            lo=rows.get(lk)
            hi=rows.get(hk)
            if hi is None and lo is not None and missing_high_state is not None:
                hi=(missing_high_state,missing_high_state,missing_high_state)
            if lo is None or hi is None:
                missing.append([m,replicate])
                continue
            seen.append(lo[endpoint]-hi[endpoint])
    pos=seen.count(1)
    neg=seen.count(-1)
    ties=seen.count(0)
    k=pos+neg
    # Two-sided sign test ONLY under hypothetical independent exchangeable
    # replicate-indexed low/high corridor labels. This assignment property
    # is not documented. This is not a design-verified p-value.
    tail=sum(math.comb(k,j) for j in range(min(pos,neg)+1))
    p=min(1.0,2*tail/2**k) if k else 1.0
    return {
        "paired_units":len(seen),"unpaired_keys":missing,
        "low_positive_only":pos,"high_positive_only":neg,"tied":ties,
        "signed_sum":sum(seen),
        "hypothetical_exchangeable_sign_test_two_sided":p
    }

def compute(groups,raw):
    measured=matrix_contrasts(groups,6)
    comparator=matrix_contrasts(groups,4)
    rows=paired_replicates_verified_raw(raw)
    hypothetical={}
    for n in N:
        for h in HET:
            hypothetical[f"{n}_{h}"]=paired_summary(rows,n,h)
    missing_cases=[
        paired_summary(rows,6,"heterogeneous",missing_high_state=x)
        for x in (0,1)
    ]
    # The six vs four difference has distinct experimental size-heterogeneity
    # doses (2:1 vs 3:1), so use as descriptive scale check ONLY.
    jack6=measured["summaries"]["difference_in_differences"]["all_three_equal_weight"]
    jack4=comparator["summaries"]["difference_in_differences"]["all_three_equal_weight"]
    return {
        "schema":"structural.wolfe_regime_matrix_replicate_robustness.v1_219",
        "status":"RETROSPECTIVE_POSTOUTCOME_DIAGNOSTIC_NOT_CONFIRMATORY",
        "source_blob_sha1":"e78003d425b646b390ae02e36c007892c1c70926",
        "endpoint":"day21 metacommunity G AND at least one S",
        "six_patch":measured,
        "four_patch_descriptive_comparator":comparator,
        "six_minus_four_heterogeneity_by_corridor_interaction":sub(jack6,jack4),
        "complete_case_replicate_matched":hypothetical,
        "six_heterogeneous_missing_high_corridor_J_equal_zero_or_one":missing_cases,
        "absence_or_assignment_missingness_bounds_not_sampling_CI":True,
        "pair_sign_probabilities_are_not_design_verified_randomization_p_values":True,
        "replicate_index_matching_does_not_prove_experimental_randomization":True,
        "matrix_leave_one_out_selected_postoutcome":True,
        "patch_count_heterogeneity_dose_confounded":True,
        "no_causal_corridor_or_rescue_claim":True,
        "original_mammal_heldout_opened":False,"eBird_used":False,
        "GEB_submission_authorized":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source_csv",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    raw=a.source_csv.read_bytes()
    answer=compute(load_source(raw),raw)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(answer,indent=2,sort_keys=True)+"\n")
    print(json.dumps(answer,sort_keys=True))

if __name__=="__main__":main()
