#!/usr/bin/env python3
"""Aggregate BioTIME v2 survey-frame audits; site proxies, never ecological responses."""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path

COLS=("coordinate_sites","sites_at_least_three_observed_years",
      "sites_at_least_five_observed_years","sites_with_consecutive_years",
      "total_consecutive_site_year_pairs","unique_site_years",
      "total_sample_events","raw_consecutive_pairs",
      "same_month_consecutive_pairs","same_month_pairs_each_visit_2plus")


def report(frame_csv:Path, transport_receipt:dict):
    if transport_receipt.get("status")!="ORIGINAL_RDS_SOURCE_VERIFIED":
        raise ValueError("Cannot score site-year frame without verified publisher bytes")
    if not transport_receipt.get("metadata",{}).get("publisher_md5_verified"):
        raise ValueError("Publisher metadata MD5 not authenticated")
    with frame_csv.open("r",encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=226:
        raise ValueError(f"Original metadata eligibility count changed: {len(rows)}")
    by_realm=defaultdict(list)
    allrows=[]
    seen=set()
    for rec in rows:
        study=str(rec.get("STUDY_ID","")).strip()
        if not study or study in seen:
            raise ValueError("Duplicate/missing study ID")
        seen.add(study)
        counts={k:int(rec.get(k) or 0) for k in COLS}
        if any(x<0 for x in counts.values()):
            raise ValueError("Negative physical-frame count")
        if counts["sites_at_least_three_observed_years"]>counts["coordinate_sites"]:
            raise ValueError("Source frame repeated sites > sampled site count")
        if counts["sites_at_least_five_observed_years"]>counts["sites_at_least_three_observed_years"]:
            raise ValueError("Five-year sites exceed three-year sites")
        if counts["same_month_consecutive_pairs"]>counts["raw_consecutive_pairs"]:
            raise ValueError("Same-month next-year pairs > all next-year pairs")
        if counts["same_month_pairs_each_visit_2plus"]>counts["same_month_consecutive_pairs"]:
            raise ValueError("Repeat-survey paired events exceed any same-month pairs")
        realm=str(rec.get("REALM","")).strip()
        if realm not in ("Terrestrial","Marine","Freshwater"):
            raise ValueError("Unknown study realm")
        c={"study":study,"realm":realm,**counts}
        allrows.append(c)
        by_realm[realm].append(c)
    if {k:len(v) for k,v in by_realm.items()} != {"Marine":107,"Terrestrial":61,"Freshwater":58}:
        raise ValueError("Frozen 226 metadata realm allocation mismatch")

    def reduction(group):
        return {
           "metadata_screen_studies":len(group),
           "some_coordinate_site_observed":sum(x["coordinate_sites"]>0 for x in group),
           "some_site_at_least_three_years":sum(x["sites_at_least_three_observed_years"]>0 for x in group),
           "some_consecutive_site_years":sum(x["raw_consecutive_pairs"]>0 for x in group),
           "some_same_month_consecutive_site_years":sum(x["same_month_consecutive_pairs"]>0 for x in group),
           "some_same_month_both_years_two_plus_events":sum(x["same_month_pairs_each_visit_2plus"]>0 for x in group),
           "at_least_10_same_month_next_year_site_pairs":sum(x["same_month_consecutive_pairs"]>=10 for x in group),
           "total_same_month_next_year_pairs":sum(x["same_month_consecutive_pairs"] for x in group),
           "total_site_years_observed":sum(x["unique_site_years"] for x in group),
        }
    result={
        "schema":"structural.biotime2_physical_siteyear_frame_result.v1_250",
        "source_doi":"10.5281/zenodo.15222193",
        "metadata_screen":"development/biotime_v2_metadata_eligibility_freeze_v1_249.json",
        "source_integrity_md5":"2fed9f6c8028d4c44d80769c594be056",
        "evidence_class":"RETROSPECTIVE_PUBLIC_RDS_LOADED_PHYSICAL_EVENT_KEYS_ONLY",
        "results_by_realm":{realm:reduction(group) for realm,group in by_realm.items()},
        "total":reduction(allrows),
        "methodological_limits":[
          "Coordinates rounded to 5 decimal places are only provisional repeated-site proxies",
          "Stable coordinate does not establish fixed subplot identity or survey effort",
          "Same-month overlap does not guarantee identical survey methodology",
          "At least 2 observed sample events per year does not itself estimate detection probability",
          "Full published RDS materialized in memory; response-bearing columns were never analyzed by this script",
          "No colonization/extinction, source identity, observed movement or ecological model has been inferred",
        ],
        "new_confirmatory_systems_admitted":0,
        "original_global_mammal_heldout_opened":False,
        "eBird_used":False,
        "GEB_scientific_HOLD":True,
    }
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv",required=True,type=Path)
    p.add_argument("--transport",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    provenance=json.loads(a.transport.read_text(encoding="utf-8"))
    result=report(a.csv,provenance)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result["total"],sort_keys=True))


if __name__=="__main__":
    main()
