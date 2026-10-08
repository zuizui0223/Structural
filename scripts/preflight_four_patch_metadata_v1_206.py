#!/usr/bin/env python3
"""Public metadata only. Hard-coded URLs exclude biological-file download."""
import json, re, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
DOI="doi:10.5061/dryad.bf4rk74"
NAME="summer 2017 metapop expt data for dryad.csv"
ROOT="https://datadryad.org"
DATASET="/api/v2/datasets/doi%3A10.5061%2Fdryad.bf4rk74"
def get_json(path):
    if path != DATASET and not re.fullmatch(r"/api/v2/versions/[0-9]+/files",path):
        raise ValueError("Non-metadata endpoint forbidden")
    req=Request(ROOT+path,headers={"Accept":"application/json",
      "User-Agent":"Structural-public-metadata-preflight-1.206"})
    with urlopen(req,timeout=20) as res:
        if urlsplit(res.url).hostname != "datadryad.org":
            raise ValueError("Off-domain redirect")
        if "json" not in res.headers.get("Content-Type","").lower():
            raise ValueError("Non-JSON response")
        payload=res.read(1000001)
    if len(payload)>1000000: raise ValueError("Metadata size over cap")
    return json.loads(payload.decode("utf-8"))
def validate(dataset,files):
    if dataset.get("identifier","").lower()!=DOI: raise ValueError("DOI mismatch")
    links=dataset.get("_links",{})
    version_link=links.get("stash:version",{}).get("href","")
    match=re.fullmatch(r"/api/v2/versions/([0-9]+)",version_link)
    if not match: raise ValueError("Unknown version")
    records=files.get("_embedded",{}).get("stash:files")
    if not isinstance(records,list) or len(records)!=1:
        raise ValueError("Unexpected file metadata shape")
    rec=records[0]
    if rec.get("path")!=NAME or not isinstance(rec.get("size"),int) or rec["size"]<=0:
        raise ValueError("Exact expected public CSV identity unsupported")
    return {"status":"PASS_EXACT_DRYAD_FILE_METADATA_ONLY",
      "doi":DOI,"version_id":int(match.group(1)),
      "dataset_version_number":dataset.get("versionNumber"),
      "filename":NAME,"size_bytes":rec["size"],
      "digest_type":rec.get("digestType"),
      "digest":rec.get("digest"),
      "biological_response_rows_read":0,"data_file_downloaded":False,
      "csv_header_decoded":False,"ecological_scoring_authorized":False}
def execute():
    try:
        dataset=get_json(DATASET)
        href=dataset.get("_links",{}).get("stash:version",{}).get("href","")
        match=re.fullmatch(r"/api/v2/versions/([0-9]+)",href)
        if not match: raise ValueError("Unverified dataset version link")
        listing=get_json("/api/v2/versions/"+match.group(1)+"/files")
        return validate(dataset,listing)
    except HTTPError as e:
        return {"status":"STOP_DRYAD_METADATA_HTTP","http_status":e.code,
          "biological_response_rows_read":0,"data_file_downloaded":False,
          "ecological_scoring_authorized":False}
    except Exception as e:
        return {"status":"STOP_DRYAD_METADATA_SCHEMA_OR_TRANSPORT",
          "reason_class":type(e).__name__,"biological_response_rows_read":0,
          "data_file_downloaded":False,"ecological_scoring_authorized":False}
if __name__=="__main__":
    out=execute()
    path=Path(sys.argv[1])
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
