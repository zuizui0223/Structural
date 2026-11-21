#!/usr/bin/env python3
"""Source author Trap_type categorical values ONLY, original response sealed."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import urllib.error
import zipfile

from england_nfi2026_canopy_subcanopy_source_gate import SOURCE_UUID, retrieve_original, SourceStop
from england_nfi2026_plot_trap_year_metadata_only import (
    ORIGINAL_BYTES, ORIGINAL_SHA256, AUTHOR_FIELDS, method_label
)
PRESPEC="docs/FOREST_NFI_ENGLAND_2026_TRAP_TYPE_AUTHOR_CODES_METADATA_ONLY_PRESPEC_20261119.md"
SAFE_CATEGORY=re.compile(r"^[A-Za-z0-9 _./()\-]{1,64}$")

def read_categories(source:Path, strict_original=True):
    with zipfile.ZipFile(source) as zipfile_source:
        members=[x for x in zipfile_source.infolist() if not x.is_dir()]
        if len(members)!=2 or any(not x.filename.lower().endswith(".csv") for x in members):
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_TWO_MEMBER_SHAPE_DRIFT")
        widths=[]
        selected=None
        for member in members:
            with zipfile_source.open(member) as fin:
                head=fin.readline(8*1024*1024+1)
            if len(head)>8*1024*1024 or not head.endswith((b"\n",b"\r\n")):
                raise SourceStop("SOURCE_NFI2026_ORIGINAL_FIRST_HEADER_INVALID")
            try:
                names=next(csv.reader([head.decode("utf-8-sig").rstrip("\r\n")],strict=True))
            except (ValueError,UnicodeError,csv.Error,StopIteration) as exc:
                raise SourceStop("SOURCE_NFI2026_HEADER_PARSE_STOP") from exc
            widths.append(len(names))
            if len(names)==24:
                if tuple(names)!=AUTHOR_FIELDS:
                    raise SourceStop("SOURCE_NFI2026_24_AUTHOR_FIELD_DRIFT")
                selected=member
        if sorted(widths)!=[24,328] or selected is None:
            raise SourceStop("SOURCE_NFI2026_ORIGINAL_TABLE_WIDTH_DRIFT")
        codes=Counter()
        method_counts=Counter()
        n=0
        with zipfile_source.open(selected) as bin_stream:
            with io.TextIOWrapper(bin_stream,encoding="utf-8-sig",newline="") as inp:
                reader=csv.DictReader(inp,strict=True)
                if tuple(reader.fieldnames or ())!=AUTHOR_FIELDS:
                    raise SourceStop("SOURCE_NFI2026_AUTHOR_FIELD_ORDER_DRIFT")
                for row in reader:
                    if None in row or set(row)!=set(AUTHOR_FIELDS):
                        raise SourceStop("SOURCE_NFI2026_SOURCE_ROW_GRAMMAR_DRIFT")
                    n+=1
                    # Only this original author field is inspected semantically.
                    c=str(row["Trap_type"] or "").strip()
                    codes[c]+=1
                    method_counts[method_label(c)]+=1
                    if n>100000:
                        raise SourceStop("SOURCE_NFI2026_UNEXPECTED_SOURCE_ROWS")
        if strict_original and (
            n!=331 or method_counts["Malaise"]!=165
            or method_counts["Other"]!=166 or method_counts["Lindgren"]!=0
            or method_counts["Missing"]!=0
        ):
            raise SourceStop("SOURCE_NFI2026_PREVIOUS_SOURCE_FROZEN_METHOD_LEDGER_DRIFT")
        raw_codes=list(codes)
        unsafe=(
            len([c for c in raw_codes if c])>12 or
            any(not SAFE_CATEGORY.fullmatch(c) for c in raw_codes if c)
        )
        result={
          "original_source_24column_metadata_rows_inspected_for_one_field_only":n,
          "original_Trap_type_distinct_nonblank_category_count":sum(bool(c) for c in codes),
          "original_Trap_type_empty_category_rows":codes[""],
          "previous_frozen_literal_Trap_type_classifier":{
            k:method_counts[k] for k in ("Lindgren","Malaise","Other","Missing")
          },
          "source_Trap_type_category_dictionary_SAFE_TO_PRINT":not unsafe,
          "source_328col_OTU_OR_species_response_rows_READ":0,
          "source_other_original_23_field_values_NOT_SEMANTICALLY_USED":True,
          "source_ID_coordinates_or_dates_original_values_NOT_OUTPUT":True,
          "source_category_code_not_method_or_layer_reinterpreted":True,
          "site_year_pair_count_RESCORED":False,
          "new_biological_response_scored":False,
        }
        if unsafe:
            result["status"]="SOURCE_NFI2026_TRAP_TYPE_CATEGORY_VALUE_UNSAFE_STOP"
        else:
            result["source_original_Trap_type_lexical_categories_counts"]={
                k:codes[k] for k in sorted(codes)
            }
            result["status"]="SOURCE_NFI2026_TRAP_TYPE_CATEGORICAL_DICTIONARY_ONLY_PASS"
        return result

def known_truth():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"mock.zip"
        vals=[]
        for code in ("Malaise","Canopy","Malaise"):
            row={key:"SECRET_OTHER_FIELD" for key in AUTHOR_FIELDS}
            row["Trap_type"]=code
            row["Plot_ID"]="PRIVATE_PLOT"
            row["SW_x_coordinates"]="12345PRIVATE"
            vals.append(row)
        s=io.StringIO(newline="")
        writer=csv.DictWriter(s,fieldnames=AUTHOR_FIELDS)
        writer.writeheader()
        writer.writerows(vals)
        with zipfile.ZipFile(p,"w") as z:
            z.writestr("DATA_with_anonymous_name.csv",s.getvalue())
            z.writestr("BIOLOGY_328col.csv",",".join("Taxon"+str(i) for i in range(328))+"\nSECRET_SPECIES_VALUES\n")
        result=read_categories(p,strict_original=False)
        assert result["status"]=="SOURCE_NFI2026_TRAP_TYPE_CATEGORICAL_DICTIONARY_ONLY_PASS"
        assert result["source_original_Trap_type_lexical_categories_counts"]=={"Canopy":1,"Malaise":2}
        assert "SECRET" not in json.dumps(result)
        assert "PRIVATE_PLOT" not in json.dumps(result)
        assert result["source_328col_OTU_OR_species_response_rows_READ"]==0
    print("SYNTHETIC_SOURCE_NFI_TRAP_ONLY_LABELS_AND_OTU_FIREWALL_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    report={
      "schema":"structural.england_NFI2026_author_Trap_type_dictionary_only.v1",
      "precommit":PRESPEC,
      "official_source_dataset_uuid":SOURCE_UUID,
      "original_2023_2026_zip_expected_bytes":ORIGINAL_BYTES,
      "original_2023_2026_zip_expected_SHA256":ORIGINAL_SHA256,
      "source_original_328col_OTU_species_rows_READ":0,
      "no_earlier_Finland_Carpathian_PREDICTS_Thai_NEON_BALA_GEB_scores_REOPENED":True,
      "no_original_site_or_sample_IDs_exposed":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"publisher_original.zip"
        try:
            size,sha,_=retrieve_original(path)
            if size!=ORIGINAL_BYTES or sha!=ORIGINAL_SHA256:
                raise SourceStop("SOURCE_NFI2026_ORIGINAL_SOURCE_SHA_SIZE_DRIFT")
            report["original_author_Trap_type_field_category_result"]=read_categories(path)
            report["status"]=report["original_author_Trap_type_field_category_result"]["status"]
        except (SourceStop,urllib.error.URLError,TimeoutError,OSError,
                UnicodeError,csv.Error,ValueError,zipfile.BadZipFile) as exc:
            report["status"]=(str(exc) if isinstance(exc,SourceStop) else
                "SOURCE_NFI2026_TRAP_FIELD_SOURCE_TRANSPORT_OR_PARSE_STOP")
            report["new_source_method_category_dictionary_NOT_VALIDATED"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"NFI2026_Trap_type_source_field_dictionary_only.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    print("NFI2026_TRAP_TYPE_LITERAL_AUTHOR_DICTIONARY_ONLY",report["status"])
    print("ALL_SPECIES_OR_OTU_BIOLOGICAL_ROWS_SEALED")
if __name__=="__main__":main()
