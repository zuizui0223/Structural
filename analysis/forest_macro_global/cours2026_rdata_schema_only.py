#!/usr/bin/env python3
"""One checksum-pinned original RData object-schema ONLY diagnostic.

Original study Cours et al 2026, CC BY official Zenodo DOI 17927769.
Rscript never reads any value; only object classes/dimensions and generic
method/predictor variable names. Original bytes private in ephemeral runner.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

RECORD=17927769
DOI="10.5281/zenodo.17927769"
REC=f"https://zenodo.org/api/records/{RECORD}"
FILENAME="Decline_Data.RData"
SIZE=33531
MD5="34312f823dafa60568fa0cd92926ee37"
UA={"User-Agent":"Structural-Cours2026-Original-RData-SCHEMA-only/1.0",
    "Accept":"application/json,application/octet-stream,*/*;q=.2"}

def read_url(url,cap):
    with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=38) as r:
        b=r.read(cap+1)
        if r.status!=200 or len(b)>cap:
            raise ValueError("SOURCE_FILE_HTTP_OR_CAP_STOP")
        return b

def pinned_source():
    j=json.loads(read_url(REC,250000))
    md=j.get("metadata") or {}
    lic=md.get("license")
    l=lic.get("id") if isinstance(lic,dict) else lic
    if j.get("id")!=RECORD or j.get("doi")!=DOI or l!="cc-by-4.0":
        raise ValueError("SOURCE_RECORD_ID_OR_CC_BY_RIGHTS_STOP")
    files=j.get("files") or []
    if isinstance(files,dict):
        files=list((files.get("entries") or {}).values())
    if len(files)!=2 or set(f.get("key") for f in files)!={FILENAME,"Analysis_Cascade_Decline_Salvage.Rmd"}:
        raise ValueError("SOURCE_ORIGINAL_2FILE_ROSTER_STOP")
    file=next(f for f in files if f.get("key")==FILENAME)
    if file.get("size")!=SIZE or file.get("checksum")!="md5:"+MD5:
        raise ValueError("SOURCE_ORIGINAL_RDATA_MD5_OR_SIZE_METADATA_STOP")
    href=(file.get("links") or {}).get("self") or (file.get("links") or {}).get("download")
    p=urllib.parse.urlparse(href or "")
    if not(p.scheme=="https" and p.hostname=="zenodo.org" and
           (p.path==f"/api/records/{RECORD}/files/{FILENAME}/content" or
            p.path.startswith("/api/files/"))):
        raise ValueError("SOURCE_OFFICIAL_RDATA_LINK_ORIGIN_STOP")
    b=read_url(href,70000)
    if len(b)!=SIZE or hashlib.md5(b).hexdigest()!=MD5:
        raise ValueError("SOURCE_ORIGINAL_RDATA_BYTES_FINGERPRINT_STOP")
    return b

def validate_only_schema(s):
    if s.get("schema")!="structural.cours2026_original_RData_schema_only.v1":
        raise ValueError("SOURCE_R_OBJECT_SCHEMA_CONTRACT_STOP")
    if not s.get("original_RData_loaded_schema_not_values") or s.get("original_RData_model_fits")!=0:
        raise ValueError("SOURCE_R_DATA_VALUES_OR_MODEL_ACCESS_STOP")
    if s.get("original_beetle_abundance_or_response_cells_read")!=0:
        raise ValueError("SOURCE_BEETLE_ABUNDANCE_VALUES_READ_STOP")
    objects=s.get("data_objects",[])
    if s.get("data_object_count")!=len(objects):
        raise ValueError("SOURCE_R_OBJECT_COUNT_STOP")
    for o in objects:
        if o.get("sample_identifiers_or_taxa_rows_read")!=0 or o.get("source_object_numeric_contents_accessed"):
            raise ValueError("SOURCE_ORIGINAL_RDATA_VALUES_ACCESSED_STOP")
    return True

def test():
    stub={"schema":"structural.cours2026_original_RData_schema_only.v1",
          "original_RData_loaded_schema_not_values":True,
          "original_RData_model_fits":0,
          "original_beetle_abundance_or_response_cells_read":0,
          "data_object_count":1,
          "data_objects":[{"sample_identifiers_or_taxa_rows_read":0,
                           "source_object_numeric_contents_accessed":False}]}
    assert validate_only_schema(stub)
    assert SIZE==33531 and len(MD5)==32
    print("SOURCE_ONLY_COURS_RDATA_READER_SYNTHETIC_GUARDS_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="cours2026_RData_schema_only/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    record={"schema":"structural.cours2026_RData_source_schema_gate.v1",
            "original_publisher_doi":DOI,
            "source_publisher_file_checksum":"md5:"+MD5,
            "RData_raw_file_uploaded":False,
            "original_beetle_numeric_values_or_cells_read":0,
            "new_ecological_effects":0,
            "source_2017_2020_original_contexts_not_as_three_independent_programmes":True,
            "historical_Ramberg2026_ZERO_CATCH_STOP_preserved":True,
            "historical_Korhonen_HTTP401_preserved":True,
            "eBird_used":False,"TinyFish_used":False,
            "status":"SOURCE_RDATA_SCHEMA_UNOPENED"}
    try:
        with tempfile.TemporaryDirectory(prefix="cours-RData-schemaonly-") as d:
            binary=pinned_source()
            fp=Path(d)/FILENAME
            fp.write_bytes(binary)
            output=Path(d)/"safe_schema.json"
            cmd=["Rscript","analysis/forest_macro_global/cours2026_rdata_schema_only.R",str(fp),str(output)]
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
            if result.returncode!=0 or not output.exists():
                raise ValueError("SOURCE_R_OBJECT_LOAD_OR_SCHEMA_RUNTIME_STOP")
            meta=json.loads(output.read_text())
            validate_only_schema(meta)
            record["source_object_schema_without_values"]=meta
            record["status"]="SOURCE_RDATA_SCHEMA_ONLY_PASS"
    except Exception as e:
        record["status"]="SOURCE_RDATA_ACCESS_OR_SCHEMA_STOP"
        record["error_type"]=type(e).__name__
        record["error_code"]=str(e)[:135] if isinstance(e,ValueError) else ""
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("COURS_RDATA_ORIGINAL_SCHEMA_GATE",record["status"])
    print("ECOLOGICAL_SCORES",record["new_ecological_effects"])
    print("ORIGINAL_RDATA_RAW_ARCHIVED",record["RData_raw_file_uploaded"])

if __name__=="__main__":
    main()
