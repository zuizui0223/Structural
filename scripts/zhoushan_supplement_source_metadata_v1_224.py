#!/usr/bin/env python3
"""Public article supplementary ZIP metadata only, never extract or parse document.xml."""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
URL="https://pmc.ncbi.nlm.nih.gov/articles/instance/11634684/bin/zoae006_suppl_supplementary_material.docx"
ALLOW={"pmc.ncbi.nlm.nih.gov","www.ncbi.nlm.nih.gov","cdn.ncbi.nlm.nih.gov"}
MAX_SIZE=2500000
NEEDED={"[Content_Types].xml","word/document.xml"}
def safe_url(url):
    u=urlsplit(url)
    return u.scheme=="https" and u.hostname in ALLOW
def member_metadata(raw):
    if len(raw)>MAX_SIZE or not raw.startswith(b"PK\x03\x04"):raise ValueError("Not bounded Office ZIP")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members=z.infolist()  # Central directory only. Never call z.open/read!
        if not NEEDED.issubset({v.filename for v in members}):raise ValueError("Missing DOCX core")
        if any(v.file_size>15000000 or v.flag_bits&1 for v in members):raise ValueError("Unsafe compressed metadata")
        return {"zip_member_count":len(members),
          "content_types_member_present":True,
          "document_xml_member_present":True,
          "document_xml_bytes_read":0,
          "table_or_field_response_values_read":0}
def execute():
    receipt={"schema":"structural.zhoushan_official_docx_metadata.v1_224",
      "source":URL,"document_xml_bytes_read":0,"table_or_field_response_values_read":0,
      "original_mammal_outcomes_read":0,"ecological_scoring_authorized":False}
    try:
        if not safe_url(URL):raise ValueError("Unexpected source host")
        req=Request(URL,headers={"User-Agent":"Structural-geography-field-preflight-v1.224"})
        with urlopen(req,timeout=25) as r:
            if not safe_url(r.url):raise ValueError("Off-host redirect")
            payload=r.read(MAX_SIZE+1)
        checks=member_metadata(payload)
        receipt.update(status="PASS_OFFICIAL_ZHOU_SHAN_SOURCE_FINGERPRINT_ONLY",
          source_file_size_bytes=len(payload),
          source_sha256=hashlib.sha256(payload).hexdigest(),**checks)
    except HTTPError as exc:
        receipt.update(status="STOP_OFFICIAL_SUPPLEMENT_HTTP",http_code=exc.code)
    except Exception as exc:
        receipt.update(status="STOP_SUPPLEMENT_TRANSPORT_OR_ZIP_SCHEMA",reason_class=type(exc).__name__)
    return receipt
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();res=execute();a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
    print(json.dumps(res,sort_keys=True))
