#!/usr/bin/env python3
"""Original AODN NRMN RLS Method-1 surveyed-denominator audit (physical only).

Uses official survey _common_metadata SHA-256 via v1.260 source_rows().
Not a fish occurrence query, colonization event, or evidence of natal dispersal.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re

from nrmn_marine_survey_event_frame_v1_260 import (
    source_rows, physical_row, program_class
)

SCHEMA="structural.nrmn_rls_method1_physical.v1_261"


def method_codes(value):
    """Return strictly comma-delimited, nonnegative method integers; None if invalid.

    This intentionally prevents method 11 or 13 matching method 1.
    """
    s="" if value is None else str(value).strip()
    if not s:
        return tuple()
    chunks=[x.strip() for x in s.split(",")]
    if any(re.fullmatch(r"[0-9]+",x) is None for x in chunks):
        return None
    return tuple(sorted(set(int(x) for x in chunks)))


def _expected_groups(contract):
    if contract.get("schema")!="structural.nrmn_rls_method1_physical_protocol.v1_261":
        raise ValueError("Frozen RLS Method-1 study contract missing")
    records=contract.get("frozen_RLS_geographic_groups")
    if not isinstance(records,list) or len(records)<1:
        raise ValueError("No pre-frozen RLS survey localities")
    expected={}
    for record in records:
        key=tuple(str(record[k]).strip().casefold() for k in ("country","area","location"))
        n=int(record["previous_strict_all_method_pairs"])
        if key in expected or n<0:
            raise ValueError("Duplicate or invalid frozen physical region")
        expected[key]=n
    return expected


def accumulate_method1(rows,contract):
    """Only source survey-event metadata is queried. Fish response columns forbidden."""
    expected=_expected_groups(contract)
    survey_ids=set()
    valid_source_events=0
    invalid_source_rows=0
    duplicate_ids=0
    all_RLS=0
    inspected=0
    all_method1_in_fixed=0
    method_problem=Counter()
    all_group_survey=Counter()
    group_m1=Counter()
    site_bounds={}  # RLS fixed groups only: all physical source events (not just Method1)
    site_m1_years=defaultdict(set)
    site_m1_counts=Counter()
    site_by_group=defaultdict(set)
    for r in rows:
        inspected+=1
        try:
            sid,pg,parts,d,lat,lon,methods=physical_row(r)
        except ValueError:
            invalid_source_rows+=1
            continue
        if sid in survey_ids:
            duplicate_ids+=1
            continue
        survey_ids.add(sid)
        valid_source_events+=1
        if pg!="RLS":
            continue
        all_RLS+=1
        group=parts[:3]
        if group not in expected:
            continue
        all_group_survey[group]+=1
        site=(group,parts[3])
        site_by_group[group].add(site)
        if site not in site_bounds:
            site_bounds[site]=[lat,lat,lon,lon]
        else:
            b=site_bounds[site]
            b[0]=min(b[0],lat)
            b[1]=max(b[1],lat)
            b[2]=min(b[2],lon)
            b[3]=max(b[3],lon)
        codes=method_codes(methods)
        if codes is None:
            method_problem["unparseable_original_survey_methods"]+=1
            continue
        if 1 not in codes:
            method_problem["no_method_1"]+=1
            continue
        all_method1_in_fixed+=1
        group_m1[group]+=1
        site_m1_years[site].add(d.year)
        site_m1_counts[(site,d.year,d.month)]+=1

    stable_sites={}
    for site,b in site_bounds.items():
        stable_sites[site]=(b[1]-b[0]<=0.01 and b[3]-b[2]<=0.01)
    unstable=sum(not v for v in stable_sites.values())
    stats={}
    for group in expected:
        sites={s for s in site_by_group[group] if stable_sites[s]}
        active_sites={s for s in sites if s in site_m1_years}
        repeat3={s for s in active_sites if len(site_m1_years[s])>=3}
        pairs=[]
        for (site,y,m),n in site_m1_counts.items():
            if site[0]!=group or site not in sites or n<2:
                continue
            if site_m1_counts.get((site,y+1,m),0)>=2:
                pairs.append((site,y,m))
        prior_yrs=len({y for _,y,_ in pairs})
        row={
            "country":group[0],"area":group[1],"location":group[2],
            "survey_events_all_methods":all_group_survey[group],
            "survey_events_method_1":group_m1[group],
            "physical_site_codes_all_methods":len(site_by_group[group]),
            "stable_method1_sites":len(active_sites),
            "sites_with_three_observed_method1_years":len(repeat3),
            "strict_method1_same_month_next_year_site_pairs":len(pairs),
            "distinct_prior_years_with_method1_pairs":prior_yrs,
            "method1_physical_qualified":(
                len(repeat3)>=5 and len(pairs)>=10 and prior_yrs>=2),
            "previous_all_methods_strict_pairs":expected[group]
        }
        if row["strict_method1_same_month_next_year_site_pairs"]>expected[group]:
            raise ValueError("Method-1 restricted pairs exceed original all-method source pairs")
        stats[group]=row

    ordered=[stats[k] for k in expected]
    qualified=[x for x in ordered if x["method1_physical_qualified"]]
    qualified_by_country=dict(Counter(x["country"] for x in qualified))
    return {
        "schema":SCHEMA,
        "status":"SOURCE_ONLY_METHOD_1_REPEATED_SURVEY_FRAME",
        "source_rows_seen":inspected,
        "unique_valid_source_survey_ids":valid_source_events,
        "invalid_source_survey_rows":invalid_source_rows,
        "duplicate_survey_ids":duplicate_ids,
        "all_RLS_unique_survey_events":all_RLS,
        "frozen_source_10_group_count":len(expected),
        "fixed_groups_with_source_survey_records":sum(x["survey_events_all_methods"]>0 for x in ordered),
        "method1_RLS_surveys_in_fixed_10_groups":all_method1_in_fixed,
        "strict_method1_pairs_total":sum(x["strict_method1_same_month_next_year_site_pairs"] for x in ordered),
        "method1_strictly_qualified_fixed_groups":len(qualified),
        "qualified_physical_groups_by_country":qualified_by_country,
        "geographically_unstable_method1_sites":unstable,
        "excluded_method_1_field_categories":dict(method_problem),
        "fixed_RLS_group_method1_physical_support":ordered,
        "no_survey_id_or_coordinate_values_exported":True,
        "fish_species_or_abundance_columns_read":False,
        "true_colonization_or_source_dispersal_measured":False,
        "original_mammal_heldout_unopened":True,
        "new_confirmatory_systems":0,
        "eBird_used":False,
        "GEB_scientific_HOLD":True
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    src=json.loads((Path(__file__).resolve().parents[1]/
          "development/nrmn_marine_survey_event_frame_protocol_v1_260.json").read_text())
    if (contract["authoritative_source"]["survey_common_metadata_sha256"] !=
            src["source"]["survey_metadata_sidecar_sha256"] or
        contract["authoritative_source"]["original_v1_260_run"]!=39233006937):
        raise ValueError("Unexpected AODN source provenance or pilot response-use change")
    result=accumulate_method1(source_rows(src),contract)
    if (result["source_rows_seen"]!=36974 or
        result["unique_valid_source_survey_ids"]!=36971 or
        result["all_RLS_unique_survey_events"]!=20657 or
        result["frozen_source_10_group_count"]!=10 or
        result["fixed_groups_with_source_survey_records"]!=10):
        raise ValueError("Official AODN source event population changed from frozen v1.260")
    result["survey_source_sidecar_sha256"]=src["source"]["survey_metadata_sidecar_sha256"]
    result["source_reference_run"]=39233006937
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({"source_rows":result["source_rows_seen"],
        "RLS_events":result["all_RLS_unique_survey_events"],
        "RLS_method1_fixed10":result["method1_RLS_surveys_in_fixed_10_groups"],
        "RLS_method1_strict_pairs":result["strict_method1_pairs_total"],
        "RLS_qualified_regions":result["method1_strictly_qualified_fixed_groups"],
        "fish_response_rows":0},sort_keys=True))


if __name__=="__main__":
    main()
