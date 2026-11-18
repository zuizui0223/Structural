#!/usr/bin/env python3
"""Frozen equipment-emergence method contexts in original BExIS20406/tag2.

Counts exact original PLOT/SUBPLOT/StammNR/Jahr GROUPS that mention an
eclector in Equipment, NOT independently observed or deployed traps.
Never reads BExIS31123/31124 organism data.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path

from belongdead20406_german_method_status_sourceonly import (
    get_exact_tagged_source, HEADER, METHOD_REGEX, is_present, SourceStop
)

PRESPEC = "docs/FOREST_BELONGDEAD_20406_ECLECTOR_METHOD_OPPORTUNITY_PRESPEC_20261118.md"
ALLOWED_YEARS = {str(y) for y in range(2009,2019)}
SOURCE_COL = {name: i for i,name in enumerate(HEADER)}
TEXT_FIELDS = ("Methode", "Status", "wann")


def analyze(raw):
    try:
        it = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""),
                        delimiter=",", strict=True)
        head = next(it)
    except (UnicodeError, csv.Error, StopIteration):
        raise SourceStop("SOURCE_ECLECTOR_ORIGINAL_CSV_DECODE_STOP") from None
    if tuple(head) != HEADER:
        raise SourceStop("SOURCE_ECLECTOR_PUBLISHED_TAG2_HEADER_DRIFT")
    source_rows = 0
    matched_rows = 0
    source_error_rows = 0
    year_counts = Counter()
    years = set()
    plots, plot_subplots, logs, logyears = set(),set(),set(),set()
    logyears_with_status, logyears_with_wann = set(),set()
    methods_nonmissing = Counter()
    status_levels = set()
    additional_keyword_rows = Counter()
    for row in it:
        if not row or not any(v.strip() for v in row):
            continue
        source_rows += 1
        if len(row) != len(HEADER):
            source_error_rows += 1
            continue
        yr = row[SOURCE_COL["Jahr"]].strip()
        if yr not in ALLOWED_YEARS:
            raise SourceStop("SOURCE_20406_JAHR_OUTSIDE_FROZEN_2009_2018_RANGE")
        keys = tuple(row[SOURCE_COL[c]].strip()
                     for c in ("PLOT","SUBPLOT","StammNR"))
        if any(not is_present(v) for v in keys):
            raise SourceStop("SOURCE_20406_ECLECTOR_METHOD_MISSING_PHYSICAL_KEY")
        equipment = row[SOURCE_COL["Equipment"]].strip()
        if not METHOD_REGEX["emergence_eclector"].search(equipment):
            continue
        matched_rows += 1
        full=(*keys,yr)
        years.add(yr)
        year_counts[yr] += 1
        plots.add(keys[0])
        plot_subplots.add(keys[:2])
        logs.add(keys)
        logyears.add(full)
        for col in TEXT_FIELDS:
            val=row[SOURCE_COL[col]].strip()
            if not is_present(val):
                continue
            methods_nonmissing[col]+=1
            if col=="Status":
                status_levels.add(val)
                logyears_with_status.add(full)
                for name in ("emergence_eclector",
                             "trap_deployment","trap_failure","explicit_zero_capture"):
                    if METHOD_REGEX[name].search(val):
                        additional_keyword_rows[name]+=1
            if col=="wann":
                logyears_with_wann.add(full)
    if source_rows != 12289 or source_error_rows or matched_rows != 4233:
        raise SourceStop("SOURCE_ECLECTOR_LOCKED_BASELINE_ROWS_OR_KEYWORD_DRIFT")
    return {
        "original_20406_tag2_method_rows": source_rows,
        "original_20406_equipment_eclector_REGEX_matched_LONG_ROWS": matched_rows,
        "original_20406_equipment_matching_original_distinct_plots": len(plots),
        "original_20406_equipment_matching_original_plot_subplot_keys": len(plot_subplots),
        "original_20406_equipment_matching_original_plot_subplot_stamm_keys": len(logs),
        "original_20406_equipment_matching_original_log_Jahr_keys": len(logyears),
        "original_20406_matching_distinct_Jahr_labels": len(years),
        "original_20406_matching_equipment_rows_per_preapproved_numeric_Jahr": {
            year: year_counts[year] for year in sorted(ALLOWED_YEARS)
        },
        "original_nonmissing_method_fields_within_matched_ROWS": dict(methods_nonmissing),
        "original_eclector_rows_unique_original_Status_level_count": len(status_levels),
        "original_eclector_log_Jahr_keys_with_nonmissing_Status": len(logyears_with_status),
        "original_eclector_log_Jahr_keys_with_nonmissing_wann": len(logyears_with_wann),
        "original_eclector_subset_Status_strong_keyword_row_counts_ONLY": {
            name: additional_keyword_rows[name] for name in (
                "emergence_eclector","trap_deployment","trap_failure","explicit_zero_capture"
            )
        },
        "actual_trap_deployment_NOT_confirmed": True,
        "number_of_true_empty_or_zero_trap_occasions_NOT_estimable": True,
        "original_stamm_vs_TreeID_author_crosswalk_NOT_verified": True,
        "original_PLOT_vs_PlotID_author_crosswalk_NOT_verified": True,
        "original_15_new_31124_TrapIDs_unexplained": True,
        "matching_equipment_rows_are_not_independent_traps": True,
        "no_original_source_IDs_or_Status_categories_exposed": True,
        "no_organism_species_abundance_or_31123_31124_data_OPENED": True,
        "status":"ECLECTOR_EQUIPMENT_MENTION_PHYSICAL_METHOD_CONTEXTS_QUANTIFIED_ONLY",
    }


def known_truth():
    base=list(HEADER)
    row=lambda id,year,device,stat: [
        id,"P1","S1","X","L1","AG1",year,"30","60",
        "Method","Ensemble",device,"spring",stat,
    ]
    rows=[base,
          row("1","2010","Eklektor","set up"),
          row("2","2010","Eklektor","reported"),
          row("3","2011","Wood inspection","kein Fang")]
    s=io.StringIO();w=csv.writer(s);w.writerows(rows)
    # Predeclared baseline assertion only applies to actual original;
    # test lexical/nested keys independently on miniature source records.
    parsed=list(csv.reader(io.StringIO(s.getvalue())))
    assert parsed[0]==base
    assert sum(bool(METHOD_REGEX["emergence_eclector"].search(x[SOURCE_COL["Equipment"]]))
               for x in parsed[1:]) == 2
    assert len({(x[SOURCE_COL["PLOT"]],x[SOURCE_COL["SUBPLOT"]],
                 x[SOURCE_COL["StammNR"]],x[SOURCE_COL["Jahr"]])
                for x in parsed[1:] if METHOD_REGEX["emergence_eclector"].search(
                    x[SOURCE_COL["Equipment"]])}) == 1
    assert all(x[SOURCE_COL["Jahr"]] in ALLOWED_YEARS for x in parsed[1:])
    print("SYNTHETIC_GERMAN_ECLECTOR_EQUIPMENT_ROW_VS_LOGYEAR_DENOMINATOR_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:
        return
    if a.out is None:
        p.error("--out required")
    result={
        "schema":"structural.BELongDead20406_equipment_emergence_method_contexts.v1",
        "precommit":PRESPEC,
        "publisher_original_dataset_id":20406,
        "tag":2,
        "source_method_only":True,
        "new_ecological_effect":False,
        "previous_frozen_Finland_Chiu_Piccini_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
        "eBird_used":False,
        "TinyFish_used":False,
    }
    try:
        result["original_author_source_method_grouping"]=analyze(get_exact_tagged_source())
        result["status"]=result["original_author_source_method_grouping"]["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["source_stop_not_biological_non_support"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead20406_original_eclector_equipment_eligible_method_contexts.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("BE20406_ECLECTOR_EQUIPMENT_SOURCE_ONLY",result["status"])


if __name__=="__main__":
    main()
