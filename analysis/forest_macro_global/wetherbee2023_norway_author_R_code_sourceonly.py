#!/usr/bin/env python3
"""Source-only Wetherbee2023 Norway270 published R code method-grammar audit.

Download official two tiny author R scripts, verify MD5, inspect lexical
method/source join grammar only; DO NOT execute any author R code, source
RData, CSV, taxon, guild or forest environmental values.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RECORD=8272489
HOST="https://zenodo.org"
UA="Structural-Wetherbee2023-author-R-join-source-only/1.0"
MAX_FILE=20000
FILES={
 "DataAnalysis_FT_with_BioDmeasures.R":(6204,"b5b02af2b3c07e741fe1e1afc3d022a5"),
 "Ord_SO.select.R":(8148,"871e3eb4ff24af8860f553fbd89b5b75")
}
FIXED_SOURCE_CSV=(
 "GBIFnormalized_SpcSite_matrix_FD_unique.csv",
 "GBIFnormalized_Trait_RAW_df.csv",
 "SiteInfo_Alltaxon_Pred_Detri_SxFD.csv"
)
METHOD_PATTERNS={
  "source_readers":r"\b(?:read[.]csv|read[.]table|read[.]delim|readRDS|load)\s*\(",
  "data_join_calls":r"\b(?:merge|left_join|inner_join|full_join|match)\s*\(",
  "key_generation_calls":r"\b(?:paste|paste0|interaction|setNames)\s*\(",
  "explicit_row_or_column_naming_calls":r"\b(?:rownames|colnames|row[.]names|col[.]names)\s*\(",
  "wide_long_orientation_calls":r"\b(?:t|transpose|pivot_longer|pivot_wider|reshape|melt|dcast)\s*\(",
  "model_fitting_calls":r"\b(?:glm|glmer|lmer|brm|lm|gam|rda|adonis2?)\s*\("
}
FIELD_TOKENS=(
 "project","projectid","study","studyid","dataset","site","siteid",
 "plot","plotid","year","trap","trapid","tree","deadwood","guild",
 "predator","trait","species","source"
)
class SourceStop(Exception):
    pass

def get_author_code(name,size,md5):
    url=HOST+"/records/"+str(RECORD)+"/files/"+urllib.parse.quote(name,safe="")+"?download=1"
    req=urllib.request.Request(url,method="GET",headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=35) as response:
            raw=response.read(MAX_FILE+1)
            status=response.status
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ACCESS_STOP_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_TRANSPORT_STOP_"+type(e).__name__) from e
    if status!=200 or len(raw)!=size or len(raw)>MAX_FILE:
        raise SourceStop("SOURCE_STOP_AUTHOR_R_CODE_BYTE_SIZE")
    if hashlib.md5(raw).hexdigest()!=md5:
        raise SourceStop("SOURCE_STOP_PUBLISHED_R_SCRIPT_MD5")
    return raw

def inspect_author_code_only(raw):
    try: s=raw.decode("utf-8-sig")
    except UnicodeError as e:raise SourceStop("SOURCE_STOP_R_CODE_NON_UTF8") from e
    # This is a lexical/documentation scan and cannot prove semantic joins.
    counts={k:len(re.findall(p,s,flags=re.IGNORECASE)) for k,p in METHOD_PATTERNS.items()}
    field_counts={k:len(re.findall(r"\b"+re.escape(k)+r"\b",s,flags=re.IGNORECASE))
                  for k in FIELD_TOKENS}
    name_hits={x:(x in s) for x in FIXED_SOURCE_CSV}
    return {
      "original_R_script_lines":len(s.splitlines()),
      "author_code_grammar_counts":counts,
      "generic_source_field_token_count":{
          k:v for k,v in field_counts.items() if v},
      "original_three_fixed_CSV_namerefs_in_code_BOOL_ONLY":name_hits,
      "exact_original_site_project_year_join_semantics_PROVEN":False,
      "code_method_tokens_are_NOT_author_ID_crosswalk":True,
      "original_R_code_NOT_EXECUTED":True,
      "original_script_text_NOT_EXPORTED":True,
      "original_taxa_guild_site_environment_values_NOT_ACCESSED":True,
    }

def source_only():
    state={"status":"SOURCE_NOT_ACCESSED",
           "original_species_site_trait_matrix_NOT_ACCESSED":True}
    findings=[]
    try:
        for name,(size,digest) in FILES.items():
            raw=get_author_code(name,size,digest)
            findings.append({"original_source_filename":name,
                             "original_publisher_md5_verified":True,
                             "publisher_original_size_bytes":size,
                             **inspect_author_code_only(raw)})
        state["author_R_method_lexical_findings"]=findings
        state["status"]="AUTHOR_ORIGINAL_R_CODE_SOURCE_JOIN_UNRESOLVED"
        state["need_original_project_site_year_field_identity"]=True
    except SourceStop as e:
        state["status"]=str(e)
        state["source_STOP_not_ecological_null"]=True
        state["author_R_method_lexical_findings"]=findings
    return state

def known_truth():
    code=b'X <- read.csv("my.csv")\na <- merge(X,y,by="site")\nrownames(X)<-X$project\nz<-t(X)\n'
    r=inspect_author_code_only(code)
    assert r["author_code_grammar_counts"]["source_readers"]==1
    assert r["author_code_grammar_counts"]["data_join_calls"]==1
    assert r["author_code_grammar_counts"]["explicit_row_or_column_naming_calls"]==1
    assert r["author_code_grammar_counts"]["wide_long_orientation_calls"]==1
    assert not r["exact_original_site_project_year_join_semantics_PROVEN"]
    assert r["original_R_code_NOT_EXECUTED"]
    print("SYNTHETIC_NORWAY_R_AUTHOR_CODE_JOIN_GRAMMAR_ONLY_NO_EXECUTION_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:p.error("--out required")
    obj={
      "schema":"structural.Wetherbee2023_Norway270_original_R_code_source_join_only.v1",
      "precommit":"docs/FOREST_BEETLE_WETHERBEE2023_AUTHOR_R_CODE_SOURCE_JOIN_PRESPEC_20261117.md",
      "original_publisher":source_only(),
      "new_biological_effect_scored":False,
      "overlap_with_Burner_Norway_UNVERIFIED":True,
      "previous_original_biodiversity_heldouts_NOT_RESCORED":True,
      "eBird_used":False,"TinyFish_used":False
    }
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Wetherbee2023_Norway270_R_code_source_join_grammar_only.json").write_text(
         json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(obj,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
