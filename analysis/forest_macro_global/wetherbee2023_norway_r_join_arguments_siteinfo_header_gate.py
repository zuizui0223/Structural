#!/usr/bin/env python3
"""Wetherbee2023 Norway: source author R join argument grammar + SiteInfo header.
DO NOT execute R code or read original species, site, guild or forest value rows.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import re
from pathlib import Path
from wetherbee2023_norway_author_R_code_sourceonly import (
    FILES, FIXED_SOURCE_CSV, SourceStop, get_author_code)
from wetherbee2023_norway270_three_csv_headers_sourceonly import (
    SOURCE_FILES, fetch_one_original)

PRESPEC="docs/FOREST_BEETLE_WETHERBEE_NORWAY_R_JOIN_AND_HOSTWOOD_HEADER_GATE_PRESPEC_20261117.md"
SITEINFO="SiteInfo_Alltaxon_Pred_Detri_SxFD.csv"
CALLS=("read.csv","read.table","read.delim","merge","left_join","inner_join",
       "full_join","match","rownames","colnames","row.names","col.names",
       "paste","paste0","t","transpose")
JOINS={"merge","left_join","inner_join","full_join"}
READERS={"read.csv","read.table","read.delim"}
GENERIC_KEY={"site","siteid","plot","plotid","project","projectid",
             "study","studyid","year","sampleid","tree","dataset","id"}
ALLOWED_ARGS={"by","by.x","by.y","all","all.x","all.y","sort","suffixes",
              "x","y","file","header","sep","row.names","check.names",
              "stringsAsFactors","quote","na.strings"}
STRONG_RESOURCE=("deadwood","dwvol","woodvolume","standingdead","downedwood",
                 "basalarea","treebasalarea","coarsewoody","snag",
                 "deadwooddensity","woodmass","woodamount","livingwood",
                 "deadwoodamount","hosttreespecies","hostwood","logvolume")
WEAK_RESOURCE=("tree","wood","stem","plot","forest","habitat")
EXACT={
    "project_parent":{"project","projectid","study","studyid","dataset","datasetid","source"},
    "physical_site":{"site","siteid","plot","plotid","locality","location","locationid"},
    "year_time":{"year","sampleyear","samplingyear","collectionyear","period","date"},
    "trap_effort":{"trap","trapid","samplingmethod","trapdays","effort","trapnights",
                   "samplingeffort","duration"},
    "naturalness":{"forestnaturalness","naturalness","managed","management",
                   "managementtype","foresttype","oldgrowth","nearnatural"},
    "resource_strong":{"deadwood","deadwoodvolume","woodvolume","standdeadwood",
                       "dwvol","dbh","basalarea","deadwooddiversity","snag",
                       "hosttreespecies","treebasalarea","logvolume"},
}

def normalized(s):
    return re.sub("[^a-z0-9]","",str(s).casefold())

def remove_comments_mask_strings(source):
    clean=list(source);masked=list(source)
    quote=None;esc=False;comment=False
    for i,ch in enumerate(source):
        if comment:
            if ch=="\n":comment=False
            else:clean[i]=" ";masked[i]=" "
            continue
        if quote:
            masked[i]=" "
            if esc:esc=False
            elif ch=="\\":esc=True
            elif ch==quote:quote=None
            continue
        if ch=="#":
            clean[i]=" ";masked[i]=" ";comment=True
        elif ch in ('"', "'", chr(96)):
            quote=ch;masked[i]=" "
    return "".join(clean),"".join(masked)

def capture_parenthesis(s,start):
    if s[start]!="(":raise SourceStop("SOURCE_R_CALL_NOT_OPEN")
    dep=0;q=None;escape=False
    for i in range(start,len(s)):
        ch=s[i]
        if q:
            if escape:escape=False
            elif ch=="\\":escape=True
            elif ch==q:q=None
            continue
        if ch in ('"', "'", chr(96)):q=ch;continue
        if ch=="(":dep+=1
        elif ch==")":
            dep-=1
            if dep==0:return s[start+1:i]
    raise SourceStop("SOURCE_R_CALL_UNBALANCED")

def split_args(s):
    out=[];piece=[];p=b=c=0;q=None;esc=False
    for ch in s:
        if q:
            piece.append(ch)
            if esc:esc=False
            elif ch=="\\":esc=True
            elif ch==q:q=None
            continue
        if ch in ('"', "'", chr(96)):q=ch;piece.append(ch);continue
        if ch=="(":p+=1
        elif ch==")":p-=1
        elif ch=="[":b+=1
        elif ch=="]":b-=1
        elif ch=="{":c+=1
        elif ch=="}":c-=1
        if ch=="," and not (p or b or c):
            if "".join(piece).strip():out.append("".join(piece).strip())
            piece=[]
        else:piece.append(ch)
        if min(p,b,c)<0:raise SourceStop("SOURCE_R_ARGUMENT_UNBALANCED")
    if "".join(piece).strip():out.append("".join(piece).strip())
    return out

def literal_keys(s):
    x=s.strip()
    one=re.fullmatch(r"""["'][^"'\\]*["']""",x)
    if one:vals=[x[1:-1]]
    else:
        arr=re.fullmatch(r"c\s*\((.*)\)",x,flags=re.DOTALL)
        if not arr:return {"kind":"computed_or_unresolved"}
        tokens=split_args(arr.group(1))
        if not tokens or not all(re.fullmatch(r"""["'][^"'\\]*["']""",
                                      t.strip()) for t in tokens):
            return {"kind":"computed_or_unresolved"}
        vals=[t.strip()[1:-1] for t in tokens]
    listed=sorted(set(normalized(v) for v in vals if normalized(v) in GENERIC_KEY))
    return {"kind":"literal_string_or_vector",
            "key_count":len(vals),
            "whitelisted_generic_key_values_only":listed,
            "non_whitelisted_literal_key_count":sum(
                 normalized(v) not in GENERIC_KEY for v in vals)}

def describe_call(func,arg_text):
    args=split_args(arg_text)
    named={};position=[]
    for arg in args:
        m=re.match(r"^\s*([A-Za-z][A-Za-z0-9._]*)\s*=(?!=)",arg)
        if m:named[m.group(1)]=arg[m.end():].strip()
        else:position.append(arg)
    out={"function":func,"argument_count":len(args),
         "positional_argument_count":len(position),
         "safe_named_arguments":sorted(k for k in named if k in ALLOWED_ARGS),
         "other_named_argument_count":sum(k not in ALLOWED_ARGS for k in named),
         "original_arguments_not_exported":True}
    if func in JOINS:
        keys={k:literal_keys(v) for k,v in named.items() if k in ("by","by.x","by.y")}
        out["join_key_syntax"]=keys
        out["join_by_explicit"]=bool(keys)
        out["join_not_automatically_author_physical_site_proof"]=True
    elif func in READERS:
        out["source_exact_published_CSV_name_references"]=[
            name for name in FIXED_SOURCE_CSV if name in arg_text]
        out["reader_row_names_option_present"]="row.names" in named
    elif func in ("rownames","colnames","row.names","col.names"):
        out["names_assignment_semantics_UNVERIFIED"]=True
    return out

def inspect_code(data,filename):
    try:raw=data.decode("utf-8-sig")
    except UnicodeError as exc:raise SourceStop("SOURCE_R_CODE_NONUTF8") from exc
    clean,masked=remove_comments_mask_strings(raw)
    regex=re.compile(r"(?<![A-Za-z0-9._])("+("|".join(
                     re.escape(v) for v in CALLS))+r")\s*\(",re.IGNORECASE)
    result=[]
    for m in regex.finditer(masked):
        opener=masked.find("(",m.start(),m.end())
        func=m.group(1).lower()
        result.append(describe_call(func,capture_parenthesis(clean,opener)))
    return {"original_author_R_filename":filename,
            "original_source_lines":len(raw.splitlines()),
            "parsed_calls":result,
            "source_exact_three_CSV_file_mentions":[
                 n for n in FIXED_SOURCE_CSV if n in raw],
            "author_R_source_code_not_executed":True,
            "R_code_original_expressions_NOT_EXPORTED":True,
            "original_species_site_trait_data_rows_NOT_READ":True}

def siteinfo_header(data):
    first=io.BytesIO(data).readline(65537)
    if len(first)>65536 or not first.endswith((b"\n",b"\r")):
        raise SourceStop("SOURCE_SITEINFO_HEADER_NOT_FULL_LINE")
    try:
        names=next(csv.reader([first.decode("utf-8-sig").rstrip("\r\n")],
                              delimiter=",",strict=True))
    except (csv.Error,UnicodeError) as exc:
        raise SourceStop("SOURCE_SITEINFO_CSV_HEADER_PARSE") from exc
    if len(names)!=41:raise SourceStop("SOURCE_SITEINFO_41_FIELD_SOURCE_DRIFT")
    norm=[normalized(x) for x in names]
    return {
       "official_source_header_column_count":len(norm),
       "predeclared_exact_generic_header_names":{
          c:sorted(set(v for v in norm if v in allowed))
          for c,allowed in EXACT.items() if any(v in allowed for v in norm)},
       "source_lexical_resource_field_candidate_counts":{
          "strong_local_hostwood_or_wood_amount_name_family":
             sum(any(word in token for word in STRONG_RESOURCE) for token in norm),
          "ambiguous_tree_wood_forest_name_family":
             sum(any(word in token for word in WEAK_RESOURCE) for token in norm)},
       "source_species_site_forest_numeric_rows_read":0,
       "original_unwhitelisted_headers_NOT_EXPORTED":True,
       "a_resource_sounding_name_is_NOT_proof_of_measured_hostwood":True}

def original_run():
    out={"status":"ORIGINAL_SOURCE_NOT_OPENED","original_biology_UNREAD":True}
    try:
        codes=[]
        for filename,(size,md5) in FILES.items():
            body=get_author_code(filename,size,md5)
            codes.append(inspect_code(body,filename))
        size,md5=SOURCE_FILES[SITEINFO]
        info=fetch_one_original(SITEINFO,size,md5)
        header=siteinfo_header(info)
        joins=[c for f in codes for c in f["parsed_calls"] if c["function"] in JOINS]
        out.update({
            "official_publisher_MD5_verified_for_two_R_and_one_SiteInfo_CSV":True,
            "author_R_static_join_grammar":codes,
            "official_siteinfo_HEADER_only":header,
            "author_lexical_join_count":len(joins),
            "literal_explicit_site_project_join_count":sum(any(
               "site" in item.get("whitelisted_generic_key_values_only",[]) or
               "project" in item.get("whitelisted_generic_key_values_only",[])
               for item in call.get("join_key_syntax",{}).values()) for call in joins),
            "author_project_site_year_source_lineage_VERIFIED":False,
            "local_measured_hostwood_values_VERIFIED":False,
            "overlap_with_Burner_Norway_VERIFIED":False,
            "status":"SOURCE_ORIGINAL_HOSTWOOD_OR_PROJECT_CROSSWALK_NOT_YET_VERIFIED"
        })
    except SourceStop as e:
        out["status"]=str(e)
        out["SOURCE_OR_METHOD_STOP_NOT_ECOLOGICAL_NULL"]=True
    return out

def known_truth():
    s=("# merge(x,y,by='ignored')\n"
       "x<-read.csv('GBIFnormalized_SpcSite_matrix_FD_unique.csv',row.names=1)\n"
       "y<-merge(x,z,by=c('site','project'),all.x=TRUE)\n"
       "z<-merge(x,y)\n"
       "print('merge(x,y,by=not-real)')\n"
       "rownames(x) <- paste0(z$site,'-',z$year)\n")
    x=inspect_code(s.encode(),"synthetic.R")
    joins=[c for c in x["parsed_calls"] if c["function"]=="merge"]
    assert len(joins)==2
    assert joins[0]["join_by_explicit"] and not joins[1]["join_by_explicit"]
    assert joins[0]["join_key_syntax"]["by"]["whitelisted_generic_key_values_only"]==[
        "project","site"]
    assert "GBIFnormalized_SpcSite_matrix_FD_unique.csv" in x[
        "source_exact_three_CSV_file_mentions"]
    h=("site,plot,tree,DW_Volume,stand_age,forest_type,"+
       ",".join("other"+str(i) for i in range(35))+"\n").encode()
    f=siteinfo_header(h)
    assert f["official_source_header_column_count"]==41
    assert f["source_lexical_resource_field_candidate_counts"][
        "strong_local_hostwood_or_wood_amount_name_family"]==1
    assert f["source_species_site_forest_numeric_rows_read"]==0
    print("SYNTHETIC_WETHERBEE_2023_R_JOIN_ARGUMENTS_AND_SITEINFO_HEADER_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    out={"schema":"structural.Wetherbee2023_author_R_joinargs_SiteInfo_original_header.v1",
         "precommit":PRESPEC,
         "original_source_only":original_run(),
         "original_Piccini_Finland_Burner_Thai_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
         "new_biodiversity_effect_estimated":False,"eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Wetherbee2023_Norway_R_joinargs_and_SiteInfo_sourceonly.json").write_text(
         json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
