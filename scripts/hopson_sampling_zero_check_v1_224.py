#!/usr/bin/env python3
"""v1.224 retrospective conditional Poisson sampling diagnostic, NOT colonization.

All 210 jars and central visits with both *adjacent* Euplotes counts positive.
The central value is NEVER used to predict its own sample-zero probability.
No published experiment outcomes are deemed independent confirmatory evidence.
"""
import argparse
import json
import math
from collections import Counter,defaultdict
from pathlib import Path
from hopson_temporal_detection_audit_v1_222 import (
    download_locked,layout_index,rows_locked,OBS_HEADER,intish,optional_count,
)

# Purely a model-assumption sensitivity grid. The "rho" values are
# hypothetical true central density / fixed flanking density, not fitted changes.
SCALE_GRID=(1.0,0.25,0.10)
PROBABILITY_BINS=((0.001,"p_lt_0001"),(0.01,"p_0001_to_001"),
                  (0.05,"p_001_to_005"),(0.20,"p_005_to_020"),
                  (1.0000001,"p_ge_020"))
EXPECTED_ROWS=4830
SOURCE_COUNT_ANCHOR=209
SOURCE_METAPOPULATIONS=14

def p_zero_fixed_density_neighbors(left_count,right_count,left_volume,
                                   right_volume,middle_volume,density_scale):
    """Gamma(.5,0) Jeffreys posterior predictive conditional on two flanks.

    Counts are Poisson(volume * fixed local density) under each hypothetical
    density-scale assumption. Returns P(middle count=0) without looking at it.
    """
    if any(type(z) is not int or z<=0 for z in (left_count,right_count)):
        raise ValueError("Positive integer flank counts required")
    vals=(left_volume,right_volume,middle_volume,density_scale)
    if any(not math.isfinite(z) or z<=0 for z in vals):
        raise ValueError("Finite strictly positive volumes/scale required")
    flank_volume=left_volume+right_volume
    effective_middle=middle_volume*density_scale
    return math.exp((left_count+right_count+0.5)*
                    math.log(flank_volume/(flank_volume+effective_middle)))

def get_interior_triples(raw_obs,raw_layout):
    layout=layout_index(raw_layout)
    perjar=defaultdict(list)
    for r in rows_locked(raw_obs,OBS_HEADER):
        jar=intish(r["jar.no"],"jar")
        if jar not in layout:raise ValueError("Observation jar absent from frozen layout")
        day=intish(r["day"],"day")
        v=float(r["samp.vol"])
        if not math.isfinite(v) or v<0:raise ValueError("Invalid source sample volume")
        count=optional_count(r["eupl"],"eupl")
        perjar[jar].append((day,count,v))
    if set(perjar)!=set(layout):raise ValueError("Missing jar series")
    if sum(map(len,perjar.values()))!=EXPECTED_ROWS:raise ValueError("Raw sample count drift")
    triples=[]
    for jar,seq in sorted(perjar.items()):
        seq=sorted(seq)
        if len(seq)!=23 or len({x[0] for x in seq})!=23:
            raise ValueError("Expected exactly 23 unique visits per jar")
        meta,patch,treatment,block=layout[jar]
        for i in range(1,len(seq)-1):
            a,b,c=seq[i-1],seq[i],seq[i+1]
            if min(a[2],b[2],c[2])<=0 or None in (a[1],b[1],c[1]):
                continue
            if not(a[0]<b[0]<c[0]):raise ValueError("Visits not chronological")
            if a[1]<=0 or c[1]<=0:continue
            triples.append({
                "meta":meta,"treatment":treatment,"block":block,
                "left_count":a[1],"middle_count":b[1],"right_count":c[1],
                "left_volume":a[2],"middle_volume":b[2],"right_volume":c[2],
                "zero":int(b[1]==0),
            })
    return triples

def category(p):
    for limit,label in PROBABILITY_BINS:
        if p<limit:return label
    raise AssertionError("P0 not within [0,1]")

def aggregate(triples,scale):
    bins=defaultdict(Counter)
    summaries=defaultdict(lambda:{"triple_count":0,"central_sample_zeros":0,
                                   "conditional_expected_zero_sum":0.0,
                                   "central_zero_where_p_lt_005":0,
                                   "central_zero_where_p_lt_001":0,
                                   "zero_flanked_by_at_least_5":0,
                                   "zero_flanked_by_at_least_20":0})
    for r in triples:
        p=p_zero_fixed_density_neighbors(
            r["left_count"],r["right_count"],r["left_volume"],
            r["right_volume"],r["middle_volume"],scale)
        b=category(p)
        for key in ("all",f"block_{r['block']}_{r['treatment']}",
                    f"meta_{r['meta']:02d}"):
            x=summaries[key]
            x["triple_count"]+=1
            x["central_sample_zeros"]+=r["zero"]
            x["conditional_expected_zero_sum"]+=p
            x["central_zero_where_p_lt_005"]+=int(r["zero"] and p<0.05)
            x["central_zero_where_p_lt_001"]+=int(r["zero"] and p<0.01)
            x["zero_flanked_by_at_least_5"]+=int(
                r["zero"] and min(r["left_count"],r["right_count"])>=5)
            x["zero_flanked_by_at_least_20"]+=int(
                r["zero"] and min(r["left_count"],r["right_count"])>=20)
            bins[key][b+"_total"]+=1
            bins[key][b+"_central_zero"]+=r["zero"]
    for key,rec in summaries.items():
        rec["conditional_expected_zero_sum"]=round(rec["conditional_expected_zero_sum"],6)
        rec["probability_bin_counts"]=dict(sorted(bins[key].items()))
    return dict(sorted(summaries.items()))

def compute(raw_obs,raw_layout):
    triples=get_interior_triples(raw_obs,raw_layout)
    if sum(x["zero"] for x in triples)!=SOURCE_COUNT_ANCHOR:
        raise ValueError("v1.223 interior isolated zero support drift")
    if {x["meta"] for x in triples}!=set(range(1,SOURCE_METAPOPULATIONS+1)):
        raise ValueError("Expected contribution from all independent metapopulations")
    variants={str(scale):aggregate(triples,scale) for scale in SCALE_GRID}
    a=variants["1.0"]["all"]
    if a["central_sample_zeros"]!=209:
        raise ValueError("Frozen single-zero between positives count differs")
    return {
      "schema":"structural.hopson_sampling_zero_posterior_predictive.v1_224",
      "status":"RETROSPECTIVE_POSTOUTCOME_FIXED_ASSUMPTION_CALIBRATION_ONLY",
      "data_source":"Hopson 2016 Euplotes counts, fixed original v1.222 MD5 files",
      "selected_triples":"Two immediately flanking positive counts; central count may be 0 or positive",
      "all_source_observations_expected":EXPECTED_ROWS,
      "independent_experimental_units":14,
      "interior_triples_total":len(triples),
      "single_zero_flanked_by_positives_anchor":209,
      "model":"Gamma(shape=sum flank counts+0.5,rate=sum flank volumes) posterior for constant concentration; conditional predictive zero P=(Vflank/(Vflank+rho*Vmid))^(counts+0.5).",
      "hypothetical_mid_density_scales":list(SCALE_GRID),
      "conditional_model_sensitivity":variants,
      "probability_bins":[{"upper_exclusive":lim,"name":name} for lim,name in PROBABILITY_BINS],
      "no_parametric_p_value_or_confidence_interval":True,
      "neighboring_timepoints_overlapping_not_independent":True,
      "expected_central_zero_counts_are_under_assumed_stationary_or_dipped_density":True,
      "shared_flank_counts_estimate_density_not_independent_ground_truth":True,
      "model_excess_zero_is_not_proof_of_true_absence_or_movement":True,
      "no_true_colonization_or_rescue_estimated":True,
      "eBird_used":False,
      "GEB_scientific_HOLD":True,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    ans=compute(download_locked("observations"),download_locked("layout"))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(ans,indent=2,sort_keys=True)+"\n")
    print(json.dumps(ans,sort_keys=True))

if __name__=="__main__":main()
