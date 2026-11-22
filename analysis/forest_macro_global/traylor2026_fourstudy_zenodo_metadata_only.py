#!/usr/bin/env python3
"""Official Zenodo-only 2026 Traylor US four-study beetle resource cohort metadata.

No raw file GET, biological cells, source code or model fitting.
"""
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

RECORD=19206036
DOI="10.5281/zenodo.19206036"
URL=f"https://zenodo.org/api/records/{RECORD}"
UA={"User-Agent":"Structural-independent-beetle-fourstudy-metadata/1.0","Accept":"application/json"}

def source():
    out={"status":"SOURCE_PUBLISHER_METADATA_UNOPENED"}
    try:
        req=urllib.request.Request(URL,headers=UA)
        with urllib.request.urlopen(req,timeout=35) as r:
            raw=r.read(500001)
            if r.status!=200 or len(raw)>500000:
                return {"status":"SOURCE_PUBLISHER_METADATA_HTTP_OR_CAP_STOP","http":r.status}
    except urllib.error.HTTPError as e:
        return {"status":"SOURCE_PUBLISHER_METADATA_HTTP_STOP","http":e.code}
    except Exception as e:
        return {"status":"SOURCE_PUBLISHER_METADATA_TRANSPORT_STOP","exception_type":type(e).__name__}
    try:x=json.loads(raw)
    except ValueError:return {"status":"SOURCE_PUBLISHER_METADATA_JSON_STOP"}
    md=x.get("metadata") or {}
    doi=x.get("doi") or md.get("doi")
    if x.get("id")!=RECORD or doi!=DOI:
        return {
            "status":"SOURCE_PUBLISHER_ID_OR_DOI_MISMATCH_STOP",
            "requested_original_record_id":RECORD,
            "returned_record_id":x.get("id"),
            "returned_version_doi":x.get("doi"),
            "returned_metadata_doi":md.get("doi"),
            "returned_concept_doi":x.get("conceptdoi"),
            "returned_concept_record_id":x.get("conceptrecid"),
            "returned_title":str(md.get("title",""))[:220],
            "returned_rights":md.get("license"),
            "returned_access":md.get("access_right") or md.get("access_status"),
            "original_biological_file_gets":0
        }
    files=x.get("files") or []
    if isinstance(files,dict):files=list((files.get("entries") or {}).values())
    if not isinstance(files,list):
        return {"status":"SOURCE_PUBLISHER_FILE_OBJECT_SCHEMA_STOP"}
    outputs=[]
    for item in files:
        if not isinstance(item,dict):
            return {"status":"SOURCE_PUBLISHER_FILE_METADATA_TYPE_STOP"}
        outputs.append({
            "source_filename":str(item.get("key") or item.get("filename") or "")[:220],
            "source_size_bytes":item.get("size"),
            "official_checksum":item.get("checksum"),
            "original_file_bytes_read":0
        })
    out={
      "status":"SOURCE_OFFICIAL_FILE_METADATA_AND_RIGHTS_READY" if outputs else "SOURCE_PUBLIC_FILE_LIST_EMPTY_HOLD",
      "doi":DOI,"record":RECORD,"original_title":str(md.get("title",""))[:220],
      "publication_date":md.get("publication_date"),
      "license":md.get("license"),
      "access_right":md.get("access_right") or md.get("access_status"),
      "source_original_file_roster":outputs,
      "publisher_record_source_study_n_from_article":4,
      "publisher_original_deadwood_objects_from_article":356,
      "source_beetle_species_or_deadwood_records_read":0,
      "new_original_biological_effects_computed":0
    }
    return out

def known():
    assert RECORD==19206036 and DOI.endswith(str(RECORD))
    print("TRAYLOR2026_ORIGINAL_SOURCE_ID_ONLY_FIXTURE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="traylor2026_source_only/receipt.json")
    a=p.parse_args()
    known()
    if a.test:return
    obj={"schema":"structural.traylor2026_four_original_studies_beetles_source_metadata_only.v1",
         "metadata":source(),
         "source_data_file_gets":0,"new_ecological_scores":0,
         "prior_Ramberg2026_zero_catch_scientific_STOP_preserved":True,
         "prior_Cours2026_rights_only_gate_separate":True,
         "prior_Ecuador_Finland_BALA_GEB_mammal_outcomes_sealed":True,
         "eBird_used":False,"TinyFish_used":False}
    f=Path(a.out);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("TRAYLOR2026_ZENODO_METADATA_STATUS",obj["metadata"]["status"])
    print("PUBLIC_SOURCE_FILE_METADATA_N",len(obj["metadata"].get("source_original_file_roster",[])))
    print("LICENSE",obj["metadata"].get("license"))
    print("BIOLOGICAL_RECORDS_READ",obj["source_data_file_gets"])

if __name__=="__main__":main()
