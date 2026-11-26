#!/usr/bin/env python3
"""Original Weiss et al. Dryad historical XLS: official 1-file byte gate ONLY.

No Excel sheet opened, never read taxon/feeding guild/abundance content,
no Gloor species header or Carpathian response, no ecological scoring.
"""
from __future__ import annotations
import argparse,hashlib,json,urllib.error,urllib.request
from pathlib import Path

from franzen425_dryad_guild_sourceonly import NoRedirect

PRE="docs/FOREST_MACRO_WEISS2016_ORIGINAL_DRYAD_XLS_ONEFILE_GATE_PRESPEC_20261118.md"
AUTHOR_DOI="10.5061/dryad.39k32"
FILENAME="FITBeetleData_CzechRepublic_2007+2008.xls"
FILE_ID=33652
URL="https://datadryad.org/api/v2/files/33652/download"
BYTES=232960
MD5="83f740353530b8f88b05260813704eab"
OLE=bytes.fromhex("d0cf11e0a1b11ae1")

class SourceStop(RuntimeError):pass

def fingerprint_only(source, mime):
    if len(source)!=BYTES:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_LENGTH_MISMATCH")
    if hashlib.md5(source).hexdigest()!=MD5:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_MD5_MISMATCH")
    if not source.startswith(OLE):
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_NOT_OLE2")
    typ=(mime or "").split(";",1)[0].casefold().strip()
    return {
        "source_original_pub_file_ID":FILE_ID,
        "source_original_pub_filename":FILENAME,
        "source_original_byte_size":len(source),
        "source_original_published_MD5_verified":MD5,
        "source_original_binary_SHA256":hashlib.sha256(source).hexdigest(),
        "source_original_legacy_Excel_OLE2_magic_verified":True,
        "source_original_MIME_category":typ if typ in {
            "application/vnd.ms-excel","application/octet-stream",
            "application/x-ole-storage","binary/octet-stream",
        } else "unclassified",
        "source_original_workbook_sheet_or_value_cells_OPENED":0,
        "original_species_guild_table_values_UNREAD":True,
        "original_Gloor_species_and_abundance_UNREAD":True,
        "same_Weiss2016_field_study_not_new_replication":True,
    }

def official_single_file_get():
    # Exactly original publisher file-ID API link, no automatic redirects.
    req=urllib.request.Request(URL,headers={
        "User-Agent":"Structural-Weiss2016-original-author-Dryad-XLS-fingerprint/1.0",
        "Accept":"application/vnd.ms-excel,application/octet-stream;q=0.5",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=50) as resp:
            if resp.status!=200:
                raise SourceStop("SOURCE_WEISS_ORIGINAL_XLS_HTTP_NOT200")
            mime=resp.headers.get("Content-Type","")
            raw=resp.read(250001)
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_WEISS_ORIGINAL_DRYAD_XLS_HTTP_"+str(exc.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_WEISS_ORIGINAL_DRYAD_XLS_TRANSPORT_"+type(exc).__name__) from None
    if len(raw)>250000:
        raise SourceStop("SOURCE_WEISS_ORIGINAL_XLS_TOO_LARGE")
    return fingerprint_only(raw,mime)

def synthetic():
    # Tests format refusal and deterministic digest gate; no original cells.
    sample=OLE+b"\x00"*(BYTES-len(OLE))
    try:
        fingerprint_only(sample,"application/vnd.ms-excel")
        raise AssertionError("unverified MD5 was accepted")
    except SourceStop as ex:
        assert str(ex)=="SOURCE_ORIGINAL_WEISS_XLS_MD5_MISMATCH"
    try:
        fingerprint_only(b"PK\x03\x04"+b"\x00"*(BYTES-4),"application/vnd.ms-excel")
        raise AssertionError("bad workbook passed")
    except SourceStop:pass
    assert URL.endswith("/files/33652/download")
    assert FILE_ID==33652
    print("SYNTHETIC_WEISS2016_LEGACY_XLS_MD5_OLE_SOURCE_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out required")
    obj={
        "schema":"structural.Weiss2016_author_Dryad_XLS_original_byte_only.v1",
        "precommit":PRE,
        "original_DOI":AUTHOR_DOI,
        "original_publisher_file_id":FILE_ID,
        "original_source_workbook_values_opened":False,
        "source_Weiss_species_guild_pair_values_read":0,
        "original_Gloor_Carpathian_beetle_taxa_and_abundance_UNREAD":True,
        "original_Franzen425_blocked_Dryad_XLSX_NOT_RETRIED":True,
        "prior_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
        "new_ecological_result_computed":False,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        obj["source_original_binary_fingerprint_ONLY"]=official_single_file_get()
        obj["status"]="ORIGINAL_WEISS_AUTHOR_XLS_PUBLISHED_BYTES_AND_OLE_VERIFIED"
    except SourceStop as exc:
        obj["status"]=str(exc)
        obj["source_access_or_format_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Weiss2016_original_Dryad_author_XLS_bytes_only.json").write_text(
        json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WEISS2016_DRYAD_ORIGINAL_XLS_BYTE_GATE",obj["status"])
    print("NO_ORIGINAL_SPECIES_TO_GUILD_OR_GLOOR_RESPONSES_OPENED")

if __name__=="__main__":
    main()
