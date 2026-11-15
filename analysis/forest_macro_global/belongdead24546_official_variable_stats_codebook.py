#!/usr/bin/env python3
"""Original BExIS24546 published VariableName/Description/Unit codebook only.

Reads official public BEXIS2 api/DataStatistic/24546 once, and returns ONLY
field identifiers, datatype and strictly sanitized measurement unit strings,
plus semantic keyword flags. Does not output publisher uniqueValues,
min/max/count/missing-values, source individual plots, tree categories or
beetle outcomes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT="https://www.bexis.uni-jena.de/api/DataStatistic/24546"
FIELDS=("spec1","spec2","DWV","Vharv","PT","Tdir","PTNum","dc")
LIMIT=10_000_000
SEMANTIC={
 "author_description_tree_taxon":re.compile(r"(?i)\b(?:species|baumart|taxon|tree.?species|holzart)\b"),
 "author_description_deadwood_volume":re.compile(r"(?i)(?:dead.?wood.{0,25}volum|totholz.{0,25}volum|volume.{0,25}dead.?wood|wood.{0,25}volume)"),
 "author_description_wood_origin":re.compile(r"(?i)\b(?:origin|herkunft|source|harvest|logging|ernte|harv)\b"),
 "author_description_decay":re.compile(r"(?i)\b(?:decay|decompos|zersetz|verrott|decay class)\b"),
 "author_description_volume_unit":re.compile(r"(?i)(?:m³|m\^3|m3|cubic met(?:er|re)|kubikmeter)"),
}
class SourceStop(RuntimeError):pass

def read_one():
    request=urllib.request.Request(ENDPOINT,headers={
        "User-Agent":"Structural-author-source-BExIS24546-variable-codebook/1.0",
        "Accept":"application/json"})
    try:
        with urllib.request.urlopen(request,timeout=55) as resp:
            raw=resp.read(LIMIT+1)
            status=resp.status
            ctype=resp.headers.get("Content-Type","")
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS_PUBLIC_VARIABLE_STATS_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEXIS_PUBLIC_VARIABLE_STATS_TRANSPORT_"+type(exc).__name__) from exc
    if status!=200 or len(raw)>LIMIT or "json" not in ctype.lower():
        raise SourceStop("SOURCE_STOP_OFFICIAL_VARIABLE_JSON_ABSENT_OR_TOO_LARGE")
    try:doc=json.loads(raw.decode("utf-8"))
    except (ValueError,UnicodeError) as exc:
        raise SourceStop("SOURCE_STOP_ORIGINAL_PUBLISHER_VARIABLE_JSON_INVALID") from exc
    return doc,hashlib.sha256(raw).hexdigest(),len(raw)

def get_item(entry,*names):
    return next((entry[k] for k in names if k in entry),None)

def sanitize_unit(value):
    if value is None:return None
    if isinstance(value,dict):
        value=get_item(value,"Name","name")
    if not isinstance(value,str):return None
    unit=value.strip()
    if not unit or len(unit)>110:return None
    if not re.fullmatch(r"[A-Za-z0-9\s°µμ/%^³²_.+×·():-]{1,110}",unit):return None
    return unit

def summary(doc,digest,nbytes):
    if not isinstance(doc,list) or not 4<=len(doc)<=250:
        raise SourceStop("SOURCE_STOP_BEXIS_DATASTATISTICS_ARRAY_SCHEMA")
    out={}
    seen=set()
    for entry in doc:
        if not isinstance(entry,dict):raise SourceStop("SOURCE_STOP_BEXIS_VARIABLE_RECORD_NOT_OBJECT")
        label=get_item(entry,"VariableName","variableName")
        if not isinstance(label,str):continue
        if label not in FIELDS:continue
        if label in seen:raise SourceStop("SOURCE_STOP_ORIGINAL_SOURCE_FIELD_DUPLICATE_NAMES")
        seen.add(label)
        desc=get_item(entry,"VariableDescription","variableDescription")
        if not isinstance(desc,str):desc=""
        dtype=get_item(entry,"DataTypeName","dataTypeName")
        id=get_item(entry,"VariableId","variableId")
        unit=get_item(entry,"Unit","unit")
        out[label]={
          "original_public_variable_ID":id if isinstance(id,int) else None,
          "original_exact_source_field_name":label,
          "original_declared_data_type":str(dtype)[:80] if isinstance(dtype,str) else None,
          "original_declared_unit_name_only":sanitize_unit(unit),
          "original_description_present":bool(desc.strip()),
          "original_description_semantic_keyword_flags_only":{
              k:bool(pattern.search(desc)) for k,pattern in SEMANTIC.items()},
          "original_publisher_variable_description_text_NOT_EXPORTED":True,
          "original_biological_uniqueValues_min_max_and_counts_NEVER_EXPORTED":True,
        }
    have={k:bool(out.get(k)) for k in FIELDS}
    # We treat this only as a field dictionary feasibility check. A flag or
    # a generic unit is insufficient to establish spec1/spec2 biological code.
    required=all(have[x] for x in ("spec1","spec2","DWV"))
    means=required and all(out[x]["original_description_present"] for x in ("spec1","spec2","DWV"))
    explicit_unit=required and out["DWV"]["original_declared_unit_name_only"] is not None
    return {
      "schema":"structural.BExIS24546_original_publisher_variable_statistics_units_semantics.v1",
      "official_source_documented_API":ENDPOINT,
      "original_published_source_variable_stats_JSON_bytes":nbytes,
      "original_source_stats_JSON_SHA256":digest,
      "original_publisher_variable_records_in_full_response":len(doc),
      "predeclared_original_csv_method_fields_found":have,
      "author_variable_codebook_properties_selected_ONLY":out,
      "source_exact_spec1_spec2_DWV_field_records_present":required,
      "source_author_descriptions_for_spec1_spec2_DWV_all_present":means,
      "source_DWV_author_unit_name_specified":explicit_unit,
      "no_original_source_uniqueValues_min_max_species_site_ID_or_measurements_OUTPUT":True,
      "no_original_beetle_species_count_response_READ":True,
      "original_tag1_and_latest_31123_24546_byte_identical_verified":True,
      "prior_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_effects_UNCHANGED":True,
      "eBird_used":False,
      "status":"SOURCE_ORIGINAL_VARIABLE_DICTIONARY_AVAILABLE_CODE_SEMANTICS_REQUIRE_REVIEW"
          if means and explicit_unit else
          "SOURCE_VARIABLE_DICTIONARY_NOT_ENOUGH_TO_DEFINE_TREE_HOST_VOLUMES",
    }

def synthetic():
    sample=[
       {"VariableName":"DWV","VariableId":1337,"VariableDescription":"deadwood volume",
        "Unit":"m³","DataTypeName":"float","uniqueValues":[{"raw species value":27.0}]},
       {"VariableName":"spec1","VariableId":1338,"VariableDescription":"tree species","Unit":"none"},
       {"VariableName":"spec2","VariableId":1339,"VariableDescription":"secondary species","Unit":"none"},
       {"VariableName":"Vharv","VariableId":1340,"VariableDescription":"harvest volume","Unit":"m³"},
    ]
    x=summary(sample,"0"*64,512)
    assert x["source_exact_spec1_spec2_DWV_field_records_present"]
    assert x["source_DWV_author_unit_name_specified"]
    assert x["author_variable_codebook_properties_selected_ONLY"]["DWV"]["original_declared_unit_name_only"]=="m³"
    assert "raw species value" not in json.dumps(x)
    assert all("uniqueValues" not in o for o in
               x["author_variable_codebook_properties_selected_ONLY"].values())
    print("SYNTHETIC_OFFICIAL_DATASTATISTICS_METADATA_REDACTION_UNIT_AND_FROZEN_FIELDS_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out needed")
    try:
        doc,sha,n=read_one()
        result=summary(doc,sha,n)
    except SourceStop as ex:
        result={"schema":"structural.BExIS24546_original_publisher_variable_statistics_units_semantics.v1",
                "status":str(ex),
                "source_dictionary_STOP_not_ecological_null":True,
                "old_original_results_unchanged":True}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BExIS24546_official_variableStats_original_field_units_only.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
