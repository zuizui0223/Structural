#!/usr/bin/env python3
"""Original Kortmann 2026 exact four-field method/effort row audit; no biology.

Response-bearing RData previously deserialized for schema; method values are
read privately in R, but original site and treatment labels never leave runner.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from kortmann2026_17775805_original_zip_directory_only import (
    SourceStop, original_file_metadata, official_get_one_zip, inspect_central_directory_only
)
PRESPEC="docs/FOREST_MACRO_KORTMANN_TRIPLET_TREATMENT_OFFSET_IDONLY_PREFREEZE_20261121.md"
MEMBER="data_public/diversity_satellite.rda"
SHA="8b3f47258b4d9c8f6fa0f7fac0d820ecccb860adadaa9c3c311f21fa28e3da3a"
SIZE=67238
R=Path(__file__).with_name("kortmann2026_original_triplet_id_frame.R")
EXPECTED={
 "original_observed_sampling_rows","original_site_triplets",
 "original_triplet_plot_pairs","original_source_treatment_codes",
 "original_triplet_treatment_pairs",
 "triplets_with_three_distinct_plots","triplets_with_three_treatment_codes",
 "source_site_treatment_groups_with_single_plot",
 "source_site_plot_groups_with_single_treatment",
 "sampled_rows_per_plot_min","sampled_rows_per_plot_max",
 "physical_patches_with_six_sample_rows",
 "physical_patches_with_fewer_than_six_rows",
 "nominal_720_minus_observed_702",
 "counted_source_patch_opportunity_deficit",
 "all_offset_values_numeric_and_finite"
}
READY="SOURCE_ORIGINAL_TRIPLET_3STATE_702_FRAME_COUNT_READY_NO_OTU"
HOLD="SOURCE_ORIGINAL_METHOD_FRAME_HOLD"

def parse_stdout(s):
    lines=s.strip().splitlines()
    if not lines or lines[0]!="ORIGINAL_METHOD_FRAME_V1":
        raise SourceStop("SOURCE_ORIGINAL_METHOD_R_OUTPUT_SCHEMA_STOP")
    m={}
    status=None
    for line in lines[1:]:
        z=line.split("\t")
        if len(z)==3 and z[0]=="METRIC":
            k=z[1]
            if k not in EXPECTED or k in m or not z[2].isdigit():
                raise SourceStop("SOURCE_ORIGINAL_METHOD_UNKNOWN_OR_DUPLICATE_METRIC")
            m[k]=int(z[2])
        elif len(z)==2 and z[0]=="SOURCE_METHOD_FRAME_STATUS" and z[1] in (READY,HOLD):
            if status is not None: raise SourceStop("SOURCE_ORIGINAL_METHOD_DUPLICATE_STATUS")
            status=z[1]
        elif len(z)==2 and z==["ORIGINAL_SOURCE_ID_OR_TREATMENT_LABEL_EXPORTED","0"]:
            pass
        elif len(z)==2 and z==["ORIGINAL_BIOLOGICAL_EFFECT_ESTIMATED","0"]:
            pass
        elif len(z)==2 and z==["SOURCE_RDA_PREVIOUSLY_DESERIALIZED_RESPONSE_BEARING","1"]:
            pass
        else:
            raise SourceStop("SOURCE_ORIGINAL_METHOD_UNEXPECTED_R_OUTPUT")
    if len(m)!=len(EXPECTED) or status is None or len(lines)!=len(EXPECTED)+5:
        raise SourceStop("SOURCE_ORIGINAL_METHOD_OUTPUT_INCOMPLETE")
    return {
        "status":status,
        "original_source_anonymous_unit_counts_only":m,
        "original_site_plot_treatment_values_NOT_EXPORTED":True,
        "original_offset_numeric_values_NOT_EXPORTED":True,
        "original_702_source_records_sample_period_IDs_NOT_VERIFIED":True,
        "original_RData_response_bearing_object_DESERIALIZED":True,
        "original_species_OTU_taxon_numeric_values_NOT_ACCESSED_OR_SCORED":True,
        "new_biological_effects_fitted":0,
    }

def call_r(args,synthetic=False):
    try:
        p=subprocess.run(["Rscript","--vanilla",str(R)]+args,
             capture_output=True,text=True,timeout=55,check=False)
    except (OSError,subprocess.TimeoutExpired):
        raise SourceStop("SOURCE_ORIGINAL_METHOD_R_EXECUTION_UNAVAILABLE") from None
    if p.returncode!=0:
        raise SourceStop("SOURCE_ORIGINAL_METHOD_R_INSPECTION_STOP")
    if synthetic:
        if p.stdout.strip()!="SYNTHETIC_KORTMANN_40_TRIPLET_18_MISSING_SOURCE_METHOD_PASS":
            raise SourceStop("SOURCE_ORIGINAL_METHOD_SYNTHETIC_FAILED")
        return None
    return parse_stdout(p.stdout)

def synthetic():
    call_r(["--synthetic"],synthetic=True)
    fake=(
      "ORIGINAL_METHOD_FRAME_V1\n"
      "METRIC\toriginal_observed_sampling_rows\t702\n"
      "METRIC\tunrecognized_sensitive_field\t123\n"
    )
    try:parse_stdout(fake)
    except SourceStop:pass
    else:raise AssertionError("Unknown source data field escaped")
    print("SYNTHETIC_KORTMANN_702_ID_FRAME_AND_PRIVACY_PASS")

def run():
    url=original_file_metadata()
    b=official_get_one_zip(url)
    if inspect_central_directory_only(b)["status"]!="SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY":
        raise SourceStop("SOURCE_ORIGINAL_ZIP_CENTRAL_DIRECTORY_CHANGED")
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        f=z.getinfo(MEMBER)
        if f.file_size!=SIZE:
            raise SourceStop("SOURCE_ORIGINAL_METHOD_MEMBER_SIZE_CHANGED")
        try:raw=z.read(MEMBER)
        except (OSError,zipfile.BadZipFile,KeyError):
            raise SourceStop("SOURCE_ORIGINAL_METHOD_MEMBER_READ_STOP") from None
    if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=SHA:
        raise SourceStop("SOURCE_ORIGINAL_METHOD_MEMBER_SHA_DRIFT")
    with tempfile.TemporaryDirectory(prefix="kortmann_4method_fields_") as d:
        tmp=Path(d)/"diversity_satellite.rda"
        tmp.write_bytes(raw)
        source=call_r([str(tmp)])
    return source

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out required")
    out={
      "schema":"structural.Kortmann2026_original_40triplet_three_state_ID_frame_v1",
      "prespec":PRESPEC,
      "original_RData_source_response_bearing_DESERIALIZED_PREVIOUSLY":True,
      "first_RData_source_schema_receipt_UNCHANGED":True,
      "previous_BETAFOR99_and_234_effects_or_STOPs_UNCHANGED":True,
      "original_separate_OTU_matrix_and_workbook_OPENED":False,
      "new_ecological_effects_scored":0,
      "eBird_used":False,"TinyFish_used":False
    }
    try:
        out["source"]=run()
        out["status"]=out["source"]["status"]
    except SourceStop as e:
        out["status"]="SOURCE_ORIGINAL_ID_FRAME_STOP_"+str(e)
        out["source_STOP_not_ecological_null"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("KORTMANN_ORIGINAL_TRIPLET_TREATMENT_OFFSET_IDFRAME",out["status"])
    print("NO_ORIGINAL_SITE_VALUES_OR_BIOLOGICAL_EFFECTS_EXPORTED")

if __name__=="__main__":
    main()
