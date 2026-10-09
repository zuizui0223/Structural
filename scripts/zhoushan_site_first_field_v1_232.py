#!/usr/bin/env python3
"""Frozen first Word table header and first field ONLY, no species incidence values."""
import argparse,hashlib,io,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError
from importlib.util import spec_from_file_location,module_from_spec

ROOT=Path(__file__).resolve().parents[1]
s=spec_from_file_location("stable229",ROOT/"scripts/zhoushan_docx_table_shapes_v1_229.py")
m=module_from_spec(s);s.loader.exec_module(m)
SHA="ec1d1d0a5dbe3f0cee955dfe4018e678a48a796d5135b2311888d47aad9ecd64"
NS="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SOURCE=m.SOURCE
CAP=5000000
def first_site_metadata(docx):
    if hashlib.sha256(docx).hexdigest()!=SHA:raise ValueError("Inner Word source SHA changed")
    with zipfile.ZipFile(io.BytesIO(docx)) as z:
        f=z.getinfo("word/document.xml")
        if f.file_size!=3018319:raise ValueError("Frozen table-document XML size drift")
        xml=z.read("word/document.xml")
    root=ET.fromstring(xml)
    tables=list(root.iter(NS+"tbl"))
    if len(tables)!=9:raise ValueError("Original nine Word tables expected")
    rows=tables[0].findall(NS+"tr")
    if len(rows)!=40 or any(len(r.findall(NS+"tc"))!=12 for r in rows):
        raise ValueError("First field-table structural identity changed")
    def text_of(cell):
        # Deliberately inspect only the specifically frozen cell.
        val="".join(t.text or "" for t in cell.iter(NS+"t"))
        val=" ".join(val.split())
        if len(val)>160:raise ValueError("Field metadata cell unexpectedly long")
        return val
    headers=[text_of(c) for c in rows[0].findall(NS+"tc")]
    island_first_fields=[text_of(r.findall(NS+"tc")[0]) for r in rows[1:]]
    if len(island_first_fields)!=39 or not all(island_first_fields):
        raise ValueError("Expected 39 nonblank site names/indices")
    return {"table_index":0,"table_rows":40,"table_columns":12,
       "first_row_column_headers":headers,
       "site_first_field_values":island_first_fields,
       "selected_data_cells_text_read":39,
       "source_table_other_data_cells_text_read":0,
       "species_specific_incidence_cells_read":0,
       "not_verified_these_are_unique_island_names":True}
def execute():
    receipt={"schema":"structural.zhoushan_site_first_column_metadata_result.v1_232",
        "field_incidence_values_opened":False,"mammal_original_response_opened":False,
        "original_predictions_scored":False}
    try:
        with urlopen(Request(SOURCE,headers={"User-Agent":"Structural-source-identity-v1.232"}),timeout=90) as f:
            host=urlsplit(f.url).hostname
            if urlsplit(f.url).scheme!="https" or host not in m.HOSTS:
                raise ValueError("Untrusted source redirect")
            payload=f.read(CAP+1)
        docx=m.validate_outer(payload)
        receipt.update(status="PASS_39_SITE_METADATA_FIRST_FIELD_ONLY",**first_site_metadata(docx))
    except HTTPError as e:
        receipt.update(status="STOP_SITE_METADATA_HTTP",http_status=e.code)
    except Exception as e:
        receipt.update(status="STOP_SITE_METADATA_SOURCE_OR_SCHEMA",reason_class=type(e).__name__)
    return receipt
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();o=execute();a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
    print(json.dumps(o,sort_keys=True))
