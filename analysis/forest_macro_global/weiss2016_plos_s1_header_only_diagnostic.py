#!/usr/bin/env python3
"""PLOS Weiss2016 S1 original header-only disambiguation. No species data rows."""

from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from weiss2016_plos_doc_schema_only import original_doc, SourceStop

PRESPEC="docs/FOREST_MACRO_WEISS2016_S1_AUTHOR_HEADER_DISAMBIGUATION_PRESPEC_20261118.md"
VOCAB=("species","taxon","indicator","family","trophic","guild","feeding",
       "status","lowland","mountain","region","number","red","list","ecological")
EXPECTED_COLS=9

class HeaderOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_table=False
        self.row_n=0
        self.in_cell=False
        self.header=[]
        self.fragments=[]
        self.total_tables=0
        self.num_cells=0
    def handle_starttag(self,tag,attrs):
        tag=tag.lower()
        if tag=="table":
            self.total_tables+=1
            self.in_table=True
        elif tag in ("td","th") and self.in_table and self.row_n==0:
            self.in_cell=True
            self.fragments=[]
            self.num_cells+=1
    def handle_data(self,data):
        if self.in_table and self.row_n==0 and self.in_cell:
            self.fragments.append(data)
        # All original 512 species/guild rows deliberately discarded.
    def handle_endtag(self,tag):
        tag=tag.lower()
        if tag in ("td","th") and self.in_table and self.row_n==0 and self.in_cell:
            self.header.append(re.sub(r"\s+"," "," ".join(self.fragments)).strip())
            self.in_cell=False
            self.fragments=[]
        elif tag=="tr" and self.in_table:
            self.row_n+=1
        elif tag=="table" and self.in_table:
            self.in_table=False
    def anonymized(self):
        if len(self.header)!=EXPECTED_COLS or self.num_cells!=EXPECTED_COLS or self.total_tables!=1:
            raise SourceStop("SOURCE_WEISS2016_AUTHOR_FIRST_HEADER_NINE_CELL_STOP")
        out=[]
        for i,value in enumerate(self.header):
            terms=set(re.sub(r"[^a-z0-9]+"," ",value.casefold()).split())
            out.append({
                "original_author_column_position_1based":i+1,
                "author_header_field_SHA256":hashlib.sha256(value.encode("utf-8")).hexdigest(),
                "predeclared_header_lexical_boolean_flags":{k:k in terms for k in VOCAB},
            })
        return {
            "source_original_first_header_only_cell_count":len(out),
            "source_original_source_table_count":self.total_tables,
            "source_512_original_species_data_row_text_nodes_INSPECTED":False,
            "original_header_literals_NOT_EXPORTED":True,
            "original_author_header_boolean_categories_by_column_ONLY":out,
            "original_author_names_or_guild_values_NOT_READ":True,
        }

def source_only():
    lo=shutil.which("libreoffice") or shutil.which("soffice")
    if not lo:raise SourceStop("SOURCE_LIBREOFFICE_UNAVAILABLE")
    with tempfile.TemporaryDirectory(prefix="weiss_header_only_") as tmp:
        p=Path(tmp)
        doc=p/"original_S1.doc"
        html=p/"original_S1.html"
        doc.write_bytes(original_doc())
        try:
            r=subprocess.run([
                lo,"-env:UserInstallation="+(p/"profile").as_uri(),
                "--headless","--convert-to","html","--outdir",str(p),str(doc)
            ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=110,check=False)
        except (OSError,subprocess.TimeoutExpired):
            raise SourceStop("SOURCE_ORIGINAL_PRIVATE_HTML_CONVERT_STOP") from None
        if r.returncode or not html.exists() or not (1000<=html.stat().st_size<=20_000_000):
            raise SourceStop("SOURCE_ORIGINAL_PRIVATE_HTML_OUTPUT_UNAVAILABLE")
        parser=HeaderOnly()
        parser.feed(html.read_bytes().decode("utf-8",errors="replace"))
        parser.close()
        result=parser.anonymized()
    return result

def known_truth():
    example="<table><tr><th>Species</th><th>Family</th><th>Count</th><th>N</th><th>Habitat</th><th>Trophic guild</th><th>Red List</th><th>Indicator species</th><th>Status</th></tr><tr><td>SECRET SPECIMEN</td></tr></table>"
    q=HeaderOnly()
    q.feed(example)
    obj=q.anonymized()
    flags=[row["predeclared_header_lexical_boolean_flags"] for row in obj["original_author_header_boolean_categories_by_column_ONLY"]]
    assert flags[0]["species"] and not flags[0]["indicator"]
    assert flags[7]["species"] and flags[7]["indicator"]
    assert flags[5]["trophic"] and flags[5]["guild"]
    assert "SECRET SPECIMEN" not in json.dumps(obj)
    assert "Indicator species" not in json.dumps(obj)
    print("SYNTHETIC_WEISS2016_AUTHOR_HEADER_FLAGS_IGNORE_ALL_DATA_ROWS_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:ap.error("--out required")
    obj={
      "schema":"structural.Weiss2016_original_PLOS_S1_first_header_9column_flags_only.v1",
      "precommit":PRESPEC,
      "original_PLOS_S1_DOI":"10.1371/journal.pone.0149506.s001",
      "previous_author_guild_integrity_source_header_STOP_not_reopened":True,
      "Gloor_original_beetle_taxa_and_abundance_READ":False,
      "Weiss_original_species_guild_pairs_READ":False,
      "Dryad_Weiss_and_Franzen_original_workbooks_HTTP401_not_retried":True,
      "previous_forest_BALA_GEB_scores_unchanged":True,
      "new_biodiversity_effect_estimated":False,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        obj["source_only_header_flags"]=source_only()
        obj["status"]="SOURCE_WEISS_ORIGINAL_FIRST_HEADER_FLAGS_ONLY_NO_BIOLOGY"
    except SourceStop as ex:
        obj["status"]=str(ex)
        obj["source_method_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Weiss2016_PLOS_S1_9header_semantic_boolean_flags_only.json").write_text(
        json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("WEISS2016_9_AUTHOR_HEADER_SCHEMA_FLAGS",obj["status"])
    print("GLOOR_ORIGINAL_SPECIES_OUTCOME_UNREAD")
if __name__=="__main__":main()
