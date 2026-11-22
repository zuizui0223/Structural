#!/usr/bin/env python3
"""Original Traylor2026 356 wood-object source cohort metadata ONLY.

Auth Zenodo concept/version, exact published CC-BY MD5 three files.
Only original CSV nonresponse fields are inspected, never source beetle
abundance/presence quantities, GLMM outputs, or response-based subsets.
"""
import argparse
import collections
import csv
import io
import json
import math
from pathlib import Path

import traylor2026_original_firstheader_methodonly as parent

SOURCE_NONRESPONSE=("study","species","origin","volume_m3","time_months")

def field_qa(blob):
    if not blob.get("ambrosia per deadwood object data.csv"):
        raise ValueError("SOURCE_ORIGINAL_CSV_MISSING_STOP")
    data=blob["ambrosia per deadwood object data.csv"]
    reader=csv.DictReader(io.StringIO(data.decode("utf-8-sig",errors="replace")),delimiter=",")
    fields=reader.fieldnames
    if not fields or len(fields)!=15 or len(fields)!=len(set(fields)):
        raise ValueError("SOURCE_ORIGINAL_15HEADER_STOP")
    if not set(SOURCE_NONRESPONSE).issubset(fields):
        raise ValueError("SOURCE_AUTHOR_REQUIRED_NONRESPONSE_FIELDS_STOP")
    extra_nonresponse=[f for f in fields if f not in SOURCE_NONRESPONSE and
                       not ("abd" in f.lower() or "pres" in f.lower())]
    frame=[]
    for original_source_row in reader:
        # Ignore organism count, occurrence, model response, presence factors:
        # only five allowlisted authored NONRESPONSE method fields accessed.
        d={k:(original_source_row.get(k) or "").strip() for k in SOURCE_NONRESPONSE}
        frame.append(d)
    if len(frame)!=356:
        raise ValueError("SOURCE_AUTHOR_356_ORIGINAL_OBJECT_ROWS_STOP")
    for key in SOURCE_NONRESPONSE:
        if sum(not r[key] or r[key].lower() in ("na","nan","null") for r in frame):
            raise ValueError("SOURCE_ORIGINAL_NONRESPONSE_MISSING_"+key)
    groups=collections.Counter(r["study"] for r in frame)
    if len(groups)!=4:
        raise ValueError("SOURCE_ORIGINAL_FOUR_STUDIES_NOT_CONFIRMED_STOP")
    tree_groups=collections.defaultdict(set)
    origin_groups=collections.defaultdict(set)
    positive_ranges={}
    for key in ["volume_m3","time_months"]:
        values=[]
        for r in frame:
            try: v=float(r[key].replace(",","."))
            except ValueError:raise ValueError("SOURCE_ORIGINAL_"+key+"_NUMBER_STOP")
            if not math.isfinite(v) or v<=0:
                raise ValueError("SOURCE_ORIGINAL_"+key+"_POSITIVE_FINITE_STOP")
            values.append(v)
        positive_ranges[key]={
            "all_356_positive_and_finite":True,
            "observed_min":min(values),
            "observed_max":max(values),
            "distinct_values_n":len(set(values))
        }
    for r in frame:
        tree_groups[r["study"]].add(r["species"])
        origin_groups[r["study"]].add(r["origin"])
    tree_study_occurrence=collections.Counter(
        species for spp in tree_groups.values() for species in spp)
    support={
       "schema":"structural.traylor2026_356_original_objects_study_nonresponse_QA.v1",
       "original_public_CSV_all_15_field_names":fields,
       "source_nonresponse_selected_fields":list(SOURCE_NONRESPONSE),
       "source_other_method_field_candidates_not_read":extra_nonresponse,
       "source_original_wood_object_rows":len(frame),
       "original_distinct_studies":len(groups),
       "study_object_counts_sorted_without_identifiers":sorted(groups.values()),
       "original_distinct_tree_substrate_taxa":len({r["species"] for r in frame}),
       "study_distinct_tree_taxa_counts_sorted":sorted(len(s) for s in tree_groups.values()),
       "tree_taxa_shared_across_multiple_studies_n":sum(n>=2 for n in tree_study_occurrence.values()),
       "original_distinct_tree_origin_labels":len({r["origin"] for r in frame}),
       "original_tree_origin_categories_n_per_study_sorted":sorted(len(s) for s in origin_groups.values()),
       "original_nonresponse_range_by_variable":positive_ranges,
       "all_356_study_keys_present":True,
       "original_sample_global_object_id_verified":False,
       "method_row_grain_author_article_says_one_sampled_deadwood_object":True,
       "zero_emergence_observation_method_qualifier":"original publication says reared sampled logs; absence of a beetle emergence record is NOT confirmed colonization failure",
       "any_original_ambrosia_abundance_or_presence_values_inspected":False,
       "original_organism_count_aggregated":0,
       "new_biological_effects_scored":0,
       "status":"SOURCE_356_WOOD_OBJECT_FOUR_STUDY_NONRESPONSE_SOURCE_PASS_NO_BEETLE_VALUES"
    }
    return support

def test():
    rows="study,species,origin,volume_m3,time_months,"+ ",".join("q"+str(i) for i in range(10))+"\n"
    rows+="\n".join(
        f"S{i//89},Tree{i%23},Native,0.02,3,"+",".join("0" for j in range(10))
        for i in range(356))
    fake={"ambrosia per deadwood object data.csv":rows.encode()}
    result=field_qa(fake)
    assert result["original_distinct_studies"]==4
    assert result["source_original_wood_object_rows"]==356
    assert result["new_biological_effects_scored"]==0
    print("TRAYLOR_356_ORIGINAL_WOOD_SOURCE_NONRESPONSE_SYNTHETIC_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="traylor2026_356_nonresponse/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    rec={
      "schema":"structural.traylor2026_356_wood_objects_prebiology_nonresponse_gate.v1",
      "original_publisher_version_doi":parent.VERSION_DOI,
      "all_original_source_MD5_verified_before_opening":True,
      "original_study_beetle_abundance_or_presence_values_inspected":False,
      "ecological_effects_scored":0,
      "previous_Ecuador_Ramberg_Finland_BALA_GEB_effects_unchanged":True,
      "eBird_used":False,"TinyFish_used":False,
      "status":"SOURCE_WOOD_OPPORTUNITY_PREBIOLOGY_HOLD"
    }
    try:
        raw=parent.source()
        rec["source_anonymous_nonresponse"]=field_qa(raw)
        rec["status"]=rec["source_anonymous_nonresponse"]["status"]
    except Exception as e:
        rec["status"]="SOURCE_ORIGINAL_NONRESPONSE_SCHEMA_OR_TRANSPORT_STOP"
        rec["error_class"]=type(e).__name__
        rec["error_code"]=str(e)[:160] if isinstance(e,ValueError) else ""
    f=Path(a.out)
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(rec,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("TRAYLOR_356_NONRESPONSE_GATE",rec["status"])
    print("AMBROSIA_ORIGINAL_RESPONSE_VALUES_READ",rec["original_study_beetle_abundance_or_presence_values_inspected"])
    print("NEW_ECOLOGICAL_EFFECTS",rec["ecological_effects_scored"])
if __name__=="__main__":
    main()
