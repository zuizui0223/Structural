#!/usr/bin/env python3
"""Pico PRIBES v1.7: original Event-core physical revisit evidence ONLY.

Never open source occurrence extensions, field names of plant taxa, or species
presence/absence responses. Do not treat unique eventIDs as locationIDs.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import date
import json
import math
from pathlib import Path
import re
import io
import zipfile
import xml.etree.ElementTree as ET

from azores_2016_dwca_structure_v1_267 import summarize_archive
from azores_PRIBES_crossisland_field_v1_271 import (
    field_columns,_table_records,get_original
)
from azores_Pico_date_diagnostic_v1_272 import slash_date_matches_author_components

SCHEMA="structural.azores_Pico_event_site_revisit.v1_275"
ALLOWED_FIELDS=("locationID","locality","decimalLatitude","decimalLongitude",
                "coordinateUncertaintyInMeters","samplingProtocol","eventDate",
                "year","month","day","island")
YEARS={"2020":171,"2021":1603,"2022":898,"2024":129}
EXPECTED_SHA="82406dbcb48e188cca6bca116437b951a80f613faadf44a173ddd5d9b92e4a02"


def parse_author_event_day(record):
    value=str(record.get("eventDate") or "").strip()
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}",value):
        raise ValueError("Original Pico author date does not satisfy M/D/YYYY")
    if slash_date_matches_author_components(value,record)!="MDY":
        raise ValueError("Original Pico author date disagrees with independent year/month/day")
    try:
        return date(int(record["year"]),int(record["month"]),int(record["day"]))
    except (TypeError,ValueError,KeyError) as ex:
        raise ValueError("Invalid original author date components") from ex


def _float_coord(record,name,low,high):
    x=(record.get(name) or "").strip()
    if not x:return None
    try:v=float(x)
    except ValueError:return None
    return v if math.isfinite(v) and low<=v<=high else None


def audit_event_core_rows(records,expected_years=YEARS):
    """Aggregate-only physical locationID/GPS repeat-years without taxon access."""
    years=Counter()
    site_years=defaultdict(list)
    gps_by_precision={p:defaultdict(set) for p in (5,4,3)}
    populated=Counter()
    eventids=set()
    source_event_rows=0
    coords=0
    no_location=0
    for record in records:
        source_event_rows+=1
        if "coreid" in record:
            eventid=str(record["coreid"])
            if eventid in eventids:raise ValueError("Original Event coreid duplicated")
            eventids.add(eventid)
        d=parse_author_event_day(record)
        years[str(d.year)]+=1
        if str(record.get("island") or "").strip().casefold()!="pico":
            raise ValueError("Source Event is outside frozen Pico island")
        for field in ALLOWED_FIELDS:
            if str(record.get(field) or "").strip():populated[field]+=1
        lat=_float_coord(record,"decimalLatitude",-90,90)
        lon=_float_coord(record,"decimalLongitude",-180,180)
        if lat is not None and lon is not None:coords+=1
        key=str(record.get("locationID") or "").strip()
        method=" ".join(str(record.get("samplingProtocol") or "").strip().casefold().split())
        if key:
            site_years[key].append((d,lat,lon,method))
        else:no_location+=1
        if lat is not None and lon is not None:
            for p in (5,4,3):
                gps_by_precision[p][(f"{lat:.{p}f}",f"{lon:.{p}f}")].add(d.year)
    if expected_years is not None and dict(sorted(years.items()))!=expected_years:
        raise ValueError("Original Pico source years disagree with independently frozen source years")
    if source_event_rows>30000:
        raise ValueError("Original Pico Event core exceeds predeclared safe cap")
    repeated=0
    unstable=0
    missing_coords=0
    stable=0
    repeat_days=0
    same_method=0
    stable_source_repeated_days=0
    for key,observations in site_years.items():
        yrs={r[0].year for r in observations}
        if len(yrs)<2:continue
        repeated+=1
        if any(x[1] is None or x[2] is None for x in observations):
            missing_coords+=1
            continue
        latitudes=[x[1] for x in observations]
        longitudes=[x[2] for x in observations]
        if max(latitudes)-min(latitudes)>0.01 or max(longitudes)-min(longitudes)>0.01:
            unstable+=1
            continue
        stable+=1
        unique_days=defaultdict(set)
        for d,_,_,_ in observations:unique_days[d.year].add(d)
        if sum(len(v)>=2 for v in unique_days.values())>=2:
            repeat_days+=1
        methods={m for _,_,_,m in observations}
        if len(methods)==1 and "" not in methods:
            same_method+=1
        if len(unique_days)>=2:
            stable_source_repeated_days+=len(observations)
    gps_repeats={p:sum(len(yrs)>=2 for yrs in gps_by_precision[p].values()) for p in (5,4,3)}
    return {
        "schema":SCHEMA,
        "original_Event_core_rows":source_event_rows,
        "source_event_year_counts":dict(sorted(years.items())),
        "source_field_populated_event_rows":dict(sorted(populated.items())),
        "source_event_rows_with_both_valid_GPS_coordinates":coords,
        "source_event_rows_without_author_locationID":no_location,
        "source_author_locationID_site_keys":len(site_years),
        "author_siteIDs_with_repeated_years_unchecked_coordinates":repeated,
        "author_siteIDs_rejected_spatial_instability":unstable,
        "author_siteIDs_with_repeated_years_but_no_all_valid_coordinates":missing_coords,
        "author_siteIDs_revisited_2plus_years_with_verified_coordinates":stable,
        "author_siteIDs_with_2plus_distinct_dates_each_in_2plus_years":repeat_days,
        "author_siteID_protocols_consistent_over_years":same_method,
        "source_events_at_stable_revisited_author_sites":stable_source_repeated_days,
        "GPS_5decimal_clusters_revisited_2plus_years":gps_repeats[5],
        "GPS_4decimal_clusters_revisited_2plus_years":gps_repeats[4],
        "GPS_3decimal_clusters_revisited_2plus_years":gps_repeats[3],
        "GPS_clusters_not_verified_permanent_plots":True,
        "site_key_not_eventID_and_not_locality":True,
        "no_taxon_specific_detection_or_absence_inferred":True,
        "no_taxon_or_geo_identifier_exported":True,
        "positive_plant_species_rows_read":0,
        "occurrence_extension_bytes_read":0,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    cfg=json.loads(args.contract.read_text(encoding="utf-8"))
    if (cfg.get("schema")!="structural.azores_Pico_event_site_revisit.v1_275"
        or cfg.get("status")!="SOURCE_EVENT_ONLY_275_FROZEN_BEFORE_SITE_YEAR_INSPECTION"
        or cfg["authority"]["original_zip_sha256"]!=EXPECTED_SHA):
        raise ValueError("Frozen original source-only Pico study/MDY date gate changed")
    manifest=json.loads((Path(__file__).resolve().parents[1]/
        "development/azores_PRIBES_original_source_manifest_v1_270.json").read_text())
    source=next(x for x in manifest["sources"] if x["label"]=="Pico PRIBES")
    if source["sha256"]!=EXPECTED_SHA or source["url"]!=cfg["authority"]["source_zip_url"]:
        raise ValueError("Source manifest and predeclared Pico study mismatch")
    out={"schema":SCHEMA,"status":"SOURCE_ACCESS_STOP_BEFORE_PHYSICAL_RESULT",
         "source_sha256":EXPECTED_SHA,"positive_plant_species_rows_read":0,
         "occurrence_extension_bytes_read":0,"GEB_scientific_HOLD":True,
         "eBird_off":True,"new_confirmatory_systems":0}
    try:
        raw=get_original(source)
        meta=summarize_archive(raw,"original Pico DOI 10.15468/vk4y7k")
        core=meta["core"]
        if not core["rowtype"].endswith("/Event"):
            raise ValueError("Pico source is not the author Event-core DwC-A")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            root=ET.fromstring(z.read("meta.xml"))
            cores=[x for x in root if x.tag.endswith("}core")]
            if len(cores)!=1:
                raise ValueError("Source Event core ambiguous")
            event_id=[x for x in cores[0] if x.tag.endswith("}id")]
            if len(event_id)!=1 or event_id[0].attrib.get("index")!="0":
                raise ValueError("Source Event ID index0 changed")
            fields=field_columns(core)
            rows=list(_table_records(z,core,fields)) # EVENT core ONLY; no occurrence ZIP member access
        audit=audit_event_core_rows(rows,YEARS)
        if audit["original_Event_core_rows"]!=2801:
            raise ValueError("Source 2801 author Pico Event denominator changed")
        out.update(audit)
        out["original_event_field_terms"]=sorted(fields)
        out["source_year_gate_verified_all_2801"]=True
        out["status"]="SOURCE_VERIFIED_EVENT_ONLY_PHYSICAL_SITE_AUDIT"
    except Exception as exc:
        out["stop_type"]=type(exc).__name__
        out["stop_reason"]=str(exc)[:500]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":out["status"],"events":out.get("original_Event_core_rows"),
       "stable_returned_author_sites":out.get("author_siteIDs_revisited_2plus_years_with_verified_coordinates"),
       "yearly_repeat_author_sites":out.get("author_siteIDs_with_2plus_distinct_dates_each_in_2plus_years"),
       "gps5_year_overlap_sites":out.get("GPS_5decimal_clusters_revisited_2plus_years"),
       "stop_reason":out.get("stop_reason")},sort_keys=True))
    if out["status"]!="SOURCE_VERIFIED_EVENT_ONLY_PHYSICAL_SITE_AUDIT":
        raise SystemExit(2)


if __name__=="__main__":
    main()
