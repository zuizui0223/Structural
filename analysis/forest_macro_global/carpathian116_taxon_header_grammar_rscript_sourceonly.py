#!/usr/bin/env python3
"""Gloor Carpathian116 taxon CSV FIRST-HEADER grammar + original author R code.

PRE-OUTCOME source method audit only. Never parses site rows, beetle counts,
individual species names into exports, or biological predictor response.
Header format diagnosis is NOT an inverse mapping or taxonomic reconciliation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import re
from pathlib import Path

from carpathian116_original_author_schema_gate import (
    FROZEN_FILES, original_record_links, official_get
)
from carpathian116_zenodo_metadata_only import SourceStop

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_TAXON_HEADER_GRAMMAR_AUTHOR_R_SOURCE_PRESPEC_20261118.md"
CSV_EXPECTED={
    "B_SR_BEETLES.csv": (242,241),
    "S_SR_BEETLES.csv": (161,160),
}
SOURCE_CODE="Rscript.R"
LATIN=r"[A-Za-z\u00c0-\u017e-]"
UPPER=r"[A-Z\u00c0-\u00de]"
LOWER=r"[a-z\u00df-\u00ff]"
GRAMMAR={
    "strict_space_binomial":re.compile(r"^"+UPPER+LATIN+r"{1,49} "+LOWER+LATIN+r"{1,49}$"),
    "exact_two_dot_Latin_tokens":re.compile(r"^"+UPPER+LATIN+r"{1,49}\."+LOWER+LATIN+r"{1,49}$"),
    "exact_two_underscore_Latin_tokens":re.compile(r"^"+UPPER+LATIN+r"{1,49}_"+LOWER+LATIN+r"{1,49}$"),
    "starts_X_followed_by_digit":re.compile(r"^X[0-9]"),
    "all_digits":re.compile(r"^[0-9]+$"),
    "contains_unicode_non_ascii":re.compile(r"[^\x00-\x7f]"),
    "starts_or_ends_with_punctuation":re.compile(r"^[^A-Za-z0-9]|[^A-Za-z0-9]$"),
    "contains_whitespace":re.compile(r"\s"),
    "contains_underscore":re.compile(r"_"),
    "contains_dot":re.compile(r"\."),
}
R_METHOD_PATTERNS={
    "read.csv":re.compile(r"\bread\.csv\s*\(",re.I),
    "read.table":re.compile(r"\bread\.table\s*\(",re.I),
    "check.names":re.compile(r"\bcheck\.names\b",re.I),
    "make.names":re.compile(r"\bmake\.names\s*\(",re.I),
    "gsub":re.compile(r"\bgsub\s*\(",re.I),
    "sub":re.compile(r"(?<!g)\bsub\s*\(",re.I),
    "str_replace":re.compile(r"\bstr_replace(?:_all)?\s*\(",re.I),
    "colnames":re.compile(r"\bcolnames\s*\(",re.I),
    "names":re.compile(r"(?<![.a-z])\bnames\s*\(",re.I),
    "readr_read_csv":re.compile(r"\breadr\s*::\s*read_csv\s*\(",re.I),
    "pivot_wider":re.compile(r"\bpivot_wider\s*\(",re.I),
    "dcast":re.compile(r"\bdcast\s*\(",re.I),
    "rename":re.compile(r"\brename\s*\(",re.I),
    "taxon_word":re.compile(r"\btaxon\b",re.I),
    "species_word":re.compile(r"\bspecies\b",re.I),
    "B_SR_BEETLES_csv_filename":re.compile(re.escape("B_SR_BEETLES.csv"),re.I),
    "S_SR_BEETLES_csv_filename":re.compile(re.escape("S_SR_BEETLES.csv"),re.I),
}

def get_one_original(name,links):
    if name not in CSV_EXPECTED and name!=SOURCE_CODE:
        raise SourceStop("SOURCE_NOT_FIXED_ORIGINAL_FILENAME")
    size,md5=FROZEN_FILES[name]
    raw=official_get(links[name],"*/*",size+1024)
    if len(raw)!=size or hashlib.md5(raw).hexdigest()!=md5:
        raise SourceStop("SOURCE_ORIGINAL_PUBLISHER_SIZE_OR_MD5_DRIFT")
    return raw

def first_header_only(raw,name):
    first=raw.split(b"\n",1)[0]
    try:
        header=next(csv.reader([first.decode("utf-8-sig").rstrip("\r")],
                               delimiter=",",strict=True))
    except (UnicodeError,csv.Error,StopIteration):
        raise SourceStop("SOURCE_ORIGINAL_CSV_FIRST_LINE_NOT_PARSEABLE") from None
    expected, taxa_n=CSV_EXPECTED[name]
    if len(header)!=expected or header[0].strip().casefold()!="plotid":
        raise SourceStop("SOURCE_ORIGINAL_CSV_HEADER_COUNT_OR_PLOTID_DRIFT")
    taxa=header[1:]
    if len(taxa)!=taxa_n or len(taxa)!=len(set(taxa)) or any(not t.strip() for t in taxa):
        raise SourceStop("SOURCE_ORIGINAL_TAXON_FIELD_EMPTY_OR_DUPLICATED")
    counters={key:sum(bool(rx.search(t)) for t in taxa) for key,rx in GRAMMAR.items()}
    dots=Counter("0" if t.count(".")==0 else "1" if t.count(".")==1
                 else "2" if t.count(".")==2 else "3plus" for t in taxa)
    underscores=Counter("0" if t.count("_")==0 else "1" if t.count("_")==1
                        else "2" if t.count("_")==2 else "3plus" for t in taxa)
    return {
      "_private_taxon_fields":set(taxa),
      "publisher_original_filename":name,
      "publisher_original_header_fields":expected,
      "original_taxon_column_count":len(taxa),
      "predeclared_RAW_HEADER_SHAPE_counts_OVERLAPPING":counters,
      "original_raw_taxon_heading_DOT_count_histogram":{k:dots[k] for k in ("0","1","2","3plus")},
      "original_raw_taxon_heading_UNDERSCORE_count_histogram":{k:underscores[k] for k in ("0","1","2","3plus")},
      "source_first_original_header_SHA256":hashlib.sha256(first).hexdigest(),
      "original_taxon_strings_NOT_EXPORTED":True,
      "original_site_rows_abundances_species_values_NOT_READ":True,
      "original_names_NOT_transformed_or_recoded":True,
      "header_shape_not_a_verified_taxonomic_crosswalk":True
    }

def original_author_Rscript_grammar(raw):
    try:
        text=raw.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SOURCE_AUTHOR_RSCRIPT_ENCODING_STOP") from None
    return {
        "original_author_Rscript_source_bytes":len(raw),
        "original_Rscript_method_lexical_counts_ONLY":{
            k:len(rx.findall(text)) for k,rx in R_METHOD_PATTERNS.items()
        },
        "author_code_read_as_text_NOT_EXECUTED":True,
        "author_Rscript_raw_source_or_variable_tokens_NOT_EXPORTED":True,
        "author_code_lexical_counts_NOT_proof_of_taxon_ID_conversion":True,
    }

def run():
    links=original_record_links()
    profiles={}
    for name in CSV_EXPECTED:
        profiles[name]=first_header_only(get_one_original(name,links),name)
    code=original_author_Rscript_grammar(get_one_original(SOURCE_CODE,links))
    b=profiles["B_SR_BEETLES.csv"]["_private_taxon_fields"]
    s=profiles["S_SR_BEETLES.csv"]["_private_taxon_fields"]
    for v in profiles.values():v.pop("_private_taxon_fields")
    if len(b)!=241 or len(s)!=160 or len(b&s)!=92 or len(b|s)!=309:
        raise SourceStop("SOURCE_GLOOR_FROZEN_RAW_TAXON_NAME_UNION_309_DRIFT")
    return {
      "original_two_CSV_header_shape_by_forest":profiles,
      "original_source_author_Rscript_only":code,
      "original_same_literal_taxon_header_in_both_forest_files":len(b&s),
      "original_taxon_header_unique_union":len(b|s),
      "original_author_paper_reports_303_beetle_species_NOT_CONFLATED_WITH_309_raw_headers":True,
      "earlier_Weiss511_guild_exact_literal_0of309_HOLD_PRESERVED":True,
      "original_source_RAW_species_heading_name_strings_EXPORTED":False,
      "original_Gloor_site_species_abundance_or_environment_values_READ":False,
      "original_no_guild_species_crosswalk_or_heldout_model_fitted":True,
      "status":"SOURCE_GLOOR_ORIGINAL_HEADER_GRAMMAR_AND_AUTHOR_METHOD_ONLY",
    }

def known_truth():
    assert GRAMMAR["exact_two_dot_Latin_tokens"].fullmatch("Carabus.nemoralis")
    assert GRAMMAR["strict_space_binomial"].fullmatch("Carabus nemoralis")
    assert not GRAMMAR["strict_space_binomial"].fullmatch("Carabus.nemoralis")
    assert GRAMMAR["exact_two_underscore_Latin_tokens"].fullmatch("Carabus_nemoralis")
    assert GRAMMAR["starts_X_followed_by_digit"].search("X1989")
    fake=b'plotid,"Carabus.nemoralis","Genus_species"\n1,1,0\n'
    # No short synthetic fixture is treated as real 242/161-column author data.
    assert "Carabus.nemoralis" not in json.dumps({
        k:v for k,v in {"count":2,"note":"synthetic"}.items()
    })
    assert SOURCE_CODE not in CSV_EXPECTED
    print("SYNTHETIC_GLOOR_AUTHOR_HEADER_GRAMMAR_R_METHOD_RESPONSE_OPAQUE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args();known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    out={
       "schema":"structural.Carpathian116_original_taxon_header_R_method_sourceonly.v1",
       "precommit":PRESPEC,
       "original_Zenodo_record_id":22142713,
       "original_Gloor_beetle_abundance_rows_READ":0,
       "original_Gloor_plot_environment_response_rows_READ":0,
       "old_Weiss2016_guild_source_ledger_NOT_REOPENED":True,
       "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
       "eBird_used":False,"TinyFish_used":False,
    }
    try:
        out["original_source_only_header_and_author_R_method"]=run()
        out["status"]=out["original_source_only_header_and_author_R_method"]["status"]
    except SourceStop as exc:
        out["status"]=str(exc)
        out["source_method_STOP_not_biological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Carpathian116_original_taxon_header_format_Rscript_sourceonly.json").write_text(
        json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("CARPATHIAN116_ORIGINAL_CSV_TAXON_HEADER_AUTHOR_R_METHOD_STATUS",out["status"])
    print("ZERO_ORIGINAL_BEETLE_ABUNDANCE_ROWS_AND_NO_BIOLOGICAL_EFFECT")
if __name__=="__main__":main()
