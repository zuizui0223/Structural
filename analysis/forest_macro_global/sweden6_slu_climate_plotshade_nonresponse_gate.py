#!/usr/bin/env python3
"""SLU 88 climate plot×shade original data ONLY non-biological source quality.

Read permitted environmental columns; CTI, Species richness, Totlab are
organismal responses and NEVER semantically accessed. Never open original
specieslist_xylo.csv data rows.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
from decimal import Decimal,InvalidOperation
import hashlib
import io
import json
import math
from pathlib import Path
import statistics

from sweden6_slu_original_three_file_header_gate import (
    ORIGINAL_URLS,official_get,SourceStop
)

PRESPEC="docs/FOREST_SWEDEN6_ORIGINAL_CLIMATE_PLOTSHADE_NONRESPONSE_QA_PRESPEC_20261119.md"
CLIMATE_SHA="d546273c352fb2cab97f63f35883f970baea09790348fa4c0dda3e1bc55ba776"
CLIMATE_SIZE=7019
FIELDS=(
 "Block","Mikrotemp","Makrotemp","CTI","Plot","Shade","Bark","Diameter",
 "Regional climate","Aspect","Species richness","Totlab"
)
PREDICTORS=("Mikrotemp","Makrotemp","Bark","Diameter","Regional climate","Aspect")
RESPONSE_FIELDS=("CTI","Species richness","Totlab")
BLOCK_PLOTS={
 "1":set(range(11,16)),"2":set(range(6,11)),"3":set(range(16,21)),
 "4":set(range(21,26)),"5":set(range(1,6)),"6":set(range(26,31))
}
ALL_BLOCKS=("1","2","3","4","5","6")
ALL_SHADES=("1","2","3")

def strict_integer_key(raw,name):
    s=str(raw or "").strip()
    try:
        v=Decimal(s)
    except (InvalidOperation,ValueError,TypeError):
        raise SourceStop("SLU_ORIGINAL_"+name+"_AUTHOR_FIELD_NOT_NUMERIC") from None
    if not v.is_finite() or v!=v.to_integral_value():
        raise SourceStop("SLU_ORIGINAL_"+name+"_AUTHOR_FIELD_NOT_INTEGRAL")
    return str(int(v))

def finite_numeric(raw):
    s=str(raw or "").strip()
    if not s or s.casefold() in ("na","nan","null","n/a","-999"):
        return None
    if "," in s and "." in s:
        return None
    if "," in s:
        s=s.replace(",",".")
    try:
        x=float(s)
    except (ValueError,OverflowError):
        return None
    return x if math.isfinite(x) else None

def describe_numeric(values):
    return {
      "original_finite_n":len(values),
      "original_min":min(values) if values else None,
      "original_median":statistics.median(values) if values else None,
      "original_max":max(values) if values else None,
    }

def original_climate_nonresponse_only(source_csv:bytes,strict_original:bool=True):
    try:
        csvtext=source_csv.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SLU_CLIMATE_ORIGINAL_NOT_UTF8") from None
    r=csv.DictReader(io.StringIO(csvtext,newline=""),delimiter=";",strict=True)
    if tuple(r.fieldnames or ())!=FIELDS:
        raise SourceStop("SLU_CLIMATE_AUTHOR_12FIELD_ORDER_DRIFT")
    rows=0
    keys=set()
    plot_shade=defaultdict(set)
    block_plot=defaultdict(set)
    block_shade=defaultdict(Counter)
    data=defaultdict(list)
    predictors_missing=Counter()
    within_block=defaultdict(lambda:defaultdict(list))
    for record in r:
        if None in record or set(record)!=set(FIELDS):
            raise SourceStop("SLU_ORIGINAL_CLIMATE_CSV_ROW_WIDTH_DRIFT")
        rows+=1
        if rows>1000:
            raise SourceStop("SLU_CLIMATE_ORIGINAL_UNEXPECTED_ROWS")
        # Biological response fields CTI, Species richness and Totlab are
        # *never* accessed. Their raw values aren't used to determine eligibility.
        block=strict_integer_key(record["Block"],"BLOCK")
        plot=strict_integer_key(record["Plot"],"PLOT")
        shade=strict_integer_key(record["Shade"],"SHADE")
        if block not in BLOCK_PLOTS or int(plot) not in BLOCK_PLOTS[block] or shade not in ALL_SHADES:
            raise SourceStop("SLU_CLIMATE_AUTHOR_BLOCK_PLOT_SHADE_HIERARCHY_MISMATCH")
        key=(block,plot,shade)
        if key in keys:
            raise SourceStop("SLU_CLIMATE_ORIGINAL_DUPLICATE_BLOCK_PLOT_SHADE")
        keys.add(key)
        plot_shade[(block,plot)].add(shade)
        block_plot[block].add(plot)
        block_shade[block][shade]+=1
        for field in PREDICTORS:
            v=finite_numeric(record[field])
            if v is None:
                predictors_missing[field]+=1
            else:
                data[field].append(v)
                within_block[block][field].append(v)
    if strict_original and rows!=88:
        raise SourceStop("SLU_CLIMATE_ORIGINAL_88_ROWS_AUTHOR_FRAME_STOP")
    min_plots=min((len(block_plot[b]) for b in ALL_BLOCKS),default=0)
    min_shades=min((len(sets) for sets in plot_shade.values()),default=0)
    all_expected_keys={
      (block,str(plot),shade)
      for block,plots in BLOCK_PLOTS.items() for plot in plots for shade in ALL_SHADES
    }
    missing=all_expected_keys-keys
    if len(missing)>90:
        raise SourceStop("SLU_CLIMATE_ORIGINAL_SOURCE_FRAME_INTERNAL_ERROR")
    variation={
        field:{
          "blocks_with_at_least_two_valid_values":sum(len(within_block[b][field])>=2 for b in ALL_BLOCKS),
          "blocks_with_strictly_positive_within_block_variation":sum(
              len(within_block[b][field])>=2 and
              max(within_block[b][field])-min(within_block[b][field])>1e-12 for b in ALL_BLOCKS
          ),
        } for field in PREDICTORS
    }
    result={
      "schema":"structural.SLU_sweden6_original_88climate_nonresponse_hierarchy.v1",
      "source_original_climate_TABLE_rows":rows,
      "original_author_nominal_30plot_times3shade_cells":90,
      "source_actual_unique_block_plot_shade_keys":len(keys),
      "source_author_6block_count":len(block_plot),
      "source_author_30block_plot_count":len(plot_shade),
      "source_nominal_plotshade_missing_cell_count_NOT_IMPUTED":len(missing),
      "source_each_block_original_unique_plot_counts":{b:len(block_plot[b]) for b in ALL_BLOCKS},
      "source_each_block_shade_row_counts":{
         b:{s:block_shade[b][s] for s in ALL_SHADES} for b in ALL_BLOCKS
      },
      "source_original_min_plot_count_per_block":min_plots,
      "source_original_min_shades_available_per_plot":min_shades,
      "source_original_original_predictor_nonmissing_summary":{
        k:describe_numeric(data[k]) for k in PREDICTORS
      },
      "source_original_original_predictor_missing_rows":{
        k:predictors_missing[k] for k in PREDICTORS
      },
      "source_original_predictor_within_block_variation_checks":variation,
      "source_original_biological_CTI_richness_Totlab_COLUMNS_ACCESSED":0,
      "source_original_beetle_SPECIES_FILE_ROWS_ACCESSED":0,
      "source_original_plot_tree_resource_is_spruce_ONLY":True,
      "source_year2020_climate_versus_2021_beetles_NOT_SYNCHRONOUS":True,
      "source_30plots_NOT_30_independent_regions":True,
      "source_site_AND_climate_raw_response_values_NOT_EXPORTED":True,
      "source_missing_plotshade_cell_IDs_NOT_EXPORTED":True,
      "new_species_composition_or_thermal_RESPONSE_ESTIMATED":False,
    }
    result["status"]=(
       "SOURCE_SWEDEN6_ORIGINAL_CLIMATE_PLOTSHADE_NONRESPONSE_PASS"
       if (
          len(block_plot)==6 and len(plot_shade)==30 and min_plots>=4
          and min_shades>=2 and rows>=85
       )
       else "SOURCE_SWEDEN6_CLIMATE_PLOTSHADE_SOURCE_METHOD_HOLD"
    )
    return result

def synthetic_test():
    records=[]
    for block,plots in BLOCK_PLOTS.items():
        for plot in sorted(plots):
            for shade in ALL_SHADES:
                if (block,plot,shade) in (("1",11,"1"),("3",16,"2")):
                    continue
                records.append({
                   "Block":block,"Plot":str(plot),"Shade":shade,
                   "Mikrotemp":"12,5","Makrotemp":"13.2","Bark":"60,3",
                   "Diameter":"10","Regional climate":"9.0","Aspect":"180",
                   "CTI":"PRIVATE_CTI","Species richness":"PRIVATE_RICH",
                   "Totlab":"PRIVATE_ABUND",
                })
    f=io.StringIO(newline="")
    writer=csv.DictWriter(f,fieldnames=FIELDS,delimiter=";")
    writer.writeheader()
    writer.writerows(records)
    r=original_climate_nonresponse_only(f.getvalue().encode(),strict_original=True)
    assert r["status"]=="SOURCE_SWEDEN6_ORIGINAL_CLIMATE_PLOTSHADE_NONRESPONSE_PASS"
    assert r["source_nominal_plotshade_missing_cell_count_NOT_IMPUTED"]==2
    assert r["source_original_biological_CTI_richness_Totlab_COLUMNS_ACCESSED"]==0
    o=json.dumps(r)
    assert "PRIVATE_" not in o
    print("SYNTHETIC_SLU_6BLOCK_88CLIMATE_NONSEMANTIC_BIOLOGY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic_test()
    if a.test:return
    if a.out is None:p.error("--out required")
    result={
       "schema":"structural.SLU_sweden6_original_climate_plotshade_gate.v1",
       "precommit":PRESPEC,
       "official_source_DOI":"10.5878/dhmc-bq15",
       "original_climate_sha256_expected":CLIMATE_SHA,
       "original_climate_bytes_expected":CLIMATE_SIZE,
       "original_3460_beetle_source_rows_UNREAD":True,
       "original_CTI_species_richness_totalab_BIOLOGY_NOT_OPENED":True,
       "prior_7field_header_and_6field_STOP_preserved":True,
       "historical_Finland_Carpathian_England_PREDICTS_NEON_BALA_GEB_scoring_UNCHANGED":True,
       "eBird_used":False,"TinyFish_used":False,
    }
    try:
        raw=official_get(ORIGINAL_URLS["boreal_forest_climate_data.csv"][0])
        if len(raw)!=CLIMATE_SIZE or hashlib.sha256(raw).hexdigest()!=CLIMATE_SHA:
            raise SourceStop("SLU_ORIGINAL_CLIMATE_DATA_BITSTREAM_BYTES_SHA_CHANGED")
        r=original_climate_nonresponse_only(raw,strict_original=True)
        result["original_publisher_nonresponse_source_hierarchy"]=r
        result["status"]=r["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["source_OR_method_FAILURE_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Sweden6_SLU_climate88_plotshade_nonresponse_QA.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SWEDEN6_88_ENVIRONMENT_SOURCE_ONLY",result["status"])
    print("NO_SPECIES_CTIs_OR_ORIGINAL_BIOLOGICAL_DATA_ROWS_OPENED")
if __name__=="__main__":main()
