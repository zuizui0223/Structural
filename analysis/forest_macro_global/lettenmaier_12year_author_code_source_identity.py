#!/usr/bin/env python3
"""Author 2025 ORIGINAL R-code crosswalk for 522 long log-years vs 525 matrix rows.

Inspects two original R scripts as published SOURCE METHODS only. Accesses
original beetle-long (plot/log/year/tree) and community FIRST row-ID column,
NEVER the 297 species abundance columns or any trait values.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import io
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from lettenmaier_12year_source_log_method_gate import (
    M, get_source, original_log_metadata, community_first_identifier_only,
    ScientificStop,
)

CODE_FILES={
 "GAM.R":(24865,"e9cbb99b1da35ea388793f0aeb28739f"),
 "NMDS.R":(13928,"4b80a1c2119b164da0442eb5a1e5b536"),
}
METHOD_REGEX=re.compile(r"(?i)\b(paste0?|merge|join|unite|mutate|row.names|rownames|read.csv|read_csv|plot|log|year|tree|community)\b")
YEAR=re.compile(r"^(?:19[89][0-9]|20[0-2][0-9])$")

def get_code(name,expected_size,digest):
    req=urllib.request.Request(
     f"https://zenodo.org/records/17337484/files/{name}?download=1",
     headers={"User-Agent":"Structural-original-author-R-method-crosswalk-sourceonly/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=40) as h:
            data=h.read(expected_size+1)
            status=h.status
    except urllib.error.HTTPError as exc:
        raise ScientificStop("SOURCE_STOP_AUTHOR_CODE_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,OSError,TimeoutError) as exc:
        raise ScientificStop("SOURCE_STOP_AUTHOR_CODE_TRANSPORT_"+type(exc).__name__) from exc
    if status!=200 or len(data)!=expected_size or hashlib.md5(data).hexdigest()!=digest:
        raise ScientificStop("SOURCE_STOP_AUTHOR_CODE_PUBLISHER_MD5_OR_BYTECOUNT_CHANGED")
    return data.decode("utf-8-sig","replace")


def infer_explicit_author_key_code(text:str):
    """Narrow ordered `paste(plot,log,year,sep=...)` only; no string guess."""
    rules=[]
    for linenum,line in enumerate(text.splitlines(),start=1):
        if re.match(r"^\s*#",line):
            continue
        # Original authored R method expression, not a text line containing
        # all terms or an unrelated ecological formula.
        for match in re.finditer(r"paste(0?)\s*\(([^\n)]*)\)",line):
            inside=match.group(2)
            fields=re.findall(r"(?<![A-Za-z0-9_])(plot|log|year)(?![A-Za-z0-9_])",inside)
            if len(fields)!=3 or len(set(fields))!=3:
                continue
            sep=re.search(r"sep\s*=\s*['\"]([_:\-. ])['\"]",inside)
            if match.group(1)=="0":
                separator=""
            elif sep:
                separator=sep.group(1)
            else:
                separator=" "
            rules.append({"source_original_R_line_number_NOT_CONTENT":linenum,
                          "author_fields_in_constructed_key_order":fields,
                          "exact_R_paste_literal_separator":separator})
    uniq={(tuple(q["author_fields_in_constructed_key_order"]),
           q["exact_R_paste_literal_separator"]) for q in rules}
    return rules,uniq


def code_method_only(code_texts):
    reports={}
    rules=[]
    for name,text in code_texts.items():
        lines=text.splitlines()
        operators=Counter()
        for line in lines:
            if re.match(r"^\s*#",line):continue
            operators.update(x.lower() for x in METHOD_REGEX.findall(line))
        matched,uniq=infer_explicit_author_key_code(text)
        rules.extend(matched)
        reports[name]={
            "source_author_pinned_R_code_line_count":len(lines),
            "original_method_join_ID_operator_tokens_count_not_code_content":dict(operators),
            "direct_author_paste_three_field_source_key_expressions":matched,
            "author_source_R_code_NOT_RUN_OR_REEXPORTED":True,
        }
    unique={
       (tuple(t["author_fields_in_constructed_key_order"]),t["exact_R_paste_literal_separator"])
       for t in rules
    }
    return reports,unique


def original_keys_and_labels(long_bytes,community_bytes):
    rd=csv.reader(io.StringIO(long_bytes.decode("utf-8-sig","replace"),newline=""),delimiter=";")
    head=next(rd)
    key_idx=[head.index(k) for k in ("plot","log","year")]
    if key_idx!=[2,3,4]:
        raise ScientificStop("SOURCE_STOP_522_AUTHOR_PLOT_LOG_YEAR_FIELD_DRIFT")
    keys=set()
    for row in rd:
        keys.add((row[2].strip(),row[3].strip(),row[4].strip()))
    if len(keys)!=522:
        raise ScientificStop("SOURCE_STOP_FROZEN_522_AUTHOR_LONG_LOG_YEAR_SOURCE_DRIFT")
    r2=csv.reader(io.StringIO(community_bytes.decode("utf-8-sig","replace"),newline=""),delimiter=",")
    head2=next(r2)
    if len(head2)!=298:
        raise ScientificStop("SOURCE_STOP_FROZEN_298_ORIGINAL_COMMUNITY_FIELDS_DRIFT")
    first=[r[0].strip() for r in r2]
    if len(first)!=525 or len(set(first))!=525:
        raise ScientificStop("SOURCE_STOP_FROZEN_525_COMMUNITY_IDENTITY_DRIFT")
    return keys,set(first),first


def source_label_shape(labels):
    positions=Counter()
    ntokens=Counter()
    for v in labels:
        tok=re.split(r"[_:\-./ ]+",v)
        ntokens[len(tok)]+=1
        positions[tuple(i for i,x in enumerate(tok) if YEAR.fullmatch(x))]+=1
    return {
        "original_community_candidate_row_ID_count":len(labels),
        "source_delimited_token_count_distribution":dict(sorted(ntokens.items())),
        "source_calendar_year_token_position_zero_based_distribution":{
           ",".join(map(str,position)) if position else "no_complete_four_digit_year":v
           for position,v in positions.items()},
        "original_source_row_identity_values_NOT_EXPORTED":True,
    }


def code_backed_matches(authorkeys,labels,rules):
    result=[]
    if len(rules)!=1:
        return {"explicit_unique_author_3field_join_pattern_count":len(rules),
                "source_exact_author_constructed_JOIN_NOT_EXECUTED":True,
                "source_community_to_long_matching_remains_UNVERIFIED":True}
    fields,sep=next(iter(rules))
    good=set()
    for plot,log,year in authorkeys:
        d={"plot":plot,"log":log,"year":year}
        good.add(sep.join(d[k] for k in fields))
    return {
        "explicit_unique_author_3field_join_pattern_count":1,
        "source_author_key_field_order":fields,
        "source_author_key_separator_literal":sep,
        "author_mapped_source_long_logyear_keys":len(good),
        "community_first_column_author_key_matches":len(good&labels),
        "community_source_IDs_not_found_in_long_author_keys":len(labels-good),
        "original_long_logyear_keys_not_in_community_matrix":len(good-labels),
        "source_crosswalk_with_no_collision":len(good)==len(authorkeys),
        "source_row_ID_values_and_author_R_code_NOT_EXPORTED":True,
        "not_an_ecological_response_score":True,
    }


def known_truth():
    rules,u=infer_explicit_author_key_code('id <- paste(plot, log, year, sep="_")\n')
    assert len(u)==1 and next(iter(u))==(("plot","log","year"),"_")
    assert len(infer_explicit_author_key_code("# paste(year,plot,log)\n")[1])==0
    a={("P1","L1","2013"),("P1","L1","2014")}
    b={"P1_L1_2013","EXTRA"}
    x=code_backed_matches(a,b,u)
    assert x["community_first_column_author_key_matches"]==1
    assert x["community_source_IDs_not_found_in_long_author_keys"]==1
    print("SYNTHETIC_SOURCE_AUTHOR_R_KEY_NOT_SPECIES_AND_MISSING_ROW_COUNT_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    known_truth()
    if args.test:return
    if not args.out:ap.error("--out")
    out={
      "schema":"structural.Lettenmaier12y_original_R_author_522vs525_firstcolumn_sourceidentity.v1",
      "original_Zenodo_DOI":"10.5281/zenodo.17337484",
      "original_author_R_code_NOT_EXECUTED":True,
      "original_beetle_taxa_and_species_counts_NOT_OPENED":True,
      "source_log_year_IDs_and_taxon_identifiers_NOT_EXPORTED":True,
      "frozen_original_2026_Finland_Burner_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
      "eBird_used":False,
    }
    try:
        codes={k:get_code(k,*v) for k,v in CODE_FILES.items()}
        long=get_source(*M["raw"])
        community=get_source(*M["comm"])
        out["source_author_two_R_scripts_plus_two_source_csv_MD5_verified"]=True
        keysa,keysb,order=original_keys_and_labels(long,community)
        method,uniq=code_method_only(codes)
        out["author_published_method_code_metadata"]=method
        out["source_original_matrix_ID_pattern_counts"]=source_label_shape(order)
        out["original_author_522_logyear_525_comm_ID_count_unchanged"]=(
           len(keysa)==522 and len(keysb)==525
        )
        out["author_code_backed_community_join"]=code_backed_matches(keysa,keysb,uniq)
        if len(uniq)==1:
            join=out["author_code_backed_community_join"]
            out["status"]=(
                "SOURCE_AUTHOR_EXPLICIT_PASTE_KEY_CROSSWALK_DIAGNOSTICS_COMPLETE_NO_BIOLOGY"
                if join["source_crosswalk_with_no_collision"]
                else "SOURCE_STOP_AUTHOR_KEY_COLLISION_NO_SPECIES_SCORING"
            )
        else:
            out["status"]="SOURCE_AUTHOR_CODE_DOES_NOT_DEFINE_UNIQUE_THREE_FIELD_JOIN"
    except ScientificStop as e:
        out["status"]=str(e)
        out["source_method_STOP_not_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Lettenmaier12y_original_author_R_join_and_522_525_sourceonly.json").write_text(
      json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(out,indent=2,ensure_ascii=False))


if __name__=="__main__":main()
