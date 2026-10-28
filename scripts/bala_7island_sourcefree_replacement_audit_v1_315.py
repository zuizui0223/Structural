#!/usr/bin/env python3
"""v1.315 source-free BALA multi-island ecological conclusion consistency audit.

Only the original already scored v1.314 *aggregate* and its immutable SHA are
examined. No new Event/Occurrence/animal taxon/site source is requested.
No significance test, model refit, new ecological effect or causal story.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"development/bala_seven_island_species_replacement_original_result_v1_314.json"
SOURCE_ORIGINAL_INNER_SHA="b30eca5283d6984ee056ca8e74dd46fa2192c83558b175fbb84ff6546170f7a1"
BEETLE="coleoptera";SPIDER="araneae"

def audit(d):
    if (d.get("schema")!="structural.bala_seven_island_community_replacement_source_observation.v1_314"
      or d.get("status")!="ORIGINAL_2024_BALA_GUILD_REPLACEMENT_SCORED"
      or d["original_source"]["source_artifact_original_inner_json_sha256"]!=SOURCE_ORIGINAL_INNER_SHA
      or d["original_source"]["original_archive_sha256"]!="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"
      or d["source_original_event_design"]["selected_original_Event_coreids_sha256"]!="39db7c6db04e022b495e233506e9c9774d8e1cf9e2e1c35830bbe6aadce9d6ac"
      or d["source_original_event_design"]["selected_same_source_sites"]!=29
      or d["source_original_event_design"]["original_native_forest_islands"]!=7
      or not d["firewall"]["GEB_scientific_HOLD"] or d["firewall"]["new_confirmatory_systems"]!=0
      or d["firewall"]["eBird"]):
        raise ValueError("Original BALA scientific evidence identity or source-response seal failed")
    guild=d["pitfall_primary"]
    if set(guild)!={SPIDER,BEETLE}:
        raise ValueError("Original guild identities changed")
    a=guild[SPIDER];b=guild[BEETLE]
    sites=a["matched_site_comparisons"]+b["matched_site_comparisons"]
    n_stable=a["sites_balanced_species_replacement_with_abs_net_richness_at_most_one"]+b["sites_balanced_species_replacement_with_abs_net_richness_at_most_one"]
    if sites!=57 or n_stable!=23:
        raise ValueError("Old published two-guild site×taxon group denominators changed")
    islands=set(a["per_island_replacement_simpson"]) & set(b["per_island_replacement_simpson"])
    if len(islands)!=7:raise ValueError("Original seven core island metric rows changed")
    counts={g:sum(v>0 for v in guild[g]["per_island_replacement_simpson"].values()) for g in guild}
    higher=sum(b["per_island_replacement_simpson"][i]>a["per_island_replacement_simpson"][i]
               for i in islands)
    if counts!={SPIDER:7,BEETLE:7} or higher!=6:
        raise ValueError("Original source seven-island replacement directions changed")
    if d["original_biological_audit"]["Event_Occurrence_join_fraction"]!=1.0:
        raise ValueError("Original source author Event→Occurrence primary identity did not match")
    frac=d["original_biological_audit"]["source_taxon_origin_classified_fraction"]
    if not 0.9<frac<=1:
        raise ValueError("Native/introduced records under declared source status taxonomy not sufficiently observed")
    return {
      "schema":"structural.bala_seven_island_sourcefree_ecological_synthesis.v1_315",
      "status":"SOURCE_FREE_ORIGINAL_SEVEN_ISLAND_REPLACEMENT_RECONCILED",
      "original_field_source_run_id":d["original_source"]["original_first_biological_access_run_id"],
      "source_aggregate_SHA256":SOURCE_ORIGINAL_INNER_SHA,
      "source_longitudinal_island_count":7,
      "source_original_independent_transects":29,
      "pitfall_observable_transect_guild_B1_B3_comparisons":sites,
      "pitfall_guild_comparisons_with_balanced_replacement_and_at_most_one_species_net_difference":n_stable,
      "fraction_of_pitfall_guild_comparisons_with_replacement_and_near_stable_richness":n_stable/sites,
      "islands_with_positive_spider_replacement":counts[SPIDER],
      "islands_with_positive_beetle_replacement":counts[BEETLE],
      "islands_with_beetle_mean_simpson_replacement_greater_than_spider_mean":higher,
      "pitfall_island_equal_spider_simpson_replacement":a["island_equal_mean_simpson_replacement"],
      "pitfall_island_equal_beetle_simpson_replacement":b["island_equal_mean_simpson_replacement"],
      "pitfall_island_equal_spider_sorensen_total":a["island_equal_mean_sorensen_beta"],
      "pitfall_island_equal_beetle_sorensen_total":b["island_equal_mean_sorensen_beta"],
      "spider_signed_richness_mean":a["island_equal_mean_signed_net_richness_change"],
      "beetle_signed_richness_mean":b["island_equal_mean_signed_net_richness_change"],
      "this_is_not_a_new_source_or_confirmatory_replication":True,
      "trait_or_origin_differences_not_randomized_causally":True,
      "no_true_species_extinction_or_recolonization_inferred":True,
      "no_original_Event_or_Occurrence_rows_reopened":True,
      "no_new_models_or_biological_scores":True,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,default=SOURCE)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    o=audit(json.loads(args.input.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({k:o[k] for k in ("status",
         "source_original_independent_transects",
         "pitfall_observable_transect_guild_B1_B3_comparisons",
         "pitfall_guild_comparisons_with_balanced_replacement_and_at_most_one_species_net_difference",
         "islands_with_positive_spider_replacement",
         "islands_with_positive_beetle_replacement",
         "islands_with_beetle_mean_simpson_replacement_greater_than_spider_mean")},sort_keys=True))
if __name__=="__main__":main()
