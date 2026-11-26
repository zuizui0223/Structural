#!/usr/bin/env python3
"""Diagnose original SLU climate CSV FIRST HEADER layout; zero climate values.

Technical source-format diagnosis, not a new biological test or correction of
prior STOP. Original body remains opaque and is never decoded.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

from sweden6_slu_original_three_file_header_gate import (
    ORIGINAL_URLS, official_get, first_header_only, SourceStop
)
PRESPEC="docs/FOREST_SWEDEN6_CLIMATE_ORIGINAL_HEADER_LAYOUT_DIAGNOSTIC_PRESPEC_20261119.md"
CLIMATE="boreal_forest_climate_data.csv"
NAME_FIELDS=("Block","Plot","Shade")
NEEDLE_PATTERNS={
  "temperature":r"(?i)(micro|mikro|macro|makro|temp|thermal|climate)",
  "resource":r"(?i)(bark|diamet|wood|log|dbh)",
  "community_RESPONSE_HEADER_ONLY":r"(?i)(CTI|richness|abund|species|number)",
  "physical_key_candidate":r"(?i)^(block|plot|shade)$",
}
def inspect(blob):
    out=first_header_only(blob,12)
    fields=out["original_HEADER_exact_author_field_names"]
    positions={key:[i+1 for i,s in enumerate(fields) if s==key] for key in NAME_FIELDS}
    count={name:sum(bool(re.search(expr,s)) for s in fields)
           for name,expr in NEEDLE_PATTERNS.items()}
    safe=(len(fields)==12 and len(set(fields))==12 and
          all(0<len(s)<=128 and not re.search(r"[\n\r\x00-\x1f]",s) for s in fields))
    if not safe:
        raise SourceStop("SLU_CLIMATE_12_HEADER_UNSAFE_FIELD_LABELS")
    return {
       "original_publisher_climate_file_bytes":len(blob),
       "original_publisher_climate_file_sha256":hashlib.sha256(blob).hexdigest(),
       "original_publisher_first_header_line_bytes":len(blob.split(b"\n",1)[0].rstrip(b"\r")),
       "original_publisher_first_header_line_sha256":hashlib.sha256(blob.split(b"\n",1)[0].rstrip(b"\r")).hexdigest(),
       "original_source_12_field_names_in_exact_ORDER":fields,
       "original_source_identifier_exact_name_positions_1based":positions,
       "original_header_field_name_family_counts_only":count,
       "original_author_block_plot_shade_exact_field_names_unique":all(len(x)==1 for x in positions.values()),
       "previous_assumed_first3_block_plot_shade_STOP_PRESERVED":True,
       "source_original_csv_DATA_ROWS_READ":0,
       "source_original_CTIRichnessAbundance_temperature_values_READ":0,
       "source_original_plotIDs_or_taxa_NOT_OUTPUT":True,
       "status":("SOURCE_SWEDEN6_CLIMATE_ORIGINAL_12_FIELD_HEADER_DIAGNOSIS_ONLY"
                 if all(len(x)==1 for x in positions.values()) else
                 "SOURCE_SWEDEN6_CLIMATE_HEADER_ID_NAME_AMBIGUITY_STOP"),
    }
def synthetic():
    b=("Study;Plot;Block;Shade;Mikrotemp;Makrotemp;Bark;Diameter;CTI;Richness;Abundance;Region\n"+
       "PRIVATE_SAMPLE;11;9;shade;14;15;16;17;18;19;20;21\n").encode()
    # Deliberately do NOT hardcode Block, Plot, Shade as the first three names.
    r=inspect(b)
    assert r["original_source_identifier_exact_name_positions_1based"]=={
        "Block":[3],"Plot":[2],"Shade":[4]}
    assert r["source_original_csv_DATA_ROWS_READ"]==0
    assert "PRIVATE_SAMPLE" not in json.dumps(r)
    print("SYNTHETIC_SWEDEN6_CLIMATE_SOURCE_HEADER_ONLY_POSITION_DIAG_PASS")
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--test",action="store_true")
    a.add_argument("--out",type=Path)
    arg=a.parse_args()
    synthetic()
    if arg.test:return
    if arg.out is None:a.error("--out required")
    result={
      "schema":"structural.SLU_sweden6_2025original_climate12_header_layout_DIAG_v1",
      "precommit":PRESPEC,
      "source_author_original_slu_DOI":"10.5878/dhmc-bq15",
      "prior_6_field_species_STOPhistory_UNCHANGED":True,
      "prior_corrected7_climate_first3_STOPhistory_UNCHANGED":True,
      "original_source_BEETLE_or_CLIMATE_data_rows_READ":0,
      "previous_England_Carpathian_Finland_PREDICTS_Thai_NEON_BALA_GEB_outcomes_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        raw=official_get(ORIGINAL_URLS[CLIMATE][0])
        result["source_original_climate_header_diagnostic_only"]=inspect(raw)
        result["status"]=result["source_original_climate_header_diagnostic_only"]["status"]
    except SourceStop as e:
        result["status"]=str(e)
        result["source_schema_or_access_STOP_not_ecological_null"]=True
    arg.out.mkdir(parents=True,exist_ok=True)
    (arg.out/"SLU_sweden6_climate12_first_header_source_diagnostic.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SLU_SWEDEN6_ORIGINAL_CLIMATE_HEADER_ONLY",result["status"])
    print("NO_ORIGINAL_CLIMATE_BEETLE_SPECIES_OR_ABUNDANCE_ROWS_OPENED")
if __name__=="__main__":main()
