#!/usr/bin/env python3
"""Zenodo official RECORD metadata only: no file downloads and no ecological rows."""
import argparse,json,re
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
API="https://zenodo.org/api/records/10780971"
RECORD_ID=10780971
DOI="10.5281/zenodo.10780971"
EXPECTED={
 "CamTrapAsia_Metadata_20231031.csv":"2b50c534737b0c98a93da54128b10a32",
 "Species_Traits_20231031.csv":"59e0748f8aaf59b23b936248f1e63fc9",
 "CamTrapAsia_Captures_20231031.csv":"a73975d7626def4012a4e1197497ba87",
}
def verify(data):
    if data.get("id")!=RECORD_ID:raise ValueError("Wrong immutable Zenodo record id")
    gotdoi=data.get("doi")
    if gotdoi!=DOI:raise ValueError("Wrong dataset DOI")
    files=data.get("files")
    if not isinstance(files,list):raise ValueError("Missing file metadata list")
    found={}
    for z in files:
        k=z.get("key");sumstr=z.get("checksum")
        if k not in EXPECTED:continue
        if not isinstance(sumstr,str) or sumstr.lower()!=("md5:"+EXPECTED[k]):
            raise ValueError("Published checksum mismatch: "+k)
        size=z.get("size")
        if not isinstance(size,int) or size<=0:raise ValueError("Invalid official file size")
        if k in found:raise ValueError("Duplicated published file")
        found[k]={"size_bytes":size,"source_md5":EXPECTED[k]}
    if set(found)!=set(EXPECTED):raise ValueError("Missing exact expected published files")
    return {"schema":"structural.camtrapasia_zenodo_public_file_metadata.v1_236",
        "status":"PASS_OFFICIAL_ZENODO_FILE_IDENTITY_ONLY",
        "dataset_doi":DOI,"record_id":RECORD_ID,
        "matched_published_source_files":found,
        "file_bodies_downloaded":0,"camera_capture_rows_read":0,
        "species_names_read":0,"site_coordinates_read":0,
        "original_mammal_heldout_response_read":0,
        "original_model_predictions_read":0,
        "external_species_prediction_score_authorized":False}
def run():
    x={"schema":"structural.camtrapasia_zenodo_public_file_metadata.v1_236",
        "camera_capture_rows_read":0,"original_mammal_heldout_response_read":0,
        "external_species_prediction_score_authorized":False}
    try:
        req=Request(API,headers={"Accept":"application/json","User-Agent":"Structural-source-only-v1.236"})
        with urlopen(req,timeout=30) as r:
            url=urlsplit(r.url)
            if url.scheme!="https" or url.hostname not in ("zenodo.org","www.zenodo.org"):
                raise ValueError("Untrusted record metadata redirect")
            if "json" not in r.headers.get("Content-Type","").lower():raise ValueError("Expected record JSON only")
            raw=r.read(3000001)
        if len(raw)>3000000:raise ValueError("Record metadata too large")
        x=verify(json.loads(raw.decode("utf-8")))
    except HTTPError as e:x.update(status="STOP_OFFICIAL_ZENODO_HTTP",http_status=e.code)
    except Exception as e:x.update(status="STOP_ZENODO_RECORD_SCHEMA_OR_CHECKSUM",reason_type=type(e).__name__)
    return x
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);args=ap.parse_args()
    obj=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(obj,sort_keys=True))
