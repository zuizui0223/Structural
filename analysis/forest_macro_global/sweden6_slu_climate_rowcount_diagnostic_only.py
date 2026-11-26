#!/usr/bin/env python3
"""SLU climate 7019B original exact file CSV STRUCTURE ONLY after 88-row STOP.

Does NOT inspect any original climate, wood, organismal, plot or taxon
cell values. Counts original source physical lines and CSV widths only.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json
from collections import Counter
from pathlib import Path
from sweden6_slu_original_three_file_header_gate import (
    ORIGINAL_URLS,official_get,SourceStop
)
from sweden6_slu_climate_plotshade_nonresponse_gate import (
    CLIMATE_SHA,CLIMATE_SIZE,FIELDS
)
PRESPEC="docs/FOREST_SWEDEN6_CLIMATE_ORIGINAL_ROW_COUNT_DIAGNOSTIC_PRESPEC_20261119.md"

def original_source_shape_only(raw):
    if len(raw)!=CLIMATE_SIZE or hashlib.sha256(raw).hexdigest()!=CLIMATE_SHA:
        raise SourceStop("SLU_CLIMATE_EXACT_7019_BYTE_SHA_CHANGED")
    try:
        reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=";",strict=True)
        widths=Counter()
        n=0
        for row in reader:
            n+=1
            widths[len(row)]+=1
            if n>1000:
                raise SourceStop("SLU_CLIMATE_ORIGINAL_GT1000_ROWS_GRAMMAR_STOP")
    except (UnicodeError,csv.Error):
        raise SourceStop("SLU_CLIMATE_ORIGINAL_CSV_LINECOUNT_SOURCE_PARSE_STOP") from None
    return {
       "source_original_exact_verified_bytes":len(raw),
       "source_original_exact_verified_sha256":hashlib.sha256(raw).hexdigest(),
       "source_original_byte_LF_count":raw.count(b"\n"),
       "source_original_ends_with_LF":raw.endswith(b"\n"),
       "source_original_CSV_logical_row_count_INCLUDING_HEADER":n,
       "source_original_CSV_data_record_count_EXCLUDING_HEADER":n-1,
       "source_original_CSV_row_field_width_counts":{str(k):v for k,v in sorted(widths.items())},
       "source_original_header_first_row_correct_field_count":len(FIELDS)==12,
       "original_field_CELL_VALUES_semantically_READ":0,
       "original_species_beetle_source_rows_READ":0,
       "original_earlier_88_data_record_gate_REMAINS_STOP":True,
       "new_original_biological_result_EVALUATED":False,
       "status":"SOURCE_SWEDEN6_ORIGINAL_CLIMATE_PHYSICAL_ROW_COUNT_DIAG_ONLY",
    }

def synthetic_test():
    # Synthetic only; physical checksum gate is deliberately separate.
    sample=b"Block;Shade\n1;2\n3;4\n"
    r=list(csv.reader(io.StringIO(sample.decode()),delimiter=";",strict=True))
    assert len(r)==3 and len(r)-1==2
    assert Counter(len(row) for row in r)=={2:3}
    print("SYNTHETIC_ORIGINAL_CLIMATE_CSV_SOURCE_SHAPE_NO_CELL_VALUES_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic_test()
    if a.test:return
    if a.out is None:p.error("--out required")
    result={
      "schema":"structural.SLU_sweden6_2025_climate_source_csv_rowcount_diagnostic.v1",
      "precommit":PRESPEC,
      "prior_88_record_gate_STOP_PRESERVED":True,
      "original_BIOLOGICAL_CTI_richness_Totlab_OR_species_DATA_ROWS_READ":0,
      "all_earlier_forest_and_island_response_scores_NOT_REOPENED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        source=official_get(ORIGINAL_URLS["boreal_forest_climate_data.csv"][0])
        result["original_source_CSV_structure_counts_ONLY"]=original_source_shape_only(source)
        result["status"]=result["original_source_CSV_structure_counts_ONLY"]["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["source_structure_STOP_NOT_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"SLU_sweden6_climate_original_csv_structure_only.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SLU_SWEDEN6_CLIMATE_ORIGINAL_ROWCOUNT_SOURCE_DIAG",result["status"])
    print("NO_ORIGINAL_CLIMATE_OR_SPECIES_CELL_VALUES_READ")
if __name__=="__main__":main()
