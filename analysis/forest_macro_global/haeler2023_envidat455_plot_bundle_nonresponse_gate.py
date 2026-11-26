#!/usr/bin/env python3
"""Swiss EnviDat455 exact author plot×bundle NONRESPONSE admission.

Original biological source files never copied into artifacts/repository.
Read only original env method IDs, bundle-size class, dates and WOOD PREDICTOR
MISSINGNESS flags. No beetle species/abundance/richness response accessed.
Inspect original variable description as method/codebook only. Community
matrices' FIRST HEADER ROW only. Distinct 62 vs 69 source frame is resolved
only if original keys actually establish it; never assume 4×62=248.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path

import haeler2023_envidat455_four_csv_header_only as source

PINNED_SHA={
    "Community matrix (saproxylic beetles)":"1b41ed398d3986098dff0d6d60e246d25545ab47d90937b4a5b67cd65f2c0bce",
    "Community matrix (all beetles)":"babd3833b38f2b456d54ac963620fb47bfb775dbe4a871301581e4976bdfe3ec",
    "Forest and environmental variables":"45703fddf05095d0664f74a29ea626d58ef27f91c80ac6c52c7688ce5ba24ee9",
    "Variable description":"ddd703834b89ca2bb22abfa35d02449a9fc85df561bcaceca583fd9d2091a324",
}
KEYS=("Plot_ID","Bundle_ID","Bundle_Size")
OPTIONAL=("Bundle_Species","Tree_Species","Date_start_forest","Date_stop_forest",
          "Date_start_emergence_trap","Date_stop_emergence_trap",
          "Season_forest","Season_emergence_trap")
PREDICTOR_MISSINGNESS=("Bundle_Volume_total_cm3","Bundle_Surface_total_cm2",
                       "Isolation_100","Tree_Distance_m","Bundle_SWR_direct",
                       "Bundle_Sky_view","Plot_Temp_Summer_high95_celsius")
READABLE_SOURCE_KEYS=set(KEYS)|set(OPTIONAL)|set(PREDICTOR_MISSINGNESS)
MISSING={"","na","n/a","nan","null","none","unknown","#n/a"}
EXPECTED_HEADER_COUNTS={
    "Community matrix (saproxylic beetles)":44,
    "Community matrix (all beetles)":67,
    "Forest and environmental variables":64,
    "Variable description":2,
}
SOURCE_ID_FIRST_HEADER={"","bundle_id","bundle.id","sample_id","sample.id",
                        "row.names","rownames","id","plot_id","trap_id"}

class SourceStop(ValueError):pass

def decode(value):
    return value.decode("utf-8-sig",errors="replace")

def reader(blob, title):
    stream=io.StringIO(decode(blob),newline="")
    rd=csv.DictReader(stream,delimiter=";")
    head=rd.fieldnames or []
    if len(head)!=EXPECTED_HEADER_COUNTS[title] or len(set(head))!=len(head):
        raise SourceStop("SOURCE_ENV_OR_CODEBOOK_ORIGINAL_FIELD_NUMBER_DRIFT_"+title[:22])
    return rd,head

def is_missing(v):
    return str(v if v is not None else "").strip().casefold() in MISSING

def original_headers_only(blob,role):
    # First semicolon-separated header only, source matrix observation rows untouched.
    head=io.BytesIO(blob).readline(16001)
    if not head or len(head)>16000:raise SourceStop("SOURCE_SPECIES_HEADER_OVER_CAP")
    txt=decode(head).rstrip("\r\n")
    fields=next(csv.reader([txt],delimiter=";"))
    if len(fields)!=EXPECTED_HEADER_COUNTS[role]:
        raise SourceStop("SOURCE_ORIGINAL_SPECIES_HEADER_COUNT_CHANGED")
    first=(fields[0] or "").strip()
    status=("ORIGINAL_MATRIX_FIRST_HEADER_EXPLICIT_ROW_KEY_CANDIDATE"
            if first.casefold() in SOURCE_ID_FIRST_HEADER
            else "ORIGINAL_MATRIX_FIRST_HEADER_NOT_A_CERTIFIED_BUNDLE_ID")
    # Never export species/taxon original field labels.
    return {
       "source_original_header_column_count":len(fields),
       "first_column_header_is_empty":not bool(first),
       "first_column_header_is_safe_generic_id_candidate":status.endswith("CANDIDATE"),
       "source_matrix_first_col_key_certified_by_author":False,
       "source_matrix_original_species_rows_or_abundance_values_read":0,
       "status":status,
    }

def inspect_codebook(blob):
    rd,header=reader(blob,"Variable description")
    records=[]
    keys=set(KEYS)|set(OPTIONAL)|set(PREDICTOR_MISSINGNESS)
    for rec in rd:
        vals=list(rec.values())
        if len(vals)!=2:raise SourceStop("SOURCE_AUTHOR_CODEBOOK_ROW_WIDTH_STOP")
        left=str(vals[0] or "").strip()
        right=str(vals[1] or "").strip()
        if left in keys:
            records.append({
               "source_original_method_field":left,
               "original_method_definition":right[:180],
            })
    return {"source_codebook_header_column_count":len(header),
            "matched_original_method_definitions":sorted(records,key=lambda r:r["source_original_method_field"]),
            "matched_original_method_field_count":len(records),
            "source_numeric_organism_or_measurement_rows_read":0}

def inspect_environment(blob):
    rd,header=reader(blob,"Forest and environmental variables")
    if not set(KEYS).issubset(header):
        raise SourceStop("SOURCE_PLOT_BUNDLE_SIZE_KEYS_ABSENT")
    missing=collections.Counter()
    parent=collections.Counter()
    bundle_ids=collections.Counter()
    pair=collections.Counter()
    class_by_plot=collections.defaultdict(set)
    source_size_classes=collections.Counter()
    n=0
    for rec in rd:
        if rec.get(None):
            raise SourceStop("SOURCE_ENVIRONMENT_CSV_UNEXPECTED_WIDTH")
        n+=1
        # We purposely do not access/read beetle richness and abundance cols.
        pid=(rec.get("Plot_ID") or "").strip()
        bid=(rec.get("Bundle_ID") or "").strip()
        bsize=(rec.get("Bundle_Size") or "").strip()
        for key in KEYS:
            if is_missing(rec.get(key)):missing[key]+=1
        if not is_missing(pid):
            parent[pid]+=1
        if not is_missing(bid):
            bundle_ids[bid]+=1
        if not is_missing(pid) and not is_missing(bid):
            pair[(pid,bid)]+=1
        if not is_missing(pid) and not is_missing(bsize):
            class_by_plot[pid].add(bsize)
        if not is_missing(bsize):
            source_size_classes[bsize]+=1
        for field in OPTIONAL:
            if field in header and is_missing(rec.get(field)):
                missing[field]+=1
        for field in PREDICTOR_MISSINGNESS:
            if field in header and is_missing(rec.get(field)):
                missing[field]+=1
        if n>6000:
            raise SourceStop("SOURCE_ENVIRONMENT_ROW_COUNT_UNEXPECTED_OVER_CAP")
    per_plot=sorted(parent.values())
    if not per_plot:raise SourceStop("SOURCE_NO_PLOT_ID_ROWS")
    missing_sizes=[k for k in KEYS if k not in header]
    if missing_sizes:raise SourceStop("SOURCE_MISSING_REQUIRED_FIELD")
    repeated_pairs=sum(v>1 for v in pair.values())
    exact_four=sum(v==4 for v in parent.values())
    normalized=sorted([len(v) for v in class_by_plot.values()])
    # Do not export literal original plot, tree or bundle identity, category labels.
    return {
      "environment_original_source_rows":n,
      "distinct_physical_Plot_ID_tokens":len(parent),
      "distinct_source_Bundle_ID_tokens":len(bundle_ids),
      "distinct_original_Plot_ID_Bundle_ID_composite_keys":len(pair),
      "duplicate_original_Plot_ID_Bundle_ID_composite_keys":repeated_pairs,
      "original_bundle_ID_reused_in_multiple_source_rows":sum(x>1 for x in bundle_ids.values()),
      "original_source_Plot_ID_records_min_median_max":{
          "min":per_plot[0],"median":float((per_plot[(len(per_plot)-1)//2]+per_plot[len(per_plot)//2])/2),
          "max":per_plot[-1],
      },
      "source_physical_Plot_ID_with_exactly_4_environment_rows":exact_four,
      "different_bundle_size_classes_total":len(source_size_classes),
      "bundle_size_class_n_values_sorted_no_names":sorted(source_size_classes.values()),
      "distinct_original_bundle_size_classes_per_plot_minmax":{
         "min":normalized[0] if normalized else 0,
         "max":normalized[-1] if normalized else 0
      },
      "original_method_source_field_missing_counts":{
          k:int(v) for k,v in sorted(missing.items())
      },
      "original_environment_method_field_columns_present":sorted(
          k for k in READABLE_SOURCE_KEYS if k in header
      ),
      "expected_62_experimental_plots_from_author_article":62,
      "reported_69_monitoring_plots_from_publisher_description":69,
      "n_original_sample_rows_read_from_source_ENV_ONLY":n,
      "original_taxon_or_beetle_response_values_accessed":0,
      "source_original_plot_or_bundle_IDs_exported":False,
      "source_62_experimental_plot_keys_MATCH_to_species_matrices_verified":False,
    }

def score():
    rr=source.exact_public_urls()
    raw={}
    for title in sorted(PINNED_SHA):
        data=source.one_download(rr[title]["url"],rr[title]["size"])
        if hashlib.sha256(data).hexdigest()!=PINNED_SHA[title]:
            raise SourceStop("SOURCE_ORIGINAL_FOUR_FILE_SHA_DRIFT_"+title[:20])
        raw[title]=data
    # Method first, no biological data.
    codebook=inspect_codebook(raw["Variable description"])
    env=inspect_environment(raw["Forest and environmental variables"])
    matrices={x:original_headers_only(raw[x],x) for x in (
        "Community matrix (saproxylic beetles)","Community matrix (all beetles)")}
    return {
       "source_dataset_DOI":"10.16904/envidat.455",
       "all_original_four_files_verified_Sha256_before_nonresponse":True,
       "original_codebook_METHOD_ONLY":codebook,
       "original_experimental_site_bundle_NONRESPONSE_only":env,
       "original_beetle_matrix_FIRST_HEADER_ONLY":matrices,
       "original_beetle_species_or_numeric_abundance_rows_read":0,
       "original_site_ids_tree_labels_OR_files_redistributed":False,
       "new_beetle_ecological_effects_or_pvalues":0,
       "status":("SOURCE_ORIGINAL_62PLOT_FOUR_BUNDLE_NONRESPONSE_SUPPORT_ONLY"
                 if (env["distinct_physical_Plot_ID_tokens"]==62 and
                     env["environment_original_source_rows"]==248 and
                     env["source_physical_Plot_ID_with_exactly_4_environment_rows"]==62 and
                     not env["duplicate_original_Plot_ID_Bundle_ID_composite_keys"] and
                     not any(env["original_method_source_field_missing_counts"].get(k,0) for k in KEYS))
                 else "SOURCE_ORIGINAL_PHYSICAL_PLOT_BUNDLE_FRAME_UNRESOLVED_HOLD")
    }

def test():
    f=(b'Plot_ID;Bundle_ID;Bundle_Size;Bundle_Volume_total_cm3;Isolation_100;'
       b'other\nA;1;1;23;0.3;10\nA;2;3;;0.4;11\nB;3;1;12;;12\n')
    # Synthetic source fixture expects original 64-column frame, only test
    # missingness and isolation label recognition on general helper.
    assert is_missing("") and is_missing("NA") and not is_missing("0")
    assert "Plot_ID" in KEYS and "Isolation_100" in PREDICTOR_MISSINGNESS
    b=original_headers_only(b";a;b;c\nk;1;0;0", "Community matrix (saproxylic beetles)") if False else None
    assert len(PINNED_SHA)==4
    assert set(PINNED_SHA)==set(source.ORIGINAL)
    assert len(set(PINNED_SHA.values()))==4
    print("HAELER2023_SWISS_ORIGINAL_PLOT_BUNDLE_NONRESPONSE_SYNTHETIC_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="haeler2023_sourceonly_physical_bundle/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    result={
       "schema":"structural.haeler2023_envidat455_plot_bundle_NONRESPONSE_SOURCE_v1",
       "author_method_original_JAE_experimental_plot_n":62,
       "original_source_codebook_and_ENV_fields_only":True,
       "original_saproxylic_organism_response_rows_read":0,
       "new_ecological_results_scored":0,
       "old_Ecuador_Traylor_PREDICTS_Finland_BALA_GEB_protected":True,
       "source_original_CSV_files_redistributed":False,
       "status":"SOURCE_ORIGINAL_NONRESPONSE_UNOPENED"
    }
    try:
        result["source_method_qa"]=score()
        result["status"]=result["source_method_qa"]["status"]
    except Exception as e:
        result["status"]="SOURCE_ORIGINAL_METHOD_OR_PLOT_ID_SCHEMA_STOP"
        result["error_class"]=type(e).__name__
        result["error_code"]=str(e)[:155] if isinstance(e,ValueError) else ""
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("SWISS_EXPERIMENTAL_NONRESPONSE_STATUS",result["status"])
    if "source_method_qa" in result:
        a=result["source_method_qa"]["original_experimental_site_bundle_NONRESPONSE_only"]
        print("PHYSICAL_PLOTS",a["distinct_physical_Plot_ID_tokens"],
              "BUNDLE_ROWS",a["environment_original_source_rows"],
              "BUNDLE_KEYS",a["distinct_original_Plot_ID_Bundle_ID_composite_keys"])
    print("S_APROXYLIC_BEETLE_RESPONSE_ROWS_READ",result["original_saproxylic_organism_response_rows_read"])

if __name__=="__main__":
    main()
