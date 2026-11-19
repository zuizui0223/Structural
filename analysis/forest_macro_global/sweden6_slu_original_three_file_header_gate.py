#!/usr/bin/env python3
"""2025 SLU Sweden six-region saproxylic beetle×microclimate source gate.

Official eArchive publisher 3 exact bitstreams. Download original files into
private memory ONLY to verify size/SHA, interpret README/source protocol,
and read CSV FIRST HEADERS only. No original climate/catch/OTU rows read.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

PRESPEC="docs/FOREST_SWEDEN6_SPRUCE_THERMAL_WOOD_SOURCE_GATE_PRESPEC_20261119.md"
ORIGINAL_URLS={
  "boreal_forest_climate_data.csv":(
      "https://earchive.slu.se/bitstreams/cac76f42-041f-489a-a568-7d92c0c7941d/download",12
  ),
  "specieslist_xylo.csv":(
      "https://earchive.slu.se/bitstreams/4394f565-ede9-457b-a1b1-c4e5d042cb88/download",6
  ),
  "readme.txt":(
      "https://earchive.slu.se/bitstreams/9c008aa7-2dba-42ff-9c42-9ade88afbf66/download",None
  ),
}
ORIGINAL_UUID_PATTERN=re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")
MAX_FILE_BYTES=1024*1024
MAX_HEADER=65536
README_KEYWORDS={
  "original_SIX_geographic_blocks":r"(?i)six different study sites",
  "original_30_plot_hierarchy":r"(?i)five study plots",
  "original_THREE_shade_levels":r"(?i)three different shade level",
  "original_2020_micro_macro_temperature":r"(?i)mikro.*makrotemp",
  "original_substrate_bark_and_diameter":r"(?i)bark:|diameter:",
  "original_2021_beetle_abundance_fields":r"(?i)number: number of each species",
  "original_88_climate_aggregate_rows":r"(?i)88 rows",
  "original_3460_species_record_rows":r"(?i)3460 rows",
}
class SourceStop(Exception):
    pass

def official_get(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme!="https" or u.hostname!="earchive.slu.se":
        raise SourceStop("SLU_ORIGINAL_URL_NOT_OFFICIAL_HOST")
    match=re.fullmatch(r"/bitstreams/([0-9a-f-]{36})/download",u.path)
    if not match or ORIGINAL_UUID_PATTERN.fullmatch(match.group(1)) is None:
        raise SourceStop("SLU_ORIGINAL_BITSTREAM_ID_BAD")
    req=urllib.request.Request(
        url,headers={"User-Agent":"Structural-forest-sweden6-SLU-original/1.0",
                     "Accept":"text/csv,text/plain,application/octet-stream;q=0.8,*/*;q=0.2"},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req,timeout=90) as r:
            fin=urllib.parse.urlsplit(r.geturl())
            if fin.scheme!="https" or fin.hostname!="earchive.slu.se" or not (
                fin.path==u.path or fin.path=="/server/api/core/bitstreams/"+match.group(1)+"/content"
            ):
                raise SourceStop("SLU_OFFICIAL_ORIGINAL_REDIRECT_PATH_OR_HOST_DRIFT")
            mime=(r.headers.get("Content-Type") or "").lower()
            if "text/html" in mime or "application/json" in mime:
                raise SourceStop("SLU_ORIGINAL_RETURNED_NON_SOURCE_FORMAT")
            raw=r.read(MAX_FILE_BYTES+1)
            if len(raw)>MAX_FILE_BYTES:
                raise SourceStop("SLU_ORIGINAL_SOURCE_OVER_1_MIB")
    except urllib.error.HTTPError as exc:
        raise SourceStop("SLU_ORIGINAL_HTTPS_HTTP_"+str(exc.code)+"_STOP") from None
    except (urllib.error.URLError,OSError,TimeoutError):
        raise SourceStop("SLU_ORIGINAL_HTTPS_TRANSPORT_STOP") from None
    if len(raw)<30 or raw[:10].lower().lstrip().startswith((b"<html",b"<!doctype")):
        raise SourceStop("SLU_ORIGINAL_EMPTY_OR_HTML_RESPONSE")
    return raw

def first_header_only(blob,expected):
    # Byte slicing discards opaque body; only author FIRST physical line decoded.
    raw=blob.split(b"\n",1)[0].rstrip(b"\r")
    if len(raw)>MAX_HEADER or not raw or b"\x00" in raw:
        raise SourceStop("SLU_ORIGINAL_FIRST_HEADER_NOT_TEXT")
    try:
        txt=raw.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SLU_ORIGINAL_SOURCE_FIRST_HEADER_UTF8_STOP") from None
    parsed=[]
    for sep in (",",";","\t"):
        try:
            cols=next(csv.reader([txt],delimiter=sep,strict=True))
        except (csv.Error,StopIteration):
            continue
        if (len(cols)==expected and
                len({c.strip() for c in cols})==expected and
                all(c.strip() and len(c)<128 for c in cols)):
            parsed.append((sep,[x.strip() for x in cols]))
    if len(parsed)!=1:
        raise SourceStop("SLU_ORIGINAL_EXACT_DECLARED_"+str(expected)+"_FIELD_HEADER_NOT_UNIQUE")
    sep,fields=parsed[0]
    return {
      "original_header_declared_field_count":expected,
      "original_HEADER_exact_author_field_names":fields,
      "original_CSV_header_delimiter":{",":"comma",";":"semicolon","\t":"tab"}[sep],
      "original_data_rows_OPENED":0,
      "original_plot_ID_species_or_abundance_values_EXPORTED":False,
      "original_taxon_species_COUNT_SCORED":False,
    }

def readme_source_only(blob):
    try:
        s=blob.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SLU_README_ORIGINAL_UTF8_DECODE_STOP") from None
    return {
       "source_author_README_protocol_families_present":{
           k:bool(re.search(pattern,s)) for k,pattern in README_KEYWORDS.items()
       },
       "source_author_README_original_bytes":len(blob),
       "original_README_lines_not_exported":True,
       "original_species_or_climate_rows_read":0,
    }

def original_once():
    output={}
    for name,(url,expected) in ORIGINAL_URLS.items():
        raw=official_get(url)
        item={
          "publisher_original_filename":name,
          "publisher_original_file_bytes":len(raw),
          "publisher_original_file_sha256":hashlib.sha256(raw).hexdigest(),
          "publisher_original_link_opened_exactly_once":True,
        }
        if expected is None:
            item.update(readme_source_only(raw))
        else:
            item.update(first_header_only(raw,expected))
        output[name]=item
    if not all(output["readme.txt"]["source_author_README_protocol_families_present"].values()):
        raise SourceStop("SLU_AUTHOR_README_REQUIRED_METHOD_DESCRIPTIONS_MISSING")
    return {
        "original_SLU_official_dataset_DOI":"10.5878/dhmc-bq15",
        "original_publication_year":2025,
        "source_files_and_first_headers_only":output,
        "actual_original_file_sum_bytes":sum(x["publisher_original_file_bytes"] for x in output.values()),
        "source_original_biology_rows_read":0,
        "source_measured_resources_are_spruce_only":True,
        "source_real_vertical_canopy_understory_pairs_NOT_PRESENT":True,
        "source_2020_climate_2021_beetle_temporal_lag_AUTHOR_REPORTED":True,
        "source_real_independent_region_N":6,
        "species_community_thermal_predictive_effect_FIT":False,
        "status":"SOURCE_SWEDEN6_SLU_ORIGINAL_THREE_FILE_HEADERS_PASS",
    }

def synthetic_test():
    c=("Block,Plot,Shade,Mikrotemp,Makrotemp,CTI,Bark,Diameter,Regional_climate,"
       "Aspect,Species_richness,Totalab\n"
       "HIDDEN_ORIGINAL_CLIMATE_VALUE,33,3,13,14,15,16,17,18,19,20,21\n").encode()
    s=("Block,Plot,Log,Sampling_date,Species,Number\n"
       "HIDDEN_ORIGINAL_BEETLE_SPECIES_NAME,8,3,2021-06-01,Carabus,99\n").encode()
    f=first_header_only(c,12)
    g=first_header_only(s,6)
    assert f["original_header_declared_field_count"]==12
    assert g["original_header_declared_field_count"]==6
    assert f["original_data_rows_OPENED"]==0
    assert g["original_data_rows_OPENED"]==0
    q=json.dumps({"climate":f,"species":g})
    for private in ("HIDDEN_ORIGINAL_CLIMATE_VALUE","HIDDEN_ORIGINAL_BEETLE_SPECIES_NAME","Carabus"):
        assert private not in q
    sample_readme=("The data set climate contains 88 rows. The data species contains 3460 rows. "
       "Block: six different study sites. Plot: five study plots. "
       "Shade: three different shade level. Mikro- and makrotemp: mean temperatures. "
       "Bark: bark. Diameter: diameter. Number: Number of each species.").encode()
    assert all(readme_source_only(sample_readme)[
       "source_author_README_protocol_families_present"].values())
    print("SYNTHETIC_SLU_SIXREGION_THREE_SOURCE_HEADERS_NO_BIOLOGY_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    synthetic_test()
    if args.test:return
    if args.out is None:parser.error("--out required")
    r={
        "schema":"structural.slu_sweden6_2025original_three_source_headers_only.v1",
        "precommit":PRESPEC,
        "official_original_slu_eArchive_item_id":"496e1831-2cb9-490a-8957-0ed8754658a8",
        "source_original_BEETLE_climate_OR_resource_data_rows_OPENED":0,
        "source_6_regions_NOT_6_biomes":True,
        "original_author_Gossmann2024_shade_temperature_RESULTS_PRIOR_ART":True,
        "previous_Finland_Carpathian_England_PREDICTS_Thai_NEON_BALA_GEB_outcomes_UNCHANGED":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        r["SLU_original_source_first_headers_aggregates"]=original_once()
        r["status"]=r["SLU_original_source_first_headers_aggregates"]["status"]
    except SourceStop as exc:
        r["status"]=str(exc)
        r["source_OR_method_STOP_NOT_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"SLU_sweden6_original_source_three_file_headers_only.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SLU_SWEDEN6_ORIGINAL_SOURCE_ONLY",r["status"])
    print("NO_ORIGINAL_SPECIES_COUNTS_OR_CLIMATE_DATA_ROWS_OPENED")
if __name__=="__main__":
    main()
