#!/usr/bin/env python3
"""Response-free, deterministic replay of frozen BioTIME 33-network screening.

This verifier uses ONLY two committed frozen metadata JSONs. It never reads
BioTIME species/taxa, original RDS, or any reserved study outcome.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REALMS=("Freshwater","Marine","Terrestrial")

def verify(cohort:dict,physical:dict)->dict:
    if cohort.get("schema")!="structural.biotime_v2_conservative_network_cohort.v1_255":
        raise ValueError("Wrong scientific cohort freeze schema")
    if physical.get("schema")!="structural.biotime2_reserved_physical_support_freeze.v1_253":
        raise ValueError("Original physical gate schema mismatch")
    qual_by_realm=physical["eligible_by_realm"]
    if set(qual_by_realm)!=set(REALMS):raise ValueError("Unknown realms")
    selected=cohort["selected_study_ids_by_realm"]
    if set(selected)!=set(REALMS):raise ValueError("Unknown realms in selected network cohort")
    allqual=[str(x) for r in REALMS for x in qual_by_realm[r]]
    if len(allqual)!=47 or len(set(allqual))!=47:
        raise ValueError("Original response-free 47 physical IDs changed")
    excluded_spatial=set(map(str,cohort["eliminated_for_less_than_five_active_strict_month_sites"]))
    excluded_pilot=set(map(str,cohort["eliminated_for_shared_geography_with_prior_burned_pilot"]))
    if len(excluded_spatial)!=3 or len(excluded_pilot)!=4 or excluded_spatial&excluded_pilot:
        raise ValueError("Frozen exclusion groups changed")
    if not excluded_spatial|excluded_pilot <= set(allqual):
        raise ValueError("Outside pilot/physical metadata eligibility")
    source_filtered=set(allqual)-excluded_spatial-excluded_pilot
    if len(source_filtered)!=40:
        raise ValueError("Frozen physical frame post-exclusion denominator changed")
    groups=cohort["within_reserved_near_duplicate_groups"]
    if len(groups)!=4:raise ValueError("Frozen independent network components changed")
    grouped=set(); skipped=set(); retained=set()
    for group in groups:
        names=list(map(str,group["members"]))
        if not 2<=len(names)<=4 or len(set(names))!=len(names) or not set(names)<=source_filtered:
            raise ValueError("Near-duplicate components outside 40 candidate IDs")
        if grouped&set(names):
            raise ValueError("Near-duplicate component overlaps")
        grouped.update(names)
        counts={str(k):int(v) for k,v in group["strict_pair_counts"].items()}
        if set(counts)!=set(names):
            raise ValueError("Per-study physical support counts missing in near-duplicate component")
        expected=sorted(names,key=lambda s:(-counts[s],int(s)))[0]
        if str(group["representative"])!=expected:
            raise ValueError("Representative not chosen by frozen physical quality rule")
        retained.add(expected)
        skipped.update(set(names)-{expected})
    original_skip=set(map(str,cohort["skipped_near_duplicate_study_ids"]))
    if skipped!=original_skip or len(skipped)!=7:
        raise ValueError("Frozen omitted duplicated study IDs changed")
    final=source_filtered-skipped
    selected_names=[str(x) for r in REALMS for x in selected[r]]
    if len(final)!=33 or len(selected_names)!=33 or set(selected_names)!=final or len(set(selected_names))!=33:
        raise ValueError("33 source-independent network representative cohort mismatch")
    for realm in REALMS:
        if not set(map(str,selected[realm]))<=set(map(str,qual_by_realm[realm])):
            raise ValueError("Realm assignments changed since response-free original physical gate")
    expected_steps={"pre_registered_study_ids":76,
                    "matched_time_and_year_qualified":47,
                    "min_five_active_sites":44,
                    "remaining_after_remove_cross_split_shared_geography":40,
                    "remaining_network_proxy_representatives":33}
    if cohort["cohort_count_steps"]!=expected_steps:
        raise ValueError("Count ladder changed from original source-free route")
    if cohort.get("reserved_species_response_rows_opened")!=0 or not cohort.get("GEB_scientific_HOLD"):
        raise ValueError("Response firewall or GEB HOLD violated")
    return {
        "schema":"structural.biotime_network_cohort_integrity_receipt.v1_255",
        "status":"RESPONSE_FREE_33_NETWORK_PROXIES_VERIFIED",
        "source_doi":cohort["source"]["doi"],
        "physical_ids":47,"active_geographic_ids":44,
        "cross_split_excluded_ids":sorted(excluded_pilot,key=int),
        "within_holdout_duplicate_removed_ids":sorted(skipped,key=int),
        "final_representatives":33,
        "by_realm":{r:len(selected[r]) for r in REALMS},
        "no_reserved_biological_responses_read":True,
        "not_claiming_33_independent_archipelagos":True
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cohort",required=True,type=Path)
    p.add_argument("--physical",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    r=verify(json.loads(args.cohort.read_text()),json.loads(args.physical.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
