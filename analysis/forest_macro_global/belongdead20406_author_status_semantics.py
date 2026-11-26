#!/usr/bin/env python3
"""Four original public BELongDead20406 author-method Status categories only.

Reports categorical method Status meaning, never specimen or site IDs.
A strict exact token match to 31123 positive-record METHOD keys is NOT a join.
"""
from __future__ import annotations
import argparse
from collections import defaultdict,Counter
import csv
import io
import json
import re
from pathlib import Path

from belongdead20406_german_method_status_sourceonly import (
    HEADER, METHOD_REGEX, get_exact_tagged_source, SourceStop
)
from belongdead20406_31123_exact_token_concordance import (
    get_publisher_original_31123_method_source, method_31123,
)

PRESPEC="docs/FOREST_BELONGDEAD_20406_ECLECTOR_AUTHOR_STATUS_SEMANTICS_PRESPEC_20261118.md"
I={n:p for p,n in enumerate(HEADER)}
YEARS={str(i) for i in range(2010,2018)}


def safe_method_label(x,original_keys):
    if not (1<=len(x)<=90 and x.isprintable() and
            "\n" not in x and "\r" not in x and "\t" not in x
            and "@" not in x and "://" not in x):
        return False
    if re.search(r"\d{3,}",x):
        return False
    if re.fullmatch(r"[A-Za-zÄÖÜäöüß]{1,6}\d{1,6}",x):
        return False
    if re.search(r"(?i)\b(?:fagus|picea|quercus|pinus|betula|larix|acer|"
                 r"fraxinus|carpinus|tilia|pseudotsuga|populus|prunus)\s+"
                 r"[A-Za-z]{3,}",x):
        return False
    if x in original_keys:
        return False
    return True


def original_categorical_audit(raw,beetle_method_triples,expected_status_levels=4,
                                expected_rows=4233,expected_all_rows=12289):
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                  delimiter=",",strict=True)
    if tuple(next(rd,[])) != HEADER:
        raise SourceStop("SOURCE_20406_AUTHOR_STATUS_ORIGINAL_HEADER_DRIFT")
    statuses=defaultdict(lambda: {
        "rows_per_year":Counter(),"keys_per_year":defaultdict(set),
        "matches_per_year":defaultdict(set)})
    token_to_status=defaultdict(set)
    keys_seen=set();source_tokens=set()
    matched_rows=0;allrows=0
    # Source individual original exact ID values intentionally stay in memory.
    for row in rd:
        if not row or not any(v.strip() for v in row):continue
        allrows+=1
        if len(row)!=len(HEADER):
            raise SourceStop("SOURCE_20406_METHOD_ROW_SHAPE_DRIFT")
        device=row[I["Equipment"]].strip()
        if not METHOD_REGEX["emergence_eclector"].search(device):
            continue
        matched_rows+=1
        plot,sub,stem,yr,st=(
            row[I[k]].strip()
            for k in ("PLOT","SUBPLOT","StammNR","Jahr","Status"))
        if not all((plot,sub,stem,st)) or yr not in YEARS:
            raise SourceStop("SOURCE_20406_ECLECTOR_METHOD_KEY_STATUS_YEAR_STOP")
        k=(plot,stem,yr)
        full=(plot,sub,stem,yr)
        keys_seen.add(full);source_tokens.update((plot,sub,stem))
        token_to_status[k].add(st)
        statuses[st]["rows_per_year"][yr]+=1
        statuses[st]["keys_per_year"][yr].add(k)
        if k in beetle_method_triples:
            statuses[st]["matches_per_year"][yr].add(k)
    if allrows!=expected_all_rows or matched_rows!=expected_rows:
        raise SourceStop("SOURCE_20406_ORIGINAL_ECLECTOR_FIXED_METHOD_ROWS_DRIFT")
    if len(statuses)!=expected_status_levels:
        raise SourceStop("SOURCE_20406_EXPECTED_AUTHOR_STATUS_LEVEL_COUNT_CHANGED")
    if len(keys_seen)!=4208 and expected_status_levels==4:
        raise SourceStop("SOURCE_20406_EXPECTED_ECLECTOR_LOGYEAR_GRAIN_DRIFT")
    redact=not all(safe_method_label(s,source_tokens) for s in statuses)
    distinct_years=sorted(YEARS)
    entries=[]
    for j,name in enumerate(sorted(statuses),start=1):
        d=statuses[name]
        entries.append({
            "original_author_public_method_Status_category_or_redacted_id":
                ("Status_category_"+str(j) if redact else name),
            "source_author_original_eclector_method_rows":sum(d["rows_per_year"].values()),
            "original_author_eclector_method_ROWS_by_year":{
                y:d["rows_per_year"][y] for y in distinct_years},
            "original_author_distinct_method_PLOT_StammNR_year_keys_by_year":{
                y:len(d["keys_per_year"][y]) for y in distinct_years},
            "source_exact_31123_METHOD_token_matching_key_count_by_year":{
                y:len(d["matches_per_year"][y]) for y in distinct_years},
        })
    return {
        "status":"SOURCE_AUTHOR_STATUS_CATEGORY_REDACTION_HOLD"
          if redact else "ORIGINAL_AUTHOR_STATUS_CATEGORICAL_METHOD_DIAGNOSTIC_ONLY",
        "original_source_20406_elector_Equipment_record_rows":matched_rows,
        "original_source_20406_elector_Equipment_full_log_year_keys":len(keys_seen),
        "original_source_20406_Equipment_Status_distinct_nonblank_levels":len(statuses),
        "original_source_20406_categorical_Status_redaction_required":redact,
        "status_level_by_source_year_and_literal_token_MATCH_only":entries,
        "source_projected_original_PLOT_StammNR_year_keys_with_multiple_Status":sum(
            len(labels)>1 for labels in token_to_status.values()),
        "original_source_category_labels_are_methods_not_species_outcomes":True,
        "original_source_31124_15_TrapIDs_NOT_reconciled":True,
        "source_yearly_2013_2017_missing_31123_method_records_NOT_trap_zeros":True,
        "no_original_sample_ID_or_taxa_catch_count_data_EXPORTED":True,
        "source_method_direct_token_matched_NOT_author_biological_join":True,
        "new_ecological_effect_estimated":False,
    }


def known_truth():
    h=list(HEADER)
    a=["001","P01","S01","x","LOG-A","AG1","2015","1","2",
       "Variable","Methode","Eklektor","spring","installed"]
    b=["002","P01","S01","x","LOG-A","AG1","2016","1","2",
       "Variable","Methode","Eklektor","spring","unknown"]
    out=io.StringIO();wr=csv.writer(out);wr.writerows([h,a,b])
    r=original_categorical_audit(out.getvalue().encode(),{("P01","LOG-A","2015")},
                                 expected_status_levels=2,expected_rows=2,expected_all_rows=2)
    assert r["original_source_20406_Equipment_Status_distinct_nonblank_levels"]==2
    assert not r["original_source_20406_categorical_Status_redaction_required"]
    assert r["status_level_by_source_year_and_literal_token_MATCH_only"][0][
        "source_exact_31123_METHOD_token_matching_key_count_by_year"]["2015"]==1
    assert "P01" not in json.dumps(r) and "LOG-A" not in json.dumps(r)
    print("SYNTHETIC_20406_FOUR_AUTHOR_METHOD_STATUS_LEVELS_SOURCE_REDACTION_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:p.error("--out required")
    out={
        "schema":"structural.BELongDead20406_original_author_eclector_Status_categories.v1",
        "precommit":PRESPEC,
        "publisher_original_20406_tag":2,
        "publisher_original_31123_tag":1,
        "original_beetle_species_trait_capture_values_read":0,
        "previous_Finland_Chiu_Piccini_Burner_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        orig=method_31123(get_publisher_original_31123_method_source())
        out["source_method_only"]=original_categorical_audit(
            get_exact_tagged_source(),orig["triple"])
        out["status"]=out["source_method_only"]["status"]
    except SourceStop as e:
        out["status"]=str(e)
        out["source_stop_not_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"BELongDead20406_original_eclector_author_Status_category_semantics.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SOURCE_AUTHOR_20406_GERMAN_STATUS_CATEGORIES",out["status"])


if __name__=="__main__":
    main()
