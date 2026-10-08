#!/usr/bin/env python3
"""v1.207: exact public file byte hash and FIRST CSV HEADER only, no row parsing."""
import csv, hashlib, io, json, re, sys
from pathlib import Path
from urllib import request
from urllib.parse import urlsplit
from urllib.error import HTTPError
FIXED_SIZE=144273
FIXED_MD5="f476181d3b701413299264ec075a91e5"
FIXED_NAME="summer 2017 metapop expt data for dryad.csv"
VER_URL="https://datadryad.org/api/v2/versions/29609/files"
def _request(url,limit):
    if url != VER_URL and not re.fullmatch(r"https://datadryad.org/api/v2/files/[0-9]+/download",url):
        raise ValueError("Unsupported source URL")
    req=request.Request(url,headers={"User-Agent":"Structural-exact-source-header-v1.207"})
    with request.urlopen(req,timeout=25) as res:
        host=urlsplit(res.url).hostname or ""
        if host!="datadryad.org" and not (host.endswith(".amazonaws.com") and "dryad" in host):
            raise ValueError("Unrecognized public data redirect")
        content=res.read(limit+1)
    if len(content)>limit: raise ValueError("Body length over immutable ceiling")
    return content
def _source_url(files):
    records=files.get("_embedded",{}).get("stash:files")
    if not isinstance(records,list) or len(records)!=1:
        raise ValueError("No exactly one file in frozen Dryad version")
    f=records[0]
    if f.get("path")!=FIXED_NAME or f.get("size")!=FIXED_SIZE:
        raise ValueError("File source identity mismatch")
    if str(f.get("digest","")).lower()!=FIXED_MD5 or str(f.get("digestType","")).lower()!="md5":
        raise ValueError("Source checksum metadata mismatch")
    selflink=f.get("_links",{}).get("self",{}).get("href","")
    link=re.fullmatch(r"(?:https://datadryad.org)?/api/v2/files/([0-9]+)",selflink)
    if not link: raise ValueError("No exact Dryad file ID link")
    return "https://datadryad.org/api/v2/files/"+link.group(1)+"/download",int(link.group(1))
def header_only(data):
    if len(data)!=FIXED_SIZE: raise ValueError("File length mismatch")
    if hashlib.md5(data).hexdigest()!=FIXED_MD5: raise ValueError("File MD5 mismatch")
    first=data.split(b"\n",1)[0]
    if len(first)>4096 or not first: raise ValueError("CSV first line not bounded")
    header=next(csv.reader(io.StringIO(first.decode("utf-8-sig").rstrip("\r"))))
    expected={"Day","metapop","disp.rate","pp.g.l"}
    eu={f"Eupl.{i}" for i in range(1,5)}
    tet={f"Tet.pres{i}" for i in range(1,5)}
    tet2={f"Tet.pres.{i}" for i in range(1,5)}
    if len(header)!=12 or len(set(header))!=12 or not expected.issubset(set(header)):
        raise ValueError("Frozen CSV column count or fixed fields mismatch")
    if set(header)-expected-eu-tet-tet2:
        raise ValueError("Unexpected density or prey fields")
    if not eu.issubset(set(header)) or not (tet.issubset(set(header)) or tet2.issubset(set(header))):
        raise ValueError("Four unique patch fields not verified")
    return header
def execute():
    receipt={"biological_rows_semantically_read":0,"model_refits":0,
             "ecological_scores":0,"downstream_outcome_access_authorized":False}
    try:
        f=json.loads(_request(VER_URL,1000000).decode("utf-8"))
        url,file_id=_source_url(f)
        data=_request(url,FIXED_SIZE)
        digest=hashlib.sha256(data).hexdigest()
        header=header_only(data)
        receipt.update(status="PASS_BYTE_AND_HEADER_PREOUTCOME",
           source_file_id=file_id,source_file_size=len(data),
           source_md5=FIXED_MD5,source_sha256=digest,header=header,
           header_field_count=len(header))
    except HTTPError as ex:
        receipt.update(status="STOP_PUBLIC_FILE_HTTP",http_status=ex.code)
    except Exception as ex:
        receipt.update(status="STOP_BYTE_OR_HEADER_SCHEMA",reason_class=type(ex).__name__)
    return receipt
if __name__=="__main__":
    record=execute()
    target=Path(sys.argv[1]);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(record,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(record,sort_keys=True))
