#!/usr/bin/env python3
"""Narrow official-URL format diagnosis, no field observation body parsing."""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
URLS=(
 "https://pmc.ncbi.nlm.nih.gov/articles/instance/11634684/bin/zoae006_suppl_supplementary_material.docx",
 "https://pmc.ncbi.nlm.nih.gov/articles/PMC11634684/bin/zoae006_suppl_supplementary_material.docx")
HOSTS={"pmc.ncbi.nlm.nih.gov","www.ncbi.nlm.nih.gov","cdn.ncbi.nlm.nih.gov"}
CAP=2500000
def safe(url):
    u=urlsplit(url)
    return u.scheme=="https" and u.hostname in HOSTS
def kind(content):
    pre=content[:256].lower().lstrip()
    if content.startswith(b"PK\x03\x04"):return "zip"
    if content.startswith(b"%PDF"):return "pdf"
    if pre.startswith((b"<!doctype html",b"<html",b"<?xml")):return "html_or_xml"
    return "other"
def describe_zip(b):
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        m=z.infolist() # only central directory, no XML file reads
        names={a.filename for a in m}
        if not {"word/document.xml","[Content_Types].xml"}.issubset(names):
            return {"valid_docx":False,"zip_members":len(m)}
        return {"valid_docx":True,"zip_members":len(m),"source_sha256":hashlib.sha256(b).hexdigest()}
def probe(url):
    r={"official_url":url,"biological_content_fields_opened":0}
    try:
        if not safe(url):raise ValueError("Source host invalid")
        with urlopen(Request(url,headers={"User-Agent":"Structural-marine-source-metadata-v1.225"}),timeout=25) as f:
            final=f.url
            if not safe(final):raise ValueError("Untrusted redirect")
            mime=f.headers.get("Content-Type","").split(";")[0].lower().strip()
            b=f.read(CAP+1)
            status=f.status
        if len(b)>CAP:raise ValueError("Source exceeds max")
        r.update(http_status=status,final_host=urlsplit(final).hostname,
                 body_class=kind(b),content_type=mime,downloaded_bytes=len(b))
        if kind(b)=="zip":
            r.update(describe_zip(b))
        else:r["valid_docx"]=False
        r["status"]="PASS_DOCX_SOURCE_ID_ONLY" if r.get("valid_docx") else "STOP_NOT_DOCX"
    except HTTPError as e:
        r.update(status="STOP_HTTP",http_status=e.code)
    except Exception as e:
        r.update(status="STOP_FORMAT_OR_TRANSPORT",reason_class=type(e).__name__)
    return r
def execute():
    r=[probe(url) for url in URLS]
    return {"schema":"structural.zhoushan_ncbi_transport_diagnostic_result.v1_225",
     "source_checks":r,"any_valid_docx":any(x["status"]=="PASS_DOCX_SOURCE_ID_ONLY" for x in r),
     "document_xml_semantically_read":False,"field_species_island_incidence_read":False,
     "original_mammal_outcome_reopened":False,"submission_authorized":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    x=execute();a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
    print(json.dumps(x,sort_keys=True))
