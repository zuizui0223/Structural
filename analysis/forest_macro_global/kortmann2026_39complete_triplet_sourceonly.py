#!/usr/bin/env python3
"""Separate original method-only 39-complete-triplet subset after old 40-site HOLD.

The first diversity RData response-bearing object has already been deserialized
for schema. Only triplet/plot/treatment/offset method fields are read privately.
OTU matrix and other original biological members remain unopened.
"""
from __future__ import annotations
import argparse, hashlib, io, json, subprocess, tempfile, zipfile
from pathlib import Path
from kortmann2026_17775805_original_zip_directory_only import (
    SourceStop, original_file_metadata, official_get_one_zip, inspect_central_directory_only
)
PRESPEC="docs/FOREST_MACRO_KORTMANN_39COMPLETE_SOURCE_SCOPE_PREFREEZE_20261121.md"
SOURCE_MEMBER="data_public/diversity_satellite.rda"
SIZE=67238
SHA="8b3f47258b4d9c8f6fa0f7fac0d820ecccb860adadaa9c3c311f21fa28e3da3a"
R=Path(__file__).with_name("kortmann2026_39complete_triplet_sourceonly.R")
EXPECTED={
  "original_observed_rows",
  "original_distinct_triplets",
  "original_source_three_treatment_codes",
  "original_sampled_patches",
  "retained_complete_triplets",
  "excluded_incomplete_triplets",
  "retained_original_observed_rows",
  "excluded_triplet_observed_rows",
  "retained_sampled_patches",
  "retained_patches_with_six_records",
  "retained_patches_with_five_records",
  "retained_patch_samples_min",
  "retained_patch_samples_max",
  "retained_nominal_missing_rounds",
  "all_original_offsets_finite_numeric",
  "retained_treatment_count_sorted_first",
  "retained_treatment_count_sorted_second",
  "retained_treatment_count_sorted_third",
}
READY="SOURCE_39_COMPLETE_TRIPLETS_METHOD_READY_NO_OTU"
HOLD="SOURCE_39_TRIPLET_METHOD_HOLD"
MARKERS={
 "NO_SOURCE_SITE_TREATMENT_OR_OFFSET_VALUES_EXPORTED\t1",
 "NO_SPECIES_OTU_BIOLOGICAL_EFFECT_SCORED\t1",
 "ORIGINAL_40_TRIPLET_STRICT_GATE_STILL_HOLD\t1",
}

def parse(s):
    rows=s.strip().splitlines()
    if not rows or rows[0]!="KORTMANN_39_METHOD_V1":
        raise SourceStop("SOURCE_39_METHOD_OUTPUT_MAGIC_STOP")
    metrics={};status=None;markers=set()
    for row in rows[1:]:
        tokens=row.split("\t")
        if len(tokens)==3 and tokens[0]=="METRIC":
            name=tokens[1]
            if name not in EXPECTED or name in metrics or not tokens[2].isdigit():
                raise SourceStop("SOURCE_39_METHOD_FORBIDDEN_METRIC_OR_VALUE")
            metrics[name]=int(tokens[2])
        elif len(tokens)==2 and tokens[0]=="STATUS" and tokens[1] in (READY,HOLD):
            if status is not None: raise SourceStop("SOURCE_39_DUPLICATE_STATUS")
            status=tokens[1]
        elif row in MARKERS:
            markers.add(row)
        else:
            raise SourceStop("SOURCE_39_METHOD_UNEXPECTED_ORIGINAL_FIELD_EXPORTED")
    if set(metrics)!=EXPECTED or markers!=MARKERS or status is None:
        raise SourceStop("SOURCE_39_METHOD_FIELDS_OR_SAFETY_MARKERS_INCOMPLETE")
    if len(rows)!=len(EXPECTED)+5:
        raise SourceStop("SOURCE_39_METHOD_ROW_COUNT_INCONSISTENT")
    # Independent arithmetic from anonymous ORIGINAL method counts only:
    m=metrics
    if (
        m["original_observed_rows"]!=702 or
        m["original_distinct_triplets"]!=40 or
        m["original_source_three_treatment_codes"]!=3 or
        m["original_sampled_patches"]!=119 or
        m["retained_original_observed_rows"]+
            m["excluded_triplet_observed_rows"]!=702
    ):
        raise SourceStop("SOURCE_39_METHOD_ORIGINAL_POPULATION_DRIFT")
    if status==READY:
        if (
            m["retained_complete_triplets"]!=39 or
            m["excluded_incomplete_triplets"]!=1 or
            m["retained_sampled_patches"]!=117 or
            m["retained_patches_with_six_records"]+
                m["retained_patches_with_five_records"]!=117 or
            6*m["retained_patches_with_six_records"]+
                5*m["retained_patches_with_five_records"]!=
                m["retained_original_observed_rows"] or
            702-m["retained_original_observed_rows"] not in (10,11,12) or
            m["retained_nominal_missing_rounds"] !=
                702-m["retained_original_observed_rows"] or
            not (
              m["retained_treatment_count_sorted_first"]<=
              m["retained_treatment_count_sorted_second"]<=
              m["retained_treatment_count_sorted_third"]
            ) or
            sum(m[z] for z in (
              "retained_treatment_count_sorted_first",
              "retained_treatment_count_sorted_second",
              "retained_treatment_count_sorted_third")) !=
                m["retained_original_observed_rows"] or
            m["all_original_offsets_finite_numeric"]!=1
        ):
            raise SourceStop("SOURCE_39_METHOD_ANONYMOUS_COUNT_ARITHMETIC_FAILURE")
    return {
      "status":status,
      "anonymous_method_only_counts":m,
      "original_40_site_strict_gate_still_HOLD":True,
      "new_secondary_population_is_not_original_strict_40_site_pass":True,
      "source_RData_previously_deserialized_response_bearing":True,
      "no_original_sample_ID_treatment_label_or_offset_values_exported":True,
      "no_OTU_biology_opened_or_fitted":True,
      "original_sampling_round_identity_NOT_ESTABLISHED":True,
      "future_treatment_semantics_AND_coverage_NOT_VERIFIED":True,
    }

def call_r(args,test=False):
    try:
        p=subprocess.run(["Rscript","--vanilla",str(R)]+args,capture_output=True,
                         text=True,timeout=55,check=False)
    except (OSError,subprocess.TimeoutExpired):
        raise SourceStop("SOURCE_39_METHOD_RSCRIPT_UNAVAILABLE") from None
    if p.returncode!=0:
        raise SourceStop("SOURCE_39_METHOD_RSCRIPT_OUTPUT_STOP")
    if test:
        if p.stdout.strip()!="SYNTHETIC_KORTMANN_39_COMPLETE_SOURCE_ONLY_PASS":
            raise SourceStop("SOURCE_39_SYNTHETIC_MISMATCH")
        return
    return parse(p.stdout)

def synthetic():
    call_r(["--synthetic"],test=True)
    try:
        parse("KORTMANN_39_METHOD_V1\nMETRIC\tPRIVATE_ID\t1\n")
    except SourceStop:
        pass
    else:
        raise AssertionError("private field escaped source-only parser")
    print("SYNTHETIC_KORTMANN_SECONDARY_39_COMPLETE_METHOD_NO_BIOLOGY_PASS")

def run():
    url=original_file_metadata()
    b=official_get_one_zip(url)
    if inspect_central_directory_only(b)["status"]!="SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY":
        raise SourceStop("SOURCE_39_ORIGINAL_ZIP_AUTHENTICATION_FAILED")
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        item=z.getinfo(SOURCE_MEMBER)
        if item.file_size!=SIZE:
            raise SourceStop("SOURCE_39_SOURCE_MEMBER_SIZE_DRIFT")
        try:raw=z.read(SOURCE_MEMBER)
        except (OSError,zipfile.BadZipFile,KeyError):
            raise SourceStop("SOURCE_39_SOURCE_MEMBER_READ_STOP") from None
    if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:
        raise SourceStop("SOURCE_39_SOURCE_MEMBER_SHA_DRIFT")
    with tempfile.TemporaryDirectory(prefix="kortmann_39_source_frame_") as folder:
        file=Path(folder)/"diversity_satellite.rda"
        file.write_bytes(raw)
        out=call_r([str(file)])
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out required")
    result={
        "schema":"structural.Kortmann2026_39complete_triplets_source_method_v1",
        "prespec":PRESPEC,
        "original_strict_40_site_gate_HOLD_UNCHANGED":True,
        "previous_RData_source_schema_exposure_UNCHANGED":True,
        "original_OTU_matrix_member_requested":False,
        "new_ecological_effects_fitted":0,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        result["source"]=run()
        result["status"]=result["source"]["status"]
    except SourceStop as e:
        result["status"]="SOURCE_39_COMPLETE_METHOD_STOP_"+str(e)
        result["source_failure_NOT_biological_null"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("KORTMANN_39_COMPLETE_TRIPLET_SOURCE_ONLY",result["status"])
    print("ORIGINAL_40_TRIPLET_STRICT_HOLD_PRESERVED_NO_OTU")

if __name__=="__main__":main()
