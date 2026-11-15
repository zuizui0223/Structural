#!/usr/bin/env python3
"""One original source-only categorical 24546 stratum discrepancy diagnostic.

Only source original 30 plot ID keys and stratum, and author published
stratum VariableDescription/Unit. NO original DWV numeric, species fields,
beetle captures, abundance, traits, forest plot coordinates or sampling zeros.
"""
from __future__ import annotations
import argparse,csv,io,json,re
from collections import Counter,defaultdict
from pathlib import Path
from belongdead24546_2012_stratum_unit_source_quality import (
    pinned,original_30_plots,FIELD_NAMES
)
from belongdead24546_official_variable_stats_codebook import read_one,SourceStop

KNOWN=("T","L","T7","S")
class ScientificStop(RuntimeError):pass

def stratum_codes(plots,b):
    reader=csv.reader(io.StringIO(b.decode("utf-8-sig"),newline=""))
    h=next(reader,[])
    if h!=FIELD_NAMES:raise ScientificStop("SOURCE_STOP_FIXED_24546_CSV_METHOD_HEADER_DRIFT")
    code_counts=Counter()
    plot_coverage=defaultdict(set)
    n=0
    for row in reader:
        if not row or not any(x.strip() for x in row):continue
        if len(row)!=12:raise ScientificStop("SOURCE_STOP_FIXED_SOURCE_CSV_ROW_SHAPE")
        p=row[1].strip()
        if p not in plots:continue
        n+=1
        stratum=row[9].strip()
        if not stratum or not re.fullmatch(r"[A-Za-z0-9_]{1,10}",stratum):
            name="[unclassified_source_field_code]"
        else:
            name=stratum
        code_counts[name]+=1
        plot_coverage[name].add(p)
    if n!=1385 or len(set().union(*plot_coverage.values()))!=30:
        raise ScientificStop("SOURCE_STOP_1385_ITEMS_30_ORIGINAL_SITES_SOURCE_DRIFT")
    return {
        "original_wood_item_rows_in_30_experimental_plots":n,
        "source_exact_original_stratum_code_counts":dict(sorted(code_counts.items())),
        "source_original_plots_per_stratum_code":{k:len(v) for k,v in sorted(plot_coverage.items())},
        "source_stratum_code_count":len(code_counts),
        "source_rows_in_author_previously_recognized_T_L_T7_S":sum(code_counts[k] for k in KNOWN),
        "source_rows_outside_four_original_codebook_strata":sum(n for k,n in code_counts.items() if k not in KNOWN),
        "individual_plot_IDs_and_biological_wood_values_NEVER_EXPORTED":True,
    }

def publisher_stratum_description():
    data,sha,n=read_one()
    if not isinstance(data,list):raise ScientificStop("SOURCE_STOP_OFFICIAL_PUBLISHER_VARIABLE_NOT_ARRAY")
    records=[x for x in data if isinstance(x,dict) and x.get("VariableName",x.get("variableName"))=="stratum"]
    if len(records)!=1:raise ScientificStop("SOURCE_STOP_STRATUM_AUTHOR_PUBLISHED_VARIABLE_ABSENT")
    x=records[0]
    desc=x.get("VariableDescription",x.get("variableDescription",""))
    if not isinstance(desc,str) or not desc.strip():
        raise ScientificStop("SOURCE_STOP_SOURCE_STRATUM_AUTHOR_DESCRIPTION_BLANK")
    if len(desc)>12000:raise ScientificStop("SOURCE_STOP_STRATUM_AUTHOR_DESCRIPTION_EXCEEDS12K")
    clean=re.sub(r"\s+"," ",desc).strip()
    unit=x.get("Unit",x.get("unit"))
    return {
        "publisher_original_variable_name":"stratum",
        "publisher_original_variable_ID_metadata":x.get("VariableId",x.get("variableId")),
        "publisher_original_declared_type":x.get("DataTypeName",x.get("dataTypeName")),
        "publisher_original_unit_name_only":unit if isinstance(unit,str) and len(unit)<100 else None,
        "publisher_original_description_char_length":len(desc),
        "publisher_original_description_CC_BY4_excerpt_first_220chars":clean[:220],
        "publisher_original_author_description_was_truncated":len(clean)>220,
        "source_api_stats_SHA256":sha,
        "source_author_original_uniqueValues_and_measurements_NOT_EXPORTED":True,
    }

def known_truth():
    assert KNOWN==("T","L","T7","S")
    assert re.fullmatch(r"[A-Za-z0-9_]{1,10}","T7")
    assert not re.fullmatch(r"[A-Za-z0-9_]{1,10}","VIP001_Location:52")
    print("SYNTHETIC_AUTHOR_STRATUM_CODE_AND_ORIGINAL_LOCATION_SUPPRESSION_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",type=Path)
    a=p.parse_args();known_truth()
    if a.test:return
    if not a.out:p.error("--out required")
    try:
        source=stratum_codes(original_30_plots(pinned(31123)),pinned(24546))
        original=publisher_stratum_description()
        z={
          "schema":"structural.BELongDead24546_original_2012_stratum_574_unclassified_method_codebook.v1",
          "original_tag1_public_CC_BY4_BExIS_dataset":24546,
          "source_30_plot_2012_stratum_code_counts_only":source,
          "source_publisher_author_stratum_description":original,
          "original_beetle_species_abundance_and_DWV_wood_measurements_NOT_READ":True,
          "no_new_ecological_effect_positivity_or_negativity_inferred":True,
          "prior_Finland_Burner_PREDICTS_NEON_BALA_GEB_scores_SEALED":True,
          "eBird_used":False,
          "status":"AUTHOR_2012_STRATUM_CODES_AND_UNIT_DICTIONARY_INSPECTED_PREDICTOR_NOT_YET_SCORED"
        }
    except (ScientificStop,SourceStop) as ex:
        z={"schema":"structural.BELongDead24546_original_2012_stratum_574_unclassified_method_codebook.v1",
           "status":str(ex),"source_method_STOP_not_biological_effect":True}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"BELongDead24546_2012_original_stratum574_code_and_author_definition_sourceonly.json").write_text(
      json.dumps(z,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(z,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
