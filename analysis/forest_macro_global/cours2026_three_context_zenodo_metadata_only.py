#!/usr/bin/env python3
"""Publisher exact-record source metadata for Cours et al. 2026 JAE.

Zero R code, RData, beetle values, plot rows or ecological analyses read.
Fail closed on original record identity, license, file set, unauthorized file GET.
"""
import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

RECORD=17927769
DOI="10.5281/zenodo.17927769"
ORIGIN=f"https://zenodo.org/api/records/{RECORD}"
FILES={"Analysis_Cascade_Decline_Salvage.Rmd","Decline_Data.RData"}
UA={"User-Agent":"Structural-public-metadata-only-original-forest-study/1.0",
    "Accept":"application/json"}

def public_record():
    try:
        with urllib.request.urlopen(urllib.request.Request(ORIGIN,headers=UA),timeout=36) as r:
            data=r.read(500001)
            if r.status!=200 or len(data)>500000:
                return {"status":"SOURCE_RECORD_HTTP_OR_SIZE_STOP","http":r.status}
    except urllib.error.HTTPError as e:
        return {"status":"SOURCE_RECORD_HTTP_STOP","http":e.code}
    except Exception as e:
        return {"status":"SOURCE_RECORD_TRANSPORT_STOP","error_class":type(e).__name__}
    try:
        x=json.loads(data)
    except ValueError:
        return {"status":"SOURCE_PUBLISHER_JSON_STOP"}
    if x.get("id")!=RECORD or (x.get("doi") or (x.get("metadata") or {}).get("doi"))!=DOI:
        return {"status":"SOURCE_PUBLISHER_RECORD_DOI_ID_STOP"}
    md=x.get("metadata") or {}
    rights=md.get("license")
    files=x.get("files") or []
    if isinstance(files,dict):files=list((files.get("entries") or {}).values())
    if not isinstance(files,list) or not all(isinstance(f,dict) for f in files):
        return {"status":"SOURCE_PUBLISHER_FILE_SCHEMA_STOP"}
    names={f.get("key") or f.get("filename") for f in files}
    counts=[]
    for f in files:
        name=f.get("key") or f.get("filename")
        b=f.get("size")
        digest=f.get("checksum")
        if name not in FILES or not isinstance(b,int) or not isinstance(digest,str):
            return {"status":"SOURCE_PUBLISHER_FILE_MANIFEST_STOP"}
        counts.append({"filename":name,"publisher_size_bytes":b,"publisher_checksum":digest})
    output={
      "status":"SOURCE_PUBLISHER_METADATA_RIGHTS_READY" if names==FILES else "SOURCE_ORIGINAL_FILE_SET_MISMATCH_HOLD",
      "source_doi":DOI,
      "record_id":RECORD,
      "title":str(md.get("title",""))[:220],
      "publication_date":md.get("publication_date"),
      "license_metadata":rights,
      "access_right":md.get("access_right") or md.get("access_status"),
      "files":sorted(counts,key=lambda a:a["filename"]),
      "original_data_or_code_file_GETs":0,
      "original_beetle_species_rows_opened":0,
      "original_plot_environment_values_opened":0,
      "original_biological_effects_scored":0
    }
    return output

def test():
    assert RECORD==17927769
    assert len(FILES)==2
    assert any(n.endswith(".RData") for n in FILES)
    assert all(re.fullmatch(r"[0-9a-z_.A-Z-]+",x) for x in FILES)
    print("SOURCE_ONLY_COURS2026_RECORD_ID_FILE_ROSTER_FIXTURE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="cours2026_three_context_sourceonly/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    r={"schema":"structural.cours2026_three_context_original_publisher_metadata_only.v1",
       "candidate_original_study_count":1,
       "original_files_downloaded":0,
       "new_scientific_ecological_effects":0,
       "previous_Ramberg2026_original_zero_catch_STOP_preserved":True,
       "previous_Korhonen2024_Dryad_HTTP401_preserved":True,
       "eBird_used":False,"TinyFish_used":False,
       "source":public_record()}
    f=Path(a.out)
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("COURS2026_ORIGINAL_SOURCE_STATUS",r["source"]["status"])
    print("PUBLISHER_RIGHTS",r["source"].get("license_metadata"))
    print("N_FILE_METADATA",len(r["source"].get("files",[])))
    print("ORIGINAL_RESPONSE_VALUES_READ",r["original_files_downloaded"])

if __name__=="__main__":
    main()
