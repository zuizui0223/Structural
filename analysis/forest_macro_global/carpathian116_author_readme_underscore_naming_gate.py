#!/usr/bin/env python3
"""Original Gloor116 README and Rscript author naming conventions ONLY.

No original beetle CSVs, guild table, species names, original forest values,
models or responses touched. An underscore format hypothesis is not scored.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

from carpathian116_original_author_schema_gate import (
    FROZEN_FILES, original_record_links, official_get
)
from carpathian116_zenodo_metadata_only import SourceStop

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_AUTHOR_UNDERSCORE_NAMING_CODEBOOK_PRESPEC_20261118.md"
ORIGINAL_FILES=("README.txt","Rscript.R")
EXPLICIT_README={
    "species_then_underscore":re.compile(
        r"\b(?:species|taxon|taxa|binomial|scientific\s+names?)\b.{0,120}\bunderscor(?:e|es|ed|ing)\b",re.I|re.S),
    "underscore_then_species":re.compile(
        r"\bunderscor(?:e|es|ed|ing)\b.{0,120}\b(?:species|taxon|taxa|binomial|scientific\s+names?)\b",re.I|re.S),
    "literal_genus_underscore_species":re.compile(r"\bgenus_species\b",re.I),
    "species_name_underscored_hint":re.compile(
        r"\b(?:species|taxon)\s+names?\b.{0,100}\b(?:replace|delimiter|separat|join|split|column|encoded)\b.{0,100}\bunderscor",re.I|re.S),
}
README_METHOD={
    "species_word":re.compile(r"\bspecies\b",re.I),
    "scientific_name":re.compile(r"\bscientific\s+names?\b",re.I),
    "genus_word":re.compile(r"\bgenus\b",re.I),
    "taxa_word":re.compile(r"\btaxa\b",re.I),
    "original_beech_beetle_filename":re.compile(re.escape("B_SR_BEETLES.csv"),re.I),
    "original_spruce_beetle_filename":re.compile(re.escape("S_SR_BEETLES.csv"),re.I),
    "guild_word":re.compile(r"\bguilds?\b",re.I),
    "taxonomic_filter":re.compile(r"\btaxonom\w*\b.{0,60}\b(?:filter|remove|exclude)\w*\b",re.I|re.S),
    "paper_reported_303_literal":re.compile(r"(?<!\d)303(?!\d)"),
}
R_CODE={
    "read.csv":re.compile(r"\bread\.csv\s*\(",re.I),
    "check.names":re.compile(r"\bcheck\.names\b",re.I),
    "make.names":re.compile(r"\bmake\.names\s*\(",re.I),
    "gsub":re.compile(r"\bgsub\s*\(",re.I),
    "sub":re.compile(r"(?<![a-z])\bsub\s*\(",re.I),
    "strsplit":re.compile(r"\bstrsplit\s*\(",re.I),
    "str_replace_all":re.compile(r"\bstr_replace_all\s*\(",re.I),
    "colnames":re.compile(r"\bcolnames\s*\(",re.I),
    "names":re.compile(r"(?<![A-Za-z.])\bnames\s*\(",re.I),
    "write.csv":re.compile(r"\bwrite\.csv\s*\(",re.I),
    "B_SR_BEETLES.csv":re.compile(re.escape("B_SR_BEETLES.csv"),re.I),
    "S_SR_BEETLES.csv":re.compile(re.escape("S_SR_BEETLES.csv"),re.I),
    "underscore_literal":re.compile(r"underscor",re.I),
    "paper_reported_303_literal":re.compile(r"(?<!\d)303(?!\d)"),
}
def get_original(name,links):
    if name not in ORIGINAL_FILES:
        raise SourceStop("SOURCE_UNDECLARED_GLOOR_README_OR_SCRIPT_FILE")
    expected,md5=FROZEN_FILES[name]
    body=official_get(links[name],"*/*",expected+1024)
    if len(body)!=expected or hashlib.md5(body).hexdigest()!=md5:
        raise SourceStop("SOURCE_AUTHOR_ORIGINAL_METHOD_FILE_DIGEST_DRIFT")
    try:
        return body.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SOURCE_AUTHOR_METHOD_TEXT_ENCODING_STOP") from None

def summarize(readme,rscript):
    counts={k:len(rx.findall(readme)) for k,rx in EXPLICIT_README.items()}
    documented=any(v>0 for v in counts.values())
    return {
        "original_author_README_source_byte_length":FROZEN_FILES["README.txt"][0],
        "original_author_Rscript_source_byte_length":FROZEN_FILES["Rscript.R"][0],
        "original_README_explicit_underscore_taxon_convention_lexical_matches":counts,
        "original_README_predeclared_general_method_word_counts":{
            k:len(rx.findall(readme)) for k,rx in README_METHOD.items()},
        "original_Rscript_predeclared_source_import_name_method_counts":{
            k:len(rx.findall(rscript)) for k,rx in R_CODE.items()},
        "source_AUTHOR_underscore_encoded_binomial_EXPLICIT_TEXT_CANDIDATE":documented,
        "author_naming_rule_semantics_not_proven_by_generic_word_count":True,
        "source_original_README_Rscript_body_or_any_taxon_NAMING_TEXT_EXPORTED":False,
        "original_taxon_header_rows_species_values_or_abundance_OPENED":0,
        "original_Weiss_guild_ontology_LEDGER_NOT_READ":True,
        "status":("SOURCE_AUTHOR_BINOMIAL_UNDERSCORE_FORMAT_DOCUMENTED_ONLY"
                  if documented else
                  "SOURCE_AUTHOR_UNDERSCORE_TO_SPACE_RULE_NOT_EXPLICIT_HOLD"),
    }

def run():
    links=original_record_links()
    readme=get_original("README.txt",links)
    script=get_original("Rscript.R",links)
    return summarize(readme,script)

def known_truth():
    x=summarize(
        "Original species names are separated by underscores in the header.",
        'read.csv("B_SR_BEETLES.csv")\ncolnames(z)\n'
    )
    assert x["source_AUTHOR_underscore_encoded_binomial_EXPLICIT_TEXT_CANDIDATE"]
    assert x["status"]=="SOURCE_AUTHOR_BINOMIAL_UNDERSCORE_FORMAT_DOCUMENTED_ONLY"
    assert x["original_README_explicit_underscore_taxon_convention_lexical_matches"]["species_then_underscore"]==1
    assert x["original_taxon_header_rows_species_values_or_abundance_OPENED"]==0
    assert "Original species names" not in json.dumps(x)
    y=summarize("Scientific names documented.", "read.csv('S_SR_BEETLES.csv')")
    assert y["status"]=="SOURCE_AUTHOR_UNDERSCORE_TO_SPACE_RULE_NOT_EXPLICIT_HOLD"
    print("SYNTHETIC_ORIGINAL_AUTHOR_UNDERSCORE_WORD_CONTEXT_NO_BIOLOGY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args();known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    out={
      "schema":"structural.Carpathian116_original_author_underscore_naming_provenance.v1",
      "precommit":PRESPEC,
      "original_source_Zenodo_record":22142713,
      "source_Gloor_401_beetle_header_occurrences_NOT_REOPENED":True,
      "source_Weiss511_trophic_pairs_NOT_REOPENED":True,
      "Gloor_species_incidence_abundance_SITE_ROWS_READ":0,
      "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_scoring_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        out["original_author_text_convention_counts_ONLY"]=run()
        out["status"]=out["original_author_text_convention_counts_ONLY"]["status"]
    except SourceStop as e:
        out["status"]=str(e)
        out["original_method_source_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Carpathian116_original_author_README_Rscript_underscore_taxon_convention.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GLOOR_ORIGINAL_AUTHOR_TAXON_UNDERSCORE_CODEBOOK_STATUS",out["status"])
    print("NO_SOURCE_SPECIES_HEADERS_OR_ABUNDANCES_OR_GUILD_MATCHING")
if __name__=="__main__":main()
