#!/usr/bin/env python3
"""Weiss et al 2016 author PLOS S1 species/guild table: BYTE-ONLY admission.

Never decodes DOC content or any guild/species values. Do NOT touch the
separately sealed Gloor Carpathian original beetle data or Franzén Dryad.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_WEISS2016_TROPHIC_SOURCE_PRESPEC_20261118.md"
URL="https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0149506.s001&type=supplementary"
DOI="10.1371/journal.pone.0149506.s001"
MAX_SIZE=2*1024*1024
OLE_MAGIC=bytes.fromhex("d0cf11e0a1b11ae1")

class SourceStop(RuntimeError):
    pass

def source_url_valid(url):
    p=urllib.parse.urlparse(url)
    allowed=urllib.parse.urlparse(URL)
    if (p.scheme!="https" or p.hostname!="journals.plos.org" or p.username or
        p.password or p.port or p.fragment or
        p.path!=allowed.path or
        urllib.parse.parse_qs(p.query,strict_parsing=True)!=
        {"id":[DOI],"type":["supplementary"]}):
        raise SourceStop("SOURCE_NOT_ORIGINAL_PLOS_ARTICLE_SUPPLEMENT_ENDPOINT")
    return True

class SamePublisherOriginalOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.count=0
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        self.count+=1
        if self.count>1:
            raise SourceStop("SOURCE_ORIGINAL_PLOS_REDIRECT_CHAIN_NOT_ALLOWED")
        source_url_valid(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def original_one_get():
    source_url_valid(URL)
    request=urllib.request.Request(URL,headers={
        "Accept":"application/msword,application/octet-stream;q=0.9,*/*;q=0.2",
        "User-Agent":"Structural-science-Weiss2016-author-PLOS-supplement-source-only/1.0",
    })
    safe_handler=SamePublisherOriginalOnlyRedirect()
    try:
        with urllib.request.build_opener(safe_handler).open(request,timeout=45) as resp:
            if resp.status!=200:
                raise SourceStop("SOURCE_ORIGINAL_PLOS_NOT_HTTP200")
            mime=resp.headers.get("Content-Type","")
            body=resp.read(MAX_SIZE+1)
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_ORIGINAL_PLOS_HTTP_"+str(ex.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as ex:
        raise SourceStop("SOURCE_ORIGINAL_PLOS_TRANSPORT_"+type(ex).__name__) from None
    if not body or len(body)>MAX_SIZE:
        raise SourceStop("SOURCE_PLOS_ORIGINAL_BINARY_EMPTY_OR_OVERSIZE")
    result=fingerprint_format_only(body,mime)
    result["original_publisher_host"]="journals.plos.org"
    result["original_publisher_original_supplement_doi"]=DOI
    result["original_request_count"]=1
    result["source_redirects_same_publisher_original_url_only"]=safe_handler.count
    return result

def fingerprint_format_only(raw,mime):
    if not raw.startswith(OLE_MAGIC):
        raise SourceStop("SOURCE_PLOS_ORIGINAL_NOT_OLE_DOC_FILE")
    if not (10_000<=len(raw)<=MAX_SIZE):
        raise SourceStop("SOURCE_PLOS_ORIGINAL_DOC_SIZE_OUTSIDE_GUARD")
    mime=(mime.split(";",1)[0].strip().casefold() if mime else "")
    safe_mimes={
        "application/msword", "application/octet-stream",
        "application/x-ole-storage", "binary/octet-stream",
    }
    return {
        "original_source_binary_byte_size":len(raw),
        "original_source_binary_SHA256":hashlib.sha256(raw).hexdigest(),
        "original_format":"OLE2_Document_Magic_Only",
        "original_media_type_class":mime if mime in safe_mimes else "unknown",
        "author_original_species_guild_table_rows_PARSED":0,
        "original_beetle_species_names_guild_labels_NOT_OPENED":True,
        "original_Gloor_species_abundance_environment_outcomes_READ":False,
        "author_reported_512_species_NOT_independently_recounted":True,
        "six_published_trophic_codes_NOT_remapped":True,
    }

def known_truth():
    assert source_url_valid(URL)
    raw=OLE_MAGIC+b"\x00"*15000
    x=fingerprint_format_only(raw,"application/msword")
    assert x["original_format"]=="OLE2_Document_Magic_Only"
    assert x["author_original_species_guild_table_rows_PARSED"]==0
    for other in (
      URL.replace("journals.plos.org","datadryad.org"),
      URL.replace("s001","s002"),
      URL.replace("type=supplementary","type=article"),
      URL+"&token=example",
    ):
        try:
            source_url_valid(other)
            raise AssertionError("unfrozen original URL admitted")
        except SourceStop:pass
    for fake in (b"<html>blocked</html>"+b" "*15000, b"%PDF-"+b" "*15000, b"PK\x03\x04"+b" "*15000):
        try:
            fingerprint_format_only(fake,"text/html")
            raise AssertionError("unoriginal DOC admitted")
        except SourceStop:pass
    print("SYNTHETIC_WEISS2016_PLOS_AUTHOR_SOURCE_IEC_DOC_MIME_AND_NO_SPECIES_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:parser.error("--out required")
    out={
      "schema":"structural.Weiss2016_PLOS_S1_original_guild_document_metadata.v1",
      "prespec":PRESPEC,
      "source_publisher":"PLOS_ONE",
      "source_original_supplement_doi":DOI,
      "original_Gloor_Carpathian_species_response_READ":False,
      "original_Franzen_Dryad_blocked_source_NOT_RETRIED":True,
      "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
      "new_ecological_effect_estimated":False,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        out["original_source_fingerprint_ONLY"]=original_one_get()
        out["status"]="ORIGINAL_PLOS_SUPPLEMENT_OLE_VERIFIED_SOURCE_ONLY"
    except SourceStop as exc:
        out["status"]=str(exc)
        out["source_transport_or_format_STOP_not_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Weiss2016_original_PLOS_S1_guild_doc_source_fingerprint_only.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WEISS2016_AUTHOR_PLOS_GUILD_SOURCE_STATUS",out["status"])
    print("NO_SPECIES_GUILD_VALUES_OR_CARPATHIAN_OUTCOMES_OPENED")

if __name__=="__main__":
    main()
