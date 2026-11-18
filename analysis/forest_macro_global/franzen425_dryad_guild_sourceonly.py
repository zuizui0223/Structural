#!/usr/bin/env python3
"""Independent Franzén2026 larval guild source: Dryad publisher metadata ONLY.

No downloaded original tableS1.xlsx, no species row, no Carpathian matrix
header/species or any beetle abundance. No biological effect is computed.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.parse,urllib.request,urllib.error
from pathlib import Path

BASE="https://datadryad.org"
DOI="doi:10.5061/dryad.gf1vhhn3w"
DATASET_URL=BASE+"/api/v2/datasets/"+urllib.parse.quote(DOI,safe="")
PRESPEC="docs/FOREST_MACRO_FRANZEN425_GUILD_SOURCE_ONLY_PRESPEC_20261118.md"
MAX_BYTES=1500000

class SourceStop(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def source_path(href):
    if not isinstance(href,str):raise SourceStop("SOURCE_DRYAD_LINK_MISSING")
    p=urllib.parse.urlparse(href)
    if p.query or p.fragment:raise SourceStop("SOURCE_DRYAD_LINK_UNEXPECTED_QUERY")
    if p.scheme:
        if p.scheme!="https" or p.hostname!="datadryad.org" or p.username or p.password or p.port:
            raise SourceStop("SOURCE_DRYAD_UNTRUSTED_LINK_ORIGIN")
        path=p.path
    else:
        path=href
    if not re.fullmatch(r"/api/v2/(?:datasets/[^?#]+|versions/[0-9]+(?:/files)?|files/[0-9]+(?:/download)?)",path):
        raise SourceStop("SOURCE_DRYAD_PUBLISHER_PATH_NOT_WHITELISTED")
    return BASE+path

def public_json(url):
    req=urllib.request.Request(source_path(url),headers={
        "User-Agent":"Structural-original-Franzen2026-trophic-guild-metadata-only/1.0",
        "Accept":"application/json",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=38) as resp:
            if resp.status!=200:raise SourceStop("SOURCE_DRYAD_PUBLISHER_NOT_HTTP200")
            mime=resp.headers.get("Content-Type","")
            data=resp.read(MAX_BYTES+1)
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_DRYAD_METADATA_HTTP_"+str(ex.code)) from None
    except (urllib.error.URLError,OSError,TimeoutError) as ex:
        raise SourceStop("SOURCE_DRYAD_METADATA_TRANSPORT_"+type(ex).__name__) from None
    if not data or len(data)>MAX_BYTES or "json" not in mime.lower():
        raise SourceStop("SOURCE_DRYAD_JSON_MISSING_OR_OVERSIZE")
    try:obj=json.loads(data.decode("utf-8"))
    except (UnicodeError,ValueError):
        raise SourceStop("SOURCE_DRYAD_JSON_PARSE_STOP") from None
    if not isinstance(obj,dict):raise SourceStop("SOURCE_DRYAD_JSON_NOT_OBJECT")
    return obj,{"metadata_SHA256":hashlib.sha256(data).hexdigest(),"metadata_bytes":len(data)}

def expected_file_list(source):
    if not isinstance(source,dict):raise SourceStop("SOURCE_DRYAD_PUBLISHER_FILE_LIST_SCHEMA_STOP")
    entries=(source.get("_embedded") or {}).get("stash:files")
    if not isinstance(entries,list):raise SourceStop("SOURCE_DRYAD_NO_ORIGINAL_FILES")
    if source.get("total") is not None and int(source["total"])!=len(entries):
        raise SourceStop("SOURCE_DRYAD_UNRESOLVED_FILES_PAGINATION")
    if not 1<=len(entries)<=30:raise SourceStop("SOURCE_DRYAD_UNEXPECTED_FILE_COUNT")
    safe=[];have=False
    for f in entries:
        if not isinstance(f,dict):raise SourceStop("SOURCE_DRYAD_FILE_RECORD_NOT_OBJECT")
        name=f.get("path",f.get("filename",""))
        if not isinstance(name,str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._() +-]{0,125}",name):
            raise SourceStop("SOURCE_DRYAD_ORIGINAL_FILENAME_NOT_SAFE")
        n=f.get("size")
        if not isinstance(n,int) or not 1<=n<=200000000:
            raise SourceStop("SOURCE_DRYAD_ORIGINAL_FILE_SIZE_NOT_VALID")
        d=f.get("digest")
        dtyp=f.get("digestType")
        if not isinstance(d,str) or not re.fullmatch(r"(?:[0-9a-fA-F]{32}|[0-9a-fA-F]{64})",d):
            raise SourceStop("SOURCE_DRYAD_PUBLISHER_FILE_DIGEST_NOT_READABLE")
        if dtyp is not None and not isinstance(dtyp,str):
            raise SourceStop("SOURCE_DRYAD_DIGEST_TYPE_INVALID")
        links=f.get("_links") or {}
        if not isinstance(links,dict):raise SourceStop("SOURCE_DRYAD_FILE_HAL_LINKS_INVALID")
        ids=[]
        for typ in ("self","stash:download"):
            href=(links.get(typ) or {}).get("href","")
            if not href:continue
            url=source_path(href)
            m=re.fullmatch(r"https://datadryad.org/api/v2/files/([0-9]+)(?:/download)?",url)
            if m:ids.append(int(m.group(1)))
        have=have or name=="tableS1.xlsx"
        safe.append({
            "original_publisher_filename":name,
            "original_publisher_bytes":n,
            "original_digest_type":dtyp,
            "original_publisher_digest":d.lower(),
            "original_file_id_if_authority_exposed":ids[0] if ids else None,
            "original_tabular_species_or_trait_ROWS_READ":0,
        })
    return {
        "official_publisher_files_metadata_only":safe,
        "original_file_count":len(safe),
        "original_target_tableS1_xlsx_present":have,
        "official_filename_only_not_source_species_coverage":True,
    }

def run():
    ds,dsinfo=public_json(DATASET_URL)
    if str(ds.get("identifier","")).casefold()!=DOI:
        raise SourceStop("SOURCE_DRYAD_ORIGINAL_DOI_MISMATCH")
    lic=str(ds.get("license","")).casefold()
    if not (lic=="cc0" or "cc0" in lic or "cc-by" in lic or "creative commons attribution" in lic):
        raise SourceStop("SOURCE_GUILD_ARCHIVE_ACCESS_OR_RIGHTS_HOLD")
    vers=(ds.get("_links") or {}).get("stash:version") or {}
    version_href=vers.get("href")
    ver,verinfo=public_json(version_href)
    filelink=((ver.get("_links") or {}).get("stash:files") or {}).get("href")
    files,filesinfo=public_json(filelink)
    manifest=expected_file_list(files)
    return {
      "original_DOI":DOI.replace("doi:",""),
      "author_reported_species_total":425,
      "author_reported_family_count":11,
      "author_larval_trophic_groups_from_legal_publisher_README":5,
      "author_reported_family_bias_NOT_resolved_by_source_file_metadata":True,
      "original_source_license":lic,
      "original_source_publisher_version_metadata_publication_date":ver.get("publicationDate"),
      "original_api_dataset_response":dsinfo,
      "original_api_version_response":verinfo,
      "original_api_file_list_response":filesinfo,
      "publisher_original_file_manifest":manifest,
      "original_species_traits_values_READ":0,
      "original_Carpathian_species_labels_or_abundance_VALUES_READ":0,
      "new_ecological_effect_estimated":False,
      "status":("SOURCE_GUILD_TAXON_LIST_FILE_PRESENT_ONLY"
                if manifest["original_target_tableS1_xlsx_present"] else
                "SOURCE_ORIGINAL_GUILD_TABLE_MISSING_HOLD")
    }

def synthetic():
    assert source_path("/api/v2/files/25/download")=="https://datadryad.org/api/v2/files/25/download"
    assert DATASET_URL.endswith("doi%3A10.5061%2Fdryad.gf1vhhn3w")
    f={"_embedded":{"stash:files":[{
       "path":"tableS1.xlsx","size":100,"digest":"a"*32,"digestType":"md5",
       "_links":{"self":{"href":"/api/v2/files/25"}}
    }]}}
    r=expected_file_list(f)
    assert r["original_target_tableS1_xlsx_present"]
    assert r["original_file_count"]==1
    assert r["official_publisher_files_metadata_only"][0]["original_tabular_species_or_trait_ROWS_READ"]==0
    try:
        source_path("https://evil.example/api/v2/files/25")
        raise AssertionError("source host escaped")
    except SourceStop:pass
    print("SYNTHETIC_FRANZEN425_PUBLISHER_METADATA_LICENSE_AND_ORIGINAL_TABLE_ONLY_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    x=ap.parse_args()
    synthetic()
    if x.test:return
    if x.out is None:ap.error("--out needed")
    result={
      "schema":"structural.Franzen2026_425spp_larval_guild_Dryad_original_metadata.v1",
      "precommit":PRESPEC,
      "original_Carpathian116_and_other_Finland_Chiu_German_BALA_GEB_values_UNREAD":True,
      "no_new_biological_effect":True,
      "eBird_used":False,"TinyFish_used":False
    }
    try:
        result["original_publisher_metadata_only"]=run()
        result["status"]=result["original_publisher_metadata_only"]["status"]
    except SourceStop as ex:
        result["status"]=str(ex)
        result["source_rights_or_manifest_STOP_not_ecological_non_support"]=True
    x.out.mkdir(parents=True,exist_ok=True)
    (x.out/"Franzen2026_425_species_original_Dryad_publisher_sourceonly.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FRANZEN425_LARVAL_GUILD_PUBLISHER_SOURCE",result["status"])

if __name__=="__main__":
    main()
