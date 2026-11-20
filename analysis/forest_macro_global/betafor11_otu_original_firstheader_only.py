#!/usr/bin/env python3
"""Source-locked BETA-FOR ORIGINAL OTU table FIRST HEADER ONLY.

Streams original com_singletons.csv bytes solely for whole-file MD5
verification. The only semantic parse is its FIRST physical header; biological
rows, OTU values, and all species IDs remain opaque and unexported.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from betafor11_publisher_metadata_preintake_only import (
    FILES, get_official_metadata_only, SourceStop,
)
from betafor11_v2_missingversion_firstheader_sourceonly import validate_publisher_v2
from betafor11_information_firstheader_gate import (
    source_publisher_file_link, official_original_file_bytes, NoRedirect,
)

PRESPEC = "docs/FOREST_MACRO_BETAFOR11_OTU_MATRIX_HEADER_ONLY_PREFREEZE_20261120.md"
SOURCE_FILE = "com_singletons.csv"
ORIGINAL_MD5 = FILES[SOURCE_FILE]
EXPECTED_SAMPLES = 594
EXPECTED_PATCHES = 99
FILE_MAX_BYTES = 80 * 1024 * 1024
HEADER_MAX_BYTES = 2 * 1024 * 1024
GENERIC = frozenset({"sample","patch","otu","species","taxon","id","x"})
ALLOWED_DELIMS = (",",";","\t")


def published_otutable_link(record):
    # Validated official record inventory before this call, exactly one frozen
    # original file. Never fabricate alternatives or allow cross-origin redirect.
    entry = [q for q in record["files"] if q.get("key")==SOURCE_FILE]
    if len(entry)!=1:
        raise SourceStop("OTU_FIRSTHEADER_ORIGINAL_MEMBER_NOT_UNIQUE")
    q=entry[0]
    size=q.get("size")
    if type(size) is not int or not 1<=size<=FILE_MAX_BYTES:
        raise SourceStop("OTU_FIRSTHEADER_PUBLISHER_SIZE_UNSUPPORTED")
    if q.get("checksum") != "md5:"+ORIGINAL_MD5:
        raise SourceStop("OTU_FIRSTHEADER_MD5_PUBLISHER_CHANGED")
    links=q.get("links")
    link=(links.get("content") or links.get("self")) if isinstance(links,dict) else None
    if not isinstance(link,str):
        raise SourceStop("OTU_FIRSTHEADER_PUBLISHER_LINK_MISSING")
    p=urllib.parse.urlparse(link)
    if (p.scheme!="https" or p.hostname!="zenodo.org"
        or p.username or p.password or p.port or p.query or p.fragment):
        raise SourceStop("OTU_FIRSTHEADER_NON_ORIGINAL_PUBLISHER_HOST")
    path_a="/api/records/15371332/files/"+SOURCE_FILE+"/content"
    path_b=re.compile(r"^/api/files/[0-9a-fA-F-]{36}/"+re.escape(SOURCE_FILE)+r"$")
    if p.path!=path_a and not path_b.fullmatch(p.path):
        raise SourceStop("OTU_FIRSTHEADER_ORIGINAL_PUBLISHER_FILE_PATH_UNRECOGNIZED")
    return link,size


def stream_md5_only_capture_first_header(reader, expected_size, expected_md5):
    """Opaque hash all bytes; retain ONLY first line, never parse data rows."""
    digest=hashlib.md5()
    total=0
    first=bytearray()
    first_closed=False
    while True:
        chunk=reader.read(64*1024)
        if not chunk:
            break
        total+=len(chunk)
        if total>expected_size or total>FILE_MAX_BYTES:
            raise SourceStop("OTU_ORIGINAL_DOWNLOAD_OVER_EXPECTED_SIZE")
        digest.update(chunk)
        if not first_closed:
            pos=chunk.find(b"\n")
            if pos>=0:
                first+=chunk[:pos]
                first_closed=True
            else:
                first+=chunk
            if len(first)>HEADER_MAX_BYTES:
                raise SourceStop("OTU_HEADER_LONGER_THAN_FROZEN_2MB")
    if total!=expected_size or digest.hexdigest()!=expected_md5:
        raise SourceStop("OTU_ORIGINAL_MEMBER_FULL_MD5_OR_BYTE_SIZE_MISMATCH")
    if not first_closed:
        raise SourceStop("OTU_ORIGINAL_FILE_NO_FIRST_HEADER_NEWLINE")
    return bytes(first),total


def original_otu_header_streamed(link,size):
    req=urllib.request.Request(
        link,headers={"Accept":"*/*",
                       "User-Agent":"Structural-BETAFOR11-firstheader-opaque-MD5/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=85) as h:
            if h.status!=200:
                raise SourceStop("OTU_PUBLISHER_ORIGINAL_HTTP_NOT200")
            return stream_md5_only_capture_first_header(h,size,ORIGINAL_MD5)
    except urllib.error.HTTPError as e:
        raise SourceStop("OTU_PUBLISHER_ORIGINAL_HTTP_"+str(e.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("OTU_PUBLISHER_ORIGINAL_TRANSPORT_"+type(e).__name__) from None


def source_method_label_universe(info_binary):
    try:
        content=info_binary.decode("utf-8-sig")
        rows=csv.DictReader(io.StringIO(content,newline=""),delimiter=";",strict=True)
        if rows.fieldnames != ["patch","sample","firstday","lastday","meanday","treatment","X","Y"]:
            raise SourceStop("SOURCE_INFO_HEADER_NO_LONGER_FROZEN")
        ids=[]
        for row in rows:
            if not isinstance(row,dict) or row.get(None) is not None:
                raise SourceStop("SOURCE_INFO_ID_ROWS_UNEXPECTED_CSV")
            patch=row["patch"].strip()
            sample=row["sample"].strip()
            if not patch or not sample:
                raise SourceStop("SOURCE_INFO_MISSING_ORIGINAL_SAMPLE_KEY")
            ids.append((patch,sample))
    except (UnicodeError,csv.Error):
        raise SourceStop("SOURCE_INFO_LABEL_CSV_PARSE_STOP") from None
    if len(ids)!=EXPECTED_SAMPLES or len(set(ids))!=EXPECTED_SAMPLES:
        raise SourceStop("SOURCE_INFO_FIXED_594_SAMPLE_PAIR_DRIFT")
    patches=set(x for x,_ in ids)
    if len(patches)!=EXPECTED_PATCHES:
        raise SourceStop("SOURCE_INFO_FIXED_99_PATCH_UNIVERSE_DRIFT")
    sample_labels=[s for _,s in ids]
    return set(sample_labels), patches, len(set(sample_labels))


def firstheader_orientation_audit(first_line, sample_set, patch_set, n_unique_sample):
    try:
        original=first_line.decode("utf-8-sig").rstrip("\r")
    except UnicodeError:
        raise SourceStop("OTU_HEADER_NON_UTF8")
    trials=[]
    for delim in ALLOWED_DELIMS:
        try:
            fields=next(csv.reader([original],delimiter=delim,strict=True))
        except (StopIteration,csv.Error):
            continue
        trials.append((len(fields),delim,fields))
    if not trials:
        raise SourceStop("OTU_HEADER_NO_VALID_CSV_DELIMITER")
    trials.sort(reverse=True,key=lambda x:x[0])
    if len(trials)<1 or trials[0][0]<2 or (len(trials)>1 and trials[0][0]==trials[1][0]):
        raise SourceStop("OTU_HEADER_DELIMITER_AMBIGUOUS")
    n,delim,fields=trials[0]
    if n>50000:
        raise SourceStop("OTU_HEADER_FIELD_COUNT_UNSUPPORTED")
    match_samples=sum(1 for f in fields if f.strip() in sample_set)
    match_patches=sum(1 for f in fields if f.strip() in patch_set)
    generic_counts={label:sum(1 for f in fields if f.strip().casefold()==label)
                    for label in sorted(GENERIC)}
    return {
        "schema":"structural.BETA_FOR_2025_response_first_header_orientation_audit.v1",
        "status":(
            "SOURCE_RESPONSE_FIRST_HEADER_SCHEMA_ONLY_MATCH_READY_FOR_AUTHOR_CODEBOOK"
            if match_samples>0 or match_patches>0 else
            "SOURCE_RESPONSE_FIRST_HEADER_SCHEMA_ONLY_UNMATCHED"
        ),
        "first_header_full_source_sha256":hashlib.sha256(first_line).hexdigest(),
        "first_header_field_count":n,
        "first_header_delimiter_class":(
            "comma" if delim=="," else "semicolon" if delim==";" else "tab"),
        "original_method_594_rows_99_patches_verified_again":True,
        "distinct_global_source_sample_literal_count":n_unique_sample,
        "raw_header_tokens_matching_source_sample_literals":match_samples,
        "raw_header_tokens_matching_source_patch_literals":match_patches,
        "predeclared_generic_header_token_counts":generic_counts,
        "header_fields_not_released_or_saved":True,
        "taxon_IDs_and_OTU_abundance_rows_NOT_PARSED":True,
        "source_OTU_numeric_cells_parsed":0,
        "new_biodiversity_effects":0,
        "orientation_remains_to_be_confirmed_from_author_codebook":True,
    }


def run():
    record=get_official_metadata_only()
    v2=validate_publisher_v2(record)
    if not v2["original_six_filenames_MD5s_and_sizes_verified"]:
        raise SourceStop("SOURCE_PUBLISHER_SIX_FILE_GATE_NOT_PASS")
    info_url,info_size=source_publisher_file_link(record)
    original_info=official_original_file_bytes(info_url,info_size)
    samples,patches,unique_n=source_method_label_universe(original_info)
    link,size=published_otutable_link(record)
    first,received=original_otu_header_streamed(link,size)
    audit=firstheader_orientation_audit(first,samples,patches,unique_n)
    return {
        "status":audit["status"],
        "original_publisher_file_MD5":ORIGINAL_MD5,
        "original_publisher_complete_byte_size_verified":size,
        "original_response_file_full_opaque_bytes_streamed_for_MD5_only":received,
        "original_information_file_MD5_pinned_also_verified":True,
        "original_community_firstheader_only":audit,
        "actual_original_organism_response_value_rows_parsed":0,
        "original_OTU_spp_identifier_values_exported":False,
        "source_method_raw_sample_and_site_IDs_exported":False,
        "other_original_four_source_members_NOT_requested":True,
    }


def synthetic():
    info=("patch;sample;firstday;lastday;meanday;treatment;X;Y\n"
          "B04_P1;S1;3;4;3.5;T1;;\n"
          "B04_P1;S2;5;6;5.5;T1;;\n"
          ).encode()
    # Synthetic private fixture exercises exact label and no-body export only.
    assert len({("B04_P1","S1")})==1
    fake=b"OTU,S1,S2\nOTU_SECRET,20,5\n"
    first,size=stream_md5_only_capture_first_header(
        io.BytesIO(fake),len(fake),hashlib.md5(fake).hexdigest()
    )
    assert size==len(fake)
    assert b"OTU_SECRET" not in first
    q=firstheader_orientation_audit(first,{"S1","S2"},{"B04_P1"},2)
    assert q["raw_header_tokens_matching_source_sample_literals"]==2
    assert q["source_OTU_numeric_cells_parsed"]==0
    assert "OTU_SECRET" not in json.dumps(q)
    try:
        stream_md5_only_capture_first_header(io.BytesIO(fake),len(fake),"0"*32)
    except SourceStop:
        pass
    else:
        raise AssertionError("Original MD5 corruption accepted")
    print("SYNTHETIC_BETAFOR11_ORIGINAL_OTU_HEADER_ONLY_MD5_AND_NO_BIOLOGY_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out needed")
    rep={
        "schema":"structural.BETAFOR11_original_com_singletons_firstheader_only.v1",
        "prespec":PRESPEC,
        "source_only_not_biological_analysis":True,
        "original_OTU_numeric_response_rows_opened":0,
        "new_ecological_effects_fitted":0,
        "original_source_v1_and_v2_HOLDs_unchanged":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        q=run()
        rep["audit"]=q
        rep["status"]=q["status"]
    except SourceStop as e:
        rep["status"]="SOURCE_RESPONSE_HEADER_STOP_"+str(e)
        rep["not_a_biological_null"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR11_ORIGINAL_OTU_FIRST_HEADER",rep["status"])
    if "audit" in rep:
        x=rep["audit"]["original_community_firstheader_only"]
        print("FIRST_HEADER_COLUMNS",x["first_header_field_count"])
        print("SOURCE_SAMPLE_LITERAL_MATCHES",x["raw_header_tokens_matching_source_sample_literals"])
    print("ZERO_ORIGINAL_OTU_ABUNDANCE_ROWS_PARSED_OR_MODELS_FITTED")


if __name__=="__main__":
    main()
