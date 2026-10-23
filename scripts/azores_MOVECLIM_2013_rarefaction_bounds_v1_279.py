#!/usr/bin/env python3
"""Exact source-free 10-plot native loss-taxon rarefaction bounds.

Uses ONLY committed aggregated 2013 MOVECLIM data. No species names, plot
identities, Event/Occurrence observations or older protected labels are read.
Under a fixed island's observed plot frame, all mathematically feasible
species occupancy allocations with the SAME (N plots, T taxa, P positives)
are bounded using hypergeometric plot sampling without replacement.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path

SCHEMA="structural.azores_MOVECLIM_source_free_plot_rarefaction.v1_279"
ORIGINAL_2013_SHA="612dad4edc1a5fb8e9fd057167320144d8a7791a02d1245513d58fd6c8cdabc4"
ISLANDS=("Flores","Pico","São Miguel","Terceira")


def _prob(n,k,m):
    return Fraction(1)-Fraction(comb(n-k,m) if n-k>=m else 0,comb(n,m))


def bounds(n,t,p,m):
    """Exact extremal E[observed richness], across all unknown species occupancies.

    Given each taxon occurs on >=1 and <=n plots and total P plot×taxon
    positives, hypergeom inclusion probability is increasing concave in k.
    Hence the minimum maximally concentrates plot occurrences; the maximum
    balances k among taxa. No species-level record data needed.
    """
    vals=(n,t,p,m)
    if any(type(x) is not int for x in vals):
        raise ValueError("Frozen plot/plant counts must be integers")
    if n<1 or t<1 or p<t or p>n*t or m<1 or m>n:
        raise ValueError("Impossible source plot-taxon incidence distribution")
    most_unequal=[1]*t
    remaining=p-t
    for i in range(t):
        take=min(remaining,n-1)
        most_unequal[i]+=take
        remaining-=take
    if remaining:raise ValueError("Source plot-count extremal allocation unassigned")
    balanced=[p//t+(i<(p%t)) for i in range(t)]
    if sum(most_unequal)!=p or sum(balanced)!=p:
        raise AssertionError("Conservation of original positive plot records failed")
    lower=sum((_prob(n,k,m) for k in most_unequal),Fraction(0))
    upper=sum((_prob(n,k,m) for k in balanced),Fraction(0))
    if lower>upper:
        raise AssertionError("Nonconcave hypergeometric sample inclusion implementation")
    return lower,upper


def _json_interval(n,t,p,m):
    low,high=bounds(n,t,p,m)
    return {
        "N_original_independent_plots":n,
        "T_observed_species":t,
        "P_original_plot_by_species_positive_cells":p,
        "random_subsample_size_m":m,
        "expected_lower_fraction":str(low),
        "expected_upper_fraction":str(high),
        "expected_lower_float":float(low),
        "expected_upper_float":float(high),
        "not_every_random_subplot_subset":True,
        "no_species_identifiers_needed":True
    }


def report_from_freeze(data):
    if data.get("schema")!="structural.azores_MOVECLIM_2013_native_refugia_field_freeze.v1_278":
        raise ValueError("Wrong original response-frozen aggregate source schema")
    if data["source"]["original_2013_SHA256"]!=ORIGINAL_2013_SHA:
        raise ValueError("Original CSIC/MOVECLIM source fingerprint mismatch")
    if (data["sampling"]["plots"]!=58 or data["sampling"]["subplots"]!=232
        or data["sampling"]["occurrences"]!=2539
        or data["historical"]["strict_S1_taxa_documented_in_standardized_2013_native_vegetation"]!=5):
        raise ValueError("Original verified plot, biological or case totals were modified")
    d=data["by_island"]
    if set(d)!=set(ISLANDS):
        raise ValueError("All four original independently surveyed islands required")
    if sum(x["plots"] for x in d.values())!=58:
        raise ValueError("Four island survey plot total changed")
    if sum(x["total_native_plot_taxon_positives"] for x in d.values())!=746:
        raise ValueError("Original 746 native incidence cells no longer reconcile")

    output={
        "schema":SCHEMA,
        "status":"SOURCE_FREE_EXACT_PLOT_EFFORT_BOUNDS",
        "provenance_frozen_2013_original_archive_SHA256":ORIGINAL_2013_SHA,
        "original_published_field_run_id":data["source"]["run"],
        "m10":{},"m8":{},
        "proportion_definition":"ratio of separately expected richness E[affected]/(E[affected]+E[reference]), not an expectation of per-subsample species proportion",
        "mathematical_conditionality":"uniform random plot subsets from the already-selected intact vegetation plots, without replacement; unknown occupancy allocated adversarially subject to source plot/taxon totals",
        "original_source_all_plots":58,
        "original_2013_occurrences":2539,
        "original_S1_strict_taxon_universe":20,
        "not_actual_population_persistence_or_rescue":True,
        "not_island_wide_extinction_risk":True,
        "historical_habitat_or_taxon_range_breadth_not_controlled":True,
        "protected_biological_rows_opened_this_run":0,
        "GEB_scientific_HOLD":True,"eBird_used":False,
        "new_confirmatory_systems_admitted":0,
    }
    for m in (10,8):
        dst=output[f"m{m}"]
        for island in ISLANDS:
            r=d[island]
            n=int(r["plots"])
            t=int(r["S1_affected_native_taxa"])
            p=int(r["S1_affected_plot_taxon_positives"])
            ref=int(r["reference_native_taxa"])
            native_total=int(r["total_native_plot_taxon_positives"])
            if int(r["source_native_taxa_total"])!=t+ref:
                raise ValueError("Reference native taxon count does not reconcile")
            if native_total<p or ref<=0:
                raise ValueError("Native source positive plot/taxon denominator impossible")
            affected=_json_interval(n,t,p,m)
            reference=_json_interval(n,ref,native_total-p,m)
            al,ah=bounds(n,t,p,m)
            rl,rh=bounds(n,ref,native_total-p,m)
            fraction_lower=al/(al+rh)
            fraction_upper=ah/(ah+rl)
            dst[island]={
                "historical_affected_taxa":affected,
                "other_native_reference_taxa":reference,
                "minimum_possible_ratio_of_expected_affected_to_total_native":float(fraction_lower),
                "maximum_possible_ratio_of_expected_affected_to_total_native":float(fraction_upper),
                "minimum_ratio_exact_fraction":str(fraction_lower),
                "maximum_ratio_exact_fraction":str(fraction_upper),
                "source_free_not_field_resampling":True,
            }
    output["primary_m10_pico_expected_affected_richness_lower_minus_largest_other_upper"]=(
        output["m10"]["Pico"]["historical_affected_taxa"]["expected_lower_float"]-
        max(output["m10"][s]["historical_affected_taxa"]["expected_upper_float"]
            for s in ISLANDS if s!="Pico"))
    output["primary_m10_pico_ratio_lower_greater_than_every_other_island_ratio_upper"]=(
        output["m10"]["Pico"]["minimum_possible_ratio_of_expected_affected_to_total_native"]>
        max(output["m10"][s]["maximum_possible_ratio_of_expected_affected_to_total_native"]
            for s in ISLANDS if s!="Pico"))
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--contract",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.moveclim2013_source_free_rarefaction_bound.v1_279"
        or c.get("status")!="FROZEN_BEFORE_SOURCE_FREE_EFFORT_BOUNDS"
        or c["source_file"]!="development/azores_MOVECLIM_2013_native_plot_field_result_freeze_v1_278.json"):
        raise ValueError("Frozen source-free rarefaction design or source path changed")
    result=report_from_freeze(json.loads(args.source.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "Pico_min_10plot_expected_richness":result["m10"]["Pico"]["historical_affected_taxa"]["expected_lower_float"],
        "other_islands_max_10plot_expected_richness":[
            result["m10"][s]["historical_affected_taxa"]["expected_upper_float"]
            for s in ISLANDS if s!="Pico"],
        "Pico_fractional_enrichment_persists_even_with_all_extremal_distributions":result["primary_m10_pico_ratio_lower_greater_than_every_other_island_ratio_upper"],
        "new_biological_records_opened":0
        },sort_keys=True))


if __name__=="__main__":
    main()
