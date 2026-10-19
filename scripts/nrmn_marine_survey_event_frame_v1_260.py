#!/usr/bin/env python3
"""AODN NRMN RLS/ATRC marine survey-event physical frame; never fish responses.

Reads the original 11 survey-metadata fields from the public Arrow dataset,
checks the previously frozen sidecar fingerprint, and reports physical sample
opportunities. No fish species or abundance columns are accessed.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re

import pyarrow as pa
import pyarrow.dataset as ds
from pyarrow import fs

SCHEMA="structural.nrmn_marine_event_frame.v1_260"
COLUMNS=("survey_id","survey_date","country","area","location","site_code",
         "latitude","longitude","depth","program","methods")
MAX_RECORDS=3_000_000
DATE_MIN=date(1992,1,1)
DATE_MAX=date(2026,10,19)


def clean(value):
    return "" if value is None else str(value).strip()


def program_class(raw):
    name=clean(raw).upper()
    labels=set(re.findall(r"[A-Z0-9]+",name))
    if "RLS" in labels and "ATRC" not in labels: return "RLS"
    if "ATRC" in labels and "RLS" not in labels: return "ATRC"
    if "RLS" in labels and "ATRC" in labels: return "MIXED"
    return "OTHER"


def physical_row(record):
    try:
        sid=int(record.get("survey_id"))
        d=date.fromisoformat(clean(record.get("survey_date"))[:10])
        lat=float(record.get("latitude"))
        lon=float(record.get("longitude"))
    except (TypeError,ValueError,OverflowError) as exc:
        raise ValueError("Invalid survey date, identity or coordinates") from exc
    if not DATE_MIN<=d<=DATE_MAX or not (math.isfinite(lat) and -90<=lat<=90) or not (
            math.isfinite(lon) and -180<=lon<=180):
        raise ValueError("Physical record outside frozen date and coordinate domain")
    parts=tuple(clean(record.get(c)).casefold() for c in ("country","area","location","site_code"))
    if sid<0 or not parts[0] or not parts[3]:
        raise ValueError("Missing public survey country or site code")
    pg=program_class(record.get("program"))
    return sid,pg,parts,d,lat,lon,clean(record.get("methods"))


def accumulate(rows, contract):
    if contract.get("schema")!="structural.nrmn_marine_event_frame_contract.v1_260":
        raise ValueError("Physical survey frame protocol does not match frozen v1.260")
    if contract["allowed_input_columns"]!=list(COLUMNS):
        raise ValueError("Only eleven source physical columns are permitted")
    seen=set()
    by_event=Counter()
    method=Counter()
    program=Counter()
    sites={}
    rejected=Counter()
    total=0
    valid=0
    for r in rows:
        total+=1
        if total>MAX_RECORDS:
            raise ValueError("Source survey exceeds original prospective 3M record cap")
        try:
            sid,pg,parts,d,lat,lon,met=physical_row(r)
        except ValueError:
            rejected["invalid_physical_survey"]+=1
            continue
        if sid in seen:
            # A survey_id may not be treated as independent transects when
            # duplicated in the original metadata source.
            rejected["duplicate_survey_id"]+=1
            continue
        seen.add(sid)
        valid+=1
        program[pg]+=1
        method[(pg,met[:100])]+=1
        site=(pg,parts)
        by_event[(site,d.year,d.month)]+=1
        if site not in sites:
            sites[site]={"first_year":d.year,"last_year":d.year,
                         "years":set(),"lat_min":lat,"lat_max":lat,
                         "lon_min":lon,"lon_max":lon,"surveys":0}
        s=sites[site]
        s["first_year"]=min(s["first_year"],d.year)
        s["last_year"]=max(s["last_year"],d.year)
        s["years"].add(d.year)
        s["surveys"]+=1
        s["lat_min"]=min(s["lat_min"],lat);s["lat_max"]=max(s["lat_max"],lat)
        s["lon_min"]=min(s["lon_min"],lon);s["lon_max"]=max(s["lon_max"],lon)

    site_good={}
    for site,s in sites.items():
        stable=(s["lat_max"]-s["lat_min"]<=0.01 and
                s["lon_max"]-s["lon_min"]<=0.01)
        site_good[site]=stable
        if not stable:rejected["site_code_spatially_unstable"]+=1

    group_sites=defaultdict(set)
    group_repeat3=defaultdict(set)
    group_pairs=Counter()
    group_pair_years=defaultdict(set)
    group_event_counts=Counter()
    group_span={}
    group_mismatches=Counter()
    for site,s in sites.items():
        pg,parts=site
        country,area,location,_=parts
        group=(pg,country,area,location)
        group_event_counts[group]+=s["surveys"]
        low,high=group_span.get(group,(9999,0))
        group_span[group]=(min(low,s["first_year"]),max(high,s["last_year"]))
        if not site_good[site]:
            group_mismatches[group]+=1
            continue
        group_sites[group].add(site)
        if len(s["years"])>=3: group_repeat3[group].add(site)
    for (site,year,month),n in by_event.items():
        if n<2 or not site_good[site]: continue
        if by_event.get((site,year+1,month),0)<2:continue
        pg,parts=site
        country,area,location,_=parts
        group=(pg,country,area,location)
        group_pairs[group]+=1
        group_pair_years[group].add(year)

    all_groups=set(group_event_counts)
    summaries=[]
    qualified_by_pg=Counter()
    qualified_by_country=Counter()
    for group in all_groups:
        pg,country,area,location=group
        stable_sites=len(group_sites[group])
        repeat3=len(group_repeat3[group])
        pairs=group_pairs[group]
        prior=len(group_pair_years[group])
        q=stable_sites>=5 and repeat3>=5 and pairs>=10 and prior>=2
        if q:
            qualified_by_pg[pg]+=1
            qualified_by_country[(pg,country)]+=1
        summaries.append({
            "program":pg,"country":country,"area":area,"location":location,
            "all_survey_events":group_event_counts[group],
            "stable_site_codes":stable_sites,
            "sites_with_three_observed_years":repeat3,
            "strict_same_month_consecutive_year_pairs_both_2plus":pairs,
            "distinct_prior_years_with_pairs":prior,
            "unstable_site_codes":group_mismatches[group],
            "survey_first_year":group_span[group][0],
            "survey_last_year":group_span[group][1],
            "preoutcome_qualified_physical_group":q
        })
    summaries.sort(key=lambda r:(-r["strict_same_month_consecutive_year_pairs_both_2plus"],
                                  -r["sites_with_three_observed_years"],r["program"],r["country"],r["location"]))
    max_out=int(contract["output"]["bounded_group_report"].split(" ")[2])
    # frozen human-readable contract says "at most 150 ...", fail if altered
    if max_out!=150: raise ValueError("Unexpected predeclared max physical groups")
    return {
        "schema":SCHEMA,
        "status":"PHYSICAL_SURVEY_METADATA_ONLY",
        "source_rows_seen":total,
        "unique_valid_survey_ids":valid,
        "count_invalid_by_reason":dict(rejected),
        "program_survey_counts":dict(program),
        "physical_distinct_site_code_program_keys":len(sites),
        "total_geographic_program_groups":len(summaries),
        "all_programs_strict_pairs":sum(group_pairs.values()),
        "RLS_strict_same_month_site_year_pairs":sum(
            n for key,n in group_pairs.items() if key[0]=="RLS"),
        "qualified_physical_groups_by_program":dict(qualified_by_pg),
        "qualified_RLS_by_country":{
            country:n for (pg,country),n in qualified_by_country.items() if pg=="RLS"},
        "physical_groups_ranked_by_repetition":summaries[:max_out],
        "other_unreported_physical_groups":max(0,len(summaries)-max_out),
        "top_method_field_labels":[
            {"program":p,"method":m,"event_count":n}
            for (p,m),n in method.most_common(25)
        ],
        "biological_fish_species_or_counts_accessed":False,
        "source_to_target_dispersal_measured":False,
        "geological_island_groups_identified":False,
        "new_confirmatory_systems_admitted":0,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }


def source_rows(contract):
    src=contract["source"]
    if (src["region"]!="ap-southeast-2"
        or src["bucket"]!="aodn-cloud-optimised"
        or src["survey_metadata_sidecar_sha256"]!="6bb15e9aff7600c7e429c989d929a4eb6841ffff423915e041adf263a8603dce"
        or src["survey_dataset"]!="diver_survey_metadata_qc.parquet"):
        raise ValueError("Source-pinned AODN physical dataset path/fingerprint modified")
    s3=fs.S3FileSystem(region=src["region"],endpoint_override=src["endpoint"],
                       anonymous=True,request_timeout=35)
    side=f"{src['bucket']}/{src['survey_dataset']}/_common_metadata"
    info=s3.get_file_info(side)
    if info.type!=fs.FileType.File or info.size>5_000_000:
        raise ValueError("Original source sidecar unavailable")
    with s3.open_input_file(side) as input:
        sha=hashlib.sha256(input.read()).hexdigest()
    if sha!=src["survey_metadata_sidecar_sha256"]:
        raise ValueError("AODN public survey schema changed since prior frozen source audit")
    dataset=ds.dataset(f"{src['bucket']}/{src['survey_dataset']}",
                       filesystem=s3,format="parquet",partitioning="hive")
    if not set(COLUMNS)<=set(dataset.schema.names):
        raise ValueError("Dataset lacks frozen eleven physical event fields")
    for batch in dataset.scanner(columns=list(COLUMNS),batch_size=16384,use_threads=True).to_batches():
        yield from batch.to_pylist()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    try:
        result=accumulate(source_rows(contract),contract)
        result["source_dataset"]=contract["source"]["survey_dataset"]
        result["source_metadata_sha256"]=contract["source"]["survey_metadata_sidecar_sha256"]
    except Exception as e:
        result={"schema":SCHEMA,"status":"STOP_BEFORE_ECOLOGICAL_INTERPRETATION",
                "error_type":type(e).__name__,"error":str(e)[:500],
                "fish_biological_rows_accessed":0,
                "GEB_scientific_HOLD":True}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in (
        "status","error","source_rows_seen","unique_valid_survey_ids",
        "RLS_strict_same_month_site_year_pairs","qualified_physical_groups_by_program")},sort_keys=True))
    if result["status"]!="PHYSICAL_SURVEY_METADATA_ONLY":
        raise SystemExit(2)


if __name__=="__main__":main()
