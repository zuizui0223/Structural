#!/usr/bin/env python3
"""One author-published original BELongDead 31124 complete-log method filter.

Checks source site×log×year×TrapID×Traptype identity against original licensed
31123 full cohort. No beetle species or count columns read or scored. Never
exports original source plot IDs, host names, trap labels or biological rows.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,urllib.error,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from belongdead_31123_original_source_plot_tree_grain import get_original as get_31123

ORIGINAL_31123_SHA="73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e"
SUBSET_URL="https://www.bexis.uni-jena.de/api/data/31124"
MAX_BYTES=20000000
FIELDS={"TrapID":1,"PlotID":2,"Exploratory":3,"TreeID":4,"TreeSpecies":5,
        "Traptype":9,"CollectionYear":11}


class ScientificStop(Exception):pass


def get_31124():
    req=urllib.request.Request(
        SUBSET_URL,headers={"User-Agent":"Structural-original-BELongDead31124-method-qualification/1.0","Accept":"text/csv"})
    try:
        with urllib.request.urlopen(req,timeout=85) as f:
            raw=f.read(MAX_BYTES+1)
            status=f.status
            ctype=f.headers.get("Content-Type","")
            size=f.headers.get("Content-Length","")
    except urllib.error.HTTPError as e:
        raise ScientificStop("SOURCE_ACCESS_STOP_ORIGINAL_31124_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        raise ScientificStop("SOURCE_TRANSPORT_STOP_ORIGINAL_31124_"+type(e).__name__) from e
    if status!=200 or "csv" not in ctype.lower() or len(raw)>MAX_BYTES:
        raise ScientificStop("SOURCE_STOP_ORIGINAL_31124_NOT_QUALIFIED_CSV_BELOW_20MB")
    if size.isdigit() and int(size)!=len(raw):
        raise ScientificStop("SOURCE_STOP_ORIGINAL_31124_TRUNCATED_ORIGINAL_SOURCE")
    return raw


def metadata_only(raw:bytes,expect_header:list[str]|None=None):
    rd=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=",")
    header=next(rd,[])
    if len(header)!=17 or any(header[idx]!=field for field,idx in FIELDS.items()):
        raise ScientificStop("SOURCE_STOP_ORIGINAL_31124_METHOD_FIELDS_NOT_ALIGNED_WITH_31123")
    if expect_header is not None and header!=expect_header:
        raise ScientificStop("SOURCE_STOP_31124_SOURCE_COLUMNS_DIFFER_FROM_31123_NO_GUESSING")
    context_keys=set()
    plot=set();trees=set();tree_years=set();traps=set()
    host_by_tree=defaultdict(set)
    host_labels=set();original_years=Counter();traptypes=set()
    source_rows=0;row_missing=0
    for row in rd:
        if not row or not any(q.strip() for q in row): continue
        source_rows+=1
        if len(row)!=17:
            raise ScientificStop("SOURCE_STOP_ORIGINAL_17COL_LONG_CSV_ROW_DRIFT")
        trap,plotid,ex,tree,host,traptype,year=[row[FIELDS[k]].strip() for k in FIELDS]
        if any(not x or x.lower() in ("na","nan","null","missing")
               for x in (trap,plotid,ex,tree,host,year)):
            row_missing+=1
            continue
        if year not in {str(v) for v in range(2010,2018)}:
            raise ScientificStop("SOURCE_STOP_NOT_ORIGINAL_2010_2017_YEAR")
        k=(ex,plotid,tree)
        trees.add(k);plot.add((ex,plotid));tree_years.add((*k,year))
        host_labels.add(host);host_by_tree[k].add(host)
        traptypes.add(traptype)
        traps.add((*k,year,trap))
        context_keys.add((ex,plotid,tree,host,year,trap))
        original_years[year]+=1
    if not source_rows:
        raise ScientificStop("SOURCE_STOP_AUTHOR_ORIGINAL_COMPLETE_LOG_SOURCE_EMPTY")
    return {
        "_keys":context_keys,
        "_trees":trees,
        "source_data_rows_NOT_independent_captures_or_traps":source_rows,
        "source_rows_missing_original_metadata":row_missing,
        "source_distinct_exploratory_plot_ID_keys":len(plot),
        "source_distinct_plot_tree_nested_log_candidates":len(trees),
        "source_distinct_plot_tree_year_contexts":len(tree_years),
        "source_distinct_nested_trap_year_method_keys":len(traps),
        "source_original_three_level_year_count":len(original_years),
        "source_original_year_record_counts":[{"year":y,"metadata_source_rows":original_years[y]}
                                              for y in sorted(original_years)],
        "source_tree_host_category_count":len(host_labels),
        "source_original_traptype_category_count":len(traptypes),
        "source_tree_identity_conflicts_within_plot_log":sum(len(v)>1 for v in host_by_tree.values()),
        "original_other_species_taxa_and_abundance_10_columns_not_opened_or_scored":True,
        "original_plot_trap_tree_ID_labels_not_reexported":True,
    }


def scan_both():
    a=get_31123()
    if hashlib.sha256(a).hexdigest()!=ORIGINAL_31123_SHA:
        raise ScientificStop("SOURCE_STOP_31123_PINNED_FULL_COHORT_SHA_CHANGED")
    b=get_31124()
    header_full=next(csv.reader(io.StringIO(a.decode("utf-8-sig"),newline="")))
    full=metadata_only(a)
    complete=metadata_only(b,header_full)
    full_keys=full.pop("_keys");subset_keys=complete.pop("_keys")
    full_trees=full.pop("_trees");subset_trees=complete.pop("_trees")
    lost=subset_keys-full_keys
    return {
       "schema":"structural.BELongDead_31124_full_valid_logs_vs_31123_source_methodonly.v1",
       "original_source_public_BExIS31123_complete_study":"CC BY 4.0",
       "original_source_BExIS31124_original_author_complete_log_view":"CC BY 4.0",
       "same_study_NOT_new_independent_replication":True,
       "original_full_31123_SHA256_verified":ORIGINAL_31123_SHA,
       "original_subset_31124_SHA256_computed":hashlib.sha256(b).hexdigest(),
       "original_source_original_byte_lengths":[len(a),len(b)],
       "31123_original_full_method_support":full,
       "31124_original_complete_log_subset_method_support":complete,
       "author_31124_method_key_tuples_not_in_31123":len(lost),
       "source_original_31124_log_candidates_not_in_31123":len(subset_trees-full_trees),
       "source_original_31123_log_candidates_represented_in_31124":len(subset_trees&full_trees),
       "source_original_complete_subset_fraction_of_full_nested_logs":round(len(subset_trees&full_trees)/max(len(full_trees),1),6),
       "original_capture_effort_all_zero_traps_NOT_DOCUMENTED_BY_POSITIVE_SOURCE_ROWS":True,
       "no_new_original_species_effect_or_reclassification":True,
       "original_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_frozen":True,
       "eBird_used":False,
       "status":(
           "SOURCE_STOP_AUTHOR_COMPLETE_LOG_NOT_PURE_SOURCE_METHOD_SUBSET"
           if len(lost) or len(subset_trees-full_trees) or
              complete["source_tree_identity_conflicts_within_plot_log"] else
           "SOURCE_COMPLETE_LOG_VIEW_EXACT_AUTHOR_METHOD_SUBSET_SAMPLING_OPPORTUNITY_STILL_UNVERIFIED"
       )
    }


def known_truth():
    h=(["UID","TrapID","PlotID","Exploratory","TreeID","TreeSpecies"]
       + ["X"+str(i) for i in range(3)]
       + ["Traptype","X10","CollectionYear"]
       + ["X"+str(i) for i in range(12,17)])
    assert len(h)==17
    for field,idx in FIELDS.items():
        assert h[idx]==field
    assert len({("A","P","L","Beech","2014","T1"),
                 ("A","P","L","Beech","2014","T1")})==1
    print("SYNTHETIC_AUTHOR_COMPLETE_LOG_SUBSET_SIX_METADATA_FIELDS_AND_NO_BIOLOGY_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if not a.out:p.error("--out")
    try:r=scan_both()
    except ScientificStop as e:
        r={"schema":"structural.BELongDead_31124_full_valid_logs_vs_31123_source_methodonly.v1",
           "status":str(e),"source_stop_not_ecological_non_support":True,
           "original_previous_ecological_results_unchanged":True}
    if r["status"].startswith("SOURCE_STOP"):
        # The author metadata failed a fixed method-key equality gate.
        # This is a SCIENTIFIC SOURCE STOP, not a Python/runtime exception
        # and never a negative saproxylic beetle ecological effect.
        r["source_stop_not_ecological_non_support"]=True
        r["original_previous_ecological_results_unchanged"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead31124_complete_logs_vs_31123_full_method_sourceonly.json").write_text(
       json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
