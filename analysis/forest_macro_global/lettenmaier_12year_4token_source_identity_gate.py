#!/usr/bin/env python3
"""One finite six-candidate original four-token matrix-vs-log source-ID check.

Only the publisher-original long table columns plot/log/year/tree and the
community matrix's first-column label are accessed. ALL six permutations of
(plot,log,tree) are evaluated; not a biodiversity model or outcome search.
"""
from __future__ import annotations

import argparse
import csv
import io
from itertools import permutations
import json
import re
from pathlib import Path
from lettenmaier_12year_source_log_method_gate import M,get_source,ScientificStop

FIELDS=("plot","log","tree")
SEP=re.compile(r"[_:\-./ ]+")
YEAR=re.compile(r"^(?:19[89][0-9]|20[0-2][0-9])$")


def source_metadata_only(long_csv:bytes, community_csv:bytes):
    rd=csv.reader(io.StringIO(long_csv.decode("utf-8-sig","replace"),newline=""),delimiter=";")
    h=next(rd,[])
    if len(h)!=15 or {k:h.index(k) if k in h else -1 for k in ("plot","log","year","tree")}!={
        "plot":2,"log":3,"year":4,"tree":6
    }:
        raise ScientificStop("SOURCE_STOP_FROZEN_FOUR_SOURCE_METADATA_FIELDS_CHANGED")
    source={}
    n=0
    for row in rd:
        n+=1
        plot,log,year,tree=(row[2].strip(),row[3].strip(),row[4].strip(),row[6].strip())
        if not plot or not log or not year or not tree or not YEAR.fullmatch(year):
            raise ScientificStop("SOURCE_STOP_SOURCE_AUTHOR_LOG_YEAR_TREE_INVALID")
        key=(plot,log,year)
        if key in source and source[key]!=tree:
            raise ScientificStop("SOURCE_STOP_AUTHOR_LOG_TREE_HOST_CONFLICT")
        source[key]=tree
    if n!=7738 or len(source)!=522:
        raise ScientificStop("SOURCE_STOP_FROZEN_7738_LONG_RECORDS_522_LOGYEARS_DRIFT")

    rd2=csv.reader(io.StringIO(community_csv.decode("utf-8-sig","replace"),newline=""),delimiter=",")
    h2=next(rd2,[])
    if len(h2)!=298:
        raise ScientificStop("SOURCE_STOP_FROZEN_COMMUNITY_298_COL_SOURCE_DRIFT")
    ids=[]
    for row in rd2:
        # Source matrix first column ONLY; remaining 297 fields are ignored.
        if len(row)!=len(h2):
            raise ScientificStop("SOURCE_STOP_ORIGINAL_COMMUNITY_WIDE_FIELD_COUNT")
        txt=row[0].strip()
        t=SEP.split(txt)
        if len(t)!=4 or not YEAR.fullmatch(t[-1]):
            raise ScientificStop("SOURCE_STOP_FOUR_TOKEN_SOURCE_ID_SCHEMA_DRIFT")
        ids.append(tuple(t))
    if len(ids)!=525 or len(set(ids))!=525:
        raise ScientificStop("SOURCE_STOP_FROZEN_525_UNIQUE_MATRIX_ROWS_DRIFT")
    return source,set(ids)


def run_all_six(source,matrix):
    candidate=[]
    for order in permutations(FIELDS):
        translated=set()
        for (plot,log,year),tree in source.items():
            d=dict(plot=plot,log=log,tree=tree)
            translated.add(tuple(d[x] for x in order)+(year,))
        hits=len(translated&matrix)
        candidate.append({
            "source_original_fields_at_matrix_ID_positions_1_2_3":list(order),
            "matrix_position_4_original_year":True,
            "original_source_unique_contexts":len(source),
            "translated_unique_source_ID_candidates":len(translated),
            "matched_matrix_source_IDs":hits,
            "long_source_contexts_not_in_matrix":len(translated-matrix),
            "community_matrix_row_IDs_not_in_original_long_contexts":len(matrix-translated),
            "source_ID_translation_collisions":len(source)-len(translated),
            "no_original_raw_ID_or_observed_species_values_exposed":True,
        })
    full=[x for x in candidate if
        x["matched_matrix_source_IDs"]==522 and
        x["source_ID_translation_collisions"]==0]
    return {
      "all_six_source_original_field_permutations_reported":candidate,
      "number_of_unique_522of522_source_ID_matches":len(full),
      "unique_full_source_ID_field_order_candidate":(
          full[0]["source_original_fields_at_matrix_ID_positions_1_2_3"]
          if len(full)==1 else None
      ),
      "source_author_published_R_method_did_NOT_explicitly_certify_candidate_rule":True,
      "no_unmatched_source_community_ID_treated_as_zero_or_absence":True,
      "source_candidate_permutation_is_method_qualification_NOT_biology":True,
      "status":(
         "SOURCE_UNIQUE_4TOKEN_SOURCE_KEY_CANDIDATE_FULL_522OF522_3_MATRIXONLY_STILL_UNRESOLVED"
         if len(full)==1 else "SOURCE_CROSSWALK_NOT_UNIQUELY_IDENTIFIABLE_NO_SPECIES_SCORING"
      )
    }


def known_truth():
    a={("P","L","2019"):"Fagus",("P","M","2020"):"Picea"}
    b={("P","L","Fagus","2019"),("P","M","Picea","2020"),("O","N","Fagus","2019")}
    x=run_all_six(a,b)
    assert len(x["all_six_source_original_field_permutations_reported"])==6
    assert x["number_of_unique_522of522_source_ID_matches"]==0 # fixed 522 only production
    assert x["all_six_source_original_field_permutations_reported"][0]["matched_matrix_source_IDs"]==2
    assert x["no_unmatched_source_community_ID_treated_as_zero_or_absence"]
    print("SYNTHETIC_SIX_FIXED_SOURCE_METADATA_PERMUTATIONS_AND_NO_BIOLOGY_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if not a.out:p.error("--out")
    result={
      "schema":"structural.Lettenmaier12y_522logyear_525community_4token_all6_sourceonly.v1",
      "original_Zenodo":"10.5281/zenodo.17337484",
      "author_2_metadata_csv_original_MD5s_checked":False,
      "prior_author_R_code_no_explicit_unique_join_premise_preserved":True,
      "all_fields_original_plot_log_tree_year_only":True,
      "original_biological_response_297_species_columns_UNREAD":True,
      "original_matrix_sample_ID_values_and_log_tokens_NOT_EXPORTED":True,
      "previous_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_scores_UNCHANGED":True,
      "eBird_used":False
    }
    try:
        long=get_source(*M["raw"])
        comm=get_source(*M["comm"])
        result["author_2_metadata_csv_original_MD5s_checked"]=True
        s,m=source_metadata_only(long,comm)
        result["source_original_522_long_logyear_and_525_matrix_ID_verified"]=True
        result["identity_test"]=run_all_six(s,m)
        result["status"]=result["identity_test"]["status"]
    except ScientificStop as e:
        result["status"]=str(e)
        result["source_identity_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Lettenmaier12y_522logyear_525matrix_fourtoken_all6_sourceonly.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8"
    )
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":main()
