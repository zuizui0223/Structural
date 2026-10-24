#!/usr/bin/env python3
"""Exact partial identification of Pico binary alien-plant co-detection (v1.290).

Reads ONLY v1.281/v1.282 published, SHA-reconciled aggregate counts. Never
downloads or reads any Event/Occurrence row, original S1 or protected data.

Not a bootstrap, significance test, prospective confirmation, or cause of
biological persistence. Synthetically constructed vectors are existence
witnesses satisfying aggregate constraints, not recovered sampled plot data.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
from math import isclose
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AGG_PATH="development/azores_pico_source_aggregates_v1_290.json"
V281_SHA="135a4c5f598f686ce3691d79aa0a59b427036128d8e99760321dbc3d4f208a27"
V282_SHA="3ea87c240c663c9c60383c49492b03240268f8b91da313a36821264a388d476f"

def _fraction(x: Fraction)->dict:
    return {"exact":str(x),"decimal":float(x)}

def _alien_vector(n,occupied,incidences,maximum):
    """Make a legal SYNTHETIC vector (not sampled site data)."""
    if not (0<=occupied<=n and 0<=incidences<=maximum*occupied
            and incidences>=occupied):
        raise ValueError("Impossible synthetic alien incidence scenario")
    a=[1]*occupied+[0]*(n-occupied)
    remaining=incidences-occupied
    for k in range(occupied):
        more=min(remaining, maximum-1)
        a[k]+=more
        remaining-=more
    if remaining!=0 or sum(a)!=incidences or max(a,default=0)>maximum:
        raise AssertionError("Synthetic construction not internally feasible")
    return a

def _species_witness(vectors,species_count):
    """Assign repeated labels s0..s11 without within-plot duplicates."""
    if species_count<1:raise ValueError("No available alien species")
    seen=set()
    index=0
    for k in vectors:
        ids=[(index+j)%species_count for j in range(k)]
        if len(ids)!=len(set(ids)):
            raise AssertionError("Multiple positives of same species in one plot")
        seen.update(ids)
        index+=k
    return {"synthetic_distinct_alien_taxa":len(seen),
            "synthetic_alien_incidence":index,
            "synthetic_total_plots":len(vectors)}

def calculate(aggregate:dict,protocol:dict)->dict:
    if (protocol.get("schema")!="structural.pico_alien_cooccurrence_partial_id_protocol.v1_290"
        or protocol.get("status")!="SOURCE_FREE_AGGREGATE_ONLY_SENSITIVITY_FROZEN"
        or protocol["provenance"]["input_path"]!=AGG_PATH):
        raise ValueError("Frozen aggregate-only protocol required")
    if aggregate.get("schema")!="structural.azores_pico_source_free_aggregate_replay.v1_290":
        raise ValueError("Unexpected input aggregate schema")
    if (aggregate["source_sha256"]["v281_extracted"]!=V281_SHA
        or aggregate["source_sha256"]["v282_extracted"]!=V282_SHA
        or protocol["provenance"]["v281_extracted_aggregate_sha256"]!=V281_SHA
        or protocol["provenance"]["v282_extracted_aggregate_sha256"]!=V282_SHA):
        raise ValueError("Original source aggregate fingerprint mismatch")

    d=aggregate["pico"]
    c=protocol["constraints"]
    expected={
        "distinct_original_plots":d["plots"],
        "focal_positive_plots":d["plots_focal_affected_native_positive"],
        "focal_negative_plots":d["plots_no_focal_affected_native_detected"],
        "all_alien_bearing_plots":d["plots_with_any_introduced_taxon"],
        "alien_species_plot_incidence_focal_positive":d["introduced_taxon_plot_positives_focal_positive"],
        "alien_species_plot_incidence_focal_negative":d["introduced_taxon_plot_positives_focal_negative"],
        "global_max_distinct_alien_species_per_plot":d["maximum_distinct_introduced_taxa_per_original_plot"],
        "recorded_alien_species_total":d["recorded_distinct_introduced_taxa"],
        "all_alien_species_plot_incidence":d["introduced_taxon_plot_positives_all"]
    }
    if expected!=c:
        raise ValueError("Current counts deviate from frozen prior-aggregate contrast")
    n1=c["focal_positive_plots"]
    n0=c["focal_negative_plots"]
    K=c["all_alien_bearing_plots"]
    A=c["alien_species_plot_incidence_focal_positive"]
    B=c["alien_species_plot_incidence_focal_negative"]
    M=c["global_max_distinct_alien_species_per_plot"]
    S=c["recorded_alien_species_total"]
    if n1+n0!=24 or A+B!=27 or K>24 or max(A,B)>27 or S!=12 or M!=5:
        raise ValueError("Original island original-plot/species-incidence denominators invalid")
    if not isclose(d["v281_mean_alien_taxa_per_focal_positive_plot"]*n1,A,abs_tol=1e-9):
        raise ValueError("Alien focal incidence does not reconcile with v1.281 mean")
    if not isclose(d["v281_mean_alien_taxa_per_focal_negative_plot"]*n0,B,abs_tol=1e-9):
        raise ValueError("Alien nonfocal incidence does not reconcile with v1.281 mean")
    if d["v281_native_focal_taxon_plot_positive"]+d["v281_native_reference_taxon_plot_positive"]!=292:
        raise ValueError("Original 292 native incidence cells do not reconcile")
    if not isclose(d["v282_total_native_mean_focal_positive_plot"]*n1,272,abs_tol=1e-9):
        raise ValueError("v1.282 focal-positive native incidence unavailable")
    if not isclose(d["v282_total_native_mean_focal_negative_plot"]*n0,20,abs_tol=1e-9):
        raise ValueError("v1.282 nonfocal native incidence unavailable")
    if d["v281_native_focal_taxa_detected"]!=5 or d["v281_native_reference_taxa_detected"]!=49:
        raise ValueError("Historical loss-affected original taxon denominator changed")
    other_native_positive=272-d["v281_native_focal_taxon_plot_positive"]
    other_native_negative=20
    if other_native_positive+other_native_negative!=266:
        raise ValueError("Non-focal native plant plot incidence does not reconcile")

    feasible=[]
    for x in range(n1+1):
        y=K-x
        if not(0<=y<=n0):continue
        if not(x<=A<=M*x and y<=B<=M*y):continue
        a=_alien_vector(n1,x,A,M)
        b=_alien_vector(n0,y,B,M)
        witness=_species_witness(a+b,S)
        if not(witness["synthetic_distinct_alien_taxa"]==S
               and witness["synthetic_alien_incidence"]==A+B
               and witness["synthetic_total_plots"]==24):
            continue
        f=Fraction(x,n1)
        nf=Fraction(y,n0)
        gap=f-nf
        rr=f/nf if nf else None
        feasible.append({
            "alien_positive_plots_focal_detected":x,
            "alien_positive_plots_focal_nondetected":y,
            "focal_detected_alien_codetection_frequency":_fraction(f),
            "focal_nondetected_alien_codetection_frequency":_fraction(nf),
            "focal_minus_nondetected_alien_codetection_gap":_fraction(gap),
            "frequency_ratio_focal_vs_nondetected":_fraction(rr) if rr is not None else None,
            "synthetic_feasible_plot_richness_focal":a,
            "synthetic_feasible_plot_richness_nondetected":b,
            "synthetic_feasibility_only_not_original_sites":True,
        })
    if not feasible:
        raise ValueError("Aggregate counts have no legal per-plot configuration")
    gaps=[Fraction(z["focal_minus_nondetected_alien_codetection_gap"]["exact"]) for z in feasible]
    rel=[Fraction(z["frequency_ratio_focal_vs_nondetected"]["exact"]) for z in feasible
         if z["frequency_ratio_focal_vs_nondetected"]]
    negative_all=all(z<0 for z in gaps)
    return {
        "schema":"structural.azores_pico_alien_codetection_partial_id_result.v1_290",
        "status":"AGGREGATE_ONLY_EXACT_CO_DETECTION_PARTIAL_IDENTIFICATION",
        "source_2013_plot_count":24,
        "focal_native_taxa_sampled":5,
        "focal_native_group_detected_plots":n1,
        "focal_native_group_not_detected_plots":n0,
        "total_alien_bearing_plots":K,
        "alien_species_plot_incidence_by_focal_group":{"detected":A,"not_detected":B},
        "observed_max_alien_species_in_a_plot":M,
        "observed_total_distinct_alien_species":S,
        "feasible_binary_alien_codetection_count_pairs":[[x["alien_positive_plots_focal_detected"],x["alien_positive_plots_focal_nondetected"]] for x in feasible],
        "all_feasible_codetection_gap_negative":negative_all,
        "alien_codetection_frequency_difference_lower_bound":_fraction(min(gaps)),
        "alien_codetection_frequency_difference_upper_bound":_fraction(max(gaps)),
        "alien_codetection_ratio_lower_bound":_fraction(min(rel)),
        "alien_codetection_ratio_upper_bound":_fraction(max(rel)),
        "nonfocal_native_taxa_in_focal_detected_plots":other_native_positive,
        "nonfocal_native_taxa_in_focal_nondetected_plots":other_native_negative,
        "mean_nonfocal_native_taxa_per_focal_detected_plot":_fraction(Fraction(other_native_positive,n1)),
        "mean_nonfocal_native_taxa_per_focal_nondetected_plot":_fraction(Fraction(other_native_negative,n0)),
        "ratio_mean_nonfocal_native_richness_detected_vs_nondetected":_fraction(Fraction(other_native_positive,n1)/Fraction(other_native_negative,n0)),
        "possible_synthetic_witnesses_not_observed_plot_values":feasible,
        "no_original_biological_rows_reopened":True,
        "source_free_posthoc_accounting_not_confirmatory":True,
        "native_focal_plot_nondetection_not_species_absence":True,
        "not_individual_taxon_specific_or_invasive_causation":True,
        "no_colonization_rescue_or_survival_inferred":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--aggregate",type=Path,default=ROOT/AGG_PATH)
    p.add_argument("--protocol",type=Path,default=ROOT/"development/azores_pico_alien_binary_partial_id_protocol_v1_290.json")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=calculate(json.loads(a.aggregate.read_text(encoding="utf-8")),
                     json.loads(a.protocol.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "feasible_pairs":result["feasible_binary_alien_codetection_count_pairs"],
        "gap_low":result["alien_codetection_frequency_difference_lower_bound"]["decimal"],
        "gap_high":result["alien_codetection_frequency_difference_upper_bound"]["decimal"],
        "indigenous_reference_richness_ratio":result["ratio_mean_nonfocal_native_richness_detected_vs_nondetected"]["decimal"],
        "biological_rows_reopened":0,
        "confirmatory_admissions":0
    },sort_keys=True))

if __name__=="__main__":
    main()
