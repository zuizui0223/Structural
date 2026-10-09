#!/usr/bin/env python3
"""Europe PMC official supplementaryFiles archive metadata, no inner file contents."""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
from urllib import request,error
from urllib.parse import urlsplit

SOURCE="https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11634684/supplementaryFiles"
SOURCE_PMC="PMC11634684"
MEMBER="zoae006_suppl_supplementary_material.docx"
HOSTS={"www.ebi.ac.uk","ebi.ac.uk","europepmc.org","www.europepmc.org"}
MAX_ARCHIVE=5000000
MAX_FILES=50
MAX_MEMBER=10000000

def is_official(url):
    u=urlsplit(url)
    return u.scheme=="https" and u.hostname in HOSTS

def catalogue(archive):
    if len(archive)>MAX_ARCHIVE or not archive.startswith(b"PK"):
        raise ValueError("Official archive absent or not a bounded ZIP")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        items=z.infolist()  # ZIP CENTRAL DIRECTORY ONLY; NO member open/read/extract.
        if not 1<=len(items)<=MAX_FILES:raise ValueError("Unexpected ZIP member count")
        if any(x.file_size>MAX_MEMBER or x.flag_bits&1 or x.is_dir() for x in items):
            raise ValueError("Archive member size/encryption/directory gate")
        matching=[x for x in items if x.filename.rsplit("/",1)[-1].casefold()==MEMBER.casefold()]
        if len(matching)!=1:raise ValueError("Expected source supplement not unique")
        return {"zip_member_count":len(items),
            "exact_expected_docx_member_present":True,
            "exact_docx_member_name":matching[0].filename,
            "exact_docx_member_uncompressed_bytes":matching[0].file_size,
            "exact_docx_member_crc32":f"{matching[0].CRC:08x}",
            "source_docx_contents_read":0,
            "other_zip_member_contents_read":0}

def run():
    x={"schema":"structural.europepmc_zhoushan_supplement_metadata.v1_227",
       "pmc_source":SOURCE_PMC,
       "distributor":"official Europe PMC supplementaryFiles",
       "field_species_by_island_values_read":0,
       "source_docx_contents_read":0,
       "original_IUCN_mammal_heldout_reopened":False,
       "external_incidence_scoring_authorized":False}
    try:
        if not is_official(SOURCE):raise ValueError("Frozen distributor URL invalid")
        req=request.Request(SOURCE,headers={"Accept":"application/zip, application/octet-stream",
            "User-Agent":"Structural-research-provenance-v1.227"})
        with request.urlopen(req,timeout=30) as res:
            if not is_official(res.url):raise ValueError("Off-authority redirect")
            media=res.headers.get("Content-Type","").split(";")[0].lower().strip()
            data=res.read(MAX_ARCHIVE+1)
            status=res.status
        if len(data)>MAX_ARCHIVE:raise ValueError("Oversized distribution")
        details=catalogue(data)
        x.update(status="PASS_OFFICIAL_EUROPEPMC_SUPPLEMENT_ZIP_IDENTITY_ONLY",
            content_type=media,http_status=status,
            zip_sha256=hashlib.sha256(data).hexdigest(),
            archive_size_bytes=len(data),
            **details)
    except error.HTTPError as e:
        x.update(status="STOP_EUROPEPMC_SUPPLEMENT_HTTP",http_status=e.code)
    except Exception as e:
        x.update(status="STOP_EUROPEPMC_SUPPLEMENT_FORMAT_OR_TRANSPORT",
                 reason_class=type(e).__name__)
    return x

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);a=ap.parse_args()
    receipt=run()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,sort_keys=True))
