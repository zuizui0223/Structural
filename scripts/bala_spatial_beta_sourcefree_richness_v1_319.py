#!/usr/bin/env python3
"""Source-free v1.319: island beetle homogenization and richness decoupling.

Reads only the already SHA-pinned original v1.318 island/guild numerical
aggregate. Original 2024 BALA 63,904 Occurrence and 10,379 Event rows remain
sealed; no site identities, taxonomy or source model scores are revisited.
"""
from __future__ import annotations
import argparse,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"development/bala_spatial_original_result_freeze_v1_318.json"
PROTOCOL=ROOT/"development/bala_spatial_beta_sourcefree_synthesis_protocol_v1_319.json"
SOURCE_SHA="f4e61ddbbd255d3a35a46fb0254273889516984b82479b3949e5edd79853af02"
ISLANDS=("fai","flo","pic","sjg","smg","smr","ter")
GUILDS=("araneae","coleoptera")

def sign(x):
    return "differentiation" if x>0 else "homogenization" if x<0 else "no_direction"

def check_close(x,y,tag):
    if not math.isclose(x,y,abs_tol=1e-12,rel_tol=0):
        raise ValueError(f"Original source spatial beta {tag} mismatch")

def calculate(d,c):
    if (c.get("schema")!="structural.bala_spatial_beta_sourcefree_richness_decoupling.v1_319"
        or c.get("status")!="FROZEN_AGGREGATE_ONLY_AFTER_ORIGINAL_SPATIAL_BETA_V1_318"
        or c.get("source")!="development/bala_spatial_original_result_freeze_v1_318.json"
        or c.get("original_source_JSON_sha256")!=SOURCE_SHA
        or d.get("schema")!="structural.bala_original_spatial_beta_numeric_freeze.v1_318"
        or d.get("status")!="ORIGINAL_SOURCE_SCORED_SEVEN_ISLAND_SPATIAL_BETA_FROZEN"
        or d["original_evidence"]["original_result_JSON_SHA256"]!=SOURCE_SHA
        or d["original_evidence"]["original_run_id"]!=40806865705
        or d["original_evidence"]["original_source_islands"]!=7
        or d["original_evidence"]["original_repeated_transects"]!=29
        or d["original_evidence"]["source_equal_Event_coreid_count"]!=4620
        or d["original_evidence"]["original_2024_DwCA_SHA256"]!="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"):
        raise ValueError("Original v1.318 source-observed site numeric evidence identity mismatch")
    guards=d["limitations"]
    if not all(guards[k] for k in (
            "original_v314_and_v316_scorers_sealed",
            "original_v318_scorer_sealed_after_success",
            "GEB_scientific_HOLD",
            "nine_salts_not_independent_biological_replicates"))
        or guards["new_confirmatory_systems"]!=0
        or guards["eBird"]):
        raise ValueError("Source biological-seal or scientific HOLD changed")
    rows={}
    for guild in GUILDS:
        original=d["main_pitfall"][guild]
        source_islands=original["per_island"]
        if set(source_islands)!=set(ISLANDS):
            raise ValueError("Source seven original island contexts changed")
        if guild=="araneae":
            expected=(29,56,4,3,13,17)
        else:
            expected=(28,49,3,4,18,18)
        obs=(
            original["source_physical_sites"],
            original["dependent_site_pairs"],
            original["islands_differentiating_simpson"],
            original["islands_homogenizing_simpson"],
            original["source_half_simpson_same_sign"],
            original["source_half_sorensen_same_sign"]
        )
        if obs!=expected or original["source_nine_salts_complementary_halves"]!=18:
            raise ValueError("Original source independent site and half-split design changed")
        site_n=sum(s["matched_physical_sites"] for s in source_islands.values())
        pairs_n=sum(s["dependent_pairs"] for s in source_islands.values())
        if site_n!=expected[0] or pairs_n!=expected[1]:
            raise ValueError("Original source site/pair sums shifted")
        original_simpson_mean=statistics.fmean(x["delta_spatial_simpson"] for x in source_islands.values())
        original_sorensen_mean=statistics.fmean(x["delta_spatial_sorensen"] for x in source_islands.values())
        check_close(original_simpson_mean,original["island_equal_delta_spatial_simpson"],f"{guild}:simpson")
        check_close(original_sorensen_mean,original["island_equal_delta_spatial_sorensen"],f"{guild}:sorensen")
        spatial_homog_with_richness_increase=[]
        spatial_diff_with_richness_decrease=[]
        metric_discordant=[]
        per_island={}
        for island in ISLANDS:
            entry=source_islands[island]
            check_close(entry["B3_spatial_simpson"]-entry["B1_spatial_simpson"],
                        entry["delta_spatial_simpson"],f"{guild}:{island}:B3-B1")
            alpha=entry["mean_B3_site_richness"]-entry["mean_B1_site_richness"]
            gamma=entry["source_B3_island_taxa"]-entry["source_B1_island_taxa"]
            spatial=sign(entry["delta_spatial_simpson"])
            soren=sign(entry["delta_spatial_sorensen"])
            if spatial=="homogenization" and alpha>0:
                spatial_homog_with_richness_increase.append(island)
            if spatial=="differentiation" and alpha<0:
                spatial_diff_with_richness_decrease.append(island)
            if spatial!=soren:
                metric_discordant.append(island)
            per_island[island]={
                "matched_original_transects":entry["matched_physical_sites"],
                "dependent_source_site_pairs":entry["dependent_pairs"],
                "spatial_Simpson_delta":entry["delta_spatial_simpson"],
                "spatial_Sorensen_delta":entry["delta_spatial_sorensen"],
                "spatial_Simpson_direction":spatial,
                "spatial_Sorensen_direction":soren,
                "mean_site_observed_richness_B1":entry["mean_B1_site_richness"],
                "mean_site_observed_richness_B3":entry["mean_B3_site_richness"],
                "mean_site_observed_richness_change":alpha,
                "observed_island_gamma_B1":entry["source_B1_island_taxa"],
                "observed_island_gamma_B3":entry["source_B3_island_taxa"],
                "observed_island_gamma_change":gamma,
                "homogenized_while_mean_local_richness_increased":spatial=="homogenization" and alpha>0,
                "differentiated_while_mean_local_richness_decreased":spatial=="differentiation" and alpha<0
            }
        if (sum(x["spatial_Simpson_direction"]=="homogenization" for x in per_island.values())!=expected[3]
            or sum(x["spatial_Simpson_direction"]=="differentiation" for x in per_island.values())!=expected[2]):
            raise ValueError("Original seven island spatial directions changed")
        rows[guild]={
            "independent_forest_transects":site_n,
            "dependent_source_pairs":pairs_n,
            "island_equal_spatial_simpson_delta":original_simpson_mean,
            "island_equal_spatial_sorensen_delta":original_sorensen_mean,
            "islands_homogenizing_spatial_simpson":expected[3],
            "islands_differentiating_spatial_simpson":expected[2],
            "islands_homogenizing_while_mean_local_richness_increased":spatial_homog_with_richness_increase,
            "islands_differentiating_while_mean_local_richness_decreased":spatial_diff_with_richness_decrease,
            "islands_Simpson_and_Sorensen_sign_disagreement":metric_discordant,
            "source_half_split_simpson_same_sign_n_of_18":expected[4],
            "source_half_split_sorensen_same_sign_n_of_18":expected[5],
            "source_half_split_simpson_delta_range":original["source_half_simpson_delta_range"],
            "source_half_split_sorensen_delta_range":original["source_half_sorensen_delta_range"],
            "per_island":per_island,
        }
    crossguild=[
        island for island in ISLANDS
        if rows["araneae"]["per_island"][island]["spatial_Simpson_direction"]
        != rows["coleoptera"]["per_island"][island]["spatial_Simpson_direction"]
    ]
    secondary=d["secondary_canopy"]
    if secondary["coleoptera"]["status"]!="STOP_FROZEN_GUILD_SPATIAL_PAIR_ESTIMABILITY" or secondary["coleoptera"]["spatial_beta_delta"] is not None or secondary["araneae"]["status"]!="OBSERVED_WITHIN_ISLAND_SPATIAL_BETA_CHANGE":
        raise ValueError("Previously fixed canopy beetle spatial beta scientific STOP was violated")
    return {
        "schema":"structural.bala_spatial_beta_richness_decoupling_sourcefree.v1_319",
        "status":"SOURCE_FREE_SPATIAL_GUILD_HETEROGENEITY_AND_ALPHA_DECOUPLING_RECONCILED",
        "original_source_v318_run_id":40806865705,
        "original_source_v318_inner_sha256":SOURCE_SHA,
        "original_island_context_n":7,
        "source_9_hash_salts_times_two_halves_not_independent":True,
        "main_pitfall":rows,
        "islands_spider_and_beetle_opposite_simpson_spatial_direction":crossguild,
        "canopy_spider_spatial_delta_simpson":secondary["araneae"]["island_equal_delta_spatial_simpson"],
        "canopy_beetle_spatial_delta_scientifically_STOPPED":True,
        "method_specific_sampling_frame_important":True,
        "original_BALA_Event_or_Occurrence_rows_reopened":0,
        "no_new_partitions_no_models_no_p_values":True,
        "not_causally_explained_by_richness_or_invasive_species":True,
        "no_biological_species_extinction_colonization_or_rescue_inferred":True,
        "prior_v314_v316_v318_original_scorers_SEALED":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,default=ORIGINAL)
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    o=calculate(json.loads(a.input.read_text(encoding="utf-8")),
                json.loads(a.protocol.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(o,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":o["status"],
        "spider_spatial_simpson_delta":o["main_pitfall"]["araneae"]["island_equal_spatial_simpson_delta"],
        "beetle_spatial_simpson_delta":o["main_pitfall"]["coleoptera"]["island_equal_spatial_simpson_delta"],
        "beetle_homogenizing_and_alpha_rising_islands":o["main_pitfall"]["coleoptera"]["islands_homogenizing_while_mean_local_richness_increased"],
        "spider_differentiating_and_alpha_declining_islands":o["main_pitfall"]["araneae"]["islands_differentiating_while_mean_local_richness_decreased"],
        "cross_guild_opposite_islands":o["islands_spider_and_beetle_opposite_simpson_spatial_direction"],
        "original_biological_rows_reopened":0
    },sort_keys=True))
if __name__=="__main__":main()
