#!/usr/bin/env python3
"""Response-opaque metadata intake of Gloor et al 2026 Carpathian 116-plot data.

Source: Zenodo record 22142713 ONLY. No published original biological file is
opened, fetched, downloaded, or parsed. No retrospective endpoint optimization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://zenodo.org/api/records/22142713"
RECORD = 22142713
EXPECTED_DOI = "10.5281/zenodo.22142713"
PRESPEC = "docs/FOREST_MACRO_CARPATHIAN116_INDEPENDENT_SOURCE_ADMISSION_PRESPEC_20261118.md"
LIMIT = 2_000_000
MAX_FILES = 120
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.,+()@\-]{0,160}\.[A-Za-z0-9]{1,12}$")
ALLOWED_RIGHTS = ("cc-by-4.0", "cc-by-sa-4.0", "cc0-1.0", "cc0")
FAMILY = {
    "species_or_community": re.compile(r"(?i)beetle|coleopt|species|occurr|community|assembl|saprox|taxa|abund|presabs"),
    "physical_plot_site_or_stand": re.compile(r"(?i)plot|site|stand|localit|study|region|mountain"),
    "measured_environment_or_wood": re.compile(r"(?i)environment|covariat|habitat|deadwood|wood|forest|structur|vegetat|canopy|predict|landscap"),
    "feeding_guild_or_trait": re.compile(r"(?i)trait|guild|feeding|trophic|functional"),
    "codebook_or_readme": re.compile(r"(?i)readme|codebook|metadata|legend|dictionary|method"),
    "collection_effort": re.compile(r"(?i)effort|trap|sampling|sample.?event"),
}
class SourceStop(RuntimeError):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def fetch_metadata():
    req = urllib.request.Request(
        URL, headers={
            "Accept": "application/json",
            "User-Agent": "Structural-Gloor2026-original-Zenodo-public-record-only/1.0",
        })
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=50) as response:
            if response.status != 200:
                raise SourceStop("SOURCE_PUBLISHER_API_NOT200")
            mime = response.headers.get("Content-Type", "")
            data = response.read(LIMIT+1)
    except urllib.error.HTTPError as exc:
        raise SourceStop(f"SOURCE_PUBLISHER_ZENODO_HTTP_{exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceStop("SOURCE_PUBLISHER_ZENODO_TRANSPORT_" + type(exc).__name__) from None
    if len(data)>LIMIT or not data or "json" not in mime.lower():
        raise SourceStop("SOURCE_PUBLISHER_METADATA_JSON_ABSENT_OR_TOO_LARGE")
    try:
        doc=json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise SourceStop("SOURCE_PUBLISHER_METADATA_INVALID_JSON") from None
    return doc, {"original_metadata_sha256": hashlib.sha256(data).hexdigest(),
                 "original_metadata_bytes": len(data),
                 "publisher_metadata_HTTP": 200}

def safe_metadata(doc):
    if not isinstance(doc, dict):
        raise SourceStop("SOURCE_ZENODO_METADATA_NOT_OBJECT")
    if doc.get("id") != RECORD:
        raise SourceStop("SOURCE_RECORD_ID_OR_VERSION_STOP")
    md = doc.get("metadata")
    if not isinstance(md, dict):
        raise SourceStop("SOURCE_RECORD_METADATA_MISSING")
    dois = [x for x in (doc.get("doi"), md.get("doi")) if isinstance(x,str)]
    if not any(x.casefold().strip() == EXPECTED_DOI for x in dois):
        raise SourceStop("SOURCE_RECORD_DOI_MISMATCH_STOP")
    status=doc.get("status", doc.get("state"))
    if status is not None and str(status).casefold() not in {"published", "done"}:
        raise SourceStop("SOURCE_RECORD_NOT_PUBLISHED")
    lic = md.get("license", doc.get("license", ""))
    if isinstance(lic,dict):
        lic = lic.get("id", lic.get("title", ""))
    if not isinstance(lic,str):
        lic=""
    normalized=lic.strip().casefold().replace("_","-")
    if normalized not in ALLOWED_RIGHTS:
        raise SourceStop("SOURCE_LICENSE_NOT_REUSABLE_HOLD")
    f=doc.get("files")
    if not isinstance(f, list) or not 1<=len(f)<=MAX_FILES:
        raise SourceStop("SOURCE_PUBLISHER_FILES_NOT_LISTED")
    files=[]
    for item in f:
        if not isinstance(item,dict):
            raise SourceStop("SOURCE_PUBLISHER_FILE_NOT_OBJECT")
        name=item.get("key",item.get("filename",item.get("name","")))
        if not isinstance(name,str) or not SAFE_NAME.fullmatch(name):
            raise SourceStop("SOURCE_FILE_NAME_UNSAFE_OR_UNEXPECTED")
        size=item.get("size")
        if not isinstance(size,int) or not 0<=size<=50_000_000_000:
            raise SourceStop("SOURCE_FILE_SIZE_UNAVAILABLE")
        checksum=item.get("checksum","")
        if isinstance(checksum,dict):
            algo=checksum.get("type", checksum.get("algorithm", ""))
            digest=checksum.get("value",checksum.get("checksum",""))
            checksum=(str(algo)+":"+str(digest)) if algo and digest else ""
        if not isinstance(checksum,str):
            checksum=""
        if ":" in checksum:
            scheme, value = checksum.split(":",1)
        else:
            scheme, value = ("",checksum)
        scheme=scheme.lower()
        if scheme and scheme not in ("md5","sha256"):
            raise SourceStop("SOURCE_PUBLISHER_CHECKSUM_UNSUPPORTED")
        if not re.fullmatch(r"[a-fA-F0-9]{32}|[a-fA-F0-9]{64}",value):
            raise SourceStop("SOURCE_PUBLISHER_CHECKSUM_MISSING_OR_INVALID")
        if not scheme:
            scheme="sha256" if len(value)==64 else "md5"
        links=item.get("links",{})
        href=(links.get("self",links.get("content","")) if isinstance(links,dict) else "")
        domain=urllib.parse.urlparse(href).hostname if href else None
        if domain is not None and domain not in ("zenodo.org", "www.zenodo.org"):
            raise SourceStop("SOURCE_NON_ZENODO_FILE_REFERENCE_STOP")
        hints=[k for k,rx in FAMILY.items() if rx.search(name)]
        ext=name.rsplit(".",1)[-1].lower()
        files.append({
          "original_publisher_filename":name,
          "original_publisher_file_bytes":size,
          "publisher_checksum_scheme":scheme,
          "publisher_original_file_digest":value.lower(),
          "file_extension":ext,
          "file_category_from_FILENAME_ONLY":hints,
          "zenodo_original_file_LINK_NOT_OPENED":True,
        })
    n={k:sum(k in f["file_category_from_FILENAME_ONLY"] for f in files) for k in FAMILY}
    biological=n["species_or_community"]>0
    environmental=n["measured_environment_or_wood"]>0
    physical=n["physical_plot_site_or_stand"]>0
    source_candidate=biological and (environmental or physical)
    return {
        "original_Zenodo_record_id":RECORD,
        "original_record_DOI":EXPECTED_DOI,
        "verified_source_rights_code":normalized,
        "original_record_status":str(status) if status else "not_explicit_in_source_payload",
        "original_files_count":len(files),
        "original_files_total_bytes":sum(x["original_publisher_file_bytes"] for x in files),
        "source_original_file_metadata_only":files,
        "predeclared_filename_hints_counts_ONLY":n,
        "filename_category_HYPOTHESIS_not_original_field_presence":True,
        "original_record_all_binary_source_files_NOT_OPENED":True,
        "original_species_plot_environment_or_guild_values_READ":0,
        "new_ecological_effect_computed":False,
        "status":("SOURCE_METADATA_ELIGIBLE_FOR_SEPARATE_SCHEMA_GATE"
                  if source_candidate
                  else "SOURCE_METADATA_AMBIGUOUS_HOLD"),
    }

def synthetic():
    fixture={
      "id":RECORD,"doi":EXPECTED_DOI,"status":"published",
      "metadata":{"license":{"id":"cc-by-4.0"}},
      "files":[
        {"key":"beetle_species.csv","size":2345,
         "checksum":"md5:"+"a"*32,
         "links":{"self":"https://zenodo.org/api/records/22142713/files/beetle_species.csv"}},
        {"key":"plot_deadwood.csv","size":101,
         "checksum":"md5:"+"b"*32,
         "links":{"self":"https://zenodo.org/api/records/22142713/files/plot_deadwood.csv"}},
      ],
    }
    result=safe_metadata(fixture)
    assert result["status"]=="SOURCE_METADATA_ELIGIBLE_FOR_SEPARATE_SCHEMA_GATE"
    assert result["original_species_plot_environment_or_guild_values_READ"]==0
    fixture["metadata"]["license"]["id"]="other"
    try:
        safe_metadata(fixture)
        raise AssertionError("unsupported license admitted")
    except SourceStop as exc:
        assert str(exc)=="SOURCE_LICENSE_NOT_REUSABLE_HOLD"
    print("SYNTHETIC_CARPATHIAN116_ZENODO_PUBLISHER_METADATA_ONLY_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:ap.error("--out required")
    result={
        "schema":"structural.Gloor2026_Carpathian116_Zenodo_original_metadata_only.v1",
        "prespec":PRESPEC,
        "original_record_id":RECORD,
        "original_data_ORIGINAL_BIOLOGY_READ":False,
        "original_forest_environment_catch_or_guild_ROWS_READ":0,
        "all_prior_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_frozen":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        doc,receipt=fetch_metadata()
        result["publisher_API_response"]=receipt
        result["publisher_source_intake"]=safe_metadata(doc)
        result["status"]=result["publisher_source_intake"]["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["publisher_access_or_rights_STOP_not_biological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    f=args.out/"Carpathian116_original_Zenodo_metadata_only.json"
    f.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("ORIGINAL_CARPATHIAN116_SOURCE_INTAKE",result["status"])
    print("NO_BEETLE_OR_FOREST_FIELD_OR_VALUES_OPENED")

if __name__=="__main__":
    main()
