#!/usr/bin/env python3
"""Kortmann 2026 first source-original RData deserialization: SCHEMA ONLY.

The original diversity_satellite.rda response-bearing object is loaded into
ephemeral R memory, so the evidence class is NOT pristine-response-unopened.
No original data values, site IDs, taxon labels, or models are exported/scored.
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
    SourceStop, original_file_metadata, official_get_one_zip, inspect_central_directory_only,
)

PRESPEC="docs/FOREST_MACRO_KORTMANN_DIVERSITY_RDA_SCHEMA_FIRST_OPEN_PREFREEZE_20261121.md"
SCRIPT=Path(__file__).with_name("kortmann2026_diversity_rda_first_schema.R")
MEMBER="data_public/diversity_satellite.rda"
MEMBER_SIZE=67238
MAX_OBJS=16
SAFE_NAMES={
 "triplet","treatment","site","siteid","plot","plotid","patch","patchid","sample","sampleid",
 "year","date","period","round","samplinglength","sampling_length","samplingdate","sampling_date",
 "trapdays","duration","effort","foresttype","forest_type","forest","management","disturbance",
 "canopy","openness","sampling_length_days","offset",
}

def safe_r_schema(stdout):
    lines=stdout.strip().splitlines()
    if len(lines)<4:
        raise SourceStop("SOURCE_RDA_SCHEMA_R_OUTPUT_INCOMPLETE")
    head=lines[0].split("\t")
    if len(head)!=2 or head[0]!="RDA_SCHEMA_V1":
        raise SourceStop("SOURCE_RDA_SCHEMA_R_MAGIC_INVALID")
    try:n=int(head[1])
    except ValueError:
        raise SourceStop("SOURCE_RDA_SCHEMA_R_OBJECT_COUNT_INVALID") from None
    if not 1<=n<=MAX_OBJS or len(lines)!=n+3:
        raise SourceStop("SOURCE_RDA_SCHEMA_R_OBJECT_ROW_COUNT_INVALID")
    records=[]
    for index,line in enumerate(lines[1:1+n],start=1):
        fields=line.split("\t")
        if len(fields)!=7 or fields[0]!="OBJECT" or fields[2] not in ("data.frame","matrix","list","other"):
            raise SourceStop("SOURCE_RDA_SCHEMA_R_OBJECT_FIELDS_INVALID")
        try:idx,nr,nc,nn=(int(fields[i]) for i in (1,3,4,5))
        except ValueError:
            raise SourceStop("SOURCE_RDA_SCHEMA_R_OBJECT_VALUES_INVALID") from None
        if idx!=index or not 0<=nr<=2_000_000 or not 0<=nc<=100_000 or nn!=nc:
            # list/other carry 0/0 by design.
            raise SourceStop("SOURCE_RDA_SCHEMA_R_OBJECT_DIMS_DRIFT")
        names=fields[6].split(",") if fields[6] else []
        if names!=sorted(set(names)) or any(v not in SAFE_NAMES for v in names):
            raise SourceStop("SOURCE_RDA_SCHEMA_UNDECLARED_FIELD_LEAK_OR_DUPLICATE")
        records.append({
            "object_anonymous_index":index,
            "container_type":fields[2],
            "rows_NOT_independent_sample_count":nr,
            "columns":nc,
            "source_column_count":nn,
            "precommitted_safe_method_names_ONLY":names,
        })
    if (lines[-2]!="BIOLOGICAL_VALUE_EXPORTS\t0" or
        lines[-1]!="SOURCE_RDA_DESERIALIZED_RESPONSE_BEARING_OBJECT\tTRUE"):
        raise SourceStop("SOURCE_RDA_SCHEMA_R_OUTPUT_SAFETY_MARKERS_MISSING")
    candidates=[r for r in records if r["container_type"]=="data.frame"
                and {"triplet","treatment"}.issubset(r["precommitted_safe_method_names_ONLY"])]
    return {
        "source_response_bearing_object_deserialized_in_ephemeral_R_memory":True,
        "source_biology_could_be_present_in_loaded_object":True,
        "fresh_response_unopened_claim_FORBIDDEN":True,
        "dataframe_structural_role_candidates":len(candidates),
        "source_objects_anonymized":records,
        "original_object_variable_names_NOT_EXPORTED":True,
        "original_site_and_treatment_VALUES_NOT_READ_OR_EXPORTED":True,
        "original_biological_numeric_values_NOT_SUMMARIZED":True,
        "original_RData_object_schema_only_NO_FIELD_ROW_CROSSWALK":True,
        "status":("SOURCE_RDA_METHOD_COLUMNS_CANDIDATES_ONLY_NO_ID_VALUES"
                  if candidates else "SOURCE_RDA_METHOD_FIELDS_HOLD"),
    }

def call_r(args):
    try:
        p=subprocess.run(
          ["Rscript","--vanilla",str(SCRIPT)]+args,
          capture_output=True,text=True,timeout=55,check=False,
        )
    except (OSError,subprocess.TimeoutExpired):
        raise SourceStop("SOURCE_RDA_RSCRIPT_EXECUTION_UNAVAILABLE") from None
    if p.returncode!=0:
        # NEVER disclose raw R stderr or original source values.
        raise SourceStop("SOURCE_RDA_RSCRIPT_INSPECTION_STOP")
    return safe_r_schema(p.stdout)

def synthetic():
    output=call_r(["--synthetic"])
    assert output["source_objects_anonymized"][0]["rows_NOT_independent_sample_count"]==2
    assert output["dataframe_structural_role_candidates"]==1
    s=json.dumps(output)
    assert "PRIVATE_ORIGINAL_SAMPLE_ID_A" not in s
    assert "PRIVATE_TREATMENT_2" not in s
    assert "999999" not in s
    try:
        safe_r_schema("RDA_SCHEMA_V1\t1\nOBJECT\t1\tdata.frame\t1\t3\t3\ttriplet,treatment,richness\nBIOLOGICAL_VALUE_EXPORTS\t0\nSOURCE_RDA_DESERIALIZED_RESPONSE_BEARING_OBJECT\tTRUE\n")
    except SourceStop:
        pass
    else:
        raise AssertionError("Unknown original data field passed export firewall")
    print("SYNTHETIC_KORTMANN_RDA_FIRST_SCHEMA_NO_VALUES_PASS")

def run():
    url=original_file_metadata()
    raw=official_get_one_zip(url)
    if inspect_central_directory_only(raw)["status"]!="SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY":
        raise SourceStop("SOURCE_ORIGINAL_ZIP_DIRECTORY_DRIFT")
    with zipfile.ZipFile(io.BytesIO(raw),"r") as z:
        objects={a.filename:a for a in z.infolist() if not a.is_dir()}
        if MEMBER not in objects or objects[MEMBER].file_size!=MEMBER_SIZE:
            raise SourceStop("SOURCE_ORIGINAL_RDA_MEMBER_WRONG_ROLE_OR_LENGTH")
        if objects[MEMBER].flag_bits & 1:
            raise SourceStop("SOURCE_ORIGINAL_RDA_MEMBER_ENCRYPTED")
        try:
            data=z.read(MEMBER)
        except (zipfile.BadZipFile,KeyError,OSError):
            raise SourceStop("SOURCE_ORIGINAL_RDA_MEMBER_READ_STOP") from None
    if len(data)!=MEMBER_SIZE:
        raise SourceStop("SOURCE_ORIGINAL_RDA_MEMBER_UNCOMPRESSED_SIZE_DRIFT")
    sh=hashlib.sha256(data).hexdigest()
    with tempfile.TemporaryDirectory(prefix="kortmann_original_rda_schema_") as folder:
        fp=Path(folder)/"diversity_satellite.rda"
        fp.write_bytes(data)
        summary=call_r([str(fp)])
    return {
        "source_versioned_original_zenodo":17775805,
        "original_ZIP_full_MD5_verified":True,
        "original_first_RData_member_verified_source_uncompressed_size":MEMBER_SIZE,
        "original_first_RData_member_SHA256":sh,
        "source_RData_schema":summary,
        "original_separate_OTU_matrix_member_OPENED":False,
        "original_phylogeny_and_XLSX_member_OPENED":False,
        "new_organismal_effect_fits":0,
        "status":summary["status"],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out required")
    result={
      "schema":"structural.Kortmann2026_first_original_RDA_deserialized_schema_only.v1",
      "prespec":PRESPEC,
      "old_BETAFOR99_original_effects_UNTOUCHED":True,
      "prior_BETAFOR234_no_files_STOP_UNCHANGED":True,
      "first_original_RData_member_DESERIALIZED_for_schema":False,
      "new_organismal_effect_fits":0,
      "original_OTU_matrix_and_workbook_data_GET":0,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
      result["source"]=run()
      result["status"]=result["source"]["status"]
      result["first_original_RData_member_DESERIALIZED_for_schema"]=True
    except SourceStop as e:
      result["status"]="SOURCE_FIRST_RDA_SCHEMA_STOP_"+str(e)
      result["source_STOP_not_ecological_null"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("KORTMANN_FIRST_RDA_STRUCTURE_SCHEMA",result["status"])
    print("NO_FIELD_VALUES_EXPORTED_NO_ORGANISM_MODELS_FITTED")

if __name__=="__main__":
    main()
