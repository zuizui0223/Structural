#!/usr/bin/env python3
"""v1.337 source-FREE check of original 2019–2020 SLAM II forest placement.

Only committed source-anonymous original numeric evidence, never original
45 Event or 2097 Occurrence contents. Verify prior v1.335/v1.336 science STOP,
three island native forests' higher source median elevation, original two
island common altitude but no adequate equal year/effort matched comparison.
"""
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"development/slamii_habitat_elevation_site_only_conclusion_v1_337.json"

def audit(x):
    source=x["source"];islands=x["island_observations"];g=x["science_gates"];guard=x["firewall"]
    if (x.get("schema")!="structural.slamII_forest_elevation_source_terminal_evidence.v1_337"
        or x.get("science_status")!="ELEVATIONAL_HABITAT_SORTING_REPEATED_BUT_MATCHED_FOREST_CAUSAL_CONTRAST_NOT_ESTIMABLE"
        or source["source_zip_sha256"]!="a0af4661f202d221ea8706dcf8a936d093dec335ce30306f3f0a2e0f474eb734"
        or source["original_source_paired_result_inner_JSON_SHA256"]!="0e09b16dd6b957a96878960cdf2f94e9745dae036873a2a7d2a2cb34d7e46f10"
        or source["independent_physical_sites"]!=45 or source["Occurrence_rows_read"]!=0
        or source["paper_2022_native_mixed_exotic_claim"]!={"native":8,"mixed":18,"exotic":19}
        or source["source_2023_native_mixed_exotic_classes"]!={"native":9,"mixed":14,"exotic":22}
        or g["old_v335_status"]!="STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED"
        or g["post_Event_v336_status"]!="TERMINAL_NO_TWO_ISLANDS_ELEVATION_YEAR_EFFORT_PAIRED_FOREST_PLOTS"
        or set(islands)!={"COR","FLO","SMR","TER"}
        or sum(r["site_n"] for r in islands.values())!=45
        or sum(r["native_n"] for r in islands.values())!=9
        or sum(r["altered_n"] for r in islands.values())!=36
        or not guard["all_old_species_scorers_SEALED"]
        or not guard["original_2097_occurrence_rows_unopened"]
        or not guard["GEB_scientific_HOLD"]
        or guard["new_confirmatory_systems"]!=0 or guard["eBird"]):
        raise ValueError("Original source full 45-plot, v335/336 STOP or taxon firewall changed")
    for isl,expected in (("FLO",260),("SMR",113),("TER",193.5)):
        if islands[isl]["native_minus_altered_median_elevation_m"]!=expected:
            raise ValueError("Original author island forest elevational contrast changed: "+isl)
    for isl,n,a,matched in (("FLO",1,1,None),("SMR",3,3,1),("TER",3,6,0)):
        row=islands[isl]
        if (row["source_native_in_overlap"]!=n or row["source_altered_in_overlap"]!=a
            or (matched is not None and row["source_year_effort_100m_pairs"]!=matched)):
            raise ValueError("Original source altitude or equal-effort pair coverage changed: "+isl)
    matched_total=islands["SMR"]["source_year_effort_100m_pairs"]+islands["TER"]["source_year_effort_100m_pairs"]
    if matched_total!=1 or not x["ecology"]["native_forest_higher_median_elevation_on_three_original_islands"]:
        raise ValueError("Source landscape direction or matched pair audit differs")
    return {
      "schema":"structural.slamII_45forest_elevation_sourcefree_scientific_result.v1_337",
      "status":"THREE_ISLAND_NATIVE_FOREST_HIGHER_ELEVATION_MATCHED_CAUSAL_GATE_TERMINAL",
      "original_source_islands_with_two_habitat_types":["FLO","SMR","TER"],
      "source_native_minus_altered_median_elevation_by_island_m":{
         i:islands[i]["native_minus_altered_median_elevation_m"] for i in ("FLO","SMR","TER")
      },
      "native_higher_original_island_n":3,
      "source_original_island_equal_native_minus_altered_median_elevation_m":statistics.fmean(
         [islands[i]["native_minus_altered_median_elevation_m"] for i in ("FLO","SMR","TER")]),
      "source_in_100m_equal_year_effort_matched_original_plot_pair_total_2islands":matched_total,
      "source_original_min_2pairs_per_island_rule_passed":False,
      "old_v335_published_vs_archive_habitat_count_stop_preserved":True,
      "new_v336_source_year_effort_pairing_stop_preserved":True,
      "original_Source_Event_and_Occurrence_rows_reopened":0,
      "no_new_biological_source_discovery_claim":True,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,default=INPUT)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=audit(json.loads(args.input.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
      "status":out["status"],
      "median_elevation_delta_by_island":out["source_native_minus_altered_median_elevation_by_island_m"],
      "island_equal_median_elevation_difference_m":out["source_original_island_equal_native_minus_altered_median_elevation_m"],
      "equal_effort_elevation_matched_pairs_in_two_islands":out["source_in_100m_equal_year_effort_matched_original_plot_pair_total_2islands"],
      "original_taxon_and_Event_reopen":0
    },sort_keys=True))
if __name__=="__main__":main()
