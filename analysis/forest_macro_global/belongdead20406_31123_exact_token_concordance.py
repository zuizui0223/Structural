#!/usr/bin/env python3
"""Original 20406 eclector METHOD vs 31123 original beetle METHOD token check.

This is NOT an author-approved join. Only source key fields accessed;
no taxon labels, species abundance or canopy/wood measurement fields read.
No renaming, fuzzy matching, ID conversions or trap incidence calculations.
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict, Counter
import hashlib
import io
import json
import urllib.error
import urllib.request
from pathlib import Path

from belongdead20406_german_method_status_sourceonly import (
    get_exact_tagged_source, HEADER, METHOD_REGEX, SourceStop
)
from belongdead_author_alias_naming_source_gate import NoRedirect

PRESPEC="docs/FOREST_BELONGDEAD_20406_31123_EXACT_TOKEN_CONCORDANCE_PRESPEC_20261118.md"
ORIGINAL_BEETLE_URL="https://www.bexis.uni-jena.de/api/data/31123/tag/1"
ORIGINAL_BEETLE_LEN=8103493
ORIGINAL_BEETLE_SHA="73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e"
EXPECTED_BEETLE_FIELDS={"PlotID":2,"Exploratory":3,"TreeID":4,"CollectionYear":11}
YEARS={str(y) for y in range(2010,2018)}
EC_COL={name:i for i,name in enumerate(HEADER)}


def get_publisher_original_31123_method_source():
    r=urllib.request.Request(ORIGINAL_BEETLE_URL,headers={
        "User-Agent":"Structural-BELongDead-original-author-method-token-only/1.0",
        "Accept":"text/csv,application/octet-stream;q=0.5"
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(r,timeout=85) as response:
            if response.status!=200:
                raise SourceStop("SOURCE_31123_ORIGINAL_TAG_NOT_HTTP200")
            raw=response.read(ORIGINAL_BEETLE_LEN+1)
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_31123_TAG1_HTTP_"+str(exc.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_31123_TAG1_TRANSPORT_"+type(exc).__name__) from None
    if len(raw)!=ORIGINAL_BEETLE_LEN or hashlib.sha256(raw).hexdigest()!=ORIGINAL_BEETLE_SHA:
        raise SourceStop("SOURCE_31123_TAG1_SHA_SIZE_DRIFT")
    return raw


def method_20406(raw):
    reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                      delimiter=",",strict=True)
    if tuple(next(reader,[])) != HEADER:
        raise SourceStop("SOURCE_20406_ORIGINAL_METHOD_HEADER_DRIFT")
    source_rows=0
    eqrows=0
    plots=set();full_keys=set();projection_to_subplots=defaultdict(set)
    for row in reader:
        if not row or not any(q.strip() for q in row):
            continue
        source_rows+=1
        if len(row)!=len(HEADER):
            raise SourceStop("SOURCE_20406_METHOD_ROW_14_COLUMNS_DRIFT")
        vals=[row[EC_COL[k]].strip() for k in
              ("PLOT","SUBPLOT","StammNR","Jahr","Equipment")]
        plot,sub,log,year,equipment=vals
        if not (plot and sub and log and year):
            raise SourceStop("SOURCE_20406_METHOD_PARENT_KEY_MISSING")
        if year not in {str(i) for i in range(2009,2019)}:
            raise SourceStop("SOURCE_20406_YEAR_DOMAIN_DRIFT")
        if not METHOD_REGEX["emergence_eclector"].search(equipment):
            continue
        eqrows+=1
        plots.add(plot)
        full_keys.add((plot,sub,log,year))
        projection_to_subplots[(plot,log,year)].add(sub)
    if source_rows!=12289 or eqrows!=4233:
        raise SourceStop("SOURCE_20406_OLD_ECLECTOR_RESPONSE_FREE_GATE_DRIFT")
    projected=set(projection_to_subplots)
    collisions=sum(len(subs)>1 for subs in projection_to_subplots.values())
    return {
        "plots":plots,"full":full_keys,"projected":projected,
        "projection_collisions":collisions,"year_counts":Counter(key[2] for key in projected)
    }


def method_31123(raw):
    reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                      delimiter=",",strict=True)
    head=next(reader,[])
    if len(head)!=17 or any(head[pos]!=name for name,pos in EXPECTED_BEETLE_FIELDS.items()):
        raise SourceStop("SOURCE_31123_TAG1_METHOD_HEADER_POSITION_DRIFT")
    rows=0
    plots=set();ex_by_plot=defaultdict(set)
    triple=set();physkeys=set()
    for row in reader:
        if not row or not any(q.strip() for q in row):
            continue
        rows+=1
        if len(row)!=17:
            raise SourceStop("SOURCE_31123_METHOD_17COLUMN_ROW_DRIFT")
        # Only method columns, not source taxa/species/counts/TrapID.
        plot,ex,log,year=(
            row[EXPECTED_BEETLE_FIELDS[k]].strip() for k in
            ("PlotID","Exploratory","TreeID","CollectionYear")
        )
        if not all((plot,ex,log,year)) or year not in YEARS:
            raise SourceStop("SOURCE_31123_ORIGINAL_METHOD_PARENT_KEY_YEAR_STOP")
        plots.add(plot)
        ex_by_plot[plot].add(ex)
        triple.add((plot,log,year))
        physkeys.add((ex,plot,log))
    if rows!=59850 or len(plots)!=30 or len(physkeys)!=379:
        raise SourceStop("SOURCE_31123_ORIGINAL_PLOT_LOG_BASELINE_DRIFT")
    return {"plots":plots,"triple":triple,"physkeys":physkeys,
            "plot_to_exploratories":ex_by_plot}


def compare(a,b):
    source_proj=a["projected"]
    source_host=set((x[0],x[1]) for x in source_proj)
    beetle_host=set((x[0],x[1]) for x in b["triple"])
    overlap=source_proj & b["triple"]
    year_matches={year:sum(key[2]==year for key in overlap) for year in sorted(YEARS)}
    year_equip={year:sum(key[2]==year for key in source_proj) for year in sorted(YEARS)}
    year_beetle={year:sum(key[2]==year for key in b["triple"]) for year in sorted(YEARS)}
    same_all=(len(a["plots"] & b["plots"])==len(a["plots"])==len(b["plots"]))
    ec_overlap=len(overlap)
    return {
        "schema":"structural.BELongDead20406_31123_original_exact_method_token_diagnostic.v1",
        "precommit":PRESPEC,
        "source_20406_original_full_ECLECTOR_equipment_PLOT_tokens":len(a["plots"]),
        "source_31123_original_biological_source_PlotID_tokens":len(b["plots"]),
        "source_between_original_plot_name_tokens_EXACT_intersection":len(a["plots"]&b["plots"]),
        "source_plot_name_token_universes_identical":same_all,
        "source_20406_original_eclector_full_subplot_log_year_method_keys":len(a["full"]),
        "source_20406_original_eclector_projected_plot_log_year_tokens":len(source_proj),
        "source_20406_projection_subplot_COLLISION_triplets":a["projection_collisions"],
        "source_31123_original_distinct_plot_tree_CollectionYear_tokens":len(b["triple"]),
        "source_31123_PlotID_reused_across_Exploratory_count":sum(
             len(v)>1 for v in b["plot_to_exploratories"].values()),
        "cross_original_plot_log_two_token_exact_overlap_count":len(source_host&beetle_host),
        "cross_original_plot_log_year_three_token_exact_overlap_count":ec_overlap,
        "source_method_year_2010_2017_eclector_candidate_token_counts":year_equip,
        "source_method_year_2010_2017_31123_PlotID_TreeID_CollectionYear_token_counts":year_beetle,
        "source_method_year_2010_2017_exact_three_token_matches":year_matches,
        "exact_source_token_match_NEVER_authorizes_join":True,
        "source_20406_StammNR_31123_TreeID_semantic_mapping_NOT_verified":True,
        "source_20406_PLOT_31123_PlotID_semantic_mapping_NOT_verified":True,
        "source_31124_new_TrapID_aliases_RESOLVED":False,
        "zero_capture_or_trap_deployment_frame_ESTIMATED":False,
        "previously_scored_biological_source_response_rows_OPENED":False,
        "source_original_sample_ID_values_EXPORTED":False,
        "status":(
            "TOKEN_CONCORDANCE_CANDIDATE_NOT_AUTHORIZED_JOIN"
            if same_all and not a["projection_collisions"] and ec_overlap==len(source_proj)
            else "SOURCE_AUTHOR_MAPPING_REQUIRED_NO_AUTOMATIC_JOIN"
        )
    }


def known_truth():
    a={
        "plots":{"A1"},
        "full":{("A1","S1","L1","2015"),("A1","S2","L1","2015"),
                ("A1","S1","L2","2016")},
        "projected":{("A1","L1","2015"),("A1","L2","2016")},
        "projection_collisions":1
    }
    b={
        "plots":{"A1"},
        "triple":{("A1","L1","2015"),("A1","L2","2016")},
        "physkeys":{("R1","A1","L1"),("R1","A1","L2")},
        "plot_to_exploratories":{"A1":{"R1"}}
    }
    c=compare(a,b)
    assert c["source_20406_projection_subplot_COLLISION_triplets"]==1
    assert c["cross_original_plot_log_year_three_token_exact_overlap_count"]==2
    assert c["status"]=="SOURCE_AUTHOR_MAPPING_REQUIRED_NO_AUTOMATIC_JOIN"
    assert "A1" not in json.dumps(c) and "L1" not in json.dumps(c)
    print("SYNTHETIC_ORIGINAL_20406_31123_NO_GUESSING_EXACT_TOKEN_PROJECTION_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    x=p.parse_args()
    known_truth()
    if x.test:
        return
    if x.out is None:
        p.error("--out required")
    report={
        "schema":"structural.BELongDead20406_31123_original_exact_token_source_only.v1",
        "precommit":PRESPEC,
        "original_20406_tag":2,"original_31123_tag":1,
        "previous_Finland_Chiu_Piccini_PREDICTS_NEON_BALA_GEB_effects_UNCHANGED":True,
        "new_biological_effect":False,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        a=method_20406(get_exact_tagged_source())
        b=method_31123(get_publisher_original_31123_method_source())
        report["exact_anonymous_source_method_token_comparison"]=compare(a,b)
        report["status"]=report["exact_anonymous_source_method_token_comparison"]["status"]
    except SourceStop as e:
        report["status"]=str(e)
        report["source_only_stop_NOT_organism_null"]=True
    x.out.mkdir(parents=True,exist_ok=True)
    (x.out/"BELongDead20406_31123_original_no_guessing_exact_method_token_comparison.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("BELONGDEAD_AUTHOR_TWO_SOURCE_EXACT_METHOD_TOKEN_AUDIT",report["status"])


if __name__=="__main__":
    main()
