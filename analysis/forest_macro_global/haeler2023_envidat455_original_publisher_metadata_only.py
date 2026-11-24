#!/usr/bin/env python3
"""EnviDat455 original Swiss resource-layout METADATA ONLY.

No download of 69-site or 62 experimental-plot field data, beetle abundance
matrix or environmental resource values. Read ONLY CKAN public package_show.
"""
from __future__ import annotations
import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SLUG="data-from-dead-wood-distributed-in-different-sized-habitat-patches-enhances-dive"
DOI="10.16904/envidat.455"
API="https://www.envidat.ch/api/3/action/package_show?id="+SLUG
UA={"User-Agent":"Structural-EnviDat455-publisher-source-METADATA/1.0",
    "Accept":"application/json"}
EXPECTED_ROLE_TITLES={
    "community matrix (saproxylic beetles)",
    "community matrix (all beetles)",
    "forest and environmental variables",
    "variable description",
}

def metadata_only():
    out={"status":"SOURCE_CKAN_METADATA_NOT_OPENED",
         "original_doi":DOI,
         "original_publisher_slug":SLUG,
         "source_original_plot_resource_organism_files_GET":0,
         "original_beetle_taxon_or_wood_source_values_read":0,
         "original_site_species_resource_crosswalk_established":False}
    try:
        req=urllib.request.Request(API,headers=UA)
        with urllib.request.urlopen(req,timeout=38) as response:
            raw=response.read(500001)
            if response.status!=200 or len(raw)>500000:
                out["status"]="SOURCE_CKAN_HTTP_OR_SIZE_STOP"
                return out
    except urllib.error.HTTPError as e:
        out["status"]="SOURCE_CKAN_HTTP_ACCESS_STOP"
        out["http_status"]=e.code
        return out
    except Exception as e:
        out["status"]="SOURCE_CKAN_TRANSPORT_STOP"
        out["error_class"]=type(e).__name__
        return out
    try:j=json.loads(raw)
    except ValueError:
        out["status"]="SOURCE_CKAN_JSON_STOP"
        return out
    if j.get("success") is not True or not isinstance(j.get("result"),dict):
        out["status"]="SOURCE_CKAN_UNSUCCESSFUL_RESULT_STOP"
        return out
    r=j["result"]
    if str(r.get("name") or "")!=SLUG:
        out["status"]="SOURCE_ORIGINAL_RECORD_SLUG_MISMATCH_STOP"
        return out
    title=str(r.get("title") or "")[:190]
    source_ident=str(r.get("doi") or r.get("identifier") or "")
    extras=r.get("extras") or []
    extras_text=" ".join(str(x.get("value","")) for x in extras
                         if isinstance(x,dict) and ("doi" in str(x.get("key","")).lower()
                            or "citation" in str(x.get("key","")).lower()))
    # Public EnviDat DOI can be stored in citation metadata rather than
    # field DOI. Do not pretend original DOI matches if not exposed.
    out["published_DOI_verified_in_CKAN_record"]=(DOI in source_ident or DOI in extras_text)
    out["original_title"]=title
    out["original_license_id"]=r.get("license_id")
    out["original_license_title"]=r.get("license_title")
    out["dataset_state"]=r.get("state")
    out["data_package_private"]=r.get("private")
    out["original_version"]=r.get("version")
    pub=r.get("resources") or []
    if not isinstance(pub,list):
        out["status"]="SOURCE_CKAN_RESOURCE_INDEX_NOT_LIST_STOP"
        return out
    sanitized=[]
    for row in pub[:60]:
        if not isinstance(row,dict):
            out["status"]="SOURCE_CKAN_RESOURCE_ITEM_INVALID_STOP"
            return out
        name=str(row.get("name") or "").strip()
        rid=str(row.get("id") or "")
        # Any URLs returned here are not fetched; no need to expose bearer
        # tokens or original signed resource URLs in public receipts.
        parsed=urllib.parse.urlparse(str(row.get("url") or ""))
        sanitized.append({
            "source_publisher_resource_title":name[:110],
            "original_resource_id":rid[:48],
            "publisher_declared_file_size_bytes":row.get("size"),
            "format":str(row.get("format") or "")[:24],
            "mimetype":str(row.get("mimetype") or "")[:75],
            "publisher_original_resource_link_hostname":parsed.hostname,
            "original_resource_data_bytes_downloaded":0,
        })
    out["published_resource_metadata_only"]=sanitized
    out["published_resource_count"]=len(pub)
    titles={row["source_publisher_resource_title"].casefold() for row in sanitized}
    out["four_reported_role_titles_matched_count"]=len(titles&EXPECTED_ROLE_TITLES)
    if r.get("private") is True or str(r.get("state")) not in ("active","None"):
        out["status"]="SOURCE_ENVIDAT_NOT_CONFIRMED_PUBLIC_ACTIVE_STOP"
    elif len(sanitized)<4:
        out["status"]="SOURCE_ENVIDAT_FEWER_THAN_FOUR_RESOURCES_HOLD"
    elif out["four_reported_role_titles_matched_count"]<4:
        out["status"]="SOURCE_ENVIDAT_RESOURCE_ROLE_TITLES_REQUIRE_RECONCILIATION"
    else:
        out["status"]="SOURCE_ENVIDAT_FOUR_RESOURCES_CATALOGUED_NO_BIOLOGY"
    return out

def synthetic():
    assert API.startswith("https://www.envidat.ch/api/3/action/package_show?")
    assert DOI=="10.16904/envidat.455"
    assert len(EXPECTED_ROLE_TITLES)==4
    expected={"name":SLUG,"private":False,"state":"active"}
    assert expected["name"]==SLUG
    print("HAELER2023_ORIGINAL_ENVIDAT_CKAN_METADATA_ONLY_FIXTURE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="haeler2023_envidat455_metadata_only/receipt.json")
    a=p.parse_args()
    synthetic()
    if a.test:return
    x={"schema":"structural.haeler2023_sihlwald_envidat455_original_source_metadata_only.v1",
       "original_article_doi":"10.1111/1365-2664.14554",
       "original_data_doi":DOI,
       "published_metadata_plot_n":69,
       "published_experimental_design_plot_n":62,
       "source_original_physical_plot_identity_conflict_unresolved":True,
       "one_original_swiss_forest_not_an_independent_region_network":True,
       "source_original_biological_values_read":0,
       "new_source_original_ecological_effects_scored":0,
       "prior_Ecuador_Finland_Germany_Traylor_PREDICTS_BALA_GEB_unreopened":True,
       "source":metadata_only()}
    pth=Path(a.out);pth.parent.mkdir(parents=True,exist_ok=True)
    pth.write_text(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("HAELER_SIHLWALD_PUBLISHER_METADATA_STATUS",x["source"]["status"])
    print("FOUR_ORIGINAL_RESOURCE_ROLES",x["source"].get("four_reported_role_titles_matched_count"))
    print("SOURCE_BIOLOGICAL_ROWS_READ",x["source_original_biological_values_read"])

if __name__=="__main__":
    main()
