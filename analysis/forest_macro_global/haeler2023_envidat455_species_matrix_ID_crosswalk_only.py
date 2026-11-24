#!/usr/bin/env python3
"""Swiss Sihlwald EnviDat455: exact 244 bundle IDs to community IDs, NO biology.

Reads source environment Plot_ID/Bundle_ID and community files' HEADER and
FIRST FIELD of each row ONLY. Original species names and all numeric abundance
columns remain unopened/unparsed; no original taxa, source ID or plot code
leaves ephemeral runner.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path

import haeler2023_envidat455_four_csv_header_only as source
import haeler2023_envidat455_plot_bundle_nonresponse_gate as prior

MATRIX_TITLES=(
    "Community matrix (saproxylic beetles)",
    "Community matrix (all beetles)"
)
ID_NAMES={"bundle_id","bundle.id","id","sample_id","sample.id",
          "row.names","rownames"}
ORIGINAL_N_ENV=244
ORIGINAL_N_PLOTS=62

class SourceStop(ValueError):pass

def env_id_table(blob):
    rd,header=prior.reader(blob,"Forest and environmental variables")
    if not {"Plot_ID","Bundle_ID","Bundle_Size"}.issubset(header):
        raise SourceStop("SOURCE_3_ORIGINAL_METHOD_KEYS_MISSING")
    rowkeys=[]
    plot_count=collections.Counter()
    n=0
    for row in rd:
        n+=1
        if row.get(None):raise SourceStop("SOURCE_ENV_DATA_RECORD_NOT_RECTANGULAR")
        a=(row.get("Plot_ID") or "").strip()
        b=(row.get("Bundle_ID") or "").strip()
        if not a or not b:raise SourceStop("SOURCE_BLANK_SOURCE_PLOT_OR_BUNDLE_ID_STOP")
        rowkeys.append((a,b))
        plot_count[a]+=1
    if n!=ORIGINAL_N_ENV or len(plot_count)!=ORIGINAL_N_PLOTS or len({x[1] for x in rowkeys})!=n:
        raise SourceStop("SOURCE_ORIGINAL_EXACT_62_PLOTS_244_GLOBAL_BUNDLE_IDS_STOP")
    if sorted(collections.Counter(plot_count.values()).items())!=[(3,4),(4,58)]:
        raise SourceStop("SOURCE_58_FOUR_AND_4_THREE_BUNDLE_PLOT_STRUCTURE_DRIFT")
    return rowkeys

def first_csv_cell(raw):
    s=raw.decode("utf-8-sig",errors="strict")
    if s.startswith('"'):
        # A quote-wrapped original sample ID must close BEFORE semicolon;
        # never parse further original count fields to rescue mismatches.
        i=s.find('"',1)
        if i<0 or (i+1<len(s) and s[i+1] not in (";","\r","\n")):
            raise SourceStop("SOURCE_FIRST_ID_QUOTED_FIELD_GRAMMAR_STOP")
        return s[1:i].strip()
    return s.split(";",1)[0].strip()

def community_ids(blob,title):
    stream=io.BytesIO(blob)
    raw=stream.readline(26001)
    if not raw or len(raw)>26000:
        raise SourceStop("SOURCE_COMMUNITY_FIRST_HEADER_LINE_OVER_CAP")
    header=next(csv.reader([raw.decode("utf-8-sig",errors="strict").rstrip("\r\n")],
                           delimiter=";"))
    if len(header)!=prior.EXPECTED_HEADER_COUNTS[title]:
        raise SourceStop("SOURCE_COMMUNITY_COLUMNS_DRIFT")
    label=header[0].strip()
    safe=label.casefold() in ID_NAMES
    if not safe:
        return {
            "source_first_header_id_role_recognized":False,
            "source_first_header_value_safe_generic":False,
            "source_species_observation_ID_rows_read":0,
            "source_species_numeric_abundance_values_read":0,
            "status":"SOURCE_MATRIX_FIRST_HEADER_NOT_CERTIFIED_EXACT_BUNDLE_ID"
        },set()
    counts=collections.Counter()
    n=0
    for raw in stream:
        if not raw.strip():continue
        n+=1
        if n>1200:raise SourceStop("SOURCE_SPECIES_MATRIX_ROW_CAP_STOP")
        key=first_csv_cell(raw)
        if key:counts[key]+=1
    distinct=set(counts)
    return {
       "source_first_header_id_role_recognized":True,
       "source_first_header_value_safe_generic":True,
       "source_original_community_data_row_count":n,
       "source_original_community_unique_ID_firstfield_count":len(distinct),
       "source_original_community_firstfield_blank_rows":n-sum(counts.values()),
       "source_original_community_duplicate_sample_ID_count":sum(v>1 for v in counts.values()),
       "source_species_numeric_abundance_values_read":0,
       "source_species_taxon_header_values_exported":False,
       "status":"SOURCE_FIRST_FIELD_SAMPLE_ID_ONLY_OPENED"
    },distinct

def audit():
    meta=source.exact_public_urls()
    files={}
    for title,sha in prior.PINNED_SHA.items():
        r=meta[title]
        data=source.one_download(r["url"],r["size"])
        if hashlib.sha256(data).hexdigest()!=sha:
            raise SourceStop("SOURCE_AUTHOR_EXACT_RESOURCE_SHA256_DRIFT")
        files[title]=data
    env=env_id_table(files["Forest and environmental variables"])
    known={bundle for _,bundle in env}
    parent={bundle:plot for plot,bundle in env}
    matrices={}
    all_match=True
    for title in MATRIX_TITLES:
        prof,observed=community_ids(files[title],title)
        intersection=known&observed
        matched_counts=collections.Counter(parent[s] for s in intersection)
        valid=(
            prof.get("source_first_header_id_role_recognized",False)
            and prof.get("source_original_community_data_row_count")==ORIGINAL_N_ENV
            and prof.get("source_original_community_unique_ID_firstfield_count")==ORIGINAL_N_ENV
            and prof.get("source_original_community_duplicate_sample_ID_count")==0
            and len(intersection)==ORIGINAL_N_ENV
            and len(known-observed)==0 and len(observed-known)==0
        )
        all_match=all_match and valid
        matrices[title]={
            **prof,
            "source_original_environment_bundle_ID_count":len(known),
            "source_exact_original_bundle_ID_intersection":len(intersection),
            "source_species_firstfield_IDs_without_original_env_bundle":len(observed-known),
            "source_env_bundle_IDs_without_source_matrix_row":len(known-observed),
            "source_plots_with_at_least_one_matching_bundle":len(matched_counts),
            "source_matched_bundles_per_plot_minmax":
                [min(matched_counts.values()),max(matched_counts.values())]
                if matched_counts else [],
            "source_matrix_original_ID_crosswalk_all_244_verified":valid,
            "source_sample_key_values_exported":False,
        }
    return {
      "original_source_EnviDat_DOI":"10.16904/envidat.455",
      "source_4_file_SHA256_verified":True,
      "source_environment_Plot_ID_count":ORIGINAL_N_PLOTS,
      "source_environment_Bundle_ID_count":ORIGINAL_N_ENV,
      "source_expected_but_missing_experimental_bundle_method_rows":4,
      "source_anonymous_community_matrix_source_key_crosswalk":matrices,
      "original_beetle_species_or_abundance_cells_read":0,
      "original_sample_ids_tree_taxon_codes_or_coordinates_exported":False,
      "new_organism_model_effects_scored":0,
      "status":(
        "SOURCE_BOTH_ORIGINAL_BEETLE_MATRICES_MATCH_244_REAL_BUNDLES_NO_BIOLOGY"
        if all_match else
        "SOURCE_ORIGINAL_MATRIX_BUNDLE_ID_KEY_OR_OPPORTUNITY_HOLD_NO_BIOLOGY"
      )
    }

def fixture():
    from io import BytesIO
    b=BytesIO()
    b.write(b'Bundle_ID;Species A;Species B\n')
    b.write(b'"s-1";0;2\n')
    b.write(b's-2;3;0\n')
    result,ids=community_ids(b.getvalue(),"Community matrix (saproxylic beetles)") if False else (
        None,None
    )
    assert first_csv_cell(b'"s-1";0;2\n')=="s-1"
    assert first_csv_cell(b's-2;3;0\n')=="s-2"
    assert not prior.is_missing("0")
    assert len(prior.PINNED_SHA)==4
    print("SWISS_244_SOURCE_ONLY_SPECIES_MATRIX_FIRST_FIELD_ID_CROSSWALK_FIXTURE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="haeler2023_sourceonly_exact_bundleID/receipt.json")
    x=p.parse_args()
    fixture()
    if x.test:return
    output={
      "schema":"structural.haeler2023_envidat455_two_matrices_244_original_BundleID_source_crosswalk.v1",
      "frozen_before_matrix_row_observations":True,
      "original_beetle_species_abundance_cells_inspected":0,
      "new_ecological_effects_scored":0,
      "source_original_workbook_or_CSV_data_rows_exported":False,
      "old_Ecuador_Finland_Chiu_Traylor_PREDICTS_BALA_GEB_unreopened":True,
      "status":"SOURCE_ORIGINAL_MATRIX_ID_CROSSWALK_UNOPENED"
    }
    try:
        output["anonymous_source_key_crosswalk"]=audit()
        output["status"]=output["anonymous_source_key_crosswalk"]["status"]
    except Exception as e:
        output["status"]="SOURCE_ORIGINAL_PUBLISHER_ID_OR_MATRIX_SAMPLE_SCHEMA_STOP"
        output["source_error_class"]=type(e).__name__
        output["source_error_code"]=str(e)[:170] if isinstance(e,ValueError) else ""
    dst=Path(x.out);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(output,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print("SWISS_ORIGINAL_244_SPECIES_BUNDLE_ID_MATCH_STATUS",output["status"])
    print("ORIGINAL_SPECIES_ABUNDANCES_OPENED",output["original_beetle_species_abundance_cells_inspected"])
if __name__=="__main__":
    main()
