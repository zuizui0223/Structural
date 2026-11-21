#!/usr/bin/env python3
"""Original 2026 GRO.data site/stand/plot×stratum×year SOURCE-ONLY audit.
Original species, guild, abundance, resource and detection values unscored.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import io
import json
import re
from datetime import date
from pathlib import Path
from piccini2026_gro_original_method_unit_gate import (
    DOI,MAX_FILE,metadata_source_files,head_shape,get_one_original_publisher_file,
    MethodStop
)
from piccini2026_gro_original_header_only_gate import normalized

MAX_RECORDS=100000
SEMICOLON_FIELDS=17
ROLE_NAMES={
  "parent_site":{"site","siteid","sitecode","forestsite"},
  "stand_category":{"stand","standtype","foresttype"},
  "plot_unit":{"plot","plotid","standid","locationid"},
  "vertical_stratum":{"layer","stratum","verticalstratum","forestlayer"},
  "year":{"year","sampleyear","samplingyear","collectionyear","date",
          "period","season","samplingperiod","samplingdate","collectiondate",
          "sampledate","month","surveyyear"},
}

def calendar_year_from_time_token(token):
    """Conservative lexical calendar check, no method/biology inference."""
    if re.fullmatch(r"(?:19|20)[0-9]{2}",token):
        return token,"FOUR_DIGIT_YEAR"
    m=re.fullmatch(r"((?:19|20)[0-9]{2})[-/]([0-9]{2})[-/]([0-9]{2})",token)
    if m:
        try:
            date(int(m.group(1)),int(m.group(2)),int(m.group(3)))
            return m.group(1),"VALID_ISO_DATE"
        except ValueError:
            pass
    return None,"NONCANONICAL_TIME_TOKEN"


def role_positions(header):
    normalized_names=[normalized(h) for h in header]
    positions={k:[i for i,n in enumerate(normalized_names) if n in v]
               for k,v in ROLE_NAMES.items()}
    safe_fields={k:[normalized_names[i] for i in positions[k]]
                 for k in ROLE_NAMES}
    return positions,safe_fields

def audit_source_method_rows(raw,checksum=None):
    try: s=raw.decode("utf-8-sig")
    except UnicodeError as e:raise MethodStop("SOURCE_STOP_NOT_UTF8") from e
    reader=csv.reader(io.StringIO(s,newline=""),delimiter=";",strict=True)
    try:header=next(reader)
    except (StopIteration,csv.Error) as e:
        raise MethodStop("SOURCE_STOP_AUTHOR_HEADER") from e
    if len(header)!=SEMICOLON_FIELDS:raise MethodStop("SOURCE_STOP_METHOD_HEADER_DRIFT")
    positions,safe_fields=role_positions(header)
    summary={
      "source_header_safe_generic_role_names_only":safe_fields,
      "author_named_field_roles_uniquely_identifiable":
         all(len(v)==1 for v in positions.values()),
      "method_only_no_species_abundance_or_trait_columns_selected":True,
    }
    if not summary["author_named_field_roles_uniquely_identifiable"]:
        summary["status"]="AUTHOR_METHOD_FIELD_ROLE_UNRESOLVED"
        return summary
    ids={k:positions[k][0] for k in positions}
    if len(set(ids.values()))!=len(ids):
        raise MethodStop("SOURCE_STOP_DUPLICATE_SEMANTIC_SOURCE_HEADERS")
    plot_site=defaultdict(set)
    plot_stand=defaultdict(set)
    site_stands=defaultdict(set)
    stand_sites=defaultdict(set)
    plot_stratum_years=defaultdict(lambda:defaultdict(set))
    plot_year_strata=defaultdict(set)
    plot_stratum_calendar_years=defaultdict(lambda:defaultdict(set))
    strata_years=defaultdict(set)
    time_value_shapes=set()
    noncanonical_time_rows=0
    all_sites=set()
    all_plots=set()
    all_stands=set()
    all_years=set()
    all_strata=set()
    missing=defaultdict(int)
    rows=0
    try:
        for row in reader:
            rows+=1
            if rows>MAX_RECORDS or len(row)!=SEMICOLON_FIELDS:
                raise MethodStop("SOURCE_STOP_METHOD_ROW_COUNT_OR_SHAPE")
            # Method-only read: no source fields other than those five positions
            # are ever accessed; source biological columns are not evaluated.
            d={k:row[i].strip() for k,i in ids.items()}
            for k,x in d.items():
                if not x:missing[k]+=1
            if any(not d[k] for k in d):
                continue
            site,stand,plot,layer,year=(d[k] for k in
                ("parent_site","stand_category","plot_unit","vertical_stratum","year"))
            all_sites.add(site);all_stands.add(stand);all_plots.add(plot)
            all_strata.add(layer);all_years.add(year)
            actual_year, time_shape=calendar_year_from_time_token(year)
            time_value_shapes.add(time_shape)
            if actual_year is None:
                noncanonical_time_rows+=1
            else:
                plot_stratum_calendar_years[plot][layer].add(actual_year)
            plot_site[plot].add(site)
            plot_stand[plot].add(stand)
            site_stands[site].add(stand)
            stand_sites[stand].add(site)
            plot_stratum_years[plot][layer].add(year)
            plot_year_strata[(plot,year)].add(layer)
            strata_years[layer].add(year)
    except csv.Error as e:raise MethodStop("SOURCE_STOP_AUTHOR_CSV_READER") from e
    summary["method_field_record_rows_scanned"]=rows
    summary["generic_field_missing_rows"]=dict(missing)
    if rows==0 or any(v>0 for v in missing.values()):
        summary["status"]="SOURCE_STOP_ORIGINAL_METHOD_FIELD_MISSING"
        return summary
    plot_three=[p for p,v in plot_stratum_years.items() if len(v)==3]
    year_intersection_sizes=[]
    for p in plot_three:
        sets=list(plot_stratum_years[p].values())
        year_intersection_sizes.append(len(set.intersection(*sets)))
    fully_calendar_interpretable=noncanonical_time_rows==0
    calendar_intersection_sizes=[]
    if fully_calendar_interpretable:
        for p in plot_three:
            sets=list(plot_stratum_calendar_years[p].values())
            calendar_intersection_sizes.append(len(set.intersection(*sets)))
    summary.update({
       "recognized_time_generic_field_name":safe_fields["year"][0],
       "source_time_field_all_tokens_unambiguously_calendar_parseable":fully_calendar_interpretable,
       "source_time_shapes_only_SORTED_NO_VALUES":sorted(time_value_shapes),
       "source_time_noncanonical_rows_count":noncanonical_time_rows,
       "source_plots_shared_calendar_year_three_layers":(
           sum(n>0 for n in calendar_intersection_sizes)
           if fully_calendar_interpretable else None),
       "calendar_year_source_support_DOES_NOT_IMPLY_EQUAL_TRAP_EFFORT":True,
       "source_named_parent_site_labels_count":len(all_sites),
       "source_named_stand_categories_count":len(all_stands),
       "source_named_plot_unit_labels_count":len(all_plots),
       "source_named_vertical_stratum_labels_count":len(all_strata),
       "source_named_year_token_count":len(all_years),
       "plot_labels_spanning_multiple_parent_site_ids":
         sum(len(v)!=1 for v in plot_site.values()),
       "plot_labels_spanning_multiple_stand_categories":
         sum(len(v)!=1 for v in plot_stand.values()),
       "parent_site_labels_with_exactly_five_stand_categories":
         sum(len(v)==5 for v in site_stands.values()),
       "stand_categories_present_at_exactly_eight_parent_sites":
         sum(len(v)==8 for v in stand_sites.values()),
       "distinct_plot_labels_with_three_vertical_labels_any_year":len(plot_three),
       "distinct_plot_labels_with_AT_LEAST_ONE_same_year_all_three_layers":
         sum(n>=1 for n in year_intersection_sizes),
       "source_plot_year_combinations_with_three_vertical_labels":
         sum(len(v)==3 for v in plot_year_strata.values()),
       "source_plot_year_combinations_total":len(plot_year_strata),
       "year_token_distinct_counts_per_vertical_label_SORTED_NO_LABELS":
         sorted(len(v) for v in strata_years.values()),
       "NO_year_tokens_original_plot_ids_species_abundances_printed":True,
       "NO_3layers_claimed_to_be_equal_trap_methods_or_effort":True,
    })
    if len(all_sites)!=8 or len(all_stands)!=5 or len(all_plots)!=40:
        summary["status"]="SOURCE_NAMED_FIELD_CARDINALITIES_DIFFER_FROM_AUTHORED_8x5x40"
    elif summary["plot_labels_spanning_multiple_parent_site_ids"]!=0 or (
        summary["plot_labels_spanning_multiple_stand_categories"]!=0):
        summary["status"]="SOURCE_SITE_STAND_PLOT_KEY_NESTING_COLLISION_STOP"
    elif summary["parent_site_labels_with_exactly_five_stand_categories"]!=8 or (
        summary["stand_categories_present_at_exactly_eight_parent_sites"]!=5):
        summary["status"]="SOURCE_AUTHOR_8SITE_FIVE_STAND_CROSS_PRODUCT_INCOMPLETE"
    elif summary["distinct_plot_labels_with_three_vertical_labels_any_year"]!=40:
        summary["status"]="SOURCE_ALL_PLOTS_THREE_LAYER_COVERAGE_INCOMPLETE"
    elif not fully_calendar_interpretable:
        summary["status"]="SOURCE_NAMED_NESTING_SUPPORTED_TIME_LABELS_NOT_PROVEN_CALENDAR_YEAR"
    elif sum(n>0 for n in calendar_intersection_sizes)==0:
        summary["status"]="SOURCE_NAMED_NESTING_SUPPORTED_NO_SAME_CALENDAR_YEAR_THREE_LAYER_SUPPORT"
    else:
        summary["status"]="SOURCE_NAMED_8SITE_5STAND_40PLOT_NESTING_SUPPORTED_CALENDAR_YEAR_GATE_RECORDED"
    return summary

def original_source_gate():
    summary={"source_original_DOI":DOI,"status":"SOURCE_UNSCORED",
             "NO_species_or_guild_numeric_outcomes_accessed_or_scored":True,
             "NO_original_2024_canopy_source_file_opened":True}
    try:
        files=metadata_source_files()
        heads=[head_shape(f["file_id"]) for f in files]
        idx17=[i for i,h in enumerate(heads) if h["header_column_count"]==17
               and h["header_delimiter_category"]=="semicolon"]
        idx3=[i for i,h in enumerate(heads) if h["header_column_count"]==3
               and h["header_delimiter_category"]=="tab"]
        if len(idx17)!=1 or len(idx3)!=1:
            raise MethodStop("SOURCE_STOP_2026_ORIGINAL_17x3_HEADER_STRUCTURE_DRIFT")
        f=files[idx17[0]]
        raw=get_one_original_publisher_file(f["file_id"],f["expected_size"])
        # Source method extraction only. Checksum verified in preceding stage.
        summary["result"]=audit_source_method_rows(raw,f.get("published_checksum"))
        summary["status"]=summary["result"]["status"]
    except MethodStop as e:
        summary["status"]=str(e)
        summary["source_STOP_not_biological_null"]=True
    return summary

def known_truth():
    cols=["Site","Stand","Plot","Layer","Year","Species","Guild","Abundance"]
    cols += ["X"+str(i) for i in range(17-len(cols))]
    def row(site,stand,plot,layer,year,count):
        return ";".join([site,stand,plot,layer,year,"protected_taxon",
                         "protected_trait",str(count)]+["0"]*9)
    tx="\n".join([";".join(cols),
       row("A","B","P1","floor","2019",111),
       row("A","B","P1","canopy","2019",222),
       row("A","B","P1","subcanopy","2019",333),
       row("A","S","P2","floor","2019",444),
       row("A","S","P2","canopy","2020",555),
       row("A","S","P2","subcanopy","2021",666)])+"\n"
    a=audit_source_method_rows(tx.encode())
    assert a["method_field_record_rows_scanned"]==6
    assert a["source_named_parent_site_labels_count"]==1
    assert a["source_named_plot_unit_labels_count"]==2
    assert a["distinct_plot_labels_with_three_vertical_labels_any_year"]==2
    assert a["distinct_plot_labels_with_AT_LEAST_ONE_same_year_all_three_layers"]==1
    assert a["source_plots_shared_calendar_year_three_layers"]==1
    assert a["source_time_field_all_tokens_unambiguously_calendar_parseable"]
    assert calendar_year_from_time_token("2019-01-31")==("2019","VALID_ISO_DATE")
    assert calendar_year_from_time_token("2019-02-31")[0] is None
    assert calendar_year_from_time_token("Spring 2019")[0] is None
    assert role_positions(["site","stand","plot","stratum","period"])[0]["year"]==[4]
    assert a["source_plot_year_combinations_with_three_vertical_labels"]==1
    assert "protected_taxon" not in json.dumps(a)
    assert "111" not in json.dumps(a)
    assert a["status"]=="SOURCE_NAMED_FIELD_CARDINALITIES_DIFFER_FROM_AUTHORED_8x5x40"
    cols[0]="NoSiteRole"
    b=audit_source_method_rows((";".join(cols)+"\n").encode())
    assert b["status"]=="AUTHOR_METHOD_FIELD_ROLE_UNRESOLVED"
    token_test=(";".join(["site","stand","plot","stratum","period"]+["X"+str(i) for i in range(12)])+"\n"+
                ";".join(["A","B","P1","floor","Spring 2019"]+["0"]*12)+"\n")
    x=audit_source_method_rows(token_test.encode())
    assert x["source_time_noncanonical_rows_count"]==1
    assert x["source_plots_shared_calendar_year_three_layers"] is None
    print("SYNTHETIC_AUTHOR_NAMED_8x5x40_NESTING_AND_TIME_TOKEN_YEAR_SEMANTICS_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out needed")
    out={
      "schema":"structural.Piccini2026_original_named_site_stand_layer_year_sourceonly.v1",
      "protocol":"docs/FOREST_BEETLE_PICCINI2026_TIME_FIELD_STRICT_SOURCE_AUDIT_PRESPEC_20261116.md",
      "original_source":original_source_gate(),
      "no_new_biological_beta_or_p_or_guild_effect":True,
      "prior_Thai_Finland_PREDICTS_NEON_BALA_GEB_originals_SEALED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Piccini2026_named_site_stand_layer_year_original_sourceonly.json").write_text(
       json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
