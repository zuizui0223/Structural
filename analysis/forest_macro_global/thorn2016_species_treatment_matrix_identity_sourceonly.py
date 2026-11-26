#!/usr/bin/env python3
"""Thorn 2016 original Babund/Bdist row/column species-label identity ONLY.

All raw source identifiers held in local runner RAM. Not one abundance/distance
cell is read for values, calculated, exported, or scored. No plot-level
experiment can be inferred from a species summary.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import re
from pathlib import Path
from thorn2016_bark_access_zenodo_source_only import (
    manifest,get_record,fetch_file,SourceStop)

EXPECTED={"Babund.csv":(4,120),"Bdist.csv":(121,120)}
LABEL_WHITELIST={
    "control","untreated","barkcontrol","scratch","scratched",
    "barkscratch","barkscratched","scratching","barkscratching",
    "debarked","debarking","debark","completelydebarked",
    "removedbark","barkremoved","fullydebarked"
}

def norm(s):
    return re.sub(r"[^a-z0-9]","",str(s).casefold())

def anonymous_first_column(raw,columns,rows):
    try:
        reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                          delimiter=",",strict=True)
        h=next(reader)
    except (UnicodeError,StopIteration,csv.Error) as exc:
        raise SourceStop("SOURCE_CSV_HEADER_PARSE_STOP") from exc
    if len(h)!=columns:
        raise SourceStop("SOURCE_ORIGINAL_COL_COUNT_DRIFT")
    keys=[];n=0;nonrect=0;blank=0
    try:
        for line in reader:
            n+=1
            if len(line)!=columns:
                nonrect+=1
                continue
            first=line[0].strip()
            if not first:blank+=1
            keys.append(first)
    except csv.Error as exc:
        raise SourceStop("SOURCE_ORIGINAL_CSV_RECTANGULARITY") from exc
    if n!=rows or nonrect or blank:
        raise SourceStop("SOURCE_ROW_COUNT_WIDTH_OR_IDENTIFIER_EMPTY")
    if len(set(keys))!=len(keys):
        raise SourceStop("SOURCE_REPEATED_SPECIES_ROW_IDENTIFIER_STOP")
    # Never export labels except explicitly fixed generic treatment names.
    return keys,h[1:],{
        "original_source_header_columns":len(h),
        "source_data_rows_excluding_header":n,
        "unique_nonempty_first_column_labels":len(set(keys)),
        "source_row_labels_NOT_EXPORTED":True,
        "source_numerical_data_cells_EVALUATED":0,
        "source_community_or_distance_coefficients_NOT_CALCULATED":True,
    }

def anonymous_comparison(bab,bheaders,bdist,dheaders):
    sa=set(bab);sd=set(bdist);sc=set(dheaders)
    treatment=[norm(x) for x in bheaders]
    return {
       "source_Babund_data_row_label_count":len(sa),
       "source_Bdist_data_row_label_count":len(sd),
       "source_Bdist_column_label_count_excluding_first_col":len(dheaders),
       "source_Babund_vs_Bdist_row_key_intersection_count":len(sa&sd),
       "source_Babund_vs_Bdist_column_key_intersection_count":len(sa&sc),
       "source_Bdist_row_vs_column_key_intersection_count":len(sd&sc),
       "source_Bdist_row_column_exact_same_key_set":sd==sc,
       "source_all_three_species_identifier_sets_match":sa==sd==sc,
       "source_Babund_and_Bdist_data_row_order_same":bab==bdist,
       "source_Bdist_row_and_column_order_same":bdist==dheaders,
       "source_three_nonkey_headers_treatment_name_whitelist_hits_only":
           sorted(set(t for t in treatment if t in LABEL_WHITELIST)),
       "source_unknown_nonkey_treatment_header_count":
           sum(t not in LABEL_WHITELIST for t in treatment),
       "all_source_row_and_column_species_labels_UNEXPORTED":True,
       "no_source_abundance_or_distance_matrix_numeric_cells_examined":True,
       "no_original_plot_treatment_year_explicit_response_rows_recovered":True,
    }

def original():
    out={"status":"SOURCE_DATA_RESPONSE_VALUES_UNSCORED",
         "original_beetle_abundance_values_NEVER_EVALUATED":True,
         "original_species_distance_values_NEVER_EVALUATED":True}
    try:
        publisher=manifest(get_record())
        source={x["name"]:x for x in publisher["original_two_files"]}
        out["original_publisher_MD5s_verified"]=True
        keys={};header={};shapes={}
        for name,(nc,nrows) in EXPECTED.items():
            body=fetch_file(source[name])
            k,h,s=anonymous_first_column(body,nc,nrows)
            keys[name]=k;header[name]=h;shapes[name]=s
        out["original_anonymous_shapes"]=shapes
        res=anonymous_comparison(
            keys["Babund.csv"],header["Babund.csv"],
            keys["Bdist.csv"],header["Bdist.csv"])
        out["original_anonymous_source_row_key_comparison"]=res
        if not res["source_all_three_species_identifier_sets_match"]:
            out["status"]="SOURCE_SPECIES_ROW_COLUMN_KEY_NOT_MATCHED_NO_PLOT_INFERENCE"
        elif res["source_unknown_nonkey_treatment_header_count"]>0:
            out["status"]="SOURCE_SPECIES_LEVEL_TREATMENT_SUMMARY_LIKELY_TREATMENT_KEY_UNVERIFIED"
        else:
            out["status"]="SOURCE_120_SPECIES_BY_3_TREATMENT_SUMMARY_AND_120_BY_120_LABELS_NO_12PLOT_RESPONSES"
    except SourceStop as exc:
        out["status"]=str(exc)
        out["SOURCE_STOP_NOT_BIOLOGICAL_NULL"]=True
    return out

def known_truth():
    bab=b"Species,Control,Bark-scratched,Debarked\nsp1,0,2,1\nsp2,5,0,1\n"
    dist=b"Species,sp1,sp2\nsp1,0,1.3\nsp2,1.3,0\n"
    b, bh, bs=anonymous_first_column(bab,4,2)
    d, dh, ds=anonymous_first_column(dist,3,2)
    x=anonymous_comparison(b,bh,d,dh)
    assert x["source_all_three_species_identifier_sets_match"]
    assert x["source_unknown_nonkey_treatment_header_count"]==0
    assert x["source_Bdist_row_column_exact_same_key_set"]
    assert bs["source_numerical_data_cells_EVALUATED"]==0
    assert ds["source_numerical_data_cells_EVALUATED"]==0
    assert "sp1" not in json.dumps(x)
    assert "1.3" not in json.dumps(x)
    bad=anonymous_comparison(b,bh,["sp1","sp3"],dh)
    assert not bad["source_all_three_species_identifier_sets_match"]
    print("SYNTHETIC_THORN2016_120_SPECIES_KEY_ALIGNMENT_AND_BIOLOGY_FIREWALL_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    obj={"schema":"structural.Thorn2016_original_120species_three_bark_treatments_source_grain.v1",
         "precommit":"docs/FOREST_BEETLE_THORN2016_AGGREGATE_SPECIES_TREATMENT_DISTANCE_IDENTITY_PRESPEC_20261117.md",
         "original":original(),
         "new_biodiversity_effect_or_p_calculated":False,
         "old_Piccini_Finland_Burner_Thai_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
         "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Thorn2016_120species_treatment_distance_source_grain.json").write_text(
        json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(obj,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
