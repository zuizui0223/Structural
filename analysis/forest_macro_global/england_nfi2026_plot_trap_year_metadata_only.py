#!/usr/bin/env python3
"""NFI England 2023–26 source-only Plot_ID × Trap_type × Year metadata audit.

Before any biological observations, inspect ONLY the author's original
24-field sample metadata CSV. The 328-field OTU CSV remains sealed.
All site/sample/pseudogeography IDs, dates and records remain private
to a single GitHub Actions runner; only anonymous aggregates are emitted.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import re
import statistics
import tempfile
import urllib.error
import zipfile

from england_nfi2026_canopy_subcanopy_source_gate import (
    SOURCE_UUID, retrieve_original, SourceStop,
)

PRESPEC = "docs/FOREST_NFI_ENGLAND_2026_AUTHOR_PLOT_TRAP_YEAR_METADATA_ONLY_PRESPEC_20261119.md"
ORIGINAL_BYTES = 486883
ORIGINAL_SHA256 = "ce3a21377238cc87bde7683917f59a771d20f8e24e81ddf47915362b92281ff4"
AUTHOR_FIELDS = (
    "Sample_ID", "Plot_ID", "Trap_type", "Trap_letter", "Year",
    "Surveyor_station", "DBH_cm", "Trap_height_m", "Tree_species",
    "Sample_sequenced", "Delocation_unique_ID", "NFI_region",
    "SW_x_coordinates", "SW_y_coordinates", "NE_x_coordinates",
    "NE_y_coordinates", "Area_ha",
    "Activation_1_date", "Collection_1_date",
    "Activation_2_date", "Collection_2_date",
    "Activation_3_date", "Collection_3_date", "Comment_collection",
)
NO_SEMANTIC_ACCESS = (
    "SW_x_coordinates", "SW_y_coordinates",
    "NE_x_coordinates", "NE_y_coordinates", "Comment_collection",
)
METHODS = ("Lindgren", "Malaise", "Other", "Missing")
YEARS = ("2023", "2024", "2025", "2026", "other_4digit", "unparseable")
SOURCE_ONLY = "SOURCE_NFI_ENGLAND_2026_ORIGINAL_PLOT_TRAP_YEAR_METADATA_ONLY_PASS"

def token(v):
    return str(v or "").strip()

def method_label(raw):
    val = token(raw).casefold()
    if not val:
        return "Missing"
    l = re.search(r"(?<![a-z])lindgren(?![a-z])", val) is not None
    m = re.search(r"(?<![a-z])malaise(?![a-z])", val) is not None
    return "Lindgren" if l and not m else "Malaise" if m and not l else "Other"

def numeric(s):
    raw = token(s)
    if raw.casefold() in ("", "na", "nan", "n/a", "null", "-999"):
        return None
    try:
        v = float(raw)
    except (ValueError, TypeError, OverflowError):
        return None
    return v if math.isfinite(v) and v >= 0 else None

def source_year(s):
    raw=token(s)
    if re.fullmatch(r"[0-9]{4}", raw) is None:
        return None, "unparseable"
    return raw, raw if raw in YEARS else "other_4digit"

def sequenced(s):
    raw = token(s).casefold().replace("_", " ").replace("-", " ")
    if raw in ("yes","y","true","1","sequenced","pass"):
        return "yes"
    if raw in ("no","n","false","0","not sequenced"):
        return "no"
    return "unknown"

def source_date(s):
    raw=token(s)
    if not raw or raw.casefold() in ("na", "n/a", "null", "none", "-999"):
        return None
    # Predeclared ISO and European formats, no US month/day ambiguity.
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
    return None

def intervals_and_quality(row):
    intervals=[]
    counts=Counter()
    for i in (1,2,3):
        a=token(row[f"Activation_{i}_date"])
        b=token(row[f"Collection_{i}_date"])
        if not a and not b:
            counts["blank_phase"]+=1
            continue
        if not a or not b:
            counts["incomplete_phase"]+=1
            continue
        aa,bb=source_date(a),source_date(b)
        if aa is None or bb is None:
            counts["unparseable_phase"]+=1
            continue
        days=(bb-aa).days
        if days <= 0 or days > 180:
            counts["nonpositive_or_over180day_phase"]+=1
            continue
        intervals.append((aa,bb))
        counts["valid_deployment_phase"]+=1
    return intervals,counts

def overlap(a,b):
    return any(x[0]<=y[1] and y[0]<=x[1] for x in a for y in b)

def summarise_numeric(vals):
    return {
        "valid_nonnegative_numeric_rows":len(vals),
        "observed_min":min(vals) if vals else None,
        "observed_median":statistics.median(vals) if vals else None,
        "observed_max":max(vals) if vals else None,
    }

def inspect_original(file:Path):
    with zipfile.ZipFile(file,"r") as z:
        infos=[x for x in z.infolist() if not x.is_dir()]
        if len(infos)!=2 or any(not x.filename.lower().endswith(".csv") for x in infos):
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_TWO_CSV_ENTRIES_CHANGED")
        metadata=None
        seen=[]
        for info in infos:
            with z.open(info) as f:
                first=f.readline(8*1024*1024+1)
            if len(first)>8*1024*1024 or b"\n" not in first:
                raise SourceStop("SOURCE_NFI2026_FIRST_HEADER_INVALID")
            try:
                names=next(csv.reader([first.decode("utf-8-sig").rstrip("\r\n")],strict=True))
            except (UnicodeDecodeError,csv.Error,StopIteration):
                raise SourceStop("SOURCE_NFI2026_FIRST_HEADER_CSV_PARSE_STOP") from None
            seen.append(len(names))
            if len(names)==24:
                if tuple(names)!=AUTHOR_FIELDS:
                    raise SourceStop("SOURCE_NFI2026_AUTHOR_24_FIELD_ORDER_DRIFT")
                metadata=info
        if sorted(seen)!=[24,328] or metadata is None:
            raise SourceStop("SOURCE_NFI2026_AUTHOR_FIELD_TABLE_FRAME_DRIFT")
        # The 328-column taxonomic response table remains COMPLETELY SEALED
        # below its first-line width. No taxon/value record is read.
        with z.open(metadata) as binary:
            with io.TextIOWrapper(binary,encoding="utf-8-sig",newline="") as stream:
                reader=csv.DictReader(stream,delimiter=",",strict=True)
                if tuple(reader.fieldnames or ())!=AUTHOR_FIELDS:
                    raise SourceStop("SOURCE_NFI2026_SOURCE_CSV_METADATA_HEADER_DRIFT")
                return summarise_rows(reader)

def summarise_rows(rows):
    n=0
    unique_sample=set()
    sample_id_blank=0
    duplicate_sample=0
    method_counts=Counter()
    year_counts=Counter()
    method_year_counts=defaultdict(Counter)
    seq_counts=Counter()
    seq_by_method=defaultdict(Counter)
    height_by_method=defaultdict(list)
    dbh_by_method=defaultdict(list)
    height_invalid=Counter()
    dbh_invalid=Counter()
    tree_by_method=defaultdict(set)
    tree_present=Counter()
    named_region=set()
    field_plots=set()
    plot_regions=defaultdict(set)
    delocation_labels=set()
    location_missing=Counter()
    siteyear=defaultdict(list)
    year_valid=0
    sampling_phase_quality=Counter()
    n_with_valid_deployment=0
    station_present=Counter()
    plot_year_sample_counts=Counter()
    for row in rows:
        n+=1
        if n>100000:
            raise SourceStop("SOURCE_NFI2026_UNEXPECTED_METADATA_OVER100K_ROWS")
        if None in row or set(row)!=set(AUTHOR_FIELDS):
            raise SourceStop("SOURCE_NFI2026_METADATA_ROW_COLUMN_COUNT_DRIFT")
        # Important: raw coordinate and free-text comment CSV transport columns
        # are parsed by DictReader, but are NEVER referenced or interpreted.
        sid=token(row["Sample_ID"])
        if not sid:sample_id_blank+=1
        elif sid in unique_sample:duplicate_sample+=1
        else:unique_sample.add(sid)
        region=token(row["NFI_region"])
        plot=token(row["Plot_ID"])
        year,year_bin=source_year(row["Year"])
        if year:year_valid+=1
        method=method_label(row["Trap_type"])
        is_seq=sequenced(row["Sample_sequenced"])
        method_counts[method]+=1
        year_counts[year_bin]+=1
        method_year_counts[year_bin][method]+=1
        seq_counts[is_seq]+=1
        seq_by_method[method][is_seq]+=1
        for label,container,errors,column in (
            ("trap_height",height_by_method,height_invalid,"Trap_height_m"),
            ("DBH",dbh_by_method,dbh_invalid,"DBH_cm"),
        ):
            value=numeric(row[column])
            if value is None:
                errors[method]+=1
            else:
                container[method].append(value)
        tree=token(row["Tree_species"])
        if tree:
            tree_by_method[method].add(tree)
            tree_present[method]+=1
        if region:named_region.add(region)
        else:location_missing["NFI_region"]+=1
        if not plot:location_missing["Plot_ID"]+=1
        if region and plot:
            field_plots.add((region,plot))
            plot_regions[plot].add(region)
        deloc=token(row["Delocation_unique_ID"])
        if deloc:delocation_labels.add(deloc)
        else:location_missing["Delocation_unique_ID"]+=1
        station=token(row["Surveyor_station"])
        if station:station_present[method]+=1
        windows,phases=intervals_and_quality(row)
        sampling_phase_quality.update(phases)
        if windows:n_with_valid_deployment+=1
        if region and plot and year and method in ("Lindgren","Malaise"):
            siteyear[(region,plot,year)].append({
                "method":method, "intervals":windows,
                "sequenced":is_seq=="yes",
                "station":station,"tree":tree,
                "height":numeric(row["Trap_height_m"]),
            })
            plot_year_sample_counts[(region,plot,year)]+=1
    if not n:
        raise SourceStop("SOURCE_NFI2026_ZERO_METADATA_RECORDS")
    # Counts only: no author plot/region/sample/delocation strings exported.
    paired=0
    concurrent=0
    sequenced_paired=0
    sequenced_concurrent=0
    paired_stations=0
    paired_trees=0
    paired_height_both=0
    paired_height_lindgren_above_malaise=0
    pair_regions=defaultdict(set)
    paired_per_region=Counter()
    for (region,plot,year),entries in siteyear.items():
        l=[x for x in entries if x["method"]=="Lindgren"]
        m=[x for x in entries if x["method"]=="Malaise"]
        if not l or not m:continue
        paired+=1
        paired_per_region[region]+=1
        pair_regions[region].add((plot,year))
        if any(overlap(a["intervals"],b["intervals"]) for a in l for b in m):
            concurrent+=1
        if any(x["sequenced"] for x in l) and any(x["sequenced"] for x in m):
            sequenced_paired+=1
        if any(a["sequenced"] and b["sequenced"] and overlap(a["intervals"],b["intervals"])
               for a in l for b in m):
            sequenced_concurrent+=1
        if {x["station"] for x in l if x["station"]} & {x["station"] for x in m if x["station"]}:
            paired_stations+=1
        if {x["tree"] for x in l if x["tree"]} & {x["tree"] for x in m if x["tree"]}:
            paired_trees+=1
        h_l=[x["height"] for x in l if x["height"] is not None]
        h_m=[x["height"] for x in m if x["height"] is not None]
        if h_l and h_m:
            paired_height_both+=1
            if min(h_l)>max(h_m):
                paired_height_lindgren_above_malaise+=1
    plot_size_by_region=Counter()
    for r,p in field_plots:
        plot_size_by_region[r]+=1
    report={
        "schema":"structural.england_NFI2026_original_metadata_plot_trap_year.v1",
        "original_24column_metadata_rows":n,
        "source_sample_id_unique_nonblank_count":len(unique_sample),
        "source_sample_id_blank_rows":sample_id_blank,
        "source_sample_id_duplicate_record_rows":duplicate_sample,
        "source_year_parsed_four_digit_rows":year_valid,
        "source_year_original_row_histogram":{k:year_counts[k] for k in YEARS},
        "source_trap_type_frozen_token_class_histogram":{k:method_counts[k] for k in METHODS},
        "source_trap_method_by_year":{
            k:{x:method_year_counts[k][x] for x in METHODS} for k in YEARS
        },
        "source_sample_sequenced_label_counts":{k:seq_counts[k] for k in ("yes","no","unknown")},
        "source_sequenced_label_by_method":{
            method:{k:seq_by_method[method][k] for k in ("yes","no","unknown")}
            for method in METHODS
        },
        "source_trap_height_m_original_numerical_summary_by_method":{
            k:summarise_numeric(height_by_method[k]) for k in METHODS
        },
        "source_DBH_cm_original_numerical_summary_by_method":{
            k:summarise_numeric(dbh_by_method[k]) for k in METHODS
        },
        "source_trap_height_missing_or_invalid_by_method":{k:height_invalid[k] for k in METHODS},
        "source_DBH_missing_or_invalid_by_method":{k:dbh_invalid[k] for k in METHODS},
        "source_associated_tree_species_present_rows_by_method":{k:tree_present[k] for k in METHODS},
        "source_associated_tree_species_distinct_label_n_by_method":{
            k:len(tree_by_method[k]) for k in METHODS
        },
        "source_unique_original_region_labels":len(named_region),
        "source_original_region_plotID_unique_candidate_keys":len(field_plots),
        "source_duplicated_plotID_string_across_regions":sum(len(x)>1 for x in plot_regions.values()),
        "source_unique_delocation_group_labels_NOT_PLOT_KEYS":len(delocation_labels),
        "source_key_missing_rows":{k:location_missing[k] for k in
                                   ("NFI_region","Plot_ID","Delocation_unique_ID")},
        "source_original_region_candidate_plot_counts_ANONYMOUS_SORTED":
            sorted(plot_size_by_region.values()),
        "source_4digit_year_region_plot_candidate_groups_with_known_method":len(siteyear),
        "source_candidates_plot_year_BOTH_methods":paired,
        "source_candidates_plot_year_BOTH_methods_same_deployment_overlap":concurrent,
        "source_candidates_plot_year_BOTH_methods_both_sample_sequenced_yes":sequenced_paired,
        "source_candidates_plot_year_BOTH_methods_both_yes_AND_overlapping_deployment":sequenced_concurrent,
        "source_candidates_plot_year_both_method_shared_Surveyor_station_label":paired_stations,
        "source_candidates_plot_year_both_method_shared_associated_Tree_species_label":paired_trees,
        "source_candidates_plot_year_both_trap_height_numeric":paired_height_both,
        "source_candidates_plot_year_lindgren_all_heights_above_malaise":paired_height_lindgren_above_malaise,
        "source_region_n_with_candidate_both_method_plot_year":len(paired_per_region),
        "source_original_candidate_both_method_plot_year_count_per_region_ANONYMOUS_SORTED":
            sorted(paired_per_region.values()),
        "source_rows_with_at_least_one_valid_deployment_interval":n_with_valid_deployment,
        "source_deployment_1to3_phase_diagnostics":dict(sorted(sampling_phase_quality.items())),
        "source_surveryor_station_field_present_rows_by_method":{
            k:station_present[k] for k in METHODS
        },
        "original_328col_OTU_species_biological_table_data_rows_READ":0,
        "original_metadata_24col_records_READ":n,
        "original_site_species_sample_coordinates_dates_raw_values_EXPORTED":False,
        "original_metadata_coordinate_and_comment_columns_NOT_SEMANTICALLY_USED":True,
        "source_delocation_is_NOT_original_physical_plot":True,
        "source_Plot_ID_physical_unit_author_method_CERTIFIED":False,
        "source_Lindgren_canopy_vs_Malaise_subcanopy_TRAP_METHOD_CONFOUNDED":True,
        "source_trap_dates_are_EFFORT_OPPORTUNITY_NOT_TAXON_RESPONSE":True,
        "new_biodiversity_effects_estimated":False,
    }
    if not (len(field_plots)>0 and year_valid>0 and
            method_counts["Lindgren"]+method_counts["Malaise"]>0):
        report["status"]="SOURCE_NFI2026_ORIGINAL_SITE_METHOD_YEAR_ADMISSION_HOLD"
    else:
        report["status"]=SOURCE_ONLY
    return report

def known_truth():
    assert method_label("Lindgren funnel")=="Lindgren"
    assert method_label("Canopy LINdgren trap")=="Lindgren"
    assert method_label("malaise")=="Malaise"
    assert method_label("Malaise-Lindgren")=="Other"
    assert method_label("aerial")=="Other"
    assert method_label("")=="Missing"
    assert sequenced("No")=="no" and sequenced("TRUE")=="yes"
    assert source_year("2024.0")== (None,"unparseable")
    assert source_date("2024-06-10")==dt.date(2024,6,10)
    assert source_date("10/06/2024")==dt.date(2024,6,10)
    assert overlap([(dt.date(2024,6,1),dt.date(2024,6,10))],
                   [(dt.date(2024,6,10),dt.date(2024,6,20))])
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/"synthetic.zip"
        def record(sample,plot,typ,tree,seq,station,start,end):
            row={k:"" for k in AUTHOR_FIELDS}
            row.update({"Sample_ID":sample,"Plot_ID":plot,"Trap_type":typ,
               "Trap_letter":"A", "Year":"2024","Surveyor_station":station,
               "DBH_cm":"43","Trap_height_m":"12" if "Lindgren" in typ else "2",
               "Tree_species":tree, "Sample_sequenced":seq,
               "Delocation_unique_ID":"PRIVATE_GEO_CELL", "NFI_region":"PRIVATE_REGION",
               "Activation_1_date":start,"Collection_1_date":end,
               "SW_x_coordinates":"MOST_PRIVATE_RAW_COORD"})
            return row
        data=[
          record("PRIVATE_SAMPLE_L","PRIVATE_PLOT_A","Lindgren","oak","yes","siteA","2024-06-01","2024-06-20"),
          record("PRIVATE_SAMPLE_M","PRIVATE_PLOT_A","Malaise","oak","yes","siteA","2024-06-10","2024-06-25"),
          record("PRIVATE_SAMPLE_O","PRIVATE_PLOT_B","Lindgren","pine","no","siteB","2024-07-01","2024-07-15"),
        ]
        mem=io.StringIO(newline="")
        w=csv.DictWriter(mem,fieldnames=list(AUTHOR_FIELDS))
        w.writeheader();w.writerows(data)
        with zipfile.ZipFile(f,"w") as z:
            z.writestr("private_sampling.csv",mem.getvalue())
            z.writestr("PRIVATE_biodiversity.csv",",".join(f"Taxon_{i}" for i in range(328))+"\nPRIVATE_SPECIES_RESPONSE,9999\n")
        x=inspect_original(f)
        assert x["status"]==SOURCE_ONLY
        assert x["original_24column_metadata_rows"]==3
        assert x["source_original_region_plotID_unique_candidate_keys"]==2
        assert x["source_candidates_plot_year_BOTH_methods"]==1
        assert x["source_candidates_plot_year_BOTH_methods_same_deployment_overlap"]==1
        assert x["source_candidates_plot_year_BOTH_methods_both_yes_AND_overlapping_deployment"]==1
        assert x["source_candidates_plot_year_both_method_shared_Surveyor_station_label"]==1
        assert x["source_candidates_plot_year_lindgren_all_heights_above_malaise"]==1
        s=json.dumps(x)
        for private in ("PRIVATE_SAMPLE","PRIVATE_PLOT","PRIVATE_REGION","PRIVATE_GEO_CELL",
                        "MOST_PRIVATE_RAW_COORD","PRIVATE_SPECIES_RESPONSE"):
            assert private not in s
    print("SYNTHETIC_NFI2026_PLOT_TRAP_YEAR_METADATA_ONLY_AND_RESPONSE_SEAL_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:parser.error("--out required")
    result={
        "schema":"structural.england_NFI2026_original_24col_method_metadata_source.v1",
        "precommit":PRESPEC,
        "original_source_official_UUID":SOURCE_UUID,
        "expected_archive_bytes":ORIGINAL_BYTES,
        "expected_archive_sha256":ORIGINAL_SHA256,
        "original_328col_OTU_response_rows_OPENED":0,
        "original_24col_sample_metadata_values_allowed_for_source_only":True,
        "original_coordinates_or_sample_ID_values_output":False,
        "Lindgren_canopy_Malaise_subcanopy_vertical_effect_NONIDENTIFIABLE":True,
        "all_old_Finland_Carpathian_Chiu_PREDICTS_Thai_NEON_BALA_GEB_scoring_UNCHANGED":True,
        "eBird_used":False,"TinyFish_used":False,
        "new_biodiversity_effect_scored":False,
    }
    with tempfile.TemporaryDirectory() as d:
        original=Path(d)/"publisher_original.zip"
        try:
            n,sha,_=retrieve_original(original)
            if n!=ORIGINAL_BYTES or sha!=ORIGINAL_SHA256:
                raise SourceStop("SOURCE_NFI2026_FROZEN_ORIGINAL_SOURCE_FINGERPRINT_DRIFT")
            result["source_original_metadata_diagnostics_ANONYMOUS_ONLY"]=inspect_original(original)
            result["status"]=result["source_original_metadata_diagnostics_ANONYMOUS_ONLY"]["status"]
        except (SourceStop,urllib.error.URLError,TimeoutError,OSError,
                UnicodeError,ValueError,csv.Error,zipfile.BadZipFile) as exc:
            if isinstance(exc,SourceStop):result["status"]=str(exc)
            else:result["status"]="SOURCE_NFI2026_ORIGINAL_METADATA_READ_OR_TRANSPORT_STOP"
            result["source_STOP_no_biological_response_or_candidate_effects"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"England_NFI2026_original_plot_method_year_metadata_only.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("ORIGINAL_ENGLAND_NFI2026_SAMPLE_METADATA_GATE",result["status"])
    print("OTU_328COL_RESPONSE_BODY_NOT_OPENED; NO_ECOLOGICAL_EFFECT")
if __name__=="__main__":main()
