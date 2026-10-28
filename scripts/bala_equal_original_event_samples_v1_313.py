#!/usr/bin/env python3
"""BALA original same-transect 3-wave *equal Event opportunity*, source-only.

Uses original 29 physically revisited transects / seven islands identified by
v1.312 Event-only author ID, then selects exactly per-site per-method minimum
Event count in B1/B2/B3 by original source core-ID order. The selected source
Event IDs are hashed, NEVER published. Opens zero arthropod Occurrence rows.
"""
from __future__ import annotations
import argparse,hashlib,json,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from bala_repeated_transect_event_only_v1_311 import (
    SRC,SHA,MAX_BYTES,original_event_rows,assign_phase,_trim,_norm
)

METHODS=("Pitfall solution","Open beating tray (with bag)")
ISLANDS=("flo","fai","pic","sjg","ter","smg","smr")
EXPECTED_REPEAT_ID_HASH="31a323a378f29e60ff656699081ccbbb47b546568f13f43e6472391adc8b7c72"

def select(events):
    """Return aggregate-only result; original selected IDs never leave function."""
    groups=defaultdict(list)
    for e in events:
        raw=_trim(e.get("year"))
        if not raw.isdigit():continue
        phase=assign_phase(int(raw))
        isl=_norm(e.get("island"))
        site=_trim(e.get("locationID"))
        method=_trim(e.get("samplingProtocol"))
        if phase is None or isl not in ISLANDS or not site or method not in METHODS:
            continue
        core=_trim(e.get("__original_coreid"))
        if not core:raise ValueError("Original Event source primary key is empty")
        groups[(isl,site,method,phase)].append(core)
    # Existence of a longitudinal site does not depend on a method appearing
    # there: verify method coverage only AFTER all three-site intersect.
    sites_by_phase=defaultdict(set)
    for isl,site,method,phase in groups:
        sites_by_phase[phase].add((isl,site))
    sites=set.intersection(*[sites_by_phase[x] for x in ("B1","B2","B3")])
    site_sha=hashlib.sha256("\n".join(sorted(isl+"|"+s for isl,s in sites)).encode()).hexdigest()
    selected=[]
    source_full_counts=[];small=[]
    island_totals=defaultdict(lambda:Counter())
    per_method=defaultdict(lambda:Counter())
    for isl,site in sorted(sites):
        for method in METHODS:
            rows=[sorted(groups.get((isl,site,method,p),[])) for p in ("B1","B2","B3")]
            if any(len(x)==0 for x in rows):
                small.append({"island_code":isl,"method":method})
                continue
            k=min(map(len,rows))
            source_full_counts.append(k)
            for phase,samples in zip(("B1","B2","B3"),rows):
                selected.extend(samples[:k])
                island_totals[isl][phase]+=k
                per_method[method][phase]+=k
    unique=sorted(set(selected))
    if len(unique)!=len(selected):
        raise ValueError("Original Event primary key appears in several independent sampling cells")
    checksum=hashlib.sha256("\n".join(unique).encode()).hexdigest()
    return {
      "schema":"structural.bala_equal_event_sampling_result.v1_313",
      "status":"SOURCE_EQUAL_EFFORT_FROZEN_EVENT_ONLY_OCCURRENCE_SEALED" if (
          len(sites)==29 and len(small)==0 and len(source_full_counts)==58) else
          "STOP_SAMPLING_METHOD_OR_SITE_SUPPORT_UNESTIMABLE",
      "all_three_period_original_sites":len(sites),
      "seven_island_source_sites":{i:sum(s[0]==i for s in sites) for i in ISLANDS},
      "original_all_three_site_key_SHA256":site_sha,
      "site_method_comparable_counts":len(source_full_counts),
      "missing_any_period_source_site_method_cells":len(small),
      "per_site_method_common_min_sample_Event_count_range":[min(source_full_counts),max(source_full_counts)] if source_full_counts else None,
      "selected_original_Event_row_count_all_3_campaigns":len(unique),
      "selected_original_Event_per_campaign":{
         p:sum(island_totals[isl][p] for isl in ISLANDS) for p in ("B1","B2","B3")},
      "selected_original_Event_by_sampling_method":{
         m:{p:per_method[m][p] for p in ("B1","B2","B3")} for m in METHODS},
      "selected_original_Event_by_island_campaign":{
         isl:{p:island_totals[isl][p] for p in ("B1","B2","B3")} for isl in ISLANDS},
      "selected_original_Event_coreids_SHA256":checksum,
      "selected_original_author_eventIDs_exported":False,
      "source_species_values_opened":0,
      "original_Occurrence_rows_opened":0,
      "no_2026_prior_abundance_or_richness_result_reused_as_new_finding":True,
      "GEB_scientific_HOLD":True,
      "new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    contract=json.loads(args.protocol.read_text())
    if (contract.get("schema")!="structural.bala_equal_event_physical_transect_source_gate.v1_313"
        or contract["status"]!="SOURCE_ONLY_SAMPLING_OPPORTUNITY_FROZEN_BEFORE_TAXON_VALUES"
        or contract["source"]["archive"]!=SRC
        or contract["source"]["archive_sha256"]!=SHA
        or contract["source"]["source_29_three_phase_matched_site_SHA256"]!=EXPECTED_REPEAT_ID_HASH):
        raise ValueError("Original source ID, sampling scope or prior Event-only result not frozen")
    result={"schema":"structural.bala_equal_event_sampling_result.v1_313",
        "status":"SOURCE_OR_SOURCE_EVENT_TECHNICAL_STOP","original_Occurrence_rows_opened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SRC,headers={"User-Agent":"Structural-BALA-SevenIsland-EqualEventOnly-v1.313"})
        with urllib.request.urlopen(req,timeout=70) as remote:blob=remote.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original source ZIP fingerprint no longer identical")
        rows=original_event_rows(blob)
        if len(rows)!=10379:raise ValueError("Published source original Event count changed")
        result=select(rows)
        if result["original_all_three_site_key_SHA256"]!=EXPECTED_REPEAT_ID_HASH:
            raise ValueError("Physical transect original source SHA differs from v1.312")
        if result["status"]=="SOURCE_EQUAL_EFFORT_FROZEN_EVENT_ONLY_OCCURRENCE_SEALED":
            if any(result["selected_original_Event_by_sampling_method"][m][p]==0
                   for m in METHODS for p in ("B1","B2","B3")):
                raise ValueError("Original source sampled equal methods are empty")
        result["original_archive_sha256"]=SHA
    except Exception as ex:
        result["stop_type"]=type(ex).__name__;result["stop_reason"]=str(ex)[:260]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:result.get(k) for k in (
       "status","all_three_period_original_sites","site_method_comparable_counts",
       "missing_any_period_source_site_method_cells",
       "per_site_method_common_min_sample_Event_count_range",
       "selected_original_Event_row_count_all_3_campaigns",
       "selected_original_Event_per_campaign","selected_original_Event_by_sampling_method",
       "original_Occurrence_rows_opened","stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_SOURCE_EVENT_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
