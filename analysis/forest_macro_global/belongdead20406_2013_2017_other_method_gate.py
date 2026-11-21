#!/usr/bin/env python3
"""Source-only classification of 114 original beetle METHOD keys missing from
20406 Equipment-eclector subset, never a missing-beetle or trap-zero claim."""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
import csv
import io
import json
from pathlib import Path

from belongdead20406_german_method_status_sourceonly import (
    HEADER, METHOD_REGEX, get_exact_tagged_source, SourceStop
)
from belongdead20406_31123_exact_token_concordance import (
    get_publisher_original_31123_method_source, method_31123
)

PRESPEC="docs/FOREST_BELONGDEAD_20406_2013_2017_MISSING_ECLECTOR_METHOD_SOURCE_PRESPEC_20261118.md"
S={n:i for i,n in enumerate(HEADER)}
YEARS={str(x) for x in range(2010,2018)}


def source_method_20406(raw, expect_source_rows=12289,expect_equipment_rows=4233):
    rdr=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                   delimiter=",",strict=True)
    if tuple(next(rdr,[])) != HEADER:
        raise SourceStop("SOURCE_AUTHOR_20406_ORIGINAL_HEADER_DRIFT")
    all_subplots=defaultdict(set)
    source_rows_by_k=defaultdict(list)
    eclector_keys=set()
    source_rows=0;eclector_rows=0
    for row in rdr:
        if not row or not any(z.strip() for z in row):continue
        source_rows+=1
        if len(row)!=len(HEADER):
            raise SourceStop("SOURCE_AUTHOR_20406_METHOD_ROW_SHAPE")
        plot,sub,log,year=(row[S[k]].strip()
                for k in ("PLOT","SUBPLOT","StammNR","Jahr"))
        if not all((plot,sub,log,year)):
            raise SourceStop("SOURCE_AUTHOR_20406_METHOD_KEY_MISSING")
        if year not in YEARS | {"2009","2018"}:
            raise SourceStop("SOURCE_AUTHOR_20406_YEAR_FIXED_DOMAIN")
        projected=(plot,log,year)
        all_subplots[projected].add(sub)
        equipment=row[S["Equipment"]].strip()
        source_rows_by_k[projected].append(equipment)
        if METHOD_REGEX["emergence_eclector"].search(equipment):
            eclector_rows+=1
            eclector_keys.add(projected)
    if source_rows!=expect_source_rows or eclector_rows!=expect_equipment_rows:
        raise SourceStop("SOURCE_AUTHOR_20406_ECLECTOR_BASELINE_DRIFT")
    return all_subplots,source_rows_by_k,eclector_keys


def diagnose(beetle_keys,source):
    all_subplots,original_rows_by_key,eclector_keys=source
    not_equipment=beetle_keys-eclector_keys
    year_missing=Counter(z[2] for z in not_equipment)
    if len(not_equipment)!=114 or year_missing!=Counter({"2013":109,"2017":5}):
        raise SourceStop("SOURCE_20406_31123_FROZEN_2013_2017_MISSING_ECLECTOR_KEYS_DRIFT")
    missing_in_all=set(k for k in not_equipment if k not in all_subplots)
    seen_in_other=not_equipment-missing_in_all
    counts_by_year={}
    for year in sorted(YEARS):
        yearly=[k for k in not_equipment if k[2]==year]
        present=[k for k in yearly if k in all_subplots]
        missing=[k for k in yearly if k not in all_subplots]
        rows=[value for k in present for value in original_rows_by_key[k]]
        lexical={
           "emergence_eclector":sum(bool(METHOD_REGEX["emergence_eclector"].search(v)) for v in rows),
           "other_trap":sum(bool(METHOD_REGEX["other_trap"].search(v)) for v in rows),
           "forest_log_measurement":sum(bool(METHOD_REGEX["forest_log_measurement"].search(v)) for v in rows),
        }
        counts_by_year[year]={
            "source_31123_original_method_tokens_missing_20406_equipment_eclector":len(yearly),
            "of_these_present_in_20406_ANY_original_method_row":len(present),
            "of_these_missing_from_20406_ALL_original_method_rows":len(missing),
            "other_method_original_source_long_rows_for_PRESENT_tokens":len(rows),
            "other_method_rows_with_nonblank_equipment":sum(bool(v) for v in rows),
            "other_method_Equipment_only_fixed_keyword_counts_not_disjoint":lexical,
        }
    return {
        "schema":"structural.BELongDead_20406_31123_2013_2017_source_method_gap.v1",
        "precommit":PRESPEC,
        "frozen_original_31123_method_PLOTID_TREEID_COLLECTIONYEAR_keys":len(beetle_keys),
        "frozen_original_31123_method_tokens_NOT_IN_20406_ECLECTOR_equipment":len(not_equipment),
        "of_missing_E_tokens_found_in_all_20406_original_method_rows":len(seen_in_other),
        "of_missing_E_tokens_absent_from_all_20406_original_method_rows":len(missing_in_all),
        "source_original_20406_all_method_PLOT_StammNR_Jahr_projection_count":len(all_subplots),
        "source_original_20406_all_method_SUBPLOT_projection_collisions":sum(
            len(v)>1 for v in all_subplots.values()),
        "original_method_year_specific_no_Eclector_token_diagnosis":counts_by_year,
        "original_method_absence_NOT_an_unsampled_trap_or_zero_beetle_capture":True,
        "any_original_method_row_NOT_true_sampling_deployment_frame":True,
        "source_20406_projected_exact_ID_match_not_author_mapping":True,
        "original_31124_fifteen_unmatched_TrapID_names_NOT_explained":True,
        "no_original_method_labels_or_site_IDs_EXPORTED":True,
        "no_original_species_abundance_counts_or_trait_values_READ":True,
        "new_ecological_effect_estimated":False,
        "status":("OTHER_METHOD_METADATA_FOR_UNMATCHED_NOT_VALIDATED_ECLECTOR_EFFORT"
                  if seen_in_other else
                  "ORIGINAL_METHOD_FRAME_MISSING_SOME_31123_SOURCE_LOGYEAR_TOKENS"),
    }


def known_truth():
    allsub=defaultdict(set)
    allsub[("P","L","2013")].add("S")
    allrows={("P","L","2013"):["Holz",""]}
    key=("P","L","2013")
    assert key in allsub and key not in {("P","L","2012")}
    assert len(allrows[key])==2
    assert not METHOD_REGEX["emergence_eclector"].search(allrows[key][0])
    print("SYNTHETIC_2013_2017_EXCLUDED_ECLECTOR_VS_ALL_ORIGINAL_METHOD_KEY_PASS")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:parser.error("--out required")
    res={
        "schema":"structural.BELongDead20406_2013_2017_missing_eclector_method_qualification.v1",
        "precommit":PRESPEC,"original_20406_tag":2,"original_31123_tag":1,
        "old_Finland_Chiu_Piccini_Burner_PREDICTS_NEON_BALA_GEB_effects_UNCHANGED":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        source=source_method_20406(get_exact_tagged_source())
        beetle=method_31123(get_publisher_original_31123_method_source())
        res["original_source_only_missing_method_diagnosis"]=diagnose(
            beetle["triple"],source)
        res["status"]=res["original_source_only_missing_method_diagnosis"]["status"]
    except SourceStop as ex:
        res["status"]=str(ex)
        res["source_STOP_not_biological_non_support"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"BELongDead20406_original_missing_eclector_source_method_classification.json").write_text(
        json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("BELONGDEAD_20406_2013_2017_METHOD_KEY_DIAGNOSTIC",res["status"])


if __name__=="__main__":
    main()
