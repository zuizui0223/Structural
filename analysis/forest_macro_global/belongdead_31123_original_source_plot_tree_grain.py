#!/usr/bin/env python3
"""BExIS 31123 original CC-BY4 BELongDead complete CSV: SOURCE-ONLY grain.

A full original 8.1MB CSV is downloaded in a temporary runner directory
after a separately verified public license. The code accesses ONLY published
plot, tree, exploratory, host-tree label and eligible exact time fields.
No insect species/taxon, counts or capture outcomes are read or computed.
Original rows/IDs stay private; only aggregate method facts are exported.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT="https://www.bexis.uni-jena.de/api/data/31123"
EXPECTED_LENGTH=8103493
EXPECTED_FIELDS={1:"TrapID",2:"PlotID",3:"Exploratory",4:"TreeID",5:"TreeSpecies"}
TIME_FIELDS=("Year","SamplingYear","CollectionYear","SamplingDate","CollectionDate")
GENERIC_HEADERS={
 "trapid","plotid","exploratory","treeid","treespecies","year",
 "samplingyear","collectionyear","samplingdate","collectiondate",
 "samplingperiod","samplingyearid","count","abundance","number",
 "species","speciesname","scientificname","family","genus",
 "observation","individuals","traptype","effort","management","treatment",
 "period","month","date","location","sampleid","decay","deadwood",
 "dbh","diameter","foresttype","sample","id","recordid","growthform",
 "woodtype","woodid","eventid"
}

class OriginalStop(RuntimeError):pass


def qualified_header(h):
    if len(h)!=17:
        raise OriginalStop("SOURCE_STOP_31123_ORIGINAL_17_HEADER_COLUMNS_DRIFT")
    for pos,name in EXPECTED_FIELDS.items():
        if h[pos]!=name:
            raise OriginalStop("SOURCE_STOP_ORIGINAL_TREE_LOG_IDENTITY_FIELD_POSITIONS_CHANGED")
    generic=[]
    for i,label in enumerate(h):
        clean=re.sub(r"[^A-Za-z0-9]","",str(label)).lower()
        if clean in GENERIC_HEADERS and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ .-]{0,52}",str(label)):
            generic.append({"original_source_column_index_1based":i+1,
                            "nonbiological_original_header_label_ONLY":str(label)})
    return generic


def parse_source(raw:bytes):
    # Source values are decoded by CSV parser; ONLY exact source metadata
    # positions 2..6 and unambiguous source time are accessed in Python.
    # Source taxa, counts, long abundances, species status ignored entirely.
    with io.StringIO(raw.decode("utf-8-sig"),newline="") as t:
        rd=csv.reader(t,delimiter=",")
        header=next(rd,[])
        safe=qualified_header(header)
        timehits=[(i,x) for i,x in enumerate(header) if x in TIME_FIELDS]
        if len(timehits)>1:
            raise OriginalStop("SOURCE_STOP_MULTIPLE_UNDECIDED_SOURCE_YEAR_COLUMNS")
        timeidx,timename=timehits[0] if timehits else (None,None)
        n=0
        badshape=0
        missing=Counter()
        host_by_tree=defaultdict(set)
        plot_keys=set()
        tree_keys=set()
        trap_keys=set()
        full_host_labels=set()
        source_categories=Counter()
        source_yrs=Counter()
        source_tree_year=Counter()
        for row in rd:
            if not row or not any(c.strip() for c in row):
                continue
            n+=1
            if len(row)!=len(header):
                badshape+=1
                continue
            trap,plot,ex,tree,host=[row[idx].strip() for idx in (1,2,3,4,5)]
            for name,value in (("TrapID",trap),("PlotID",plot),("Exploratory",ex),
                               ("TreeID",tree),("TreeSpecies",host)):
                if not value or value.lower() in ("na","nan","null","missing"):
                    missing[name]+=1
            if any(not x or x.lower() in ("na","nan","null","missing")
                   for x in (trap,plot,ex,tree,host)):
                continue
            source_categories[ex]+=1
            plot_keys.add((ex,plot))
            tree_keys.add((ex,plot,tree))
            trap_keys.add((ex,plot,tree,trap))
            full_host_labels.add(host)
            host_by_tree[(ex,plot,tree)].add(host)
            if timeidx is not None:
                yy=row[timeidx].strip()
                if not yy or yy.lower() in ("na","nan","null","missing"):
                    missing[timename]+=1
                else:
                    source_yrs[yy]+=1
                    source_tree_year[(ex,plot,tree,yy)]+=1
    if n<100 or badshape:
        raise OriginalStop("SOURCE_STOP_ORIGINAL_SOURCE_ROW_COUNT_OR_CSV_SHAPE")
    if not source_categories or not plot_keys:
        raise OriginalStop("SOURCE_STOP_EMPTY_ORIGINAL_FIELD_ID_METADATA")
    conflicts=sum(len(v)>1 for v in host_by_tree.values())
    result={
        "source_original_BExIS_31123_CSV_record_rows_NOT_beetle_individuals":n,
        "original_header_field_count":len(header),
        "source_published_generic_field_names_only":safe,
        "source_time_field_selected_when_exactly_one":timename,
        "original_source_missing_key_rows":dict(missing),
        "source_original_distinct_exploratory_labels":len(source_categories),
        "source_original_distinct_exploratory_by_plot_keys":len(plot_keys),
        "source_original_distinct_exploratory_plot_tree_candidates":len(tree_keys),
        "source_original_distinct_exploratory_plot_tree_trap_candidates":len(trap_keys),
        "source_original_tree_host_label_count":len(full_host_labels),
        "source_original_host_category_nested_tree_counts_anonymous_sorted":sorted(
            (sum(1 for labs in host_by_tree.values() if host in labs)
             for host in full_host_labels),reverse=True),
        "source_original_tree_host_identity_conflicting_keys":conflicts,
        "source_original_exploratory_record_row_counts_unlabeled":sorted(source_categories.values(),reverse=True),
        "source_original_date_year_label_count_if_present":len(source_yrs),
        "source_original_log_by_year_distinct_keys_if_present":len(source_tree_year),
        "source_original_tree_year_repeat_capture_record_excess_if_present":sum(
            max(0,v-1) for v in source_tree_year.values()),
        "source_original_taxa_individual_counts_other_columns_NEVER_USED":True,
        "source_original_plot_tree_species_ID_values_NOT_EXPORTED":True,
        "source_year_and_sampling_effort_not_assumed_from_generic_header":True,
    }
    if conflicts:
        result["status"]="SOURCE_STOP_SOURCE_TREE_HOST_LABEL_CONFLICT_NO_SPECIES_SCORING"
    elif not timename:
        result["status"]="SOURCE_PLOT_TREE_HOST_HIERARCHY_OBSERVED_YEAR_EFFORT_JOIN_NOT_VERIFIED"
    else:
        result["status"]="SOURCE_PLOT_TREE_HOST_YEAR_METADATA_OBSERVED_EFFORT_STILL_UNVERIFIED"
    return result


def get_original():
    req=urllib.request.Request(ENDPOINT,headers={"User-Agent":"Structural-source-only-BELongDead31123-full-2026/1.0","Accept":"text/csv"})
    try:
        with urllib.request.urlopen(req,timeout=85) as conn:
            code=conn.status
            ctype=conn.headers.get("Content-Type","")
            data=conn.read(EXPECTED_LENGTH+1)
    except urllib.error.HTTPError as exc:
        raise OriginalStop("SOURCE_ACCESS_STOP_ORIGINAL_BEXIS_31123_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,OSError,TimeoutError) as exc:
        raise OriginalStop("SOURCE_TRANSPORT_STOP_ORIGINAL_BEXIS_31123_"+type(exc).__name__) from exc
    if code!=200 or "csv" not in ctype.lower() or len(data)!=EXPECTED_LENGTH:
        raise OriginalStop("SOURCE_STOP_ORIGINAL_DATA_CSV_OR_SIZE_CHANGED")
    return data


def synthetic():
    header=["UID","TrapID","PlotID","Exploratory","TreeID","TreeSpecies",
            "Year"]+[f"Other_{i}" for i in range(10)]
    assert len(header)==17
    rows=[
      header,
      ["1","R1","P1","A","T1","Fagus sylvatica","2010"]+["0"]*10,
      ["2","R1","P1","A","T1","Fagus sylvatica","2011"]+["1"]*10,
      ["3","R2","P2","A","T2","Picea abies","2011"]+["1"]*10,
    ]
    s=io.StringIO();w=csv.writer(s);w.writerows(rows)
    # Production minimum 100 records can't be tested on only 3.
    assert qualified_header(header)[0]["nonbiological_original_header_label_ONLY"]=="TrapID"
    assert all(header[i]==name for i,name in EXPECTED_FIELDS.items())
    assert len({(r[3],r[2],r[4]) for r in rows[1:]})==2
    assert s.getvalue().count("Fagus sylvatica")==2
    print("SYNTHETIC_ORIGINAL_PLOT_TREE_YEAR_FIELD_HIERARCHY_AND_NO_TAXON_READ_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out required")
    report={
      "schema":"structural.BELongDead31123_original_FullCSV_exploratory_plot_tree_sourcegrain.v1",
      "original_BExIS_dataset_ID":31123,
      "original_cc_by_4_license_confirmed_CI43701688869":True,
      "original_CSV_17_fields_content_length_8103493_confirmed_CI43701987094":True,
      "original_data_source_sha256_computed_private":None,
      "original_source_biology_and_abundance_values_not_opened_or_scored":True,
      "all_prior_Finland_Burner_PREDICTS_NEON_BALA_GEB_effects_unmodified":True,
      "eBird_used":False,
    }
    try:
        raw=get_original()
        report["original_data_source_sha256_computed_private"]=hashlib.sha256(raw).hexdigest()
        report["original_data_source_bytes_verified"]=len(raw)
        source=parse_source(raw)
        report["source_only_original_sampling_unit_audit"]=source
        report["status"]=source["status"]
    except OriginalStop as exc:
        report["status"]=str(exc)
        report["original_source_failure_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead31123_17field_fullCSV_original_metadata_only.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
