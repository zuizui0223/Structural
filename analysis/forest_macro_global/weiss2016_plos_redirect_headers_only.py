#!/usr/bin/env python3
"""PLOS original supplementary: ONE GET, headers only, do not follow redirect.

Previously rejected original author DOC redirect URI before reading source bytes.
No archived file values, names, authors' guild assignment or Gloor response.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

URL="https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0149506.s001&type=supplementary"
PRESPEC="docs/FOREST_MACRO_WEISS2016_PLOS_OFFICIAL_REDIRECT_SOURCE_PRESPEC_20261118.md"

class SourceStop(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def public_redirect_metadata(location):
    if not location:
        raise SourceStop("SOURCE_PUBLISHER_REDIRECT_LOCATION_EMPTY")
    # Original Location is processed in memory, NEVER included in any output.
    resolved=urllib.parse.urljoin(URL,location)
    p=urllib.parse.urlparse(resolved)
    if len(resolved)>12000:
        raise SourceStop("SOURCE_PUBLISHER_REDIRECT_URL_OVERSIZE")
    pieces=[x for x in p.path.split("/") if x][:3]
    safe_pieces=tuple(x.casefold() if x.casefold() in {
        "plosone","article","file","resource","articles","static","download",
        "files","bin","supplementary","plos"
    } else "other" for x in pieces)
    return {
        "redirect_target_https":p.scheme=="https",
        "redirect_target_host":p.hostname if p.hostname and len(p.hostname)<180 else "unresolved",
        "redirect_target_path_category":list(safe_pieces),
        "redirect_target_query_parameter_NAMES_only":sorted(set(
            q for q,v in urllib.parse.parse_qsl(p.query,keep_blank_values=True)
            if q.isascii() and q.replace("_","").isalnum() and len(q)<=64
        ))[:15],
        "original_redirect_target_sha256":hashlib.sha256(location.encode("utf-8")).hexdigest(),
        "publisher_original_Location_URL_and_query_values_NOT_EXPORTED":True,
    }

def source_one_no_follow():
    req=urllib.request.Request(URL,headers={
        "Accept":"application/msword,application/octet-stream;q=0.8,*/*;q=0.2",
        "User-Agent":"Structural-science-PLOS2016-header-redirect-provenance-only/1.0",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=35) as response:
            return {
                "original_publisher_HTTP_status":response.status,
                "original_publisher_content_type_category":response.headers.get("Content-Type","").split(";",1)[0].lower()[:100],
                "original_file_bytes_READ":0,
                "original_source_redirect_followed":False,
                "status":"SOURCE_ORIGINAL_PLOS_DIRECT_PUBLIC_200_HEADERS_ONLY"
                if response.status==200 else "SOURCE_ORIGINAL_PLOS_UNEXPECTED_NONREDIRECT_STATUS",
            }
    except urllib.error.HTTPError as exc:
        code=exc.code
        receipt={
            "original_publisher_HTTP_status":code,
            "original_file_bytes_READ":0,
            "original_source_redirect_followed":False,
        }
        if 300<=code<400:
            receipt["official_publisher_redirect_header_only"]=public_redirect_metadata(
                exc.headers.get("Location",""))
            receipt["status"]="SOURCE_PLOS_REDIRECT_HEADER_ONLY_NO_FILE_BYTES"
        else:
            receipt["status"]="SOURCE_ORIGINAL_PLOS_HTTP_"+str(code)
        return receipt
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_TRANSPORT_"+type(exc).__name__) from None

def known_truth():
    a=public_redirect_metadata("https://journals.plos.org/plosone/article/file?id=example&type=supplementary")
    assert a["redirect_target_host"]=="journals.plos.org"
    assert a["redirect_target_query_parameter_NAMES_only"]==["id","type"]
    b=public_redirect_metadata("/plosone/article/file?id=example&type=supplementary")
    assert b["redirect_target_https"]
    assert "example" not in json.dumps(a)
    print("SYNTHETIC_PLOS_REDIRECT_HEADER_SANITIZATION_NO_ORIGINAL_RESPONSE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    obj={
       "schema":"structural.Weiss2016_original_PLOS_s1_headers_redirect_only.v1",
       "precommit":PRESPEC,
       "DOI":"10.1371/journal.pone.0149506.s001",
       "source_Gloor_beetles_or_guild_DOC_values_READ":False,
       "previous_Franzen_Dryad_HTTP401_NOT_RETRIED":True,
       "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
       "eBird_used":False,"TinyFish_used":False,
    }
    try:
        obj["original_publisher_one_header_only"]=source_one_no_follow()
        obj["status"]=obj["original_publisher_one_header_only"]["status"]
    except SourceStop as exc:
        obj["status"]=str(exc)
        obj["source_or_transport_STOP_not_organism_result"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Weiss2016_original_PLOS_s1_publisher_redirect_headers_only.json").write_text(
        json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WEISS2016_PLOS_ORIGINAL_REDIRECT_HEADER_DIAGNOSTIC",obj["status"])
    print("NO_ORIGINAL_GUILD_OR_CARPATHIAN_SPECIES_VALUES_OPENED")

if __name__=="__main__":main()
