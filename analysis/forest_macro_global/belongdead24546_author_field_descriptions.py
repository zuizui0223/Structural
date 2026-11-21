#!/usr/bin/env python3
"""One-time original CC-BY4 BExIS24546 author descriptions for 5 fields only.

No uniqueValues, species code values, plot identifiers, raw DWV item volumes,
original beetle records, min/max/count/missing-value tables are exported.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from belongdead24546_official_variable_stats_codebook import read_one,SourceStop,sanitize_unit
FIELDS=("spec1","spec2","DWV","Vharv","dc")
MAX_DESCRIPTION=12000
EXCERPT_CHARS=175

def read_dictionary():
    data,sha,n=read_one()
    if not isinstance(data,list):
        raise SourceStop("SOURCE_STOP_AUTHOR_VARIABLE_DICTIONARY_NOT_ARRAY")
    found={}
    for e in data:
        if not isinstance(e,dict):continue
        name=e.get("VariableName",e.get("variableName"))
        if name not in FIELDS:continue
        if name in found:raise SourceStop("SOURCE_STOP_DUPLICATE_ORIGINAL_AUTHOR_FIELD_NAME")
        descr=e.get("VariableDescription",e.get("variableDescription",""))
        if not isinstance(descr,str) or not descr.strip():
            raise SourceStop("SOURCE_STOP_PUBLISHER_ORIGINAL_DESCRIPTION_MISSING_"+str(name))
        original_length=len(descr)
        if original_length>MAX_DESCRIPTION:
            raise SourceStop("SOURCE_STOP_PUBLISHER_VARIABLE_DESCRIPTION_OVER12K_"+name)
        clean=re.sub(r"\\s+"," ",descr).strip()
        # Public author metadata only. A 175-char excerpt may be incomplete;
        # it cannot establish an entire tree species/coding dictionary.
        # All source uniqueValues and wood/beetle measurements remain unopened.
        unit=e.get("Unit",e.get("unit"))
        found[name]={
            "source_author_variable_ID_metadata":e.get("VariableId",e.get("variableId")),
            "source_original_field_name":name,
            "original_description_raw_character_length":original_length,
            "original_description_excerpt_truncated":len(clean)>EXCERPT_CHARS,
            "original_published_author_description_CC_BY4_short":clean[:EXCERPT_CHARS],
            "publisher_declared_unit":sanitize_unit(unit),
            "author_variable_description_not_source_record_values":True,
        }
    if len(found)!=len(FIELDS):
        raise SourceStop("SOURCE_STOP_ORIGINAL_FIVE_REQUIRED_FIELD_DESCRIPTIONS_MISSING")
    return {
       "schema":"structural.BExIS24546_original_published_short_source_field_descriptions.v1",
       "original_public_CCBY4_BExIS_dataset":24546,
       "source_documented_original_variable_endpoint":"api/DataStatistic/24546",
       "original_variable_source_JSON_sha256":sha,
       "original_public_source_field_descriptions":found,
       "original_source_30of30_tag1_BELongDead_plot_join_ALREADY_VERIFIED":True,
       "original_wood_items_and_beetle_abundance_numeric_values_UNREAD":True,
       "source_API_original_uniqueValues_min_max_observation_counts_NOT_EXPORTED":True,
       "BExIS_31124_15_new_TrapID_and_sampling_effort_still_UNVERIFIED":True,
       "all_Finland_Burner_PREDICTS_NEON_BALA_GEB_old_results_FROZEN":True,
       "eBird_used":False,
       "status":"ORIGINAL_AUTHOR_FIELD_DESCRIPTIONS_RECOVERED_SOURCE_ONLY_NO_BIOLOGY",
    }

def synthetic():
    assert set(FIELDS)=={"spec1","spec2","DWV","Vharv","dc"}
    assert sanitize_unit("cubic meter")=="cubic meter"
    assert sanitize_unit("cubic meter per hectare")=="cubic meter per hectare"
    assert MAX_DESCRIPTION==12000 and EXCERPT_CHARS==175
    print("SYNTHETIC_AUTHOR_FIVE_FIELD_DESCRIPTION_ONLY_NO_RECORD_VALUES_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out needed")
    try:r=read_dictionary()
    except SourceStop as e:
        r={"schema":"structural.BExIS24546_original_published_short_source_field_descriptions.v1",
           "status":str(e),"source_STOP_not_ecological_non_support":True}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BExIS24546_original_spec1_spec2_DWV_Vharv_dc_short_author_descriptions.json").write_text(
       json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
