#!/usr/bin/env python3
"""v1.312 independent original BALA Event-only published island-code correction.

The old v1.311 full-name gate remains TERMINAL. This is a new source-Event-
only check with exact 2024-published three-letter island codes. Opens zero
Original Occurrence/taxon values. Does NOT change any site/campaign cutoffs.
"""
import argparse,hashlib,json,urllib.request
from pathlib import Path
from bala_repeated_transect_event_only_v1_311 import (
    SRC,SHA,MAX_BYTES,original_event_rows,summarize
)

def recode_and_audit(events,contract):
    codebook=contract["source_codebook"]
    if set(codebook)!={"flo","fai","pic","sjg","ter","smg","smr"}:
        raise ValueError("Changed seven-island published source island codebook")
    if contract["unchanged_gates"]["required_same_source_B1_B3_transects"]!=20:
        raise ValueError("Retuned old matched physical site minimum")
    # The v1.311 source-response-blind sampling gate is REUSED unchanged,
    # except its old semantically incorrect full island name vocabulary.
    base=Path(__file__).resolve().parents[1]
    old=json.loads((base/"development/bala_original_event_repeat_gate_v1_311.json").read_text())
    old["field_role"]["island_exact_expected"]=sorted(codebook)
    r=summarize(events,old)
    n_other=r["original_Event_counts_by_phase"].get("OTHER_ISLAND_OR_SOURCE",0)
    if n_other!=198 or r["raw_source_Event_counts_by_island"].get("gra",0)!=198:
        raise ValueError("Unexpected Graciosa non-native reference period source counts; no scope change allowed")
    r["schema"]="structural.bala_original_island_code_physical_event_result.v1_312"
    r["original_v1_311_source_code_GATE_remains_TERMINAL"]=True
    r["original_source_7_island_abbreviations_to_island_names"]=codebook
    r["source_graciosa_secondary_forest_Events_excluded"]=198
    r["all_matched_site_and_campaign_cutoffs_inherited_unchanged"]=True
    r["original_Occurrence_rows_opened"]=0
    r["GEB_scientific_HOLD"]=True
    r["new_confirmatory_systems"]=0
    r["eBird_used"]=False
    if r["status"]=="EVENT_SAME_TRANSECT_THREE_PHASE_DESIGN_QUALIFIED_OCCURRENCE_SEALED":
        r["status"]="AUTHOR_CODE_CORRECTED_EVENT_REPEATS_QUALIFIED_OCCURRENCE_UNOPENED"
    else:
        r["status"]="AUTHOR_CODE_CORRECTED_SITE_OVERLAP_INSUFFICIENT_STOP"
    return r

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    cfg=json.loads(a.protocol.read_text(encoding="utf-8"))
    if (cfg.get("schema")!="structural.bala_source_island_abbreviation_corrected_event_gate.v1_312"
        or cfg.get("status")!="NEW_RESPONSE_OPAQUE_EVENT_CODE_GATE_AFTER_V1_311_TERMINAL"
        or cfg["original_source"]["archive"]!=SRC
        or cfg["original_source"]["source_sha256"]!=SHA):
        raise ValueError("Original BALA source/author-code correction not pre-frozen")
    r={"schema":"structural.bala_original_island_code_physical_event_result.v1_312",
       "status":"SOURCE_OR_SOURCE_EVENT_TECHNICAL_STOP",
       "original_Occurrence_rows_opened":0,
       "original_v1_311_source_code_GATE_remains_TERMINAL":True,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SRC,headers={"User-Agent":"Structural-BALA-PublishedSevenIslandCode-v1.312"})
        with urllib.request.urlopen(req,timeout=70) as data:blob=data.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original fixed 2024 DWCA source archive digest changed")
        r=recode_and_audit(original_event_rows(blob),cfg)
        r["original_archive_sha256"]=SHA
    except Exception as e:
        r["stop_type"]=type(e).__name__;r["stop_reason"]=str(e)[:290]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":r["status"],
        "B1_B3_same_source_sites":r.get("same_physical_transect_paired_site_count_B1_B3"),
        "all_three_periods":r.get("same_physical_transect_all_three_phase_site_count"),
        "islands_with_longitudinal_sites":r.get("island_count_with_B1_B3_repeated_transects"),
        "physical_sites_by_island":r.get("island_repeated_site_table"),
        "Graciosa_Events_excluded":r.get("source_graciosa_secondary_forest_Events_excluded"),
        "original_Occurrence_rows_opened":0,
        "stop_reason":r.get("stop_reason")},sort_keys=True))
    if r["status"]=="SOURCE_OR_SOURCE_EVENT_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
