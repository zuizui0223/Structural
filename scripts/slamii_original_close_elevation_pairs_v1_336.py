#!/usr/bin/env python3
"""SLAM II v1.336: alternate response-blind exact low-altitude gap field pairs.

The original v1.335 author class-count integrity FAIL is kept TERMINAL.
This new lower-evidence matching protocol was frozen after source EVENT
metadata but before any of the 2,097 taxonomic rows was opened.
Use original SMR and TER sites with elevation common support, exact
year/method/sampling effort and <=100m elevation difference. Max cardinality
and min altitude distance, with Event-ID tie break, never species outcomes.
"""
from __future__ import annotations
import argparse,hashlib,json,math,statistics,urllib.request
from collections import Counter
from pathlib import Path
from slamii_original_meta_only_v1_334 import SOURCE,MAX_BYTES
from slamii_original_forest_elevation_event_v1_335 import (
    SHA,source_events,evaluate,island_code,classify_habitat,normalize
)

def _best_pairs(native,altered,maxgap):
    native=sorted(native,key=lambda x:x["core"])
    altered=sorted(altered,key=lambda x:x["core"])
    best=(0,float("inf"),(),[])
    def recurse(i,used,pairs):
        nonlocal best
        if i==len(native):
            n=len(pairs)
            cost=sum(abs(a["elevation"]-b["elevation"]) for a,b in pairs)
            ties=tuple(sorted((a["core"],b["core"]) for a,b in pairs))
            if (-n,cost,ties)<(-best[0],best[1],best[2]):
                best=(n,cost,ties,list(pairs))
            return
        recurse(i+1,used,pairs)
        a=native[i]
        for k,b in enumerate(altered):
            if k in used:continue
            if abs(a["elevation"]-b["elevation"])>maxgap:continue
            if (a["year"],a["unit"],a["size"],a["method"]) != (b["year"],b["unit"],b["size"],b["method"]):
                continue
            used.add(k);pairs.append((a,b))
            recurse(i+1,used,pairs)
            pairs.pop();used.remove(k)
    recurse(0,set(),[])
    return best[3]

def compare(events,study,old):
    previous=evaluate(events,old)
    if (previous["status"]!="STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED"
        or previous["original_habitat_site_totals"]!=study["source"]["observed_actual_source_habitat_n"]
        or previous["original_Event_values_read"]!=45
        or previous["original_source_site_metadata_invalid_counts"]):
        raise ValueError("Original pre-response v1.335 scientific source STOP/denominator changed")
    for island in ("SMR","TER","FLO","COR"):
        declared=study["source_eligible_islands"][island]
        observed=previous["original_per_island_habitat_elevation"][island]
        if (observed["original_native_site_n"]!=declared["observed_author_native_plots"]
            or sum(observed["original_mixed_site_n"] for _ in [0])+observed["original_exotic_site_n"]!=declared["altered_plots"]
            or observed["common_elevation_interval_m"]!=declared["source_range_overlap"]
            or observed["n_original_native_plots_in_common_elevation_range"]!=declared["native_in_overlap"]
            or observed["n_original_altered_plots_in_common_elevation_range"]!=declared["altered_in_overlap"]):
            raise ValueError("Original v1.335 source physical per-island common elevation support changed")
    plots={isl:{"native":[],"altered":[]} for isl in study["pairing_frozen_before_source_reaccess"]["islands_exact"]}
    for row in events:
        island=island_code(row.get("island"),old)
        if island not in plots:continue
        habitat=classify_habitat(row.get("habitat"),old)
        group="native" if habitat=="native" else "altered"
        source_core=str(row["__original_coreid"]).strip()
        if not source_core:raise ValueError("Original Event ID missing")
        try:height=float(row.get("minimumElevationInMeters"))
        except (ValueError,TypeError):raise ValueError("Original source site elevation unverified")
        unit=normalize(row.get("sampleSizeUnit"))
        size=str(row.get("sampleSizeValue","")).strip()
        meth=normalize(row.get("samplingProtocol"))
        year=str(row.get("year","")).strip() or str(row.get("eventDate",""))[:4]
        if not meth or not year or not unit or not size or not math.isfinite(height):
            raise ValueError("Original SLAM Event lacked year/effort/method/elevation")
        plots[island][group].append({
            "core":source_core,"elevation":height,
            "year":year,"unit":unit,"size":size,"method":meth})
    max_gap=study["pairing_frozen_before_source_reaccess"]["maximum_native_altered_elevation_distance_m"]
    rec={};all_matches=[]
    valid_islands=[]
    for island in study["pairing_frozen_before_source_reaccess"]["islands_exact"]:
        overlap=previous["original_per_island_habitat_elevation"][island]["common_elevation_interval_m"]
        if overlap is None:raise ValueError("Original common source elevational support missing")
        lo,hi=overlap
        native=[x for x in plots[island]["native"] if lo<=x["elevation"]<=hi]
        altered=[x for x in plots[island]["altered"] if lo<=x["elevation"]<=hi]
        pairs=_best_pairs(native,altered,max_gap)
        if len(pairs)>=study["pairing_frozen_before_source_reaccess"]["site_pairs_min_per_island"]:
            valid_islands.append(island)
        gaps=[abs(a["elevation"]-b["elevation"]) for a,b in pairs]
        rec[island]={
            "eligible_native_original_plots_in_common_support":len(native),
            "eligible_altered_original_plots_in_common_support":len(altered),
            "matched_one_to_one_original_forest_plot_pairs":len(pairs),
            "maximum_source_plot_pair_elevation_difference_m":max(gaps) if gaps else None,
            "mean_source_plot_pair_elevation_difference_m":statistics.fmean(gaps) if gaps else None,
            "source_pairing_year_counts":dict(Counter(a["year"] for a,b in pairs)),
            "source_matching_one_hour_unit_per_pair":dict(Counter(f'{a["size"]}|{a["unit"]}' for a,b in pairs)),
            "matched_original_coreid_pairs_SHA256":hashlib.sha256(
                "\n".join(sorted(a["core"]+"|"+b["core"] for a,b in pairs)).encode()).hexdigest()
        }
        all_matches.extend((island,a["core"],b["core"]) for a,b in pairs)
    eligible=len(valid_islands)>=study["pairing_frozen_before_source_reaccess"]["original_islands_with_2plus_pairs_required"]
    return {
        "schema":"structural.slamII_close_elevation_original_pair_result.v1_336",
        "status":"NEW_SEPARATE_SMRT_TER_FOREST_ELEVATION_PAIR_FRAME_TAXON_SEALED" if eligible else
                 "TERMINAL_NO_TWO_ISLANDS_ELEVATION_YEAR_EFFORT_PAIRED_FOREST_PLOTS",
        "original_source_v18_SHA256":SHA,
        "original_Source_Event_rows_reexamined":45,
        "original_Source_Occurrence_rows_opened":0,
        "previous_v1_335_original_author_class_gate":"STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED",
        "source_original_habitat_counts_v18":previous["original_habitat_site_totals"],
        "source_original_island_site_counts":previous["original_4island_physical_sites"],
        "max_permitted_site_altitude_gap_m":max_gap,
        "source_matched_plot_pairs_by_island":rec,
        "source_islands_passing_2_pairs_and_matched_sampling":valid_islands,
        "source_matched_source_coreid_triplets_SHA256":hashlib.sha256(
            "\n".join("|".join(x) for x in sorted(all_matches)).encode()).hexdigest(),
        "source_pairing_taxon_responses_not_inspected":True,
        "source_original_site_IDs_and_taxa_not_exported":True,
        "old_SLAM_BALA_PRIBES_Madeira_Terceira2024_taxon_rows_reopened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--old-contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text())
    old=json.loads(a.old_contract.read_text())
    if (c.get("schema")!="structural.slamII_physical_elevation_paired_habitat.v1_336"
        or c.get("status")!="SEPARATE_POST_SOURCE_METADATA_RECLASSIFICATION_BEFORE_TAXON_VALUES"
        or c["source"]["archive"]!=SOURCE
        or c["source"]["original_zip_SHA256"]!=SHA
        or old.get("schema")!="structural.slamII_45forest_original_event_elevation_gate.v1_335"):
        raise ValueError("New lower-evidence source-pair ecological study not frozen")
    result={"schema":"structural.slamII_close_elevation_original_pair_result.v1_336",
            "status":"ORIGINAL_SOURCE_OR_EVENT_TECHNICAL_STOP",
            "original_Source_Occurrence_rows_opened":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-v1.336-SLAMII-Source-Pairs-EVENT-ONLY"})
        with urllib.request.urlopen(req,timeout=65) as f:blob=f.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original source archive SHA changed")
        result=compare(source_events(blob),c,old)
    except Exception as exc:
        result["stop_type"]=type(exc).__name__
        result["stop_reason"]=str(exc)[:300]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({
        "status":result["status"],
        "old_original_45site_gate":result.get("previous_v1_335_original_author_class_gate"),
        "matched_original_plot_pairs":result.get("source_matched_plot_pairs_by_island"),
        "taxa_opened":result["original_Source_Occurrence_rows_opened"],
        "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="ORIGINAL_SOURCE_OR_EVENT_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
