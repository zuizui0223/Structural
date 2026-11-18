#!/usr/bin/env python3
"""Original PLOS S1 DOC bytes from publisher-issued, fingerprinted R2 redirect.

Source-only: no species/guild/trait table parse. Never open Gloor species or
old Dryad blocked source. PLOS 302 Location must match pre-recorded SHA256.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PRESPEC="docs/FOREST_MACRO_WEISS2016_PLOS_R2_ISSUED_SOURCE_PRESPEC_20261118.md"
PLOS_URL="https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0149506.s001&type=supplementary"
R2_HOST="corpus-prod.f505aadad1e46610c8f8563037eb3c4b.r2.cloudflarestorage.com"
LOCATION_SHA="2595cce0ff5b38d31337d871b664fe7bb3878ab55c1ed714eb7407845cbeb5fc"
DOI="10.1371/journal.pone.0149506.s001"
OLE_MAGIC=bytes.fromhex("d0cf11e0a1b11ae1")
MAX_SIZE=2*1024*1024

class SourceStop(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def validate_original_r2_location(loc,sha=LOCATION_SHA):
    if not isinstance(loc,str) or not 10<len(loc)<12000:
        raise SourceStop("SOURCE_ORIGINAL_PLOS_LOCATION_EMPTY_OR_OVERSIZE")
    if hashlib.sha256(loc.encode("utf-8")).hexdigest()!=sha:
        raise SourceStop("SOURCE_PLOS_302_LOCATION_SHA_CHANGED")
    p=urllib.parse.urlparse(loc)
    if p.scheme!="https" or p.hostname!=R2_HOST or p.username or p.password or p.port or p.fragment:
        raise SourceStop("SOURCE_ORIGINAL_ISSUED_R2_HOST_OR_URL_NOT_ALLOWED")
    # The complete source-issued URL (including any query) is SHA-frozen above.
    # Do not inspect, export, build or modify query values.
    if not p.path.startswith("/") or len(p.path)<2 or any(
        token in (".","..") for token in urllib.parse.unquote(p.path).split("/")
    ):
        raise SourceStop("SOURCE_ORIGINAL_ISSUED_R2_OBJECT_PATH_UNSAFE")
    return loc

def original_publisher_location_one_get():
    req=urllib.request.Request(PLOS_URL,headers={
        "Accept":"application/msword,application/octet-stream;q=0.9,*/*;q=0.2",
        "User-Agent":"Structural-PLOS-2016-pinned-source-issuer-verification/1.0"
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=40):
            raise SourceStop("SOURCE_PLOS_EXPECTED_302_BUT_DIRECT_RESPONSE")
    except urllib.error.HTTPError as exc:
        if exc.code!=302:
            raise SourceStop("SOURCE_PLOS_ORIGINAL_UNEXPECTED_HTTP_"+str(exc.code)) from None
        location=exc.headers.get("Location")
        return validate_original_r2_location(location)
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_PLOS_ISSUER_TRANSPORT_"+type(exc).__name__) from None

def source_doc_bytes_only(loc):
    validate_original_r2_location(loc)
    req=urllib.request.Request(loc,headers={
        "Accept":"application/msword,application/octet-stream;q=0.9,*/*;q=0.2",
        "User-Agent":"Structural-PLOS-2016-original-issuer-R2-legal-guild-source/1.0"
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=55) as response:
            if response.status!=200:
                raise SourceStop("SOURCE_R2_PLOS_ORIGINAL_NOT_HTTP200")
            mime=response.headers.get("Content-Type","")
            raw=response.read(MAX_SIZE+1)
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_R2_PLOS_ORIGINAL_HTTP_"+str(exc.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_R2_PLOS_ORIGINAL_TRANSPORT_"+type(exc).__name__) from None
    if not raw.startswith(OLE_MAGIC):
        raise SourceStop("SOURCE_R2_ORIGINAL_NOT_EXPECTED_OLE_DOC")
    if not 10000<=len(raw)<=MAX_SIZE:
        raise SourceStop("SOURCE_R2_ORIGINAL_DOC_SIZE_GUARD_STOP")
    media=mime.split(";",1)[0].casefold().strip()
    return {
        "original_publisher_issued_object_host":R2_HOST,
        "original_PLOS_302_Location_SHA256_verified":LOCATION_SHA,
        "original_external_object_http_status":200,
        "original_author_S1_binary_size":len(raw),
        "original_author_S1_binary_sha256":hashlib.sha256(raw).hexdigest(),
        "original_author_S1_binary_OLE_DOC_magic":True,
        "original_author_S1_media_class":media if media in {
            "application/msword","application/octet-stream",
            "binary/octet-stream","application/x-ole-storage"
        } else "unknown",
        "original_DOC_species_table_guild_values_parsed":0,
        "source_species_names_body_numeric_values_or_guild_values_READ":False,
        "Carpathian_Gloor_original_species_response_READ":False,
    }

def known_truth():
    # Synthetic *location* fingerprint is separate from published issuer SHA.
    demo="https://"+R2_HOST+"/original-object-S1.doc"
    sh=hashlib.sha256(demo.encode()).hexdigest()
    assert validate_original_r2_location(demo,sha=sh)==demo
    for invalid in (
        demo.replace("https://","http://"),
        demo.replace(R2_HOST,"evil.example.org"),
        demo.replace("/original-object-S1.doc","/../private"),
    ):
        try:
            validate_original_r2_location(invalid,sha=hashlib.sha256(invalid.encode()).hexdigest())
            raise AssertionError("unauthorized PLOS issued location allowed")
        except SourceStop:pass
    # An issuer query is legal ONLY as part of the exact entire pinned URI.
    signed=demo+"?source-issued-query=1"
    signed_sha=hashlib.sha256(signed.encode()).hexdigest()
    assert validate_original_r2_location(signed,sha=signed_sha)==signed
    try:
        validate_original_r2_location(signed,sha=sh)
        raise AssertionError("changed issuer query was not rejected")
    except SourceStop:pass
    print("SYNTHETIC_PLOS_ORIGINAL_R2_LOCATION_PINNING_AND_NO_BIOLOGY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    x=p.parse_args()
    known_truth()
    if x.test:return
    if x.out is None:p.error("--out required")
    r={
        "schema":"structural.Weiss2016_original_PLOS_S1_issued_R2_byte_gate.v1",
        "prespec":PRESPEC,
        "author_S1_DOI":DOI,
        "previous_original_Franzen425_Dryad_HTTP401_NOT_RETRIED":True,
        "original_Gloor_Carpathian_species_or_capture_outcome_READ":False,
        "prior_Finland_Germany_PREDICTS_NEON_BALA_GEB_scores_UNCHANGED":True,
        "new_guild_or_deadwood_ecological_effect_ESTIMATED":False,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        loc=original_publisher_location_one_get()
        r["original_PLOS_issuer_verified"]=True
        r["original_supplement_byte_fingerprint_only"]=source_doc_bytes_only(loc)
        r["status"]="SOURCE_PLOS_ISSUED_ORIGINAL_OLE_DOC_FINGERPRINT_ONLY"
    except SourceStop as exc:
        r["status"]=str(exc)
        r["source_or_transport_STOP_not_biological_evidence"]=True
    x.out.mkdir(parents=True,exist_ok=True)
    (x.out/"Weiss2016_original_PLOS_issuer_R2_S1_DOC_fingerprint_only.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WEISS2016_ORIGINAL_PLOS_R2_GUILD_SOURCE",r["status"])
    print("NO_AUTHOR_GUILD_VALUES_OR_CARPATHIAN_RESPONSES_OPENED")

if __name__=="__main__": main()
