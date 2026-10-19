#!/usr/bin/env python3
"""Source-only RLS Method 1 transect denominator: no fish species response columns."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from typing import Iterable, Mapping

from nrmn_marine_survey_event_frame_v1_260 import (
    COLUMNS, MAX_RECORDS, physical_row, source_rows,
)

SCHEMA="structural.nrmn_rls_method1_frame.v1_261"

def parse_method1(value)->bool:
    """Method 1 is an integer method code; do not mistake 12, 13 or off-line 0 for M1."""
    if value is None:
        return False
    return "1" in re.findall(r"\b\d+\b", str(value))

def group_key(parts):
    return tuple(parts[:3])

def tally_method1(rows:Iterable[Mapping],protocol:dict)->dict:
    if protocol.get("schema")!="structural.nrmn_rls_method1_pre_fish_frame.v1_261":
        raise ValueError("Method 1 source-only protocol not frozen")
    if protocol.get("status")!="FROZEN_FROM_OFFICIAL_SURVEY_METADATA_AND_METHODS_BEFORE_ANY_FISH_RESPONSE_ACCESS":
        raise ValueError("Source method1 protocol evidence status changed")
    source_groups=protocol["frozen_RLS_physical_group_candidates"]
    if len(source_groups)!=10 or len({
        (r["country"],r["area"],r["location"]) for r in source_groups
    })!=10:
        raise ValueError("Original 10 RLS eligible geographic source groups changed")
    if protocol["allowed_source_fields"]!=list(COLUMNS):
        raise ValueError("Only eleven RLS source physical survey metadata fields may be read")
    program_counts=Counter()
    method_counts=Counter()
    invalid=Counter()
    seen=set()
    sites={}
    month_counts=Counter()
    group_method_count=Counter()
    total=0
    for record in rows:
        total+=1
        if total>MAX_RECORDS:
            raise ValueError("Source rows exceed frozen 3-million-event guard")
        try:
            sid,program,parts,d,lat,lon,_=physical_row(record)
        except ValueError:
            invalid["invalid_physical_survey"]+=1
            continue
        is_m1=parse_method1(record.get("methods"))
        if sid in seen:
            invalid["duplicate_survey_id"]+=1
            if is_m1:
                invalid["method1_duplicate_survey_id"]+=1
            continue
        seen.add(sid)
        program_counts[program]+=1
        if not is_m1:
            invalid["valid_survey_without_method1"]+=1
            continue
        method_counts[program]+=1
        group=(program,)+group_key(parts)
        group_method_count[group]+=1
        key=(program,parts)
        month_counts[(key,d.year,d.month)]+=1
        if key not in sites:
            sites[key]={
                "years":set(),"min_lat":lat,"max_lat":lat,
                "min_lon":lon,"max_lon":lon
            }
        st=sites[key]
        st["years"].add(d.year)
        st["min_lat"]=min(st["min_lat"],lat);st["max_lat"]=max(st["max_lat"],lat)
        st["min_lon"]=min(st["min_lon"],lon);st["max_lon"]=max(st["max_lon"],lon)
    stable={}
    group_stable=defaultdict(set)
    group_repeat3=defaultdict(set)
    for site,rec in sites.items():
        good=(rec["max_lat"]-rec["min_lat"]<=0.01 and
              rec["max_lon"]-rec["min_lon"]<=0.01)
        stable[site]=good
        if good:
            group=(site[0],)+group_key(site[1])
            group_stable[group].add(site)
            if len(rec["years"])>=3:
                group_repeat3[group].add(site)
        else:
            invalid["method1_site_code_spatially_unstable"]+=1
    pair_counts=Counter()
    pair_years=defaultdict(set)
    for (site,y,m),n in month_counts.items():
        if n<2 or not stable[site] or month_counts.get((site,y+1,m),0)<2:
            continue
        group=(site[0],)+group_key(site[1])
        pair_counts[group]+=1
        pair_years[group].add(y)
    ten=[]
    for source in source_groups:
        key=("RLS",source["country"],source["area"],source["location"])
        n=len(group_stable[key])
        n3=len(group_repeat3[key])
        npair=pair_counts[key]
        ny=len(pair_years[key])
        q=(n>=5 and n3>=5 and npair>=10 and ny>=2)
        ten.append({
            "country":source["country"],
            "area":source["area"],
            "location":source["location"],
            "original_all_methods_strict_pairs":source["prior_all_method_pair_n"],
            "method1_survey_events":group_method_count[key],
            "method1_stable_sites":n,
            "method1_sites_3plus_observed_years":n3,
            "method1_strict_site_month_year_pairs":npair,
            "method1_distinct_prior_years":ny,
            "method1_physically_qualified":q
        })
    ten.sort(key=lambda r:(-r["method1_strict_site_month_year_pairs"],r["country"],r["location"]))
    return {
        "schema":SCHEMA,
        "status":"METHOD1_PHYSICAL_SURVEY_ONLY",
        "source_rows_seen":total,
        "all_methods_unique_events_by_program":dict(program_counts),
        "method1_unique_events_by_program":dict(method_counts),
        "method1_exclusions":dict(invalid),
        "method1_duplicate_survey_ids_rejected":invalid["method1_duplicate_survey_id"],
        "RLS_method1_strict_site_year_month_pairs":sum(
            n for group,n in pair_counts.items() if group[0]=="RLS"),
        "method1_all_programs_strict_site_year_month_pairs":sum(pair_counts.values()),
        "method1_qualified_primary_RLS_geographic_groups":sum(r["method1_physically_qualified"] for r in ten),
        "frozen_RLS_candidate_physical_gate":ten,
        "fish_method0_off_transect_as_complete_absence":False,
        "biological_fish_responses_accessed":False,
        "observed_natal_dispersal_or_true_colonization":False,
        "eBird_used":False,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems_admitted":0
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--frame-contract",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding="utf-8"))
    frame=json.loads(args.frame_contract.read_text(encoding="utf-8"))
    if (frame.get("schema")!="structural.nrmn_marine_event_frame_contract.v1_260"
        or protocol["source"]["survey_sidecar_sha256"]!=frame["source"]["survey_metadata_sidecar_sha256"]
        or protocol["source"]["site_source"]!="aodn-cloud-optimised/diver_survey_metadata_qc.parquet"):
        raise ValueError("Source identity/survey sidecar changed")
    try:
        result=tally_method1(source_rows(frame),protocol)
        result["source_metadata_sha256"]=protocol["source"]["survey_sidecar_sha256"]
        result["fish_schema_provenance"]=protocol["source"]["fish_schema_verified_no_rows"]
    except Exception as exc:
        result={
            "schema":SCHEMA,
            "status":"STOP_PRE_FISH_BIOLOGY_SOURCE_ONLY",
            "error_type":type(exc).__name__,
            "error":str(exc)[:500],
            "fish_biological_rows_accessed":0,
            "GEB_scientific_HOLD":True
        }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in (
        "status","source_rows_seen","RLS_method1_strict_site_year_month_pairs",
        "method1_qualified_primary_RLS_geographic_groups","error"
    )},sort_keys=True))
    if result["status"]!="METHOD1_PHYSICAL_SURVEY_ONLY":
        raise SystemExit(2)

if __name__=="__main__":
    main()
