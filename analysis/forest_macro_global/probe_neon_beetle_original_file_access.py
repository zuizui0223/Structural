#!/usr/bin/env python3
"""One anonymous official NEON 2026 beetle file-catalog access probe.

The sample is a source-confirmed STRICT_FOREST_ONLY_SITE context candidate,
BART, common to NEON ground beetles, woody vegetation, and multilevel air
temperature in RELEASE-2026. Before probing the data endpoint, fetch only
public product metadata to select an ACTUALLY advertised shared YYYY-MM.

No API credential or species/temperature/canopy response rows are read.
200 = data file catalog reachable anonymously (not that file bytes or beetle
plots are verified); 401/403 = authorization gate. A single fixed site-month
request is made; do not silently retry adjacent dates or borrow other releases.
"""
from __future__ import annotations
import argparse,json,urllib.error,urllib.parse,urllib.request
from pathlib import Path

from audit_neon_beetle_vegetation_temp_support import (
    RELEASE,API,ROLES,fetch_product,profile
)

STRICT_SITE="BART"
DATA_URL="https://data.neonscience.org/api/v0/data/"


def probe(site=STRICT_SITE, *, product_get=fetch_product, opener=urllib.request.urlopen):
    # NEON source product sites/months are previously audited; this fresh
    # call rechecks the month strictly before touching an original file catalog.
    sources={role:product_get(API+code+"?release="+RELEASE)
             for role,code in ROLES.items()}
    sites={role:profile(role,source) for role,source in sources.items()}
    common=set.intersection(*(sites[role].get(site,set()) for role in ROLES))
    if not common:
        raise ValueError("NEON_source_BART_no_common_original_site_calendar_month")
    month=sorted(common)[0]
    url=DATA_URL+ROLES["ground_beetle"]+"/"+site+"/"+month+"?release="+RELEASE
    request=urllib.request.Request(url,headers={
        "User-Agent":"Structural-Forest-Beetle-Original-FileCatalog-Probe/1.0",
        "Accept":"application/json",
    })
    report={
        "schema":"structural.neon_2026_original_beetle_file_catalog_one_probe.v1",
        "source_release":RELEASE,
        "original_data_product_code":ROLES["ground_beetle"],
        "strict_source_site_code":site,
        "source_confirmed_three_product_sample_month":month,
        "source_confirmed_common_month_count":len(common),
        "anonymous_Neon_beetle_file_catalog_http_status":None,
        "access_status":"UNKNOWN",
        "source_original_files_in_catalog":None,
        "file_names_original_taxon_response_data_not_opened":True,
        "downloaded_file_contents":False,
        "original_beetle_species_count_or_plot_join_verified":False,
        "original_plot_habitat_not_proven_by_site_NLCD":True,
        "not_vertical_beetle_traps_or_actual_movement":True,
        "one_source_site_calendar_month_probe_only":True,
        "eBird_used":False
    }
    try:
        with opener(request,timeout=45) as fd:
            http=fd.status
            data=fd.read(2_000_001)
        if len(data)>2_000_000:
            raise ValueError("NEON_data_catalog_exceeds_2MB_safety_cap")
        report["anonymous_Neon_beetle_file_catalog_http_status"]=http
        if http!=200:
            report["access_status"]="NON_200_SOURCE_RESPONSE_STOP"
        else:
            obj=json.loads(data)
            files=obj.get("data",{}).get("files") if isinstance(obj,dict) else None
            if not isinstance(files,list):
                report["access_status"]="UNEXPECTED_ORIGINAL_CATALOG_SCHEMA_STOP"
            else:
                report["access_status"]="PUBLIC_ORIGINAL_FILE_CATALOG_AVAILABLE"
                report["source_original_files_in_catalog"]=len(files)
                report["original_file_types_catalog_frequency"]={
                    kind:sum(str(q.get("name","")).lower().endswith(kind)
                             for q in files)
                    for kind in (".csv",".zip",".txt",".json") }
    except urllib.error.HTTPError as error:
        report["anonymous_Neon_beetle_file_catalog_http_status"]=error.code
        report["access_status"]=(
            "ORIGINAL_FILES_REQUIRE_AUTHENTICATION_OR_ACCESS" if error.code in (401,403)
            else "PUBLIC_ORIGINAL_FILE_CATALOG_HTTP_"+str(error.code)+"_STOP")
    except urllib.error.URLError:
        report["access_status"]="PUBLIC_ORIGINAL_FILE_CATALOG_NETWORK_UNREACHABLE_STOP"
    return report


def run(out):
    report=probe()
    dst=Path(out)
    dst.mkdir(parents=True,exist_ok=True)
    (dst/"NEON_one_forest_beetle_file_catalog_access_gate.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    run(args.out)
