#!/usr/bin/env python3
"""PRIBES v1.322: source-Event-only exact one-hour ecological source frame.

The earlier all-Event v1.321 method/effort gate is permanently TERMINAL.
This is a separate lower-evidence response-blind survey cohort following
the original authors' fixed one-hour vegetation-beating design. Exclude
unknown or 30-minute Event samples solely by original sampling metadata.
Original site/taxon/colonisation values stay sealed.
"""
import argparse,hashlib,json,math,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from pribes_original_event_sites_v1_321 import (
    SOURCE,SHA,MAX_SOURCE,event_source_only,audit as old_event_audit,
    normalized_island,alphabetize,OVERLAP,ISLAND_LABELS
)

def original_onehour_cohort(rows,contract,old_contract):
    old=old_event_audit(rows,old_contract)
    if (old["status"]!="PRIBES_EVENT_SOURCE_SITE_OR_EFFORT_TERMINAL_NO_SPECIES_OPEN"
        or old["source_physical_location_key_n"]!=78
        or old["overlapping_BALA_island_site_count"]!=73
        or old["original_Event_rows_examined"]!=80
        or old["observed_overlap_effort_vocabulary_counts"]!={"1 hour":72,"30 minutes":1}
        or old["source_rows_missing_source_site_coordinate_effort"]!={"sampling_effort_missing_or_invalid":1}):
        raise ValueError("Original response-free v1.321 TERMINAL diagnosis not fixed")
    aliases=old_contract["field_contract"]["island_mapping_predeclared"]
    groups=defaultdict(list)
    reasons=Counter()
    original_islands=set()
    seen=set()
    for r in rows:
        core=str(r.get("original_coreid","")).strip()
        if not core or core in seen:raise ValueError("Duplicate original Event coreid")
        seen.add(core)
        island=normalized_island(r.get("island"),aliases)
        if island not in ISLAND_LABELS:raise ValueError("Unrecognized island after source Event exposure")
        original_islands.add(island)
        method=" ".join(str(r.get("samplingProtocol","")).casefold().split())
        unit=" ".join(str(r.get("sampleSizeUnit","")).casefold().split())
        sample=str(r.get("sampleSizeValue","")).strip()
        try:value=float(sample)
        except (TypeError,ValueError):value=float("nan")
        if not math.isfinite(value) or not unit:
            reasons["unknown_source_effort"]+=1;continue
        if not (value==1.0 and unit=="hour"):
            reasons["not_original_published_one_hour"]+=1;continue
        if method!="vegetation beating":
            reasons["not_original_one_hour_vegetation_beating_method"]+=1;continue
        loc=alphabetize(r.get("locationID"))
        if not loc:
            reasons["blank_original_locationID"]+=1;continue
        date=str(r.get("eventDate","")).strip()
        yr=date[:4]
        if not yr.isdigit() or not 2019<=int(yr)<=2025:
            raise ValueError("Source original Event date not within 2019–2025")
        if str(r.get("year","")).strip() and str(r.get("year")).strip()!=yr:
            raise ValueError("Source original date vs year mismatch")
        try:
            lat=float(r.get("decimalLatitude"));lon=float(r.get("decimalLongitude"))
        except (TypeError,ValueError):
            raise ValueError("Source original coordinate not parseable at 1-hour admitted Event")
        if not math.isfinite(lat) or not math.isfinite(lon):
            raise ValueError("Source coordinate missing at 1-hour event")
        groups[(island,loc)].append({"core":core,"lat":lat,"lon":lon,"year":int(yr)})
    selected=[];out_counts=Counter();years=defaultdict(Counter)
    duplicates=0;geocollision=0
    for (island,loc),records in sorted(groups.items()):
        chosen=min(records,key=lambda item:item["core"])
        duplicates+=len(records)-1
        geocollision+=sum(
             max(abs(chosen["lat"]-row["lat"]),abs(chosen["lon"]-row["lon"]))>0.0003
             for row in records)
        if island in OVERLAP:
            selected.append(chosen["core"])
            out_counts[island]+=1
            years[island][chosen["year"]]+=1
    min_sites=contract["event_only_site_selection"]["original_qualifying_sites_per_overlap_island_min"]
    eligible=(set(original_islands)==set(ISLAND_LABELS)
           and len(selected)==contract["event_only_site_selection"]["original_expected_full_hour_overlap_sites"]
           and all(out_counts[i]>=min_sites for i in OVERLAP)
           and not geocollision
           and reasons=={"unknown_source_effort":1,"not_original_published_one_hour":1})
    return {
      "schema":"structural.pribes_equal_onehour_original_event_result.v1_322",
      "status":"NEW_SEPARATE_72_RUDERAL_SITES_ONEHOUR_EACH_TAXON_RESPONSES_SEALED"
         if eligible else "TERMINAL_NO_EXACT_PUBLISHED_ONEHOUR_SIX_ISLAND_FRAME",
      "original_source_Event_rows_inspected":len(rows),
      "previous_v1_321_full_source_equal_effort_gate":"TERMINAL",
      "published_original_islands_seen":len(original_islands),
      "source_event_exclusions_by_exact_effort_metadata":dict(sorted(reasons.items())),
      "source_additional_duplicate_onehour_Events_per_site":duplicates,
      "source_duplicate_original_site_coordinate_conflicts":geocollision,
      "onehour_source_sites_overlapping_BALA_n":len(selected),
      "onehour_source_physical_sites_by_BALA_overlap_island":{i:out_counts[i] for i in OVERLAP},
      "onehour_source_site_years_by_island":{i:dict(sorted(years[i].items())) for i in OVERLAP},
      "source_onehour_selected_original_Event_coreids_sha256":hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest(),
      "source_onehour_selected_physical_site_count_all_seven":len(groups),
      "source_origin_and_species_values_OPENED":0,
      "original_BALA_Event_or_Occurrence_rows_reopened":0,
      "original_source_exact_v1_3_SHA256":SHA,
      "new_confirmatory_systems":0,
      "GEB_scientific_HOLD":True,
      "eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--previous-event-contract",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    old=json.loads(args.previous_event_contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.pribes_ruderal_equal_1h_source_sites.v1_322"
        or c.get("status")!="EXPLICIT_SEPARATE_POST_EVENT_QA_SOURCE_FRAME_FROZEN_BEFORE_ANY_PRIBES_TAXON_RESPONSE"
        or c["source"]["official_archive"]!=SOURCE or c["source"]["original_sha256"]!=SHA
        or old.get("schema")!="structural.pribes_ruderal_original_event_site_design.v1_321"):
        raise ValueError("Separate source-only one-hour cohort protocol not frozen")
    result={
      "schema":"structural.pribes_equal_onehour_original_event_result.v1_322",
      "status":"ORIGINAL_SOURCE_OR_EVENT_DETERMINISTIC_STOP",
      "previous_v1_321_full_source_equal_effort_gate":"TERMINAL",
      "source_origin_and_species_values_OPENED":0,
      "original_BALA_Event_or_Occurrence_rows_reopened":0,
      "new_confirmatory_systems":0,"GEB_scientific_HOLD":True,"eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-PRIBES-OneHour-EventOnly-v1.322"})
        with urllib.request.urlopen(req,timeout=60) as f:source=f.read(MAX_SOURCE+1)
        if len(source)>MAX_SOURCE or hashlib.sha256(source).hexdigest()!=SHA:
            raise ValueError("PRIBES archived original source bytes changed")
        result=original_onehour_cohort(event_source_only(source),c,old)
    except Exception as e:
        result["stop_type"]=type(e).__name__;result["stop_reason"]=str(e)[:300]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:result.get(key) for key in (
        "status","onehour_source_sites_overlapping_BALA_n",
        "onehour_source_physical_sites_by_BALA_overlap_island",
        "source_event_exclusions_by_exact_effort_metadata",
        "source_origin_and_species_values_OPENED","stop_reason"
    )},sort_keys=True))
    if result["status"]=="ORIGINAL_SOURCE_OR_EVENT_DETERMINISTIC_STOP":
        raise SystemExit(2)
if __name__=="__main__":
    main()
