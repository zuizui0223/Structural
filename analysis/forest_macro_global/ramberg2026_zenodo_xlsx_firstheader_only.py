#!/usr/bin/env python3
"""Zenodo 23021809 exact 2026 beetle stump Excel first-row identity audit.

Frozen source-only: no species abundance/count values, stump rows, site codes,
individual or environmental measurements are inspected, scored or exported.
"""
import argparse, collections, hashlib, io, json, posixpath, re
import urllib.error, urllib.parse, urllib.request, xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

DOI="10.5281/zenodo.23021809"
RECORD="https://zenodo.org/api/records/23021809"
FILE="Beetles_data.xlsx"
SIZE=56235
MD5="42b6ba1d401cf77fc70efcfa91bf7adf"
SHA="352c28b0615a3186914e95fbac27a6159b95d4c28f4028d5f47671513f818344"
MAIN="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOCREL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKGREL="http://schemas.openxmlformats.org/package/2006/relationships"
FIELDS=re.compile(r"(?i)(^|[_\s-])(sample|site|stand|plot|pair|stump|tree|wood|forest|location|region|management|"
                  r"history|year|date|dbh|diameter|height|age|species|taxon|abundance|richness|"
                  r"trap|effort|status|treatment|volume|dead|landscape|cutover|sieving)([_\s-]|$)")
UA={"User-Agent":"Structural-Ramberg2026-source-firstheader/1.0","Accept":"application/json,*/*;q=0.1"}

def fetch(url,limit):
    with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=38) as r:
        a=r.read(limit+1)
        if len(a)>limit or r.status!=200:
            raise ValueError("ORIGINAL_PUBLISHER_FILE_RESPONSE_OR_CAP_STOP")
        return a

def original_file():
    meta=json.loads(fetch(RECORD,200000))
    if meta.get("id")!=23021809 or meta.get("doi")!=DOI:
        raise ValueError("SOURCE_ZENODO_RECORD_ID_STOP")
    fs=meta.get("files") or []
    if isinstance(fs,dict):fs=list((fs.get("entries") or {}).values())
    if len(fs)!=1 or not isinstance(fs[0],dict):
        raise ValueError("SOURCE_PUBLISHER_FILE_INDEX_STOP")
    f=fs[0]
    if f.get("key")!=FILE or f.get("size")!=SIZE or f.get("checksum")!="md5:"+MD5:
        raise ValueError("SOURCE_PUBLISHER_CHECKSUM_FILE_STOP")
    href=(f.get("links") or {}).get("self") or (f.get("links") or {}).get("download")
    p=urllib.parse.urlparse(href or "")
    if (p.scheme!="https" or p.hostname!="zenodo.org" or
        p.path!="/api/records/23021809/files/Beetles_data.xlsx/content"):
        raise ValueError("SOURCE_PUBLISHER_EXACT_FILE_URL_STOP")
    binary=fetch(href,100000)
    if (len(binary)!=SIZE or hashlib.md5(binary).hexdigest()!=MD5 or
        hashlib.sha256(binary).hexdigest()!=SHA):
        raise ValueError("SOURCE_PUBLISHER_FILE_SHA_STOP")
    return binary

def sheet_paths(z):
    names=z.namelist()
    if len(names)!=13 or len(set(names))!=len(names):
        raise ValueError("SOURCE_XLSX_OPENXML_MEMBER_COUNT_STOP")
    w=ET.fromstring(z.read("xl/workbook.xml"))
    rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    by_id={x.attrib.get("Id"):x.attrib.get("Target","")
           for x in rel if x.tag.endswith("Relationship")}
    out={}
    for s in w.iter("{"+MAIN+"}sheet"):
        name=s.attrib.get("name","")
        rid=s.attrib.get("{"+DOCREL+"}id")
        target=by_id.get(rid,"")
        if target.startswith("/xl/"):
            path=target.lstrip("/")
        else:
            path=posixpath.normpath(posixpath.join("xl",target))
        if not target or path not in names or not path.startswith("xl/worksheets/"):
            raise ValueError("SOURCE_ORIGINAL_WORKSHEET_PATH_STOP")
        out[name]=path
    if set(out)!={"Samples","Species"}:
        raise ValueError("SOURCE_SHEET_TITLES_STOP")
    return out

def firstrow(z,filename):
    # Streaming XML reads only first ROW, no subsequent original data rows.
    dim=None
    cells=[]
    row1=None
    with z.open(filename) as fh:
        for event,elem in ET.iterparse(fh,events=("end",)):
            local=elem.tag.rsplit("}",1)[-1]
            if local=="dimension":
                dim=elem.attrib.get("ref","")[:40]
                elem.clear()
            elif local=="row":
                row1=elem.attrib.get("r")
                if row1 not in ("1",None):
                    raise ValueError("SOURCE_HEADER_ROW1_ABSENT_STOP")
                for c in elem.iter("{"+MAIN+"}c"):
                    t=c.attrib.get("t","n")
                    text=""
                    x=c.find("{"+MAIN+"}v")
                    if t=="s" and x is not None and x.text and x.text.isdecimal():
                        text=int(x.text)
                    elif t=="inlineStr":
                        text="".join(x.text or "" for x in c.iter("{"+MAIN+"}t"))
                    # Numeric and formula cell values are NEVER read as numbers.
                    cells.append((c.attrib.get("r","")[:8],t,text))
                break
            elem.clear()
    if not cells or row1 is None:
        raise ValueError("SOURCE_FIRST_HEADER_ROW_EMPTY")
    return {"original_dimension_literal":dim, "first_row_cell_storage":cells}

def selected_sharedstrings(z,indices):
    if not indices:
        return {}
    if "xl/sharedStrings.xml" not in z.namelist():
        raise ValueError("SOURCE_SHAREDSTRINGS_MISSING_STOP")
    vals={}
    n=0
    with z.open("xl/sharedStrings.xml") as fh:
        for event,elem in ET.iterparse(fh,events=("end",)):
            if elem.tag=="{"+MAIN+"}si":
                if n in indices:
                    vals[n]="".join(t.text or "" for t in elem.iter("{"+MAIN+"}t"))[:180]
                n+=1
                elem.clear()
    if len(vals)!=len(indices):
        raise ValueError("SOURCE_HEADER_SHAREDSTRING_REFERENCE_STOP")
    return vals

def inspect(binary):
    out={}
    with zipfile.ZipFile(io.BytesIO(binary)) as z:
        paths=sheet_paths(z)
        raw={name:firstrow(z,path) for name,path in paths.items()}
        ints={val for rec in raw.values() for _,t,val in rec["first_row_cell_storage"] if t=="s" and isinstance(val,int)}
        strings=selected_sharedstrings(z,ints)
        for name,rec in raw.items():
            types=collections.Counter(t for _,t,_ in rec["first_row_cell_storage"])
            safe=[]
            for _,t,value in rec["first_row_cell_storage"]:
                label=strings[value] if t=="s" and isinstance(value,int) else (value if isinstance(value,str) else "")
                if label and FIELDS.search(label):
                    safe.append(label[:90])
            out[name]={
              "worksheet_source_dimension_metadata":rec["original_dimension_literal"],
              "first_header_row_cell_count":len(rec["first_row_cell_storage"]),
              "header_cell_storage_type_counts":dict(types),
              "generic_method_field_names_only":safe[:30],
              "all_field_strings_examined_beyond_first_header":False,
              "original_sample_ids_values_read":0,
              "beetle_taxon_abundance_cells_read":0}
    return out

def test():
    assert FIELDS.search("plot_ID") and FIELDS.search("Tree Species")
    assert not FIELDS.search("Ips typographus")
    assert not FIELDS.search("BOLD_AA123")
    assert len(MD5)==32 and len(SHA)==64
    print("ZENODO2026_FIRST_HEADER_SOURCEONLY_KNOWN_TRUTH_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="ramberg2026_firstheader_sourceonly/receipt.json")
    a=ap.parse_args()
    test()
    if a.test:return
    x={"schema":"structural.ramberg2026_zenodo_23021809_firstheader_sourceonly.v1",
       "original_doi":DOI,"original_sha256":SHA,"original_file_size":SIZE,
       "read_original_ecological_sample_rows":0,
       "read_beetle_species_response_cells":0,
       "new_ecological_effects":0,
       "prior_Ramberg2025_Frostgard2026_401_status_unchanged":True,
       "status":"SOURCE_FIRST_HEADER_HOLD"}
    try:
        x["original_sheet_first_headers_method_only"]=inspect(original_file())
        x["status"]="SOURCE_FIRST_HEADER_METADATA_READY_NO_BIOLOGY"
    except Exception as e:
        x["status"]="SOURCE_FIRST_HEADER_SCHEMA_OR_TRANSPORT_STOP"
        x["error_class"]=type(e).__name__
        x["error_message_code"]=str(e)[:100] if isinstance(e,ValueError) else ""
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("RAMBERG2026_FIRST_HEADER_STATUS",x["status"])
    print("NO_ORIGINAL_RESPONSE_OR_SAMPLES_READ",x["read_beetle_species_response_cells"]==0 and x["read_original_ecological_sample_rows"]==0)
if __name__=="__main__":main()
