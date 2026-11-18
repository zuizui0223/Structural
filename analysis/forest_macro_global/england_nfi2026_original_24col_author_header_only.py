#!/usr/bin/env python3
"""After the first frozen publisher ZIP proof: inspect only 24 schema field names.

No source physical sample rows, coordinates, delocation IDs, OTU data or
ecological values can be opened. This resolves ambiguity of NFI source keys.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from england_nfi2026_canopy_subcanopy_source_gate import (
    SOURCE_UUID, MAX_FIRST_HEADER, retrieve_original, SourceStop
)

EXPECTED_BYTES=486883
EXPECTED_SHA256="ce3a21377238cc87bde7683917f59a771d20f8e24e81ddf47915362b92281ff4"
EXPECTED_COLS=(24,328)
PRESPEC="docs/FOREST_NFI_ENGLAND_2026_24COL_AUTHOR_FIELD_HEADERS_PRESPEC_20261118.md"

def first_header(zf,info):
    with zf.open(info) as f:
        raw=f.readline(MAX_FIRST_HEADER+1)
    if len(raw)>MAX_FIRST_HEADER or b"\n" not in raw:
        raise SourceStop("SOURCE_NFI_2026_ORIGINAL_FIRST_HEADER_INVALID")
    try:
        header=raw.decode("utf-8-sig").strip("\r\n")
        return next(csv.reader([header],delimiter=",",strict=True))
    except (UnicodeError,csv.Error,StopIteration) as exc:
        raise SourceStop("SOURCE_NFI_2026_ORIGINAL_CSV_HEADER_PARSE_STOP") from exc

def inspect(p):
    with zipfile.ZipFile(p) as zf:
        infos=[x for x in zf.infolist() if not x.is_dir()]
        if len(infos)!=2 or any(not x.filename.lower().endswith(".csv") for x in infos):
            raise SourceStop("SOURCE_NFI_2026_ORIGINAL_TWO_CSV_FRAME_DRIFT")
        headers=[first_header(zf,x) for x in infos]
        if sorted(map(len,headers))!=list(EXPECTED_COLS):
            raise SourceStop("SOURCE_NFI_2026_ORIGINAL_24_328_FIELD_FRAME_DRIFT")
        fields=next(h for h in headers if len(h)==24)
        if len(set(fields))!=24 or any(not x.strip() for x in fields):
            raise SourceStop("SOURCE_NFI_2026_DUPLICATED_OR_BLANK_AUTHOR_FIELDS")
        if any(len(x)>128 or "\n" in x or "\r" in x for x in fields):
            raise SourceStop("SOURCE_NFI_2026_UNSAFE_SOURCE_HEADER_LITERAL")
        if not any("deloc" in x.casefold() for x in fields):
            raise SourceStop("SOURCE_NFI_2026_SOURCE_AUTHOR_DELOCATION_SCHEMA_NOT_FOUND")
        return {
            "original_source_metadata_24_AUTHOR_COLUMN_NAMES":fields,
            "original_source_metadata_columns":len(fields),
            "other_source_otu_wide_header_COLUMNS_ONLY":328,
            "source_original_sample_ID_values_READ":0,
            "source_original_plot_or_delocation_ID_values_READ":0,
            "source_original_otu_rows_READ":0,
            "source_original_data_rows_READ":0,
            "source_filename_and_species_column_names_NOT_EXPORTED":True,
        }

def test():
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/"fake.zip"
        a=["field"+str(i) for i in range(24)]
        a[3]="delocation_id"
        with zipfile.ZipFile(f,"w") as z:
            z.writestr("sample.csv",",".join(a)+"\nsecret,hidden,site,code\n")
            z.writestr("otu.csv",",".join("taxon"+str(i) for i in range(328))+"\n1,2,3\n")
        r=inspect(f)
        assert r["original_source_metadata_24_AUTHOR_COLUMN_NAMES"][3]=="delocation_id"
        assert r["source_original_data_rows_READ"]==0
        assert "secret" not in json.dumps(r)
        assert "hidden" not in json.dumps(r)
    print("SYNTHETIC_NFI2026_AUTHOR_24COL_FIRST_ROW_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    test()
    if a.test:return
    if a.out is None:p.error("--out required")
    result={
      "schema":"structural.england_NFI2026_original_author_24field_schema_only.v1",
      "source_official_dataset_uuid":SOURCE_UUID,
      "precommit":PRESPEC,
      "pin_original_archive_bytes":EXPECTED_BYTES,
      "pin_original_archive_sha256":EXPECTED_SHA256,
      "source_original_biological_OR_sample_rows_READ":0,
      "source_method_Lindgren_canopy_Malaise_subcanopy_CONFOUNDED":True,
      "source_delocation_is_NOT_original_physical_plot":True,
      "new_ecological_effect_estimated":False,
      "previous_biological_scores_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    with tempfile.TemporaryDirectory() as d:
        file=Path(d)/"publisher_zip"
        try:
            n,sha,_=retrieve_original(file)
            if n!=EXPECTED_BYTES or sha!=EXPECTED_SHA256:
                raise SourceStop("SOURCE_NFI_2026_ORIGINAL_ARCHIVE_SHA256_DRIFT")
            result.update(inspect(file))
            result["status"]="SOURCE_NFI_ENGLAND_2026_AUTHOR_24COL_HEADER_ONLY_PASS"
        except (SourceStop,OSError,TimeoutError) as exc:
            result["status"]=str(exc) if isinstance(exc,SourceStop) else "SOURCE_NFI_ENGLAND_2026_24COL_HEADER_STOP_TRANSPORT"
            result["no_original_sample_body_or_biology_access_allowed"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"NFI2026_author24_original_header_only.json").write_text(
       json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    print("NFI2026_ORIGINAL_AUTHOR_24COL_HEADER_ONLY",result["status"])
    print("NO_SAMPLE_ROWS_OR_SPECIES_RESPONSES_READ")
if __name__=="__main__":main()
