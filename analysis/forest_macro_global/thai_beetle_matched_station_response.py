#!/usr/bin/env python3
"""Matched Thai beetle canopy/understorey SLAM study: 18 physical points × 2 rounds.

Exploratory retrospective analysis of two source forests. Preserves paired
canopy/understory traps, merges TOP/BOTTOM jars from the SAME trap deployment,
then aggregates repeated seasons within station BEFORE inference.
No forest-wide causal inference, no global replication, no species-richness
inference from mixed taxonomic resolutions. Internal IDs and coords never export.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,math,random,statistics
from collections import Counter,defaultdict
from pathlib import Path
from audit_thai_beetle_canopy_original import UID,API,fetch_json,get_archive_endpoint,download_small_archive
from thai_beetle_canopy_family_response import original_tables,protocol_category,valid_family,bray_relative
from thai_beetle_pairing_diagnostic import haversine_m,campaigns

SRC_SHA="1565cf6d7f1e7289e28756367e3d137f64723dc1fa0a06d799f6abdb523e1339"

def paired_site_response(events,occs):
    rows=[e.copy() for e in events if protocol_category(e["samplingProtocol"])[0]=="SLAM"]
    if len(rows)!=144:raise ValueError("source_original_144_SLAM_jar_Events_required")
    forests=sorted({e["locationID"] for e in rows})
    if len(forests)!=2:raise ValueError("source_two_forests_required")
    coords={}
    campaign_index={}
    for f in forests:
        ef=[e for e in rows if e["locationID"]==f]
        ca=sorted({(round(float(e["decimalLatitude"]),6),round(float(e["decimalLongitude"]),6))
                    for e in ef if protocol_category(e["samplingProtocol"])[1]=="canopy"})
        un=sorted({(round(float(e["decimalLatitude"]),6),round(float(e["decimalLongitude"]),6))
                    for e in ef if protocol_category(e["samplingProtocol"])[1]=="understorey"})
        if len(ca)!=9 or len(un)!=9:raise ValueError("nine_station_per_stratum_required")
        assignment=[]
        for i,c in enumerate(ca):
            j=min(range(9),key=lambda k:haversine_m(c,un[k]))
            d=haversine_m(c,un[j])
            if d>60 or min(range(9),key=lambda k:haversine_m(un[j],ca[k]))!=i:
                raise ValueError("ambiguous_or_distance_over60m_station_matching")
            assignment.append(j)
            coords[(f,"canopy",c)]=(f,i)
            coords[(f,"understorey",un[j])]=(f,i)
        if len(set(assignment))!=9:raise ValueError("station_mapping_not_bijective")
        days=[e["eventDate"] for e in ef]
        sets,clusters=campaigns(days)
        if len(clusters)!=2:raise ValueError("two_time_repeats_per_forest_required")
        for phase,mapping in enumerate(sets):
            for date in mapping:campaign_index[f,date]=phase
    group_events={}
    by_core={}
    effort=defaultdict(Counter)
    for e in rows:
        f=e["locationID"]
        method,layer=protocol_category(e["samplingProtocol"])
        p=e["samplingProtocol"].lower()
        jar="top" if "top jar" in p else "bottom" if "bottom jar" in p else None
        if not jar:raise ValueError("SLAM_top_bottom_jar_undefined")
        loc=(round(float(e["decimalLatitude"]),6),round(float(e["decimalLongitude"]),6))
        site=coords.get((f,layer,loc))
        day=datetime.date.fromisoformat(e["eventDate"][:10])
        round_id=campaign_index.get((f,day))
        if site is None or round_id is None:raise ValueError("event_unmatched_to_source_station_and_round")
        k=(site,round_id,layer,jar)
        if k in group_events:raise ValueError("duplicate_station_campaign_stratum_jar")
        group_events[k]=e["_core_id"]
        by_core[e["_core_id"]]=k
        effort[layer][(e["sampleSizeValue"],e["sampleSizeUnit"],e["samplingEffort"])]+=1
    if len(group_events)!=144:raise ValueError("SLAM_jar_units_not_144")
    # Check all 18×2×2×2 combinations were physically sampled (including zeros).
    for f in forests:
        for i in range(9):
            for phase in range(2):
                for layer in ("canopy","understorey"):
                    for jar in ("top","bottom"):
                        if ((f,i),phase,layer,jar) not in group_events:
                            raise ValueError("missing_complete_two_level_trap_jars")
    # Exact effort metadata distribution equality protects naive comparable counts.
    if effort["canopy"]!=effort["understorey"]:
        raise ValueError("unequal_original_SLAM_effort_metadata_by_stratum")
    beetles=defaultdict(int)
    families=defaultdict(Counter)
    invalid_family=Counter()
    other_method_rows=0
    for r in occs:
        core=r["_core_id"]
        k=by_core.get(core)
        if k is None:
            other_method_rows+=1
            continue
        val=float(r["individualCount"])
        if not val.is_integer() or val<1:raise ValueError("nonpositive_or_invalid_individual_count")
        n=int(val)
        trap=k[:3]
        beetles[trap]+=n
        fam=valid_family(r["family"])
        if fam:families[trap][fam]+=n
        else:invalid_family[trap]+=n
    if other_method_rows:raise ValueError("non_SLAM_original_occurrence_present")
    # Exact source endpoint expected to sum 1622; CI is bound to original source sha.
    table=[]
    site_contrasts=defaultdict(list)
    forest_campaign=defaultdict(lambda: {"canopy":0,"understorey":0})
    for f in forests:
        for i in range(9):
            for phase in range(2):
                s=(f,i)
                C=beetles[s,phase,"canopy"]
                U=beetles[s,phase,"understorey"]
                famC=families[s,phase,"canopy"]
                famU=families[s,phase,"understorey"]
                d=C-U
                site_contrasts[s].append(d)
                forest_campaign[f,phase]["canopy"]+=C
                forest_campaign[f,phase]["understorey"]+=U
                table.append({
                   "anonymous_forest":forests.index(f)+1,
                   "phase":phase+1,
                   "canopy_individuals":C,"understorey_individuals":U,
                   "canopy_minus_understorey":d,
                   "valid_family_Bray_Curtis_if_both_present":bray_relative(famC,famU)
                })
    # Statistical unit=physical sampling point (n=18), not jar (n=144)
    # nor a point×season repeated record (n=36).
    station_diff=[sum(site_contrasts[f,i])/2 for f in forests for i in range(9)]
    pooled_mean=sum(station_diff)/len(station_diff)
    observed=abs(sum(station_diff))
    n=len(station_diff)
    # Exact sign-flip diagnostic conditional on sampled stations; NOT
    # independent cross-forest confirmation (2 forests only).
    extreme=0
    for mask in range(1<<n):
        v=sum(d if (mask>>i)&1 else -d for i,d in enumerate(station_diff))
        if abs(v)>=observed-1e-10:extreme+=1
    p=extreme/(1<<n)
    # Balanced bootstrap: 9 sites WITHIN EACH of two forests, preserving both rounds.
    r=random.Random(20261108)
    boot=[]
    for _ in range(10000):
        picked=[]
        for f in forests:
            block=[sum(site_contrasts[f,i])/2 for i in range(9)]
            picked.extend(block[r.randrange(9)] for _ in range(9))
        boot.append(statistics.mean(picked))
    boot.sort()
    forest_signs=[]
    for f in forests:
        d=[sum(site_contrasts[f,i])/2 for i in range(9)]
        forest_signs.append({
          "anonymous_forest":forests.index(f)+1,
          "sites_positive_canopy_minus_understorey":sum(x>0 for x in d),
          "sites_negative":sum(x<0 for x in d),
          "sites_tied":sum(x==0 for x in d),
          "mean_per_site_per_season_difference":statistics.mean(d),
          "forest_total_canopy":sum(forest_campaign[f,k]["canopy"] for k in range(2)),
          "forest_total_understorey":sum(forest_campaign[f,k]["understorey"] for k in range(2))
        })
    phase_summaries=[]
    for f in forests:
        for k in range(2):
            phase_summaries.append({
                "anonymous_forest":forests.index(f)+1,
                "campaign":k+1,
                **forest_campaign[f,k],
                "canopy_minus_understorey":forest_campaign[f,k]["canopy"]-forest_campaign[f,k]["understorey"]
            })
    paired_fam_bray=[v["valid_family_Bray_Curtis_if_both_present"] for v in table
                     if v["valid_family_Bray_Curtis_if_both_present"] is not None]
    return {
      "schema":"structural.thai_beetle_canopy_18_station_2_campaign_paired_exploratory.v1",
      "original_independent_forests":2,
      "independent_physical_station_pairs_within_forests":18,
      "station_campaign_layer_trap_deployments":72,
      "actual_original_SLAM_jar_events":len(group_events),
      "complete_pairs_station_x_campaign":len(table),
      "identical_sampling_effort_metadata_distribution_across_strata":True,
      "original_effort_metadata_value_groups":len(effort["canopy"]),
      "canopy_total_beetles":sum(v["canopy_individuals"] for v in table),
      "understorey_total_beetles":sum(v["understorey_individuals"] for v in table),
      "mean_paired_canopy_minus_understorey_beetles_per_station_per_campaign":pooled_mean,
      "median_site_mean_pair_difference":statistics.median(station_diff),
      "site_means_positive_canopy_difference":sum(d>0 for d in station_diff),
      "site_means_negative_canopy_difference":sum(d<0 for d in station_diff),
      "site_means_tied":sum(d==0 for d in station_diff),
      "two_sided_site_signflip_exact_p_CONDITIONAL_ON_TWO_FORESTS":p,
      "within_forest_stratified_site_bootstrap_95CI_mean_paired_difference":[boot[249],boot[9749]],
      "within_site_season_pair_mean_valid_family_Bray_Curtis":(
          statistics.mean(paired_fam_bray) if paired_fam_bray else None),
      "within_site_season_pair_with_both_valid_family_records_n":len(paired_fam_bray),
      "forest_station_direction_summaries":forest_signs,
      "four_independent_forest_by_campaign_total_summaries_NOT_independent_forests":phase_summaries,
      "resampling_inference_scope":"two particular forests, repeated stations nested; no across-forest or biome generalization",
      "abundance_effect_not_equivalent_to_species_richness":True,
      "not_an_estimate_of_canopy_height_causal_effect":True,
      "forest_fragment_or_island_source_connectivity_not_tested":True,
      "raw_coords_trap_ids_forest_names_not_exported":True
    }

def analyze(data):
    if hashlib.sha256(data).hexdigest()!=SRC_SHA:
        raise ValueError("original_archive_version_changed_reaudit_required")
    events,occ=original_tables(data)
    r=paired_site_response(events,occ)
    if r["canopy_total_beetles"]+r["understorey_total_beetles"]!=1622:
        raise ValueError("reaggregated_beetle_total_not_reproduced")
    r["frozen_original_archive_sha256"]=SRC_SHA
    return r

def run(out,request=fetch_json,download=download_small_archive):
    d=request(API+UID)
    if str(d.get("key"))!=UID:raise ValueError("GBIF_dataset_uuid_mismatch")
    data=download(get_archive_endpoint(d))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    result=analyze(data)
    (out/"thai_beetle_matched_SLAM_station_season_results.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.out)
