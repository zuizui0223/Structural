#!/usr/bin/env python3
"""Gloor Weiss original taxon HEADERS: ONE exploratory reversible format check.

The earlier primary exact name-only 0/309 gate remains formally HOLD.
Uses only source CSV FIRST HEADERS and frozen Weiss 511 guild table privately.
Never reads Gloor abundance rows or fits ecological models.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from carpathian116_weiss_original_name_only_coverage import (
    validate_original_weiss_private_ledger,
    source_gloor_name_headers,
    coverage as original_literal_coverage,
    EXACT_BINOMIAL,
)
from carpathian116_taxon_header_grammar_rscript_sourceonly import GRAMMAR
from carpathian116_zenodo_metadata_only import SourceStop

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_GLOOR_WEISS_UNDERSCORE_FORMAT_EXPLORATORY_PRESPEC_20261118.md"
AUTHOR_VERIFIED_MAPPING=False
EXPECTED_RAW_B=241
EXPECTED_RAW_S=160
EXPECTED_RAW_UNION=309
EXPECTED_RAW_SHARED=92
EXPECTED_WEISS=511
GUILD_CODES=tuple("mnpsxz")

def single_source_format_only(names):
    normalized=set()
    for name in names:
        if GRAMMAR["exact_two_underscore_Latin_tokens"].fullmatch(name) is None:
            raise SourceStop("SOURCE_GLOOR_ORIGINAL_UNDERSCORE_TWO_LATIN_TOKENS_NOT_UNIVERSAL")
        converted=name.replace("_"," ",1)
        if EXACT_BINOMIAL.fullmatch(converted) is None:
            raise SourceStop("SOURCE_GLOOR_EXPLORATORY_CONVERTED_BINOMIAL_NOT_STRICT")
        if converted in normalized:
            raise SourceStop("SOURCE_GLOOR_SOURCE_FORMAT_CONVERSION_COLLISION")
        normalized.add(converted)
    if len(normalized)!=len(names):
        raise SourceStop("SOURCE_GLOOR_SOURCE_FORMAT_KEY_DUPLICATE")
    return normalized

def assess(weiss,original):
    if len(weiss)!=EXPECTED_WEISS:
        raise SourceStop("SOURCE_WEISS511_REFERENCE_GUILD_UNEXPECTED_SIZE")
    b=original["B_SR_BEETLES.csv"]["private_taxa"]
    s=original["S_SR_BEETLES.csv"]["private_taxa"]
    if (len(b)!=EXPECTED_RAW_B or len(s)!=EXPECTED_RAW_S
        or len(b&s)!=EXPECTED_RAW_SHARED or len(b|s)!=EXPECTED_RAW_UNION):
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_RAW_HEADER_FRAME_309_CHANGED")
    # The previously frozen literal primary remained HOLD and counts zero.
    old=original_literal_coverage(weiss,original)
    if (old["source_literal_Weiss_guild_exact_taxon_matches_combined"]!=0
        or old["source_literal_Weiss_guild_exact_coverage_fraction_combined"]!=0
        or old["status"]!="SOURCE_GLOOR_WEISS_EXACT_GUILD_TAXON_COVERAGE_HOLD"):
        raise SourceStop("SOURCE_ORIGINAL_PRIMARY_EXACT_ZERO_HOLD_DRIFT")
    B=single_source_format_only(b)
    S=single_source_format_only(s)
    combined=B|S
    if len(combined)!=309 or len(B&S)!=92:
        raise SourceStop("SOURCE_FORMAT_ONLY_CONVERSION_UNEXPECTED_COLLISION_OR_SAMPLES")
    allmatched=combined&set(weiss)
    bmatched=B&set(weiss)
    smatched=S&set(weiss)
    counts=Counter(weiss[k] for k in allmatched)
    meets={
      "unchanged_primary_numerical_overall_min0p50":len(allmatched)/len(combined)>=.5,
      "unchanged_primary_numerical_beech_min0p40":len(bmatched)/len(B)>=.4,
      "unchanged_primary_numerical_spruce_min0p40":len(smatched)/len(S)>=.4,
      "unchanged_primary_numerical_at_least_three_guilds_each_10_taxa":
          sum(counts[x]>=10 for x in GUILD_CODES)>=3,
    }
    return {
       "status":"SECONDARY_EXPLORATORY_SOURCE_FORMAT_COVERAGE_COUNTS_ONLY",
       "source_reference_original_Weiss_six_guild_valid_taxa":len(weiss),
       "Gloor_raw_primary_exact_match_count_UNCHANGED":0,
       "Gloor_raw_primary_exact_coverage_STATUS_UNCHANGED":"SOURCE_GLOOR_WEISS_EXACT_GUILD_TAXON_COVERAGE_HOLD",
       "Gloor_raw_beech_header_taxon_columns":len(b),
       "Gloor_raw_spruce_header_taxon_columns":len(s),
       "Gloor_raw_beech_spruce_shared_literal":len(b&s),
       "Gloor_raw_union_taxon_columns":len(b|s),
       "Gloor_header_instances_all_exactly_two_Latin_tokens_one_underscore":len(b)+len(s),
       "exploratory_format_only_single_underscore_replaced_by_ASCII_space":True,
       "exploratory_FORMAT_transformed_headings_unique_union":len(combined),
       "exploratory_FORMAT_cross_forest_transformed_common_count":len(B&S),
       "exploratory_FORMAT_conversion_collisions":0,
       "exploratory_Weiss511_exact_matches_combined":len(allmatched),
       "exploratory_Weiss511_exact_matches_beech":len(bmatched),
       "exploratory_Weiss511_exact_matches_spruce":len(smatched),
       "exploratory_Weiss511_exact_fraction_combined":round(len(allmatched)/len(combined),6),
       "exploratory_Weiss511_exact_fraction_beech":round(len(bmatched)/len(B),6),
       "exploratory_Weiss511_exact_fraction_spruce":round(len(smatched)/len(S),6),
       "exploratory_four_original_guilds_counts_among_source_taxon_matches":{
           k:counts[k] for k in GUILD_CODES
       },
       "exploratory_unchanged_threshold_flags_FOR_DESCRIPTION_NOT_GUILD_FIT":meets,
       "original_author_paper_reported_303_vs_source_309_UNRESOLVED":True,
       "original_author_documented_underscore_to_space_rule_VERIFIED":AUTHOR_VERIFIED_MAPPING,
       "original_Weiss_six_guild_categories_not_collapsed":True,
       "no_fuzzy_synonym_genus_only_or_casefold_taxonomic_remapping":True,
       "no_original_species_guild_pairs_or_taxon_identifiers_EXPORTED":True,
       "Gloor_beetle_site_abundance_or_environment_values_READ":0,
       "new_biodiversity_effect_estimated":False,
       "source_outcome_frozen_thresholds_NOT_WEAKENED":True,
       "source_format_exploratory_result_DOES_NOT_AUTHORIZE_CONFIRMATORY_GUILD_MODEL":True,
       "exploratory_normalized_Gloor_name_LEDGER_SHA256":
           hashlib.sha256("".join(n+"\n" for n in sorted(combined)).encode("utf-8")).hexdigest(),
    }

def known_truth():
    tokens={"Carabus_nemoralis","Pterostichus_melanarius"}
    got=single_source_format_only(tokens)
    assert got=={"Carabus nemoralis","Pterostichus melanarius"}
    for malformed in ({"Carabus.nemoralis"},{"Carabus_nemoralis_extra"}):
        try:
            single_source_format_only(malformed)
            raise AssertionError("unexpected source syntax converted")
        except SourceStop:pass
    assert not AUTHOR_VERIFIED_MAPPING
    print("SYNTHETIC_SINGLE_UNDERSCORE_SOURCE_FORMAT_EXPLORATORY_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args();known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    obj={
      "schema":"structural.Carpathian116_Weiss511_single_underscore_exploratory_source_nameonly.v1",
      "precommit":PRESPEC,
      "primary_prior_exact_0of309_HOLD_UNCHANGED":True,
      "source_Gloor_abundance_site_environment_rows_OPENED":False,
      "previous_Weiss_reference_source_ledger_SHA256":"6b63db8577e8bb65bbdef5aaf30b9f078b5ee02bdcb0b434eed0554ed0bdca6b",
      "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_scores_UNCHANGED":True,
      "new_ecological_effect":False,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        weiss=validate_original_weiss_private_ledger()
        original=source_gloor_name_headers()
        obj["secondary_format_sensitivity_anonymous_only"]=assess(weiss,original)
        obj["status"]=obj["secondary_format_sensitivity_anonymous_only"]["status"]
    except SourceStop as e:
        obj["status"]=str(e)
        obj["source_taxonomy_method_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Carpathian116_Weiss511_genus_underscore_species_format_secondary_coverage.json").write_text(
        json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("CARPATHIAN116_WEISS_EXPLORATORY_GENUS_UNDERSCORE_FORMAT",obj["status"])
    print("NO_GLOOR_RESPONSE_SCORING_AND_PRIMARY_EXACT_HOLD_RETAINED")
if __name__=="__main__":main()
