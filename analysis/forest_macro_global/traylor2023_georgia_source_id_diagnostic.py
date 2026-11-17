#!/usr/bin/env python3
"""Traylor 2023 Georgia: frozen original site-ID lexical/codebook SOURCE-ONLY diagnostic.

Only forest 'site' values, species-matrix first HEADER, and published README
documentation are inspected. Species/guild/abundance/environmental row values
are never accessed. Header lexical concordance is NOT an authorized join.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import urllib.parse
from collections import Counter
from pathlib import Path

from traylor2023_georgia_original_source_only import (
    FILES,HOST,RECORD,LIMIT,SourceStop,get,official_manifest
)

ENV_FILE="site_forest_variables.csv"
BEETLE_FILE="species_list_abundance_per_site_functional_group.csv"
README_FILE="READ ME metadata.txt"

def downloaded_published_one(filename,expected_sizes):
    if filename not in FILES:
        raise SourceStop("SOURCE_STOP_NOT_FROZEN_FILE")
    url=HOST+"/records/"+str(RECORD)+"/files/"+urllib.parse.quote(filename,safe="")+"?download=1"
    data=get(url,LIMIT)
    if len(data)!=expected_sizes[filename] or hashlib.md5(data).hexdigest()!=FILES[filename]:
        raise SourceStop("SOURCE_STOP_ORIGINAL_PUBLISHER_MD5_OR_SIZE_CHANGED")
    return data

def read_forest_IDs_only(raw):
    try:
        reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=",",strict=True)
        header=next(reader)
    except (csv.Error,UnicodeError,StopIteration) as exc:
        raise SourceStop("SOURCE_STOP_FOREST_HEADER_OR_ENCODING") from exc
    if len(header)!=96:
        raise SourceStop("SOURCE_STOP_FOREST_ORIGINAL_FIELD_WIDTH_CHANGED")
    positions=[i for i,n in enumerate(header) if re.sub("[^a-z0-9]","",n.lower())=="site"]
    if len(positions)!=1:
        raise SourceStop("SOURCE_STOP_AUTHOR_SITE_ID_FIELD_AMBIGUOUS")
    ids=[]
    try:
        for row in reader:
            if len(row)!=96:
                raise SourceStop("SOURCE_STOP_FOREST_SITE_ROW_SHAPE")
            label=row[positions[0]].strip()
            if not label:raise SourceStop("SOURCE_STOP_FOREST_SITE_CODE_BLANK")
            ids.append(label)
            if len(ids)>500:raise SourceStop("SOURCE_STOP_TOO_MANY_FOREST_SITES")
    except csv.Error as exc:raise SourceStop("SOURCE_STOP_CSV_FIELD_READ") from exc
    if len(ids)!=40 or len(set(ids))!=40:
        raise SourceStop("SOURCE_STOP_AUTHOR_40_PHYSICAL_SITES_NOT_VALIDATED")
    return ids

def first_beetle_HEADER_only(raw):
    first=io.BytesIO(raw).readline(16384)
    if not first.endswith((b"\n",b"\r")):
        raise SourceStop("SOURCE_STOP_BEETLE_HEADER_LINE_OVERSIZED")
    try:
        columns=next(csv.reader([first.decode("utf-8-sig").rstrip("\r\n")],
                                delimiter=",",strict=True))
    except (csv.Error,UnicodeError,StopIteration) as exc:
        raise SourceStop("SOURCE_STOP_BEETLE_HEADER_PARSE") from exc
    if len(columns)!=58 or len(set(columns))!=58:
        raise SourceStop("SOURCE_STOP_BEETLE_58_COLUMN_HEADER_CHANGED")
    return [x.strip() for x in columns]

def lexical_category(label):
    if re.fullmatch(r"[0-9]+",label):return "digits_only"
    if re.fullmatch(r"[A-Za-z]+",label):return "letters_only"
    if re.fullmatch(r"[A-Za-z0-9]+",label):return "alphanumeric_mixed"
    return "punctuated_or_other"

def alnum(x):
    return re.sub(r"[^a-z0-9]","",x.lower())

def r_lexical(x):
    # A diagnostic emulation of R make.names on simple IDs, not a join rule.
    # Other syntactic effects (duplicates, reserved names, locale) are not assumed.
    y=re.sub(r"[^A-Za-z0-9._]","_",x)
    if not y or not re.match(r"^[A-Za-z.]",y) or re.match(r"^\.[0-9]",y):
        y="X"+y
    return y

def matching_report(sites,headers,op):
    a=[op(x) for x in sites]
    b=[op(x) for x in headers]
    sa,sb=set(a),set(b)
    matched=len(sa & sb)
    original_ids_matched=sum(x in sb for x in a)
    header_labels_matched=sum(x in sa for x in b)
    return {
       "site_normalized_ID_collisions":len(a)-len(sa),
       "header_normalized_ID_collisions":len(b)-len(sb),
       "distinct_source_IDs_matching_a_header":matched,
       "original_site_rows_matching_any_header":original_ids_matched,
       "header_fields_matching_any_site_ID":header_labels_matched,
       "40_ID_complete_collision_free":bool(
           matched==40 and len(a)==40 and len(sa)==40 and len(sb)==58),
       "no_site_header_ID_values_exported":True,
    }

def README_field_rules(raw):
    try:s=raw.decode("utf-8-sig")
    except UnicodeError as exc:raise SourceStop("SOURCE_STOP_README_UTF8") from exc
    if len(s)>16000:raise SourceStop("SOURCE_STOP_README_TOO_LONG")
    l=s.casefold().splitlines()
    patterns={
       "site_and_column_same_line":r"(site|sampling location).*(column|header)|(column|header).*(site|sampling location)",
       "site_and_abundance_same_line":r"site.*(abundan|species)|(?:abundan|species).*site",
       "group_and_species_same_line":r"(functional|group|guild).*(species|beetle)|(species|beetle).*(functional|group|guild)",
       "source_column_identifier_words":r"column\s+(id|names?|headings?)|site\s+(id|codes?|numbers?)",
       "R_specific_column_header_rules":r"make[.]names|prefix|^x[0-9]|r\s+format|spreadsheet.*column",
    }
    counts={k:sum(bool(re.search(p,line)) for line in l) for k,p in patterns.items()}
    # Conclusively interpreting an ID correspondence needs the author's
    # literal rule; codebook word co-occurrence alone is NOT enough.
    return {"author_readme_line_count":len(l),
            "author_method_line_pattern_counts":counts,
            "explicit_unambiguous_author_ID_transform_verified":False,
            "original_readme_text_and_source_IDs_NOT_EXPORTED":True}

def inspect(env,beetles,readme):
    site=read_forest_IDs_only(env)
    header=first_beetle_HEADER_only(beetles)
    # Prespecified, not optimized: transformations are diagnostic summaries.
    ops={
      "exact":lambda x:x,
      "casefold":lambda x:x.casefold(),
      "remove_punctuation_and_casefold":alnum,
      "R_simple_make_names_source_only":r_lexical,
      "remove_single_X_prefix_on_header_only":None,
    }
    results={}
    for name,op in ops.items():
        if op is not None:
            results[name]=matching_report(site,header,op)
        else:
            # X-prefix on syntactically digit-leading IDs in matrix headers,
            # but NOT arbitrary dropping letters/number suffixes.
            def strip_R_X(y):
                return y[1:] if re.fullmatch(r"X[0-9]+",y) else y
            results[name]={
              **matching_report(site,header,lambda x:x),
              "specific_column_X_prefix_diagnostic_only":True,
              "source_IDs_matching_after_X_prefix_column_rule":len(
                  set(site)&{strip_R_X(z) for z in header}),
              "not_an_author_verified_rule":True,
            }
    cat={
     "forest_ID_string_categories":dict(Counter(lexical_category(x) for x in site)),
     "beetle_header_string_categories":dict(Counter(lexical_category(x) for x in header)),
    }
    doc=README_field_rules(readme)
    return {"status":"SOURCE_SITE_ID_CROSSWALK_UNVERIFIED_NO_GUILD_RESPONSE",
            "source_forest_unique_site_labels":len(set(site)),
            "beetle_original_header_columns":len(header),
            "predeclared_lexical_diagnostics_ONLY":results,
            "broad_original_field_shapes_only":cat,
            "author_method_documentation":doc,
            "no_key_conversion_authorized_by_diagnostic":True,
            "species_guild_abundance_or_forest_numeric_rows_UNREAD":True,
            "raw_site_species_header_labels_NOT_EXPORTED":True}

def synthetic():
    forest=("site,"+",".join("x"+str(i) for i in range(95))+"\n"+
            "\n".join(str(i)+","+",".join(["0"]*95) for i in range(1,41))+"\n").encode()
    beetle=("species,group,"+",".join("X"+str(i) for i in range(1,41))+
            ","+",".join("m"+str(i) for i in range(16))+"\n"+
            "protected_taxon,protected_guild,"+",".join(["900"]*56)+"\n").encode()
    assert len(first_beetle_HEADER_only(beetle))==58
    z=inspect(forest,beetle,b"site numbers correspond to column names in source data\n")
    assert z["source_forest_unique_site_labels"]==40
    assert z["predeclared_lexical_diagnostics_ONLY"]["exact"]["distinct_source_IDs_matching_a_header"]==0
    assert z["predeclared_lexical_diagnostics_ONLY"]["remove_single_X_prefix_on_header_only"][
      "source_IDs_matching_after_X_prefix_column_rule"]==40
    assert "protected_taxon" not in json.dumps(z)
    assert "protected_guild" not in json.dumps(z)
    assert "900" not in json.dumps(z)
    assert z["status"]=="SOURCE_SITE_ID_CROSSWALK_UNVERIFIED_NO_GUILD_RESPONSE"
    print("SYNTHETIC_GEORGIA40_AUTHOR_ID_SOURCE_ONLY_LEXICAL_DIAGNOSTIC_PASS")

def original_source():
    out={"status":"ORIGINAL_NOT_READ",
         "new_biological_OR_environmental_values_SCORING":False,
         "previous_original_forest_and_island_heldouts_SEALED":True}
    try:
        m,sizes=official_manifest()
        assert m["record"]==RECORD
        env=downloaded_published_one(ENV_FILE,sizes)
        beetle=downloaded_published_one(BEETLE_FILE,sizes)
        readme=downloaded_published_one(README_FILE,sizes)
        out["result"]=inspect(env,beetle,readme)
        out["status"]=out["result"]["status"]
    except SourceStop as exc:
        out["status"]=str(exc)
        out["source_STOP_not_ecological_null"]=True
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out needed")
    obj={"schema":"structural.Traylor2023_Georgia40_source_lexical_ID_diagnostic.v1",
         "precommit":"docs/FOREST_BEETLE_TRAYLOR_US40_SOURCE_ID_DIAGNOSTIC_PRESPEC_20261117.md",
         "original":original_source(),
         "new_eco_guild_coefficient_or_p":False,
         "Piccini_Kriegel_Finland_Burner_Thai_PREDICTS_NEON_BALA_GEB_originals_unopened":True,
         "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Traylor2023_Georgia40_site_ID_source_diagnostic.json").write_text(
        json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(obj,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
