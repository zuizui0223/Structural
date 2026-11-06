#!/usr/bin/env python3
"""BALA v1.318 original seven-island SPATIAL beta change, not site temporal beta.

One explicitly retrospective source read after original v1.314/v1.316 exposure,
under a frozen NEW ecological estimand. Neither old scorer is rerun.
Matched physical forest transects, matched source methods, and strictly
response-independent 4620 source Event coreids are held fixed.

Main: within-island cross-transect spatial Simpson and Sorensen beta in
B3 minus B1. Positive=differentiation; negative=homogenization. All original
transect pairs are DEPENDENT, not independent tests. Nine predefined split
salts × complementary original Event halves are sensitivity partitions,
never 18 independent surveys or a detection corrected occupancy model.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import urllib.request

from bala_repeated_transect_event_only_v1_311 import (
    SRC,SHA,MAX_BYTES,original_event_rows,_norm,_trim
)
from bala_equal_original_event_samples_v1_313 import METHODS,ISLANDS
from bala_original_species_replacement_v1_314 import (
    original_occurrence_rows,reconstruct_selected_original_event_design
)
from bala_within_campaign_detection_control_v1_316 import _partition

GUILDS=("araneae","coleoptera")
PERIODS=("B1","B3")
MAIN_METHOD="Pitfall solution"
CANOPY_METHOD="Open beating tray (with bag)"
SOURCE_SELECTED_SHA="39db7c6db04e022b495e233506e9c9774d8e1cf9e2e1c35830bbe6aadce9d6ac"
SOURCE_V314_AGGREGATE_SHA="b30eca5283d6984ee056ca8e74dd46fa2192c83558b175fbb84ff6546170f7a1"
EXPECTED_SITES={"fai":3,"flo":4,"pic":4,"sjg":4,"smg":4,"smr":2,"ter":8}
SALTS=tuple("split-"+str(k) for k in range(9))

def avg(values):
    return statistics.fmean(values) if values else None

def pair_beta(a,b):
    """Two nonempty physical-plot taxon sets within SAME island and campaign."""
    if not a or not b:
        return None
    shared=len(a&b)
    onlya=len(a-b)
    onlyb=len(b-a)
    sor=(onlya+onlyb)/(2*shared+onlya+onlyb)
    sim=min(onlya,onlyb)/(shared+min(onlya,onlyb)) if shared+min(onlya,onlyb) else 0.
    return {"sorensen":sor,"simpson":sim}

def island_pairs(island, eligible_sites,sets,method,guild):
    """Actual pairwise β, while retaining independent site denominator."""
    ordered=sorted(site for isl,site in eligible_sites if isl==island)
    per_period={p:[] for p in PERIODS}
    pair_count=0
    for i in range(len(ordered)):
        for j in range(i+1,len(ordered)):
            a,b=ordered[i],ordered[j]
            values={}
            for period in PERIODS:
                left=sets.get((island,a,method,guild,period),set())
                right=sets.get((island,b,method,guild,period),set())
                values[period]=pair_beta(left,right)
            # Restrict to SAME physical pair across both periods. If
            # half-split detection absent, omit the pair from that half.
            if any(v is None for v in values.values()):
                continue
            pair_count+=1
            for p in PERIODS:per_period[p].append(values[p])
    if not pair_count:return None
    return {
        "physical_sites_available":len(ordered),
        "dependent_matched_pairs":pair_count,
        "B1_spatial_sorensen":avg([v["sorensen"] for v in per_period["B1"]]),
        "B3_spatial_sorensen":avg([v["sorensen"] for v in per_period["B3"]]),
        "B1_spatial_simpson":avg([v["simpson"] for v in per_period["B1"]]),
        "B3_spatial_simpson":avg([v["simpson"] for v in per_period["B3"]]),
        "delta_sorensen":avg([v["sorensen"] for v in per_period["B3"]])-avg([v["sorensen"] for v in per_period["B1"]]),
        "delta_simpson":avg([v["simpson"] for v in per_period["B3"]])-avg([v["simpson"] for v in per_period["B1"]])
    }

def site_period_sets(selected,source_taxa,methods=METHODS):
    sets=defaultdict(set)
    for core,(island,site,method,period) in selected.items():
        if method not in methods or period not in PERIODS:continue
        for guild in GUILDS:
            sets[(island,site,method,guild,period)].update(source_taxa.get((core,guild),set()))
    return sets

def _sign(value):
    if value>0:return "differentiation"
    if value<0:return "homogenization"
    return "no_delta"

def one_guild_spatial(source_sets,source_sites,method,guild,contract,selected,source_taxa):
    islands=contract["sampling"]["islands_exact"]
    supported_site_pairs=set()
    for island,site in source_sites:
        if source_sets.get((island,site,method,guild,"B1"),set()) and source_sets.get(
            (island,site,method,guild,"B3"),set()):
            supported_site_pairs.add((island,site))
    by_island={}
    eligible_total=0
    pair_total=0
    for island in islands:
        result=island_pairs(island,supported_site_pairs,source_sets,method,guild)
        eligible_sites=sorted(site for isl,site in supported_site_pairs if isl==island)
        if result is None:
            by_island[island]={
                "sites_with_both_phase_taxon_detections":len(eligible_sites),
                "dependent_matched_pairs":0,
                "status":"STOP_TOO_FEW_WITHIN_ISLAND_NONEMPTY_SOURCE_SITE_PAIRS"
            }
            continue
        richness={}
        for p in PERIODS:
            sampled=[source_sets[(island,site,method,guild,p)] for site in eligible_sites]
            richness[p]={
                "mean_original_source_plot_species_richness":avg([len(s) for s in sampled]),
                "union_observed_island_source_taxa":len(set.union(*sampled))
            }
        result.update({
            "status":"ELIGIBLE_ORIGINAL_MATCHED_ISLAND_TRANSECT_PAIRS",
            "sites_with_both_phase_taxon_detections":len(eligible_sites),
            "source_phase_richness":richness,
            "Simpson_spatial_direction":_sign(result["delta_simpson"]),
            "Sorensen_spatial_direction":_sign(result["delta_sorensen"]),
            "no_independent_pairwise_inference":True
        })
        by_island[island]=result
        eligible_total+=len(eligible_sites)
        pair_total+=result["dependent_matched_pairs"]
    min_sites=contract["sampling"]["island_eligibility"]
    # The frozen scientific sample gate applies to every guild/method, so
    # weaker canopy guilds stop rather than silently selecting islands.
    good=(
        set(by_island)==set(islands)
        and all(by_island[i]["status"]=="ELIGIBLE_ORIGINAL_MATCHED_ISLAND_TRANSECT_PAIRS"
                and by_island[i]["sites_with_both_phase_taxon_detections"]>=2
                for i in islands)
        and eligible_total>=24 and pair_total>=40
    )
    scores={
        "schema":"structural.bala_spatial_beta_by_guild_and_method.v1_318",
        "status":"OBSERVED_WITHIN_ISLAND_SPATIAL_BETA_CHANGE" if good else "STOP_FROZEN_GUILD_SPATIAL_PAIR_ESTIMABILITY",
        "guild":guild,
        "source_sampling_method":method,
        "physical_sites_with_two_phase_detected_guild":eligible_total,
        "dependent_source_island_site_pairs":pair_total,
        "eligible_islands":sum(by_island[i]["status"]=="ELIGIBLE_ORIGINAL_MATCHED_ISLAND_TRANSECT_PAIRS" for i in islands),
        "per_island":by_island,
        "primary_island_equal_spatial_simpson_delta":None,
        "secondary_island_equal_spatial_sorensen_delta":None,
        "islands_differentiating_simpson":None,
        "islands_homogenizing_simpson":None,
        "islands_differentiating_sorensen":None,
        "islands_homogenizing_sorensen":None,
        "source_9_partition_sensitivity":None,
        "not_7_independent_archipelagos":True,
        "not_true_colonization_or_causal_invasion":True,
    }
    if not good:return scores
    for metric in ("simpson","sorensen"):
        delta=avg([by_island[i]["delta_"+metric] for i in islands])
        scores["primary_island_equal_spatial_simpson_delta" if metric=="simpson" else "secondary_island_equal_spatial_sorensen_delta"]=delta
        scores["islands_differentiating_"+metric]=sum(by_island[i]["delta_"+metric]>0 for i in islands)
        scores["islands_homogenizing_"+metric]=sum(by_island[i]["delta_"+metric]<0 for i in islands)

    # Source-independent nine Event-ID-only salts; each salt has 2
    # complementary half-effort contrasts using the same physical sites.
    original_groups=defaultdict(list)
    for core,(isl,site,m,period) in selected.items():
        if m==method and period in PERIODS:
            original_groups[(isl,site,period)].append(core)
    full_sensitivity=[]
    for salt in contract["statistics"]["sample_split_sensitivity"]["salts"]:
        first={};second={}
        for (isl,site,period),cores in original_groups.items():
            a,b=_partition(cores,salt)
            first[(isl,site,period)]=a
            second[(isl,site,period)]=b
        for label,partition in (("first",first),("complementary",second)):
            halfsets=defaultdict(set)
            for (isl,site,period),cores in partition.items():
                for core in cores:
                    halfsets[(isl,site,method,guild,period)].update(
                        source_taxa.get((core,guild),set()))
            halfislands={}
            pair_counts={}
            for island in islands:
                result=island_pairs(island,supported_site_pairs,halfsets,method,guild)
                if result is not None:
                    halfislands[island]=result
                    pair_counts[island]=result["dependent_matched_pairs"]
            if len(halfislands)==len(islands):
                ds=avg([halfislands[i]["delta_simpson"] for i in islands])
                dr=avg([halfislands[i]["delta_sorensen"] for i in islands])
                full_sensitivity.append({
                    "split":salt,
                    "half":label,
                    "source_islands_with_matched_two_period_pairs":len(halfislands),
                    "source_dependent_pair_total":sum(pair_counts.values()),
                    "delta_simpson":ds,
                    "delta_sorensen":dr
                })
    sensitivity={
        "fixed_salt_count":len(contract["statistics"]["sample_split_sensitivity"]["salts"]),
        "complementary_half_estimates_possible":18,
        "valid_half_estimates_with_all_seven_islands":len(full_sensitivity),
        "minimum_required_to_label_stable":6,
        "status":"SENSITIVITY_DIRECTIONS_ESTIMABLE" if len(full_sensitivity)>=6 else "STOP_INSUFFICIENT_CROSS_ISLAND_SPLIT_DETECTION",
        "source_half_deltas_simpson_min_max":None,
        "source_half_deltas_sorensen_min_max":None,
        "source_half_simpson_same_direction_as_full_primary":None,
        "source_half_sorensen_same_direction_as_full_secondary":None,
        "source_half_simpson_same_direction_fraction":None,
        "source_half_sorensen_same_direction_fraction":None,
        "nine_salts_times_two_halves_not_independent_replicates":True
    }
    if len(full_sensitivity)>=6:
        for name,baseline in (("simpson",scores["primary_island_equal_spatial_simpson_delta"]),
                              ("sorensen",scores["secondary_island_equal_spatial_sorensen_delta"])):
            values=[v["delta_"+name] for v in full_sensitivity]
            same=sum(_sign(v)==_sign(baseline) for v in values)
            sensitivity["source_half_deltas_"+name+"_min_max"]=[min(values),max(values)]
            sensitivity["source_half_"+name+"_same_direction_as_full_"+("primary" if name=="simpson" else "secondary")]=same
            sensitivity["source_half_"+name+"_same_direction_fraction"]=same/len(values)
    scores["source_9_partition_sensitivity"]=sensitivity
    return scores

def calculate(events,occurrences,contract,old,receipt,old_aggregate):
    selected,all_cores,sites=reconstruct_selected_original_event_design(events,old,receipt)
    if (len(events)!=10379 or len(occurrences)!=63904 or len(sites)!=29
        or len(selected)!=4620):
        raise ValueError("Original source Event/Occurrence population changed")
    raw_counts=Counter()
    source_taxa=defaultdict(set)
    union_by_guild=defaultdict(set)
    source_join=0
    original_ranks=set(old["taxon_reader"]["allowed_source_taxonRank_exact"])
    for row in occurrences:
        core=_trim(row.get("__foreign_coreid"))
        if core in all_cores:source_join+=1
        if core not in selected:continue
        guild=_norm(row.get("order"))
        if guild not in GUILDS:continue
        raw_counts["guild"]+=1
        name=_norm(row.get("scientificName"))
        rank=_norm(row.get("taxonRank"))
        if not name or rank not in original_ranks:continue
        raw_counts["accepted"]+=1
        source_taxa[(core,guild)].add(name)
        union_by_guild[guild].add(name)
    expected=contract["quality"]
    if (source_join/len(occurrences)<expected["minimum_Event_to_Occurrence_source_join"]
        or raw_counts["guild"]!=expected["previously_verified_original_selected_guild_Records_before_species_rank"]
        or raw_counts["accepted"]!=expected["previously_verified_accepted_species_rank_guild_Records"]
        or {g:len(union_by_guild[g]) for g in GUILDS}!=expected["previously_verified_original_taxa_by_guild"]):
        raise ValueError("Previously scored v1.314 source scientific response identity failed")
    sets=site_period_sets(selected,source_taxa)
    outputs={}
    for method in (MAIN_METHOD,CANOPY_METHOD):
        outputs[method]={
            guild:one_guild_spatial(sets,sites,method,guild,contract,selected,source_taxa)
            for guild in GUILDS
        }
    status="OBSERVED_WITHIN_ISLAND_SPATIAL_HOMOGENIZATION_DIFFERENTIATION_ADJUDICATED" if all(
         outputs[MAIN_METHOD][g]["status"]=="OBSERVED_WITHIN_ISLAND_SPATIAL_BETA_CHANGE"
         for g in GUILDS) else "STOP_FROZEN_PITFALL_SPATIAL_PAIR_SUPPORT"
    return {
        "schema":"structural.bala_seven_island_original_spatial_beta.v1_318",
        "status":status,
        "original_source_zip_sha256":SHA,
        "original_source_Event_rows_reexamined":len(events),
        "original_source_Occurrence_rows_reexamined":len(occurrences),
        "original_matched_repeated_physical_transects":len(sites),
        "original_equal_sampled_source_Event_total":len(selected),
        "original_equal_source_Event_SHA256":SOURCE_SELECTED_SHA,
        "original_site_count_by_island":EXPECTED_SITES,
        "guild_eligible_species_ranks":sorted(original_ranks),
        "original_all_occurrence_source_join_fraction":source_join/len(occurrences),
        "source_original_selected_guild_rows":raw_counts["guild"],
        "source_original_accepted_operational_taxa_rows":raw_counts["accepted"],
        "source_original_distinct_taxa_by_guild":{g:len(union_by_guild[g]) for g in GUILDS},
        "main_pitfall":outputs[MAIN_METHOD],
        "secondary_canopy_beating":outputs[CANOPY_METHOD],
        "status_is_post_outcome_exploratory_not_confirmatory":True,
        "previous_v314_and_v316_oneshot_scorers_remain_SEALED":True,
        "no_species_island_local_extinction_or_immigration_inferred":True,
        "no_source_site_IDs_or_species_exported":True,
        "no_eBird_used":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("--protocol","--old-protocol","--old-aggregate",
                 "--source-event-receipt"):
        parser.add_argument(name,type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    protocol=json.loads(a.protocol.read_text(encoding="utf-8"))
    old=json.loads(a.old_protocol.read_text(encoding="utf-8"))
    old_aggregate=json.loads(a.old_aggregate.read_text(encoding="utf-8"))
    receipt=json.loads(a.source_event_receipt.read_text(encoding="utf-8"))
    if (protocol.get("schema")!="structural.bala_island_spatial_beta_change.v1_318"
        or protocol.get("status")!="SEPARATE_POST_OUTCOME_EXPLORATORY_SPATIAL_BETA_STUDY_FROZEN_BEFORE_THIS_SOURCE_READ"
        or protocol["source"]["original_zip_sha256"]!=SHA
        or protocol["source"]["v313_original_selected_events_sha256"]!=SOURCE_SELECTED_SHA
        or old.get("schema")!="structural.bala_longitudinal_community_replacement_scoring.v1_314"
        or receipt.get("selected_original_Event_coreids_SHA256")!=SOURCE_SELECTED_SHA
        or old_aggregate["original_source"]["source_artifact_original_inner_json_sha256"]!=SOURCE_V314_AGGREGATE_SHA
        or not old_aggregate["firewall"]["GEB_scientific_HOLD"]):
        raise ValueError("Independent ecological question was not frozen to exact original source cohort")
    result={
        "schema":"structural.bala_seven_island_original_spatial_beta.v1_318",
        "status":"ORIGINAL_SOURCE_OR_SPATIAL_READER_TECHNICAL_STOP",
        "original_source_Occurrence_rows_reexamined":0,
        "previous_v314_and_v316_oneshot_scorers_remain_SEALED":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "no_eBird_used":True
    }
    try:
        req=urllib.request.Request(SRC,headers={
          "User-Agent":"Structural-BALA-SpatialBeta-Source-Locked-v1.318"})
        with urllib.request.urlopen(req,timeout=70) as stream:
            blob=stream.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original source archived ZIP hash/size changed")
        events=original_event_rows(blob)
        reconstruct_selected_original_event_design(events,old,receipt)
        obs=original_occurrence_rows(blob)
        result["original_source_Occurrence_rows_reexamined"]=len(obs)
        result=calculate(events,obs,protocol,old,receipt,old_aggregate)
    except Exception as error:
        result["stop_type"]=type(error).__name__
        result["stop_reason"]=str(error)[:330]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_species_rows_reexamined":result["original_source_Occurrence_rows_reexamined"],
        "spider_primary":result.get("main_pitfall",{}).get("araneae",{}).get("primary_island_equal_spatial_simpson_delta"),
        "beetle_primary":result.get("main_pitfall",{}).get("coleoptera",{}).get("primary_island_equal_spatial_simpson_delta"),
        "spider_islands_differentiating":result.get("main_pitfall",{}).get("araneae",{}).get("islands_differentiating_simpson"),
        "beetle_islands_differentiating":result.get("main_pitfall",{}).get("coleoptera",{}).get("islands_differentiating_simpson"),
        "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="ORIGINAL_SOURCE_OR_SPATIAL_READER_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":
    main()
