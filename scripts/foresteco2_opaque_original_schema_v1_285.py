#!/usr/bin/env python3
"""ForestEco2 v1.285 source ZIP central-directory/meta.xml-only entrance gate.

Reuses the original BioMonI *reader* purely as an XML parser and overwrites
its context with ForestEco2's independently frozen identity. Opens zero
biological Event/Occurrence rows, labels or sampling units.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

from biomoni_three_island_opaque_schema_intake_v1_283 import schema_inventory_from_archive

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=plants-azo-foresteco2&v=1.2"
UUID="158e0f0d-26e3-4883-bf5e-6040c1bb1ff4"
MAX_ZIP_BYTES=5_000_000


def check_foresteco_schema(data):
    # The underlying schema reader never opens Event or Occurrence data files.
    result = schema_inventory_from_archive(data)
    result["schema"]="structural.foresteco2_response_opaque_schema_result.v1_285"
    result["source_dataset_uuid"]=UUID
    result["source_archive_url"]=SOURCE
    result["published_event_rows_claimed_not_verified"]=90
    result["published_occurrence_rows_claimed_not_verified"]=1150
    result["publisher_method_paragraph_also_says_105_events"]=True
    result["published_forest_types_expected"]=["NF","EW","PF"]
    result["islands_expected"]=["Pico","São Miguel","Terceira"]
    result["fresh_confirmatory_status"]="not_admitted"
    result["biological_outcome_opened"]=False
    event = set(result.get("Event_meta_only",{}).get("declared_field_terms",[]))
    occ = set(result.get("Occurrence_meta_only",{}).get("declared_field_terms",[]))
    # Forest type class might be under plot 'habitat', 'samplingProtocol',
    # or 'locationRemarks'. Declaring alternatives here BEFORE any data value.
    priority = ("habitat","samplingProtocol","locationRemarks")
    chosen = next((x for x in priority if x in event),None)
    result["frozen_first_available_forest_type_column"]=chosen
    result["still_unknown"]=[
        "Actual 90 vs contradictory 105 Event source row count",
        "Whether forest-type codes occur in the selected field",
        "Original plot IDs and 10×3×3 full balanced island/forest frame",
        "Native and nonnative establishmentMeans exact vocabulary",
        "At least two of fixed S1 local-loss taxa across at least two islands",
        "Any conditional focal-composition advantage"
    ]
    required_occ={"taxonRank"}
    if (result["status"]=="METADATA_SCHEMA_POSSIBLE_RESPONSE_SEALED_HOLD" and
        chosen is not None and required_occ.issubset(occ)):
        result["status"]="SCHEMA_QUALIFIED_BIOLOGICAL_RESPONSE_STILL_SEALED"
    else:
        result["status"]="STOP_OR_HOLD_INCOMPLETE_FOREST_OR_TAXON_SCHEMA"
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.foresteco2_island_forest_type_independent_response_gate.v1_285"
        or c.get("status")!="PRE_RESPONSE_FREEZE_INDEPENDENT_SOURCE_AND_FOCAL_TEST"
        or c["source"]["official_archive"]!=SOURCE
        or c["source"]["GBIF_uuid"]!=UUID):
        raise ValueError("ForestEco2 source and scientific question not frozen")
    result={
        "schema":"structural.foresteco2_response_opaque_schema_result.v1_285",
        "status":"TRANSPORT_STOP_NO_BIOLOGICAL_READ",
        "source_archive_url":SOURCE,
        "source_dataset_uuid":UUID,
        "Event_rows_opened":0,
        "Occurrence_rows_opened":0,
        "data_files_opened":0,
        "biological_outcome_opened":False,
        "new_confirmatory_systems":0,
        "GEB_scientific_HOLD":True,
        "eBird_used":False,
    }
    try:
        request=urllib.request.Request(SOURCE,headers={
            "User-Agent":"Structural-ForestEco2-schema-response-opaque-v1.285/1.0"})
        with urllib.request.urlopen(request,timeout=60) as response:
            raw=response.read(MAX_ZIP_BYTES+1)
        result=check_foresteco_schema(raw)
    except Exception as e:
        result["stop_type"]=type(e).__name__
        result["stop_reason"]=str(e)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "archive_sha256":result.get("archive_sha256"),
        "event_fields":result.get("Event_meta_only",{}).get("declared_field_terms"),
        "occ_fields":result.get("Occurrence_meta_only",{}).get("declared_field_terms"),
        "forest_field":result.get("frozen_first_available_forest_type_column"),
        "data_files_opened":0,"biology_scored":False,
        "stop_reason":result.get("stop_reason")},sort_keys=True))


if __name__=="__main__": main()
