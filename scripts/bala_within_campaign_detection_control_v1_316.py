#!/usr/bin/env python3
"""BALA v1.316: retrospective same-campaign sample-split detection-heterogeneity test.

The 2026 v1.314 original biological scorer remains SEALED. This is a separate,
explicitly nonconfirmatory falsification: for each of nine predeclared
source-ID-only partitions, compare B1/B3 half-EVent community dissimilarity
with B1A/B1B and B3A/B3B pseudo-turnover under equal original capture effort.
No taxonomic-source labels, original Event IDs or site IDs are exported.
"""
from __future__ import annotations

import argparse,hashlib,json,math,statistics,urllib.request
from collections import Counter,defaultdict
from pathlib import Path

from bala_repeated_transect_event_only_v1_311 import (
    SRC,SHA,MAX_BYTES,original_event_rows,_norm,_trim
)
from bala_equal_original_event_samples_v1_313 import (
    METHODS,ISLANDS
)
from bala_original_species_replacement_v1_314 import (
    original_occurrence_rows,reconstruct_selected_original_event_design,site_beta,
)

SALTS=tuple(f"split-{n}" for n in range(9))
PHASES=("B1","B3")
GUILDS=("araneae","coleoptera")
MAIN="Pitfall solution"
SOURCE_V314_SHA="b30eca5283d6984ee056ca8e74dd46fa2192c83558b175fbb84ff6546170f7a1"

def mean(xs):
    return statistics.fmean(xs) if xs else None

def _partition(ids,salt):
    if len(ids)<10:
        raise ValueError("Original pre-frozen minimum sampling effort <10 Event rows at site phase")
    m=len(ids)//2
    if m<5:
        raise ValueError("At least 5 original source Events required per sub-sample")
    ordered=sorted(ids,key=lambda c:(hashlib.sha256((salt+"|"+c).encode("utf-8")).hexdigest(),c))
    a=ordered[:m]
    b=ordered[m:2*m]
    if len(a)!=len(b) or len(set(a)&set(b)):
        raise AssertionError("Original source split not disjoint/equal effort")
    return a,b

def _score_split(a,b,c,d):
    """B1A,B1B,B3A,B3B; require all four observed source species sets."""
    if any(not x for x in (a,b,c,d)):
        return None
    within=[site_beta(a,b),site_beta(c,d)]
    across=[site_beta(x,y) for x in (a,b) for y in (c,d)]
    if any(x is None for x in within+across):
        raise AssertionError("All four nonempty sets must have defined pair dissimilarity")
    within_s=mean([x["sorensen_beta_total"] for x in within])
    across_s=mean([x["sorensen_beta_total"] for x in across])
    within_r=mean([x["simpson_beta_replacement"] for x in within])
    across_r=mean([x["simpson_beta_replacement"] for x in across])
    return {
        "within_sorensen":within_s,"across_sorensen":across_s,
        "delta_sorensen":across_s-within_s,
        "within_simpson":within_r,"across_simpson":across_r,
        "delta_simpson":across_r-within_r,
    }

def evaluate_selected(selected,sites,source_taxa,contract):
    """Source-time-frozen Event selection; guild labels never select source sites."""
    if contract["sampling"]["predefined_salts"]!=list(SALTS):
        raise ValueError("Original nine source-only partition salts changed")
    if contract["sampling"]["main_method_exact"]!=MAIN:
        raise ValueError("Original source pitfall primary method changed")
    if set(contract["sampling"]["main_guilds_exact"])!=set(GUILDS):
        raise ValueError("Original taxonomic guild identity changed")

    events=defaultdict(list)
    for original, (isl,site,method,phase) in selected.items():
        if phase in PHASES:
            events[(isl,site,method,phase)].append(original)
    if len(sites)!=29 or sum(sum(isl==i for isl,site in sites) for i in ISLANDS)!=29:
        raise ValueError("Original 29 site seven-island population identity changed")
    results={}
    for method in METHODS:
        method_results={}
        for guild in GUILDS:
            island_entries=defaultdict(list)
            lost_sites=Counter()
            split_counts=Counter()
            for island,site in sorted(sites):
                b1=events.get((island,site,method,"B1"),[])
                b3=events.get((island,site,method,"B3"),[])
                if not b1 or not b3 or len(b1)!=len(b3):
                    raise ValueError("Original equal Event opportunity no longer holds for B1/B3")
                splits=[]
                for salt in SALTS:
                    ea,eb=_partition(b1,salt)
                    ec,ed=_partition(b3,salt)
                    sa=set.union(*(source_taxa.get((core,guild),set()) for core in ea))
                    sb=set.union(*(source_taxa.get((core,guild),set()) for core in eb))
                    sc=set.union(*(source_taxa.get((core,guild),set()) for core in ec))
                    sd=set.union(*(source_taxa.get((core,guild),set()) for core in ed))
                    pair=_score_split(sa,sb,sc,sd)
                    if pair is not None:splits.append(pair)
                split_counts[len(splits)]+=1
                if len(splits)<5:
                    lost_sites[island]+=1
                    continue
                island_entries[island].append({
                    k:mean([row[k] for row in splits])
                    for k in ("within_sorensen","across_sorensen","delta_sorensen",
                              "within_simpson","across_simpson","delta_simpson")
                })
            summary={}
            for i in ISLANDS:
                raw=island_entries[i]
                summary[i]={
                    "original_transects_eligible_from_source_physical_frame":sum(x[0]==i for x in sites),
                    "original_transects_passing_half_sample_detection_gate":len(raw),
                    "original_transects_failing_half_sample_detection_gate":lost_sites[i],
                    "mean_within_campaign_sorensen":mean([r["within_sorensen"] for r in raw]),
                    "mean_across_campaign_sorensen":mean([r["across_sorensen"] for r in raw]),
                    "mean_across_minus_within_sorensen":mean([r["delta_sorensen"] for r in raw]),
                    "mean_within_campaign_simpson_replacement":mean([r["within_simpson"] for r in raw]),
                    "mean_across_campaign_simpson_replacement":mean([r["across_simpson"] for r in raw]),
                    "mean_across_minus_within_simpson":mean([r["delta_simpson"] for r in raw]),
                    "original_sites_positive_delta_sorensen":sum(r["delta_sorensen"]>0 for r in raw),
                    "original_sites_nonpositive_delta_sorensen":sum(r["delta_sorensen"]<=0 for r in raw),
                }
            accepted=[x for x in summary.values()
                      if x["original_transects_passing_half_sample_detection_gate"]>0]
            actual_sites=sum(x["original_transects_passing_half_sample_detection_gate"]
                             for x in summary.values())
            threshold=contract["metrics"]["inferential_threshold"]
            qualified=(len(accepted)>=5 and actual_sites>=20)
            method_results[guild]={
                "schema":"structural.bala_detection_control_per_guild.v1_316",
                "status":"RETROSPECTIVE_PAIRED_SAMPLING_CONTROL_SCORED" if qualified
                          else "STOP_INSUFFICIENT_HALF_SAMPLE_GUILD_DETECTION_SUPPORT",
                "original_matched_transect_universe":29,
                "original_sites_observed_in_four_halves_at_least_five_of_nine_salts":actual_sites,
                "islands_with_at_least_one_eligible_original_site":len(accepted),
                "original_sites_valid_salt_count_histogram":{str(k):v for k,v in sorted(split_counts.items())},
                "island_equal_delta_sorensen":mean([x["mean_across_minus_within_sorensen"] for x in accepted]) if qualified else None,
                "island_equal_across_campaign_sorensen":mean([x["mean_across_campaign_sorensen"] for x in accepted]) if qualified else None,
                "island_equal_within_campaign_sorensen":mean([x["mean_within_campaign_sorensen"] for x in accepted]) if qualified else None,
                "island_equal_delta_simpson_replacement":mean([x["mean_across_minus_within_simpson"] for x in accepted]) if qualified else None,
                "island_equal_within_campaign_simpson":mean([x["mean_within_campaign_simpson_replacement"] for x in accepted]) if qualified else None,
                "island_equal_across_campaign_simpson":mean([x["mean_across_campaign_simpson_replacement"] for x in accepted]) if qualified else None,
                "islands_positive_excess_temporal_dissimilarity":sum(
                    x["mean_across_minus_within_sorensen"]>0 for x in accepted) if qualified else None,
                "per_island":summary,
                "source_original_nine_fixed_splits_are_not_nine_independent_replications":True,
                "source_transect_not_trap_is_independent_spatial_unit":True,
            }
        results[method]=method_results
    return {
        "schema":"structural.bala_within_campaign_detection_control_source_result.v1_316",
        "status":"RETROSPECTIVE_TWO_GUILD_WITHIN_CAMPAIGN_FALSIFICATION_COMPLETE",
        "main_method":MAIN,"source_methods":list(METHODS),
        "source_original_transects":len(sites),
        "source_islands":len(ISLANDS),
        "nine_predeclared_source_only_halving_salts":list(SALTS),
        "main_pitfall":results[MAIN],
        "secondary_canopy_beating":results["Open beating tray (with bag)"],
        "main_ten_percent_dissimilarity_is_not_a_detectability_corrected_effect":True,
        "positive_excess_if_any_is_not_a_true_colonization_extinction_measure":True,
        "same_original_species_source_as_v1_314_not_independent_confirmation":True,
        "old_v1_314_original_one_shot_workflow_remains_SEALED":True,
        "original_mammal_BioTIME_RLS_S2S3S4_heldouts_unopened":True,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False,
    }

def analyse_original(events,occurrences,contract,old,source_receipt):
    selected,all_ids,sites=reconstruct_selected_original_event_design(events,old,source_receipt)
    if len(events)!=10379 or len(occurrences)!=63904 or len(selected)!=4620:
        raise ValueError("Original 2024 BALA source Event/Occurrence universe shifted")
    source_taxa=defaultdict(set)
    all_found=0;selected_guild=0;accepted=0
    source_taxa_all=defaultdict(set)
    ranks=set(old["taxon_reader"]["allowed_source_taxonRank_exact"])
    for item in occurrences:
        core=_trim(item.get("__foreign_coreid"))
        if core in all_ids:all_found+=1
        if core not in selected:continue
        guild=_norm(item.get("order"))
        if guild not in GUILDS:continue
        selected_guild+=1
        taxon=_norm(item.get("scientificName"))
        rank=_norm(item.get("taxonRank"))
        if not taxon or rank not in ranks:continue
        accepted+=1
        source_taxa[(core,guild)].add(taxon)
        source_taxa_all[guild].add(taxon)
    if (all_found!=len(occurrences) or selected_guild!=12699 or accepted!=12649
        or {g:len(source_taxa_all[g]) for g in GUILDS}!={"araneae":64,"coleoptera":110}):
        raise ValueError("Original v1.314 source biological identity did not reconcile")
    result=evaluate_selected(selected,sites,source_taxa,contract)
    result["original_2024_Event_rows"]=len(events)
    result["original_2024_Occurrence_rows_read_once"]=len(occurrences)
    result["original_selected_equal_Event_rows"]=len(selected)
    result["source_original_guild_records_before_species_rank_filter"]=selected_guild
    result["source_species_rank_accepted_guild_records"]=accepted
    result["original_source_SHA256"]=SHA
    result["original_v1_314_aggregate_inner_SHA256"]=SOURCE_V314_SHA
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--old-protocol",type=Path,required=True)
    ap.add_argument("--old-aggregate",type=Path,required=True)
    ap.add_argument("--source-event-receipt",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    contract=json.loads(args.contract.read_text())
    old=json.loads(args.old_protocol.read_text())
    prev=json.loads(args.old_aggregate.read_text())
    receipt=json.loads(args.source_event_receipt.read_text())
    if (contract.get("schema")!="structural.bala_within_campaign_detection_control.v1_316"
       or contract.get("status")!="SEPARATE_RETROSPECTIVE_TEST_FROZEN_BEFORE_WITHIN_PHASE_SPECIES_SPLIT_RECALCULATION"
       or contract["source"]["sha256"]!=SHA
       or old.get("schema")!="structural.bala_longitudinal_community_replacement_scoring.v1_314"
       or prev["original_source"]["source_artifact_original_inner_json_sha256"]!=SOURCE_V314_SHA
       or prev["source_original_event_design"]["selected_original_Event_coreids_sha256"]!=contract["source"]["selected_source_Event_coreids_SHA"]
       or not prev["firewall"]["GEB_scientific_HOLD"]
       or prev["firewall"]["new_confirmatory_systems"]!=0):
        raise ValueError("Original seven-island source and separate retrospective test not frozen")
    result={
        "schema":"structural.bala_within_campaign_detection_control_source_result.v1_316",
        "status":"SOURCE_OR_SOURCE_RESPONSE_REPLAY_TECHNICAL_STOP",
        "original_2024_Occurrence_rows_read_once":0,
        "old_v1_314_original_one_shot_workflow_remains_SEALED":True,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False,
    }
    try:
        req=urllib.request.Request(SRC,headers={
          "User-Agent":"Structural-BALA-BetweenVsWithin-Time-Source-v1.316"})
        with urllib.request.urlopen(req,timeout=70) as stream:
            blob=stream.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original BALA source ZIP SHA256 changed")
        ev=original_event_rows(blob)
        reconstruct_selected_original_event_design(ev,old,receipt)
        obs=original_occurrence_rows(blob)
        result["original_2024_Occurrence_rows_read_once"]=len(obs)
        result=analyse_original(ev,obs,contract,old,receipt)
    except Exception as err:
        result["stop_type"]=type(err).__name__
        result["stop_reason"]=str(err)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
       "status":result["status"],
       "source_site_count":result.get("source_original_transects"),
       "spider":result.get("main_pitfall",{}).get("araneae",{}).get("island_equal_delta_sorensen"),
       "beetle":result.get("main_pitfall",{}).get("coleoptera",{}).get("island_equal_delta_sorensen"),
       "spider_sites":result.get("main_pitfall",{}).get("araneae",{}).get("original_sites_observed_in_four_halves_at_least_five_of_nine_salts"),
       "beetle_sites":result.get("main_pitfall",{}).get("coleoptera",{}).get("original_sites_observed_in_four_halves_at_least_five_of_nine_salts"),
       "science_stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="SOURCE_OR_SOURCE_RESPONSE_REPLAY_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":main()
