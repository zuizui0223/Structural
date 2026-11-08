#!/usr/bin/env python3
"""Inspect NEON's 2026 official field-site vegetation CSV metadata safely.

Header/vocabulary audit only. Do not classify beetle sites into forest by
guessing a site name, tower domain, or vegetation product availability.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re
from collections import Counter
from pathlib import Path

URL="https://www.neonscience.org/field-sites/exports/NEON_Field_Site_Metadata_20260805"

def identify(raw_bytes):
    if len(raw_bytes)<100 or len(raw_bytes)>5_000_000:raise ValueError("invalid_Neon_site_metadata_size")
    try:
        text=raw_bytes.decode("utf-8-sig")
    except UnicodeError:raise ValueError("field_site_metadata_non_UTF8")
    if text.lstrip().lower().startswith("<!doctype") or text.lstrip().lower().startswith("<html"):
        raise ValueError("official_NEON_site_metadata_download_was_HTML")
    first=text[:30000]
    try:
        dialect=csv.Sniffer().sniff(first,delimiters=",;\t")
        delimiter=dialect.delimiter
    except csv.Error:
        f=text.splitlines()[0]
        delimiter=max([",",";","\t"],key=f.count)
    d=csv.DictReader(io.StringIO(text),delimiter=delimiter)
    fields=[str(f or "").strip() for f in d.fieldnames or []]
    if len(fields)<4 or len(fields)!=len(set(fields)):
        raise ValueError("site_metadata_columns_missing_or_duplicate")
    d.fieldnames=fields
    data=list(d)
    if len(data)<50:
        raise ValueError("NEON_field_site_metadata_too_few_rows")
    candidate=[f for f in fields if re.search(
        r"(?i)vegetat|cover|habitat|forest|ecoregion|biome|land.?use|site.?code|site.?id|terrain|NLCD|dominant",f)]
    columns={}
    for f in candidate:
        c=Counter(str(row.get(f) or "").strip() for row in data)
        columns[f]={
            "nonempty_count":len(data)-c[""],
            "distinct_nonempty_values":len([v for v in c if v]),
            "value_examples_only_if_small_vocabulary":dict(c) if len(c)<=12 else None
        }
    return {
        "schema":"structural.neon_official_field_site_vegetation_metadata_header_v1",
        "source_metadata_url":URL,
        "original_source_sha256":hashlib.sha256(raw_bytes).hexdigest(),
        "original_record_rows":len(data),
        "original_field_names":fields,
        "source_fields_relevant_to_habitat_eligibility":columns,
        "published_dominant_NLCD_class_vocabulary_counts":dict(Counter(str(row.get("dominant_nlcd_classes") or "").strip() for row in data)),
        "original_row_values_siteIDs_coordinates_not_exported":True,
        "forest_habitat_sites_verified":0,
        "species_plot_or_temperature_effect_not_scored":True,
    }

def run(source,out):
    data=Path(source).read_bytes()
    r=identify(data)
    path=Path(out);path.mkdir(parents=True,exist_ok=True)
    (path/"neon_fieldsite_2026_header_habitat_fields.json").write_text(
        json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,ensure_ascii=False))
    return r

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--out",required=True)
    opt=p.parse_args()
    run(opt.source,opt.out)
