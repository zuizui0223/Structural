#!/usr/bin/env python3
"""Balducci 2026 Nature Communications publisher public Source Data ZIP:
catalogue/first-row-only, no biological response or private BOTTOMS-UP data.

Article doi 10.1038/s41467-026-68668-x, source attachment link extracted
unchanged from publisher article 'Source Data' (MOESM4). Figure-source file
provenance does NOT establish plot x species community matrix availability.
"""
import argparse
import hashlib
import io
import json
import posixpath
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

PUBLIC_ARTICLE="https://www.nature.com/articles/s41467-026-68668-x"
PUBLISHER_SOURCE_DATA_URL=(
    "https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1038%2Fs41467-026-68668-x/MediaObjects/"
    "41467_2026_68668_MOESM4_ESM.zip"
)
MAX_COMPRESSED=3_000_000
MAX_UNCOMPRESSED=40_000_000
MAX_ENTRIES=80
TYPES={".csv",".tsv",".txt",".json",".xlsx",".xls",".rds",".rdata",".pdf",".png",".jpg",".svg"}
MAIN="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
DOCREL="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKGREL="{http://schemas.openxmlformats.org/package/2006/relationships}"
GENERIC=re.compile(
   r"(?i)(study|forest|site|plot|point|sample|trap|year|month|date|effort|"
   r"taxon|species|beetle|guild|richness|diversity|carbon|living|"
   r"deadwood|dead_wood|lying|standing|diameter|diam|decay|tree|"
   r"wood|habitat|siteid|foresttype|country|region|area|volume|"
   r"size|forest_management|stand|abundance|incidence|scaled|"
   r"method|protocol)"
)
def one_request():
    url=urllib.parse.urlparse(PUBLISHER_SOURCE_DATA_URL)
    if url.scheme!="https" or url.netloc!="media.springernature.com":
        raise ValueError("SOURCE_PUBLISHER_LINK_ORIGIN_NOT_EXACT")
    req=urllib.request.Request(PUBLISHER_SOURCE_DATA_URL,
        headers={"User-Agent":"Structural-sourceonly-springernature-MOESM4/1.0",
                 "Accept":"application/zip,application/octet-stream,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=48) as response:
            final=urllib.parse.urlparse(response.url)
            if final.scheme!="https" or not (
                final.hostname=="media.springernature.com" or
                final.hostname=="static-content.springer.com" or
                final.hostname.endswith(".springernature.com")):
                raise ValueError("SOURCE_FINAL_REDIRECT_NOT_OFFICIAL_PUBLISHER")
            if response.status!=200:
                raise ValueError("SOURCE_OFFICIAL_HTTP_STATUS_NOT_200")
            data=response.read(MAX_COMPRESSED+1)
            if len(data)>MAX_COMPRESSED:
                raise ValueError("SOURCE_OFFICIAL_ATTACHED_ZIP_OVER_3MB")
        return data
    except urllib.error.HTTPError as exc:
        raise ValueError("SOURCE_PUBLISHER_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise ValueError("SOURCE_PUBLISHER_TRANSPORT_"+type(exc).__name__) from exc

def xlsx_titles(raw):
    """Only OpenXML workbook sheet metadata; never worksheet cell values."""
    f=io.BytesIO(raw)
    if not zipfile.is_zipfile(f):return {"status":"SOURCE_XLSX_CONTAINER_NOT_ZIP"}
    with zipfile.ZipFile(f) as z:
        if "xl/workbook.xml" not in z.namelist():
            return {"status":"SOURCE_NO_XLSX_WORKBOOK_XML"}
        xml=z.read("xl/workbook.xml")
    w=ET.fromstring(xml)
    names=[x.attrib.get("name","")[:80]
           for x in w.iter(MAIN+"sheet")]
    return {"status":"SOURCE_XLSX_SHEET_TITLES_ONLY",
            "n_sheets":len(names),
            "sheet_titles":[s if re.fullmatch(r"[A-Za-z0-9 ._()+\-]{1,80}",s)
                            else "masked_nonstandard_sheet_title" for s in names],
            "original_worksheet_cells_read":0}

def inspect(raw):
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError("SOURCE_PUBLISHER_ATTACHMENT_NOT_ZIP")
    result={"source_original_bytes":len(raw),
            "source_original_sha256":hashlib.sha256(raw).hexdigest(),
            "source_article_url":PUBLIC_ARTICLE,
            "source_publisher_attachment_url":PUBLISHER_SOURCE_DATA_URL,
            "source_author_underlying_plot_species_data_request_only":True,
            "source_field_plot_taxon_species_abundance_values_read":0,
            "source_article_figure_data_values_read":0,
            "original_biological_effects_estimated":0}
    items=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist()
        if len(entries)>MAX_ENTRIES or sum(q.file_size for q in entries)>MAX_UNCOMPRESSED:
            raise ValueError("SOURCE_ARCHIVE_UNCOMPRESSED_SIZE_OR_COUNT_STOP")
        for entry in entries:
            name=entry.filename
            if (name.startswith("/") or "\\" in name or ".." in name.split("/")
                or not name.strip()):
                raise ValueError("SOURCE_ARCHIVE_UNSAFE_PATH")
            if entry.is_dir():continue
            ext=Path(name).suffix.lower()
            item={"source_member_path":name[:180],
                  "source_member_extension":ext,
                  "source_uncompressed_bytes":entry.file_size,
                  "source_compressed_bytes":entry.compress_size}
            if ext==".xlsx":
                item["nonresponse_workbook_sheet_titles"]=xlsx_titles(z.read(entry))
            elif ext in {".csv",".tsv",".txt"}:
                # First line, metadata ONLY. Publication figure numerical values
                # and all subsequent rows are never inspected.
                with z.open(entry) as fh:
                    line=fh.readline(10001)
                if len(line)>10000:
                    item["status"]="SOURCE_TEXT_HEADER_OVER_LIMIT"
                else:
                    txt=line.decode("utf-8-sig",errors="replace").rstrip("\r\n")
                    delim=max((",", ";","\t"), key=lambda x:txt.count(x))
                    h=[x.strip("\" '") for x in txt.split(delim)]
                    item["source_first_row_field_count"]=len(h)
                    item["bounded_generic_first_row_FIELD_NAMES_only"]=sorted(set(
                        a[:80] for a in h if GENERIC.search(a) and
                        re.fullmatch(r"[A-Za-z0-9_ .()+\-]{1,80}",a)
                    ))[:50]
                    item["source_subsequent_rows_read"]=0
            items.append(item)
    result["source_original_files"]=items
    result["source_file_count"]=len(items)
    result["original_file_types"]=dict(Counter(x["source_member_extension"] for x in items))
    result["status"]="SOURCE_OFFICIAL_PUBLISHER_FIGURE_ATTACHMENT_CONTENTS_CATALOGUED"
    return result

def test():
    assert PUBLISHER_SOURCE_DATA_URL.endswith("MOESM4_ESM.zip")
    tmp=io.BytesIO()
    with zipfile.ZipFile(tmp,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("SourceData_Fig1.csv","plot,standing_deadwood,scaled_richness\n123,0.4,0.1\n")
        x=io.BytesIO()
        with zipfile.ZipFile(x,"w") as zw:
            zw.writestr("xl/workbook.xml",
               '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Fig 2" sheetId="1"/></sheets></workbook>')
        z.writestr("SourceData_Fig2.xlsx",x.getvalue())
    q=inspect(tmp.getvalue())
    assert q["source_file_count"]==2
    assert q["source_field_plot_taxon_species_abundance_values_read"]==0
    assert q["source_article_figure_data_values_read"]==0
    assert q["source_original_files"][1]["nonresponse_workbook_sheet_titles"]["n_sheets"]==1
    print("BALDUCCI2026_NATURE_ORIGINAL_ATTACHMENT_SOURCEFREE_TEST_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="balducci2026_original_public_attachment_sourceonly/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    result={"schema":"structural.balducci2026_europe12_publisher_source_data_catalogue.v1",
            "source_article_DOI":"10.1038/s41467-026-68668-x",
            "author_reported_all_taxa_plot_count":7971,
            "author_reported_all_taxa_country_count":12,
            "author_reported_original_source_dataset_count":32,
            "author_reported_multitaxa_plot_count":2615,
            "author_reported_multitaxa_forest_site_count":99,
            "original_beetle_only_validated_plot_count":None,
            "original_site_species_wood_field_join_verified":False,
            "underlying_biodiversity_data_declared_request_only":True,
            "original_taxon_response_cells_accessed":0,
            "new_original_ecological_scores":0,
            "status":"SOURCE_PUBLISHER_ATTACHMENT_NOT_INSPECTED"}
    try:
        result["catalogue"]=inspect(one_request())
        result["status"]=result["catalogue"]["status"]
    except Exception as e:
        result["status"]="SOURCE_OFFICIAL_ATTACHMENT_DOWNLOAD_OR_SCHEMA_STOP"
        result["error_class"]=type(e).__name__
        result["error_code"]=str(e)[:150] if isinstance(e,ValueError) else ""
    fp=Path(a.out)
    fp.parent.mkdir(parents=True,exist_ok=True)
    fp.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("BALDUCCI2026_SOURCE_ADMISSION",result["status"])
    if "catalogue" in result:
        print("SOURCE_PUBLIC_FILE_COUNT",result["catalogue"]["source_file_count"])
        print("ORIGINAL_SOURCE_SHA256",result["catalogue"]["source_original_sha256"])
    print("BEETLE_SITE_RESOURCE_TAXON_ROWS_OPENED",result["original_taxon_response_cells_accessed"])
if __name__=="__main__":
    main()
