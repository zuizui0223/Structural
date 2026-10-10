#!/usr/bin/env python3
"""Read ONLY first CSV header after exact Zenodo bytes/hash; never decode data rows."""
import argparse,csv,hashlib,io,json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit,quote
RECORD=10780971
FILES={
 "CamTrapAsia_Metadata_20231031.csv":(245677,"2b50c534737b0c98a93da54128b10a32"),
 "Species_Traits_20231031.csv":(67450,"59e0748f8aaf59b23b936248f1e63fc9")
}
HOSTS={"zenodo.org","www.zenodo.org","files.zenodo.org","s3.cern.ch"}
def header_only(payload,expected_size,expected_md5):
    if len(payload)!=expected_size or hashlib.md5(payload).hexdigest()!=expected_md5:
        raise ValueError("Official file bytes fail frozen identity")
    first=payload.split(b"\n",1)[0]
    if not first or len(first)>12000:raise ValueError("Unexpected header length")
    try:
        fields=next(csv.reader(io.StringIO(first.decode("utf-8-sig").rstrip("\r"))))
    except (UnicodeDecodeError,csv.Error) as exc:
        raise ValueError("Unknown CSV header encoding") from exc
    if not 1<=len(fields)<=160 or any(not s.strip() for s in fields) or len(set(fields))!=len(fields):
        raise ValueError("Invalid CSV field header")
    return fields
def fetch_exact(file):
    expected_size,expected_md5=FILES[file]
    url=f"https://zenodo.org/api/records/{RECORD}/files/{quote(file)}/content"
    with urlopen(Request(url,headers={"User-Agent":"Structural-site-schema-only-v1.237"}),
        timeout=45) as r:
        p=urlsplit(r.url)
        if p.scheme!="https" or p.hostname not in HOSTS:
            raise ValueError("Unexpected Zenodo file CDN redirect")
        raw=r.read(expected_size+1)
    fields=header_only(raw,expected_size,expected_md5)
    return {"filename":file,"byte_length":len(raw),"md5":expected_md5,
        "column_count":len(fields),"csv_field_headers":fields,
        "source_data_rows_semantically_read":0}
def execute():
    x={"schema":"structural.camtrapasia_source_header_preflight.v1_237",
       "source_capture_rows_opened":0,"source_site_rows_opened":0,"source_species_rows_opened":0,
       "original_mammal_response_opened":False,"external_prediction_score_authorized":False}
    try:
        a=[fetch_exact(name) for name in FILES]
        x.update(status="PASS_ZENODO_EXACT_BYTES_CSV_HEADERS_ONLY",source_files=a)
    except HTTPError as err:x.update(status="STOP_ZENODO_HEADER_DOWNLOAD_HTTP",http_status=err.code)
    except Exception as err:x.update(status="STOP_ZENODO_HEADER_BYTES_OR_SCHEMA",reason_type=type(err).__name__)
    return x
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    x=execute();a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
    print(json.dumps(x,sort_keys=True))
