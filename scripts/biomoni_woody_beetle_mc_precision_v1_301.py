#!/usr/bin/env python3
"""Source-free numerical precision of already observed v1.300 plot permutations."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"development/biomoni_woody_beetle_v1_300_observed_aggregate_freeze.json"
PROTOCOL=ROOT/"development/biomoni_woody_beetle_mc_precision_protocol_v1_301.json"

def wilson(successes,attempts,z=1.959963984540054):
    p=successes/attempts
    center=p+z*z/(2*attempts)
    half=z*math.sqrt(p*(1-p)/attempts+z*z/(4*attempts*attempts))
    return (max(0.0,(center-half)/(1+z*z/attempts)),min(1.0,(center+half)/(1+z*z/attempts)))

def audit(source,proto):
    if (source.get("schema")!="structural.biomoni_colocated_source_observed_aggregate.v1_300"
        or source.get("source_run_id")!=40081020518
        or source.get("original_inner_json_sha256")!="df577a6cf44c70defcd5c675ab1ff8dc6bab810d2f11434bcadd2ed2eadb4954"
        or proto.get("schema")!="structural.biomoni_beta_permutation_mc_precision.v1_301"
        or proto.get("status")!="SOURCE_FREE_PRECALCULATION_FROZEN"
        or source.get("GEB_scientific_HOLD") is not True
        or source.get("new_confirmatory_systems")!=0):
        raise ValueError("Original full outcome identity or source-free protocol changed")
    n=source["permutation_n"]; rank=source["permutation_plot_label_rank"]
    if n!=999 or source["permutation_seed"]!=20261024 or source["independent_plots"]!=10:
        raise ValueError("Original n/seed/site count changed")
    k_exact=rank*(n+1)-1
    k=round(k_exact)
    if abs(k-k_exact)>1e-9 or not 0<=k<=n:
        raise ValueError("Original plot permutation exceedance count not recoverable")
    lo,hi=wilson(k,n)
    baseline=source["baseline_geo_only_LOPO_MSE"]
    enhanced=source["added_beetle_LOPO_MSE"]
    gain=source["primary_LOPO_gain"]
    null95=source["permutation_null_gain_95pct"]
    if not math.isclose(baseline-enhanced,gain,rel_tol=0,abs_tol=1e-14):
        raise ValueError("LOPO improvement changed")
    if not math.isclose(gain/baseline,source["relative_gain"],rel_tol=0,abs_tol=1e-12):
        raise ValueError("Relative gain changed")
    if source["old_full_method_gate_status"]!="TERMINAL":
        raise ValueError("Original full method scientific STOP cannot be overridden")
    return {
        "schema":"structural.biomoni_beta_permutation_mc_precision_result.v1_301",
        "status":"SOURCE_FREE_FINITE_PERMUTATION_PRECISION_COMPLETE",
        "source_v1_300_SHA256":source["original_inner_json_sha256"],
        "original_woody_beta_baseline_MSE":baseline,
        "original_woody_beta_plus_beetle_MSE":enhanced,
        "original_MSE_gain":gain,
        "original_relative_MSE_gain":source["relative_gain"],
        "frozen_null_95pct_gain":null95,
        "gain_exceeds_frozen_95pct_null_by":gain-null95,
        "original_plus_one_permutation_rank":rank,
        "null_label_permutations":n,
        "null_gain_ge_observed_count":k,
        "raw_null_exceedance_fraction":k/n,
        "conditional_mc_wilson_95_interval_for_raw_null_fraction":[lo,hi],
        "conditional_mc_wilson_upper_crosses_0_05":hi>0.05,
        "mc_interval_is_not_ecological_uncertainty":True,
        "random_permutation_null_assumes_plot_label_exchangeability":True,
        "spatial_fragment_confounding_not_controlled":True,
        "no_site_or_taxon_data_reopened":True,
        "no_new_permutations_or_models_fit":True,
        "old_v1_298_full_method_gate_terminal":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,default=SOURCE)
    ap.add_argument("--contract",type=Path,default=PROTOCOL)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=audit(json.loads(args.input.read_text()),json.loads(args.contract.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:result[k] for k in ("status","original_MSE_gain",
       "original_relative_MSE_gain","gain_exceeds_frozen_95pct_null_by",
       "original_plus_one_permutation_rank","null_gain_ge_observed_count",
       "conditional_mc_wilson_95_interval_for_raw_null_fraction")},sort_keys=True))
if __name__=="__main__":main()
