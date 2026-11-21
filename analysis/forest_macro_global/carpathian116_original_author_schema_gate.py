#!/usr/bin/env python3
"""Gloor et al. 2026 Carpathian116 original author files: method and header ONLY.

Read exactly seven source-pinned original files. Original beetle and forest
CSV data rows remain opaque SHA-checked bytes: only first-line schema parsed.
Published README + Rscript inspected lexically, never run or emitted as text.
No original guild/plot/biological response fitted, selected, or scored.
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

from carpathian116_zenodo_metadata_only import (
    URL as API_URL, RECORD, EXPECTED_DOI, NoRedirect, SourceStop
)

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_AUTHOR_SCHEMA_GATE_PRESPEC_20261118.md"
METADATA_SHA="c1ec934e700ebfa150d32d71ee23373bff28042c63d8eb55c2fbb56334b6ce30"
FROZEN_FILES={
    "B_SR_BEETLES.csv": (34504,"711755433cd6ec452ae1971f20b3c281"),
    "S_SR_BEETLES.csv": (21701,"9320f3803ebfb9002cdcea42c14dd2f1"),
    "Beech.csv": (7936,"78ce4d753000f8945c3984bb2bba8b06"),
    "Spruce.csv": (7584,"0fa184c63bbb227f04097e15083bc9ec"),
    "Beech_Spruce.csv": (15231,"223239b47d513aebd703777483a76277"),
    "README.txt": (8985,"0d707ef099271af8470759bf877f1b51"),
    "Rscript.R": (98489,"25836117f89d5c96f6e5c54c33ba0c94"),
}
BIO_FILES=("B_SR_BEETLES.csv","S_SR_BEETLES.csv")
ENV_FILES=("Beech.csv","Spruce.csv","Beech_Spruce.csv")
FIXED_SOURCES=tuple(FROZEN_FILES)
META_LIMIT=500000
SAFE_ALNUM_FIELD=re.compile(r"^[A-Za-z][A-Za-z0-9._\-]{0,50}$")
KEYS={
    "original_plot_key":("plot","plotid","plot_id","site","siteid","site_id","id","ep"),
    "original_stand_block_key":("stand","standid","stand_id","range","mountain","mountainrange","foreststand","region"),
    "original_habitat_class":("habitat","forest","foresttype","forest_type","type","beech","spruce"),
    "original_time_or_effort":("date","year","sampledate","samplingdate","month","effort","trapdays","deployment"),
}
SOURCE_LEX={
    "physical_plot_or_stand":re.compile(r"(?i)\b(?:plot|site|stand|range|mountain|locality|sample.?unit)\b"),
    "local_deadwood_resource":re.compile(r"(?i)\b(?:deadwood|dead.?wood|coarse.?woody|wood.?volume|lying.?wood|snag|log)\b"),
    "canopy_and_structure":re.compile(r"(?i)\b(?:canopy|stem.?diameter|tree.?age|structur|dbh)\b"),
    "saproxylic_beetle_response":re.compile(r"(?i)\b(?:beetles?|coleopter|saproxylic|species|occurrence|matrix)\b"),
    "feeding_guild_trait":re.compile(r"(?i)\b(?:feeding.?guild|guild|mycetophag|xylophag|zoophag|trophic|trait)\b"),
    "source_effort_zeros":re.compile(r"(?i)\b(?:effort|trap.?days|trap.?nights|deploy|zero.?captures?|no.?capture|sampling.?occasion)\b"),
    "explicit_source_join":re.compile(r"(?i)\b(?:left_join|inner_join|full_join|merge|match)\s*\("),
    "position_binding":re.compile(r"(?i)\b(?:cbind|bind_cols|data\.frame)\s*\("),
}
SOURCE_FILE_MENTIONS=tuple(name for name in FROZEN_FILES if name.endswith(".csv"))
SOURCE_PATH_PREFIX=f"/api/records/{RECORD}/files/"
EXPECTED_LICENSE={"cc-by-4.0"}

def validate_original_publisher_link(url):
    """Permit ONLY source-supplied Zenodo links from frozen original record."""
    p=urllib.parse.urlparse(url)
    if p.scheme!="https" or p.hostname!="zenodo.org" or p.username or p.password or p.port or p.query or p.fragment:
        raise SourceStop("SOURCE_NON_ORIGINAL_ZENODO_FILE_REFERENCE")
    if url==API_URL:
        return "record_metadata"
    if p.path.startswith(SOURCE_PATH_PREFIX) and p.path.endswith("/content"):
        name=p.path[len(SOURCE_PATH_PREFIX):-len("/content")]
        if name not in FROZEN_FILES:
            raise SourceStop("SOURCE_UNFROZEN_RECORD_FILE_CONTENT_LINK")
        return "original_record_file_content"
    parts=p.path.split("/")
    if (len(parts)==5 and parts[1:3]==["api","files"]
        and re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",parts[3])
        and parts[4] in FROZEN_FILES):
        return "original_bucket_file_self"
    raise SourceStop("SOURCE_ORIGINAL_PUBLISHER_PATH_NOT_SUPPORTED")

def official_get(url,accept,cap):
    validate_original_publisher_link(url)
    req=urllib.request.Request(url,headers={
        "Accept":accept,
        "User-Agent":"Structural-Carpathian116-Gloor-original-method-only/1.0",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=45) as r:
            if r.status!=200:
                raise SourceStop("SOURCE_OFFICIAL_ZENODO_HTTP_NOT200")
            data=r.read(cap+1)
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_OFFICIAL_ZENODO_HTTP_"+str(ex.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as ex:
        raise SourceStop("SOURCE_OFFICIAL_ZENODO_TRANSPORT_"+type(ex).__name__) from None
    if not data or len(data)>cap:
        raise SourceStop("SOURCE_OFFICIAL_ZENODO_EMPTY_OR_OVERSIZE")
    return data

def original_record_links():
    raw=official_get(API_URL,"application/json",META_LIMIT)
    if hashlib.sha256(raw).hexdigest()!=METADATA_SHA:
        raise SourceStop("SOURCE_ORIGINAL_METADATA_VERSION_OR_COUNTER_DRIFT")
    try:
        doc=json.loads(raw.decode("utf-8"))
    except (UnicodeError,ValueError):
        raise SourceStop("SOURCE_ORIGINAL_METADATA_PARSE_STOP") from None
    md=doc.get("metadata",{})
    if doc.get("id")!=RECORD or doc.get("doi",md.get("doi"))!=EXPECTED_DOI:
        raise SourceStop("SOURCE_ZENODO_RECORD_ID_DOI_STOP")
    lic=md.get("license",{})
    lic=lic.get("id") if isinstance(lic,dict) else lic
    if not isinstance(lic,str) or lic.casefold() not in EXPECTED_LICENSE:
        raise SourceStop("SOURCE_PUBLISHED_LICENSE_CHANGED")
    if doc.get("status") not in ("published",None):
        raise SourceStop("SOURCE_ZENODO_PUBLICATION_STATUS_DRIFT")
    actual={}
    for item in doc.get("files",[]):
        if not isinstance(item,dict):continue
        name=item.get("key")
        if name not in FROZEN_FILES:continue
        size,md5=FROZEN_FILES[name]
        if item.get("size")!=size or item.get("checksum")!="md5:"+md5:
            raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_FILE_SIZE_MD5_DRIFT")
        links=item.get("links",{})
        link=(links.get("content") or links.get("self")) if isinstance(links,dict) else None
        if not isinstance(link,str):
            raise SourceStop("SOURCE_ZENODO_ORIGINAL_SELF_AND_CONTENT_LINK_ABSENT")
        validate_original_publisher_link(link)
        if name in actual:raise SourceStop("SOURCE_DUPLICATE_ORIGINAL_FILE")
        actual[name]=link
    if set(actual)!=set(FROZEN_FILES):
        raise SourceStop("SOURCE_MISSING_EXACT_PREDECLARED_FILE")
    return actual

def first_header_csv(raw,name):
    header=raw.split(b"\n",1)[0]+b"\n"
    if len(header)>65536:
        raise SourceStop("SOURCE_ORIGINAL_CSV_HEADER_TOO_LONG")
    try:
        decoded=header.decode("utf-8-sig").rstrip("\r\n")
    except UnicodeError:
        raise SourceStop("SOURCE_ORIGINAL_CSV_NOT_UTF8") from None
    # Use only FIRST physical header, never parse a subsequent original value row.
    delim=max((",",";","\t"),key=lambda x:decoded.count(x))
    try:
        fields=next(csv.reader([decoded],delimiter=delim,strict=True))
    except (csv.Error, StopIteration):
        raise SourceStop("SOURCE_ORIGINAL_CSV_HEADER_PARSE_FAILED") from None
    if not 2<=len(fields)<=1500:
        raise SourceStop("SOURCE_ORIGINAL_CSV_HEADER_FIELD_COUNT_NOT_SUPPORTED")
    # Author may store species names as headers: NEVER disclose the names.
    generic={label:sum(field.casefold().strip() in words for field in fields)
             for label,words in KEYS.items()}
    safe_print=[{"index":i+1,"field":f} for i,f in enumerate(fields)
                if f.casefold().strip() in
                set(word for words in KEYS.values() for word in words)
                and SAFE_ALNUM_FIELD.fullmatch(f)]
    return {
      "original_filename":name,
      "first_line_original_CSV_delimiter_class":(
         "comma" if delim=="," else "semicolon" if delim==";" else "tab"),
      "original_first_header_column_count":len(fields),
      "original_strict_generic_field_name_match_counts":generic,
      "only_generic_non_species_field_names_if_any":safe_print,
      "original_species_taxon_labels_NOT_EXPORTED":True,
      "all_original_CSV_data_rows_UNOPENED":True,
      "source_plot_IDs_and_response_values_NOT_READ":True,
    }

def source_code_method_hints(raw,name):
    try:
        text=raw.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SOURCE_ORIGINAL_AUTHOR_TEXT_NOT_UTF8") from None
    return {
        "source_text_role":name,
        "original_source_text_bytes_verified":len(raw),
        "original_source_code_NEVER_EXECUTED":True,
        "method_lexical_mentions_only":{
            key:len(rx.findall(text)) for key,rx in SOURCE_LEX.items()
        },
        "exact_frozen_CSV_file_literal_mention": {
            filename:(filename in text) for filename in SOURCE_FILE_MENTIONS
        },
        "source_original_author_text_NOT_EXPORTED":True,
        "no_model_coefficient_or_species_data_READ":True,
    }

def run():
    links=original_record_links()
    docs={}
    for name in FIXED_SOURCES:
        size,md5=FROZEN_FILES[name]
        raw=official_get(links[name],"*/*",size+1024)
        if len(raw)!=size or hashlib.md5(raw).hexdigest()!=md5:
            raise SourceStop("SOURCE_ORIGINAL_FILE_DIGEST_OR_LENGTH_FAILED")
        if name.endswith(".csv"):
            details=first_header_csv(raw,name)
        else:
            details=source_code_method_hints(raw,name)
        details["original_verified_file_size"]=size
        details["original_verified_publisher_MD5"]=md5
        docs[name]=details
    # Do not claim join by row order or filename shape.
    can_join=all(any(v>0 for v in
                   [docs[n]["original_strict_generic_field_name_match_counts"]["original_plot_key"]])
                 for n in BIO_FILES+ENV_FILES[:2])
    code=docs["Rscript.R"]["method_lexical_mentions_only"]
    guild=docs["Rscript.R"]["method_lexical_mentions_only"]["feeding_guild_trait"]>0
    return {
       "schema":"structural.Carpathian116_original_author_method_schema_v1",
       "original_publisher_record":RECORD,
       "publisher_metadata_SHA256_verified":METADATA_SHA,
       "source_original_file_count":len(docs),
       "original_7_file_source_method_and_first_header_only":docs,
       "original_community_environment_safe_generic_plot_id_header_candidate_all_four":can_join,
       "published_R_code_contains_feeding_guild_words_NOT_an_ontology":guild,
       "published_R_code_has_join_call_patterns":code["explicit_source_join"],
       "original_site_key_semantics_NOT_PROVED":True,
       "original_feeding_guild_ontology_NOT_PROVED":True,
       "source_zero_capture_effort_NOT_PROVED":True,
       "original_species_or_environment_DATA_ROWS_READ":0,
       "new_biodiversity_effect_ESTIMATED":False,
       "status":("SOURCE_SCHEMA_CANDIDATES_ONLY_NO_JOIN_OR_GUILD_AUTHORIZED"
                 if can_join else
                 "SOURCE_SPECIES_ENVIRONMENT_SITEKEY_OR_GUILD_UNVERIFIED"),
    }

def synthetic():
    assert validate_original_publisher_link(
        "https://zenodo.org/api/files/12345678-aaaa-bbbb-cccc-123456789abc/Beech.csv"
    ) == "original_bucket_file_self"
    try:
        validate_original_publisher_link("https://zenodo.org/api/files/12345678-aaaa-bbbb-cccc-123456789abc/OTHER.csv")
        raise AssertionError("unfrozen source file link allowed")
    except SourceStop:
        pass
    fixture=b"plotID,TreeVolume,Fagus sylvatica,Quercus robur\n1,2.3,4,5\n"
    got=first_header_csv(fixture,"B_SR_BEETLES.csv")
    assert got["original_first_header_column_count"]==4
    assert got["only_generic_non_species_field_names_if_any"]==[
        {"index":1,"field":"plotID"}]
    assert "Fagus sylvatica" not in json.dumps(got)
    src=source_code_method_hints(b"abc <- merge(x, y, by='plotID')\nread.csv('Beech.csv')", "Rscript.R")
    assert src["method_lexical_mentions_only"]["explicit_source_join"]==1
    assert src["exact_frozen_CSV_file_literal_mention"]["Beech.csv"]
    assert not src["exact_frozen_CSV_file_literal_mention"]["Spruce.csv"]
    print("SYNTHETIC_CARPATHIAN116_GLOOR_SCHEMA_AND_AUTHOR_METHOD_NO_RESPONSE_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:ap.error("--out required")
    report={
       "schema":"structural.Carpathian116_Zenodo_original_author_schema_sourceonly.v1",
       "prespec":PRESPEC,
       "original_file_metadata_only_previous_intake_sha":METADATA_SHA,
       "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_effects_UNCHANGED":True,
       "original_raw_beetle_species_counts_wood_environment_values_READ":False,
       "eBird_used":False,"TinyFish_used":False
    }
    try:
        report["source_qualification"]=run()
        report["status"]=report["source_qualification"]["status"]
    except SourceStop as ex:
        report["status"]=str(ex)
        report["source_STOP_not_biological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Carpathian116_original_author_schema_only.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("ORIGINAL_CARPATHIAN116_AUTHOR_SCHEMA_GATE",report["status"])
    print("NO_ORIGINAL_SPECIES_ROW_OR_PLOT_ENVIRONMENT_VALUES_OPENED")

if __name__=="__main__":
    main()
