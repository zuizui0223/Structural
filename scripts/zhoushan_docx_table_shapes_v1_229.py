#!/usr/bin/env python3
"""Only source DOCX byte-identity & table tags; outer ZIP may change packaging."""
import argparse,hashlib,io,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError

SOURCE="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11634684/supplementaryFiles"
OUTER_SHA="9de7694fba84f8afacddc54a93a4f9101684b8302797f60cf3ab8ee300fa337b"
OUTER_SIZE=841453
DOCX_NAME="zoae006_suppl_supplementary_material.docx"
DOCX_SIZE=678993
DOCX_CRC=0x8874d873
HOSTS={"www.ebi.ac.uk","ebi.ac.uk","www.europepmc.org","europepmc.org"}
NS="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_DOC_XML=12000000

def validate_outer(blob):
    if not 0 < len(blob) <= 5000000 or not blob.startswith(b"PK"):
        raise ValueError("Official source is not a bounded ZIP")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        matches=[x for x in z.infolist() if x.filename.rsplit("/",1)[-1].casefold()==DOCX_NAME.casefold()]
        if len(matches)!=1:raise ValueError("Frozen source DOCX missing/ambiguous")
        item=matches[0]
        if item.file_size!=DOCX_SIZE or item.CRC!=DOCX_CRC:
            raise ValueError("Frozen member size/CRC changed")
        if item.flag_bits&1:raise ValueError("Encrypted source")
        payload=z.read(item)  # Read DOCX archive bytes, no semantic DOCX values yet.
    if len(payload)!=DOCX_SIZE or not payload.startswith(b"PK"):
        raise ValueError("Inner DOCX source format changed")
    return payload

def table_shapes(docx):
    with zipfile.ZipFile(io.BytesIO(docx)) as archive:
        infos=archive.infolist()
        if not any(x.filename=="word/document.xml" for x in infos):
            raise ValueError("Main WordprocessingML part missing")
        target=archive.getinfo("word/document.xml")
        if target.file_size>MAX_DOC_XML or target.flag_bits&1:
            raise ValueError("Main Word XML exceeds frozen cap")
        xml=archive.read(target)
        # Build XML element tree but read ONLY element TAGS. No .text or text nodes ever exposed.
        root=ET.fromstring(xml)
        tables=[]
        for table in root.iter(NS+"tbl"):
            row_shapes=[]
            for row in table.findall(NS+"tr"):
                row_shapes.append(sum(1 for _ in row.findall(NS+"tc")))
            if row_shapes:
                tables.append({
                  "rows":len(row_shapes),
                  "first_row_cells":row_shapes[0],
                  "min_cells_per_row":min(row_shapes),
                  "max_cells_per_row":max(row_shapes)
                })
        # Header text, species names, island labels and cell values are NEVER read.
        return {
          "docx_zip_member_count":len(infos),
          "word_xml_member_bytes":len(xml),
          "table_count":len(tables),
          "tables":tables,
          "potential_39_by_18_or_larger_table_structures":
             sum(t["rows"] in (39,40,41,42) and t["max_cells_per_row"]>=18 for t in tables),
          "all_table_text_fields_read":0,
          "all_species_island_incidence_fields_read":0
        }
def execute():
    r={"schema":"structural.zhoushan_table_shape_result.v1_229",
       "source":"official Europe PMC, frozen v1.227 ZIP",
       "field_species_island_incidence_rows_opened":0,
       "table_text_decoded":False,
       "original_mammal_response_opened":False,
       "new_biological_scoring_authorized":False}
    try:
        req=Request(SOURCE,headers={"User-Agent":"Structural-public-provenance-v1.229",
           "Accept":"application/zip, application/octet-stream"})
        with urlopen(req,timeout=90) as response:
            host=urlsplit(response.url).hostname
            if urlsplit(response.url).scheme!="https" or host not in HOSTS:
                raise ValueError("Untrusted source redirect")
            blob=response.read(OUTER_SIZE+1)
        docx=validate_outer(blob)
        r.update(status="PASS_OFFICIAL_DOCX_TABLE_GEOMETRY_ONLY",
            outer_sha256_observed=hashlib.sha256(blob).hexdigest(),
            outer_zip_size_observed=len(blob),
            inner_docx_sha256=hashlib.sha256(docx).hexdigest(),
            docx_member=DOCX_NAME,
            **table_shapes(docx))
    except HTTPError as e:
        r.update(status="STOP_OFFICIAL_EUROPEPMC_HTTP",http_status=e.code)
    except Exception as e:
        r.update(status="STOP_DOCX_CONTENT_IDENTITY_OR_TABLE_SCHEMA",
            reason_type=type(e).__name__)
    return r
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    x=p.parse_args();result=execute()
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
