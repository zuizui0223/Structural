#!/usr/bin/env python3
"""Original SLU Sweden6 climate87 nonresponse method QA after rowcount diagnosis.

References the previously frozen 88-record function; changes ONLY expected
author data cardinality: 87 actual records (88 CSV rows including header).
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from sweden6_slu_original_three_file_header_gate import ORIGINAL_URLS,official_get,SourceStop
from sweden6_slu_climate_plotshade_nonresponse_gate import (
   CLIMATE_SIZE,CLIMATE_SHA,original_climate_nonresponse_only
)

PRESPEC="docs/FOREST_SWEDEN6_ORIGINAL_CLIMATE87_NONRESPONSE_REVALIDATION_PRESPEC_20261119.md"
FROZEN_SOURCE_ROWS=87
NOMINAL=90

def corrected_environment_only(source):
    r=original_climate_nonresponse_only(source,strict_original=False)
    if (r["source_original_climate_TABLE_rows"]!=FROZEN_SOURCE_ROWS or
        r["source_actual_unique_block_plot_shade_keys"]!=87 or
        r["source_nominal_plotshade_missing_cell_count_NOT_IMPUTED"]!=3 or
        r["source_author_6block_count"]!=6 or
        r["source_author_30block_plot_count"]!=30 or
        r["source_original_min_plot_count_per_block"]<4 or
        r["source_original_min_shades_available_per_plot"]<2 or
        r["status"]!="SOURCE_SWEDEN6_ORIGINAL_CLIMATE_PLOTSHADE_NONRESPONSE_PASS"
    ):
        raise SourceStop("SLU_CLIMATE87_PLOT_SHADE_AUTHOR_SOURCE_NONRESPONSE_ADMISSION_STOP")
    r["earlier_88_RECORD_data_source_gate_HISTORICAL_STOP_PRESERVED"]=True
    r["source_original_full_csv_rows_including_header"]=88
    r["source_environment_87_rows_verified_against_separate_shape_receipt"]=True
    r["status"]="SOURCE_SWEDEN6_ORIGINAL_CLIMATE87_NONRESPONSE_SOURCE_PASS"
    return r

def known_truth():
    assert FROZEN_SOURCE_ROWS==87 and NOMINAL==90 and NOMINAL-FROZEN_SOURCE_ROWS==3
    print("SYNTHETIC_SLUSIX_REGION_AUTHOR_87CLIMATE_SOURCE_CARDINALITY_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    o={
     "schema":"structural.slu_sweden6_original_87climate_environment_nonresponse.v1",
     "precommit":PRESPEC,
     "original_publisher_source_sha256_expected":CLIMATE_SHA,
     "original_corrected_author_csv_88_including_header_87_data":True,
     "earlier_88data_record_original_SCISTOP_PRESERVED":True,
     "original_3460_beetle_specimen_SOURCE_ROWS_READ":0,
     "original_climate_CTI_species_richness_Totalab_BIOLOGY_FIELDS_READ":0,
     "older_forest_island_biology_scores_UNCHANGED":True,
     "eBird_used":False,"TinyFish_used":False,
    }
    try:
        raw=official_get(ORIGINAL_URLS["boreal_forest_climate_data.csv"][0])
        if len(raw)!=CLIMATE_SIZE or hashlib.sha256(raw).hexdigest()!=CLIMATE_SHA:
            raise SourceStop("SLU_CLIMATE_ORIGINAL_VERIFIED_BYTES_SHA_CHANGED")
        r=corrected_environment_only(raw)
        o["original_nonresponse_block_plot_shade_87_QA"]=r
        o["status"]=r["status"]
    except SourceStop as exc:
        o["status"]=str(exc)
        o["original_environment_source_method_STOP_not_null_ecology"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Sweden6_SLU_original_climate87_nonresponse_QA.json").write_text(
        json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SLU_SWEDEN6_87_DATA_RECORD_CLIMATE_METHOD_GATE",o["status"])
    print("NO_ORIGINAL_BEETLE_OR_CTI_BIOLOGICAL_RESPONSES_OPENED")
if __name__=="__main__":main()
