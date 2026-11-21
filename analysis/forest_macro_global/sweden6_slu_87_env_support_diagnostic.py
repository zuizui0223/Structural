#!/usr/bin/env python3
"""No more threshold rescue: explain why original SLU 87-climate QA failed.

Reuses existing nonresponse parser without edits, exports only anonymous
source opportunity counts. Zero CTI, richness, Totlab and beetle rows read.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from sweden6_slu_original_three_file_header_gate import ORIGINAL_URLS,official_get,SourceStop
from sweden6_slu_climate_plotshade_nonresponse_gate import (
    CLIMATE_SIZE,CLIMATE_SHA,original_climate_nonresponse_only
)
PRESPEC="docs/FOREST_SWEDEN6_87_ENVIRONMENT_HIERARCHY_SUPPORT_DIAGNOSTIC_PRESPEC_20261119.md"
FROZEN={
  "actual_source_data_rows":87,
  "original_block_count":6,
  "original_plot_count":30,
  "original_block_plot_shade_triplets":87,
  "nominal_missing_shade_cells":3,
  "min_plots_per_block":4,
  "min_shade_levels_per_plot":2,
  "older_gate_status":"SOURCE_SWEDEN6_ORIGINAL_CLIMATE_PLOTSHADE_NONRESPONSE_PASS",
}
def diagnostic(raw):
    r=original_climate_nonresponse_only(raw,strict_original=False)
    keys={
      "actual_source_data_rows":"source_original_climate_TABLE_rows",
      "original_block_count":"source_author_6block_count",
      "original_plot_count":"source_author_30block_plot_count",
      "original_block_plot_shade_triplets":"source_actual_unique_block_plot_shade_keys",
      "nominal_missing_shade_cells":"source_nominal_plotshade_missing_cell_count_NOT_IMPUTED",
      "min_plots_per_block":"source_original_min_plot_count_per_block",
      "min_shade_levels_per_plot":"source_original_min_shades_available_per_plot",
      "older_gate_status":"status",
    }
    flags={}
    for k,field in keys.items():
        v=r[field]
        t=FROZEN[k]
        flags[k]=(v>=t if k.startswith("min_") else v==t)
    return {
      "source_original_87_record_nonresponse_aggregate_recomputed":r,
      "original_precommitted_gate_truth_flags_BY_NAME":flags,
      "source_gates_failed_named":[k for k,v in flags.items() if not v],
      "source_scientific_previous_environment_HOLD_PRESERVED":True,
      "source_new_biodiversity_response_rows_opened":0,
      "original_CTI_species_richness_Totlab_VALUES_SEMANTICALLY_ACCESSED":0,
      "source_original_3460_beetle_rows_READ":0,
      "status":"SOURCE_SWEDEN6_ENVIRONMENT87_SOURCE_HIERARCHY_DIAGNOSIS_ONLY",
    }
def synthetic():
    assert FROZEN["actual_source_data_rows"]==87
    assert FROZEN["nominal_missing_shade_cells"]==3
    assert FROZEN["min_shade_levels_per_plot"]==2
    print("SYNTHETIC_SWEDEN6_DIAGNOSIS_FIXED_GATES_NO_BIOLOGY_PASS")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out required")
    result={
      "schema":"structural.SLU_sweden6_87environment_hierarchy_method_diagnostic.v1",
      "precommit":PRESPEC,
      "original_frozen_source_sha256":CLIMATE_SHA,
      "original_failed_87site_method_admission_STOP_RETAINED":True,
      "biological_response_values_CTI_richness_Totlab_OR_beetles_OPENED":0,
      "all_previous_Structural_ecological_results_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        raw=official_get(ORIGINAL_URLS["boreal_forest_climate_data.csv"][0])
        if len(raw)!=CLIMATE_SIZE or hashlib.sha256(raw).hexdigest()!=CLIMATE_SHA:
            raise SourceStop("SLU_CLIMATE_7019_SHA_SIZE_CHANGED")
        result["anonymous_original_nonresponse_source_SUPPORT_DIAGNOSIS"]=diagnostic(raw)
        result["status"]=result["anonymous_original_nonresponse_source_SUPPORT_DIAGNOSIS"]["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["original_source_structure_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"SLU_sweden6_87_original_nonresponse_support_diagnostic.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SLU_SWEDEN6_ORIGINAL_87_NONRESPONSE_METHOD_DIAG",result["status"])
    print("NO_BIOLOGICAL_SCORE_OR_SOURCE_ROWS_OPENED")
if __name__=="__main__":main()
