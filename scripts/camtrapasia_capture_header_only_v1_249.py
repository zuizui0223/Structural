#!/usr/bin/env python3
"""CamTrapAsia capture CSV HEADER ONLY after exact Zenodo file byte/MD5 check."""
import argparse,csv,hashlib,io,json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError

URL="https://zenodo.org/api/records/10780971/files/CamTrapAsia_Captures_20231031.csv/content"
BYTES=956340
MD5="a73975d7626def4012a4e1197497ba87"
HOSTS={"zenodo.org","www.zenodo.org","files.zenodo.org","s3.cern.ch"}
def inspect(raw):
    if len(raw)!=BYTES or hashlib.md5(raw).hexdigest()!=MD5:
        raise ValueError("Exact capture file identity not pinned")
    first=raw.split(b"\n",1)[0]
    if not first or len(first)>16000:raise ValueError("Invalid header byte length")
    cols=next(csv.reader(io.StringIO(first.decode("utf-8-sig").rstrip("\r"))))
    if not 1<=len(cols)<=150 or any(not z.strip() for z in cols) or len(set(cols))!=len(cols):
        raise ValueError("Duplicate/blank CSV field name")
    return {"schema":"structural.camtrapasia_capture_headers_only_result.v1_249",
      "status":"PASS_CAPTURE_CSV_EXACT_HASH_AND_HEADER_ONLY",
      "source_csv_full_MD5":MD5,"source_csv_bytes":BYTES,
      "CSV_header_fields":cols,"CSV_header_field_count":len(cols),
      "source_camera_capture_observation_rows_read":0,
      "original_IUCN_heldout_response_rows_read":0,
      "original_model_predictions_read":0,
      "external_529_species_model_validation_admitted":False}
def run():
    try:
        with urlopen(Request(URL,headers={"User-Agent":"Structural-response-safe-capture-schema-v1.249"}),timeout=60) as f:
            q=urlsplit(f.url)
            if q.scheme!="https" or q.hostname not in HOSTS:raise ValueError("Unexpected source redirect")
            raw=f.read(BYTES+1)
        return inspect(raw)
    except HTTPError as e:
        return {"status":"STOP_OFFICIAL_CAPTURE_SOURCE_HTTP","http_status":e.code}
    except Exception as e:
        return {"status":"STOP_CAPTURE_SOURCE_BYTE_IDENTITY_OR_SCHEMA","reason_type":type(e).__name__}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();result=run()
    result.setdefault("schema","structural.camtrapasia_capture_headers_only_result.v1_249")
    result.setdefault("source_camera_capture_observation_rows_read",0)
    result.setdefault("original_IUCN_heldout_response_rows_read",0)
    result.setdefault("external_529_species_model_validation_admitted",False)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
