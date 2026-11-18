#!/usr/bin/env python3
"""Weiss 2016 *own* Dryad archived legacy XLS: publisher metadata ONLY.

This is the same study as the authenticated PLOS S1 DOC, not a second
independent replication. No XLS GET, no original species names/guilds,
no Carpathian/Gloor species values or ecological effects.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from franzen425_dryad_guild_sourceonly import (
    public_json, SourceStop, source_path, expected_file_list
)
import urllib.parse

DOI="doi:10.5061/dryad.39k32"
DATASET="https://datadryad.org/api/v2/datasets/"+urllib.parse.quote(DOI,safe="")
FILENAME="FITBeetleData_CzechRepublic_2007+2008.xls"
PRESPEC="docs/FOREST_MACRO_WEISS2016_ORIGINAL_DRYAD_XLS_SOURCE_PRESPEC_20261118.md"

def original_publisher_source_manifest():
    # One exact dataset GET and one GET per publisher-declared HAL relation.
    ds,ds_receipt=public_json(DATASET)
    if str(ds.get("identifier","")).casefold()!=DOI:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_DRYAD_DOI_ID_MISMATCH")
    lic=str(ds.get("license","")).casefold()
    if not any(term in lic for term in ("cc0","cc-by","creative commons attribution")):
        raise SourceStop("SOURCE_ORIGINAL_WEISS_DRYAD_LICENSE_NOT_OPEN")
    links=ds.get("_links") or {}
    verhref=(links.get("stash:version") or {}).get("href")
    if not verhref:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_DRYAD_VERSION_LINK_ABSENT")
    ver,ver_receipt=public_json(verhref)
    filhref=((ver.get("_links") or {}).get("stash:files") or {}).get("href")
    if not filhref:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_DRYAD_FILE_LIST_LINK_ABSENT")
    files,file_receipt=public_json(filhref)
    manifest=expected_file_list(files)
    original=manifest["official_publisher_files_metadata_only"]
    names=[x["original_publisher_filename"] for x in original]
    if names.count(FILENAME)!=1:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_FILENAME_NOT_UNIQUE_OR_MISSING")
    if len(original)!=1:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_AUTHOR_ARCHIVE_UNEXPECTED_MULTIFILE")
    target=original[0]
    if not target["original_file_id_if_authority_exposed"]:
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_FILE_ID_NOT_EXPOSED")
    dtype=(target["original_digest_type"] or "").casefold()
    digest=target["original_publisher_digest"]
    if dtype and dtype not in ("md5","sha256"):
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_UNKNOWN_DIGEST_SCHEME")
    if len(digest) not in (32,64):
        raise SourceStop("SOURCE_ORIGINAL_WEISS_XLS_DIGEST_BAD_LENGTH")
    return {
        "original_Dryad_DOI":DOI.removeprefix("doi:"),
        "publisher_record_rights":lic,
        "original_version_publication_date":ver.get("publicationDate"),
        "publisher_dataset_metadata_digest_and_size":ds_receipt,
        "publisher_version_metadata_digest_and_size":ver_receipt,
        "publisher_files_metadata_digest_and_size":file_receipt,
        "original_author_is_same_Weiss2016_PLOS_study_NOT_independent_replication":True,
        "original_published_author_workbook_metadata_ONLY":{
            "publisher_exact_filename":FILENAME,
            "publisher_original_file_id":target["original_file_id_if_authority_exposed"],
            "publisher_original_bytes":target["original_publisher_bytes"],
            "publisher_original_digest_scheme":dtype or ("sha256" if len(digest)==64 else "md5"),
            "publisher_original_digest":digest,
            "original_species_feeding_guild_values_READ":0,
        },
        "published_source_workbook_data_rows_REQUESTED":0,
        "Gloor_Carpathian_response_species_headers_and_values_READ":0,
        "same_study_NOT_additional_ecological_validation":True,
        "status":"SOURCE_ORIGINAL_WEISS_AUTHOR_XLS_MANIFEST_VERIFIED_ONLY",
    }

def synthetic():
    # Ensure target is the original Weiss catalogue filename and versioned
    # Dryad path, not an alternate URL to the inaccessible Franzén source.
    assert DATASET.endswith("doi%3A10.5061%2Fdryad.39k32")
    assert FILENAME.endswith(".xls")
    assert source_path("/api/v2/files/123456/download")=="https://datadryad.org/api/v2/files/123456/download"
    assert "gf1vhhn3w" not in DATASET
    print("SYNTHETIC_WEISS2016_ORIGINAL_DRYAD_METADATA_NO_XLS_DATA_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--out",type=Path)
    a=parser.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:parser.error("--out is required")
    receipt={
        "schema":"structural.Weiss2016_author_Dryad_original_XLS_manifest_only.v1",
        "precommit":PRESPEC,
        "exact_original_author_DOI":DOI.removeprefix("doi:"),
        "original_XLS_file_GET_requests":0,
        "original_Weiss_species_guild_sheet_values_READ":False,
        "original_Gloor_Carpathian_species_and_abundance_READ":False,
        "original_Franzen_Dryad_HTTP401_dataset_NOT_RETRIED":True,
        "prior_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_frozen":True,
        "new_ecological_effect_estimated":False,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        receipt["original_publisher_manifest_ONLY"]=original_publisher_source_manifest()
        receipt["status"]=receipt["original_publisher_manifest_ONLY"]["status"]
    except SourceStop as exc:
        receipt["status"]=str(exc)
        receipt["source_rights_or_manifest_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Weiss2016_Dryad_original_author_XLS_publisher_manifest_only.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WEISS2016_DRYAD_OWN_ORIGINAL_XLS_MANIFEST_STATUS",receipt["status"])
    print("NO_WEISS_XLS_OR_GLOOR_BEETLE_DATA_OPENED")

if __name__=="__main__":
    main()
