#!/usr/bin/env python3
"""Manual, secret-backed NEON original beetle file MANIFEST gate.

Official NEON 2026 REST /data requires an account API token. This never
downloads beetle observations or temperatures: it asks only for BART 2015-08
(originally confirmed three-product common source month) file metadata.

The token is read ONLY from the runner's NEON_API_TOKEN environment, sent ONLY
via HTTPS X-API-Token header, NEVER placed in GitHub code, query parameters,
saved JSON artifacts or stdout. If secret is missing, STOP safely.
"""
from __future__ import annotations
import argparse, json, os, urllib.request, urllib.error
from pathlib import Path

URL="https://data.neonscience.org/api/v0/data/DP1.10022.001/BART/2015-08?release=RELEASE-2026"


def probe(*,token,opener=urllib.request.urlopen):
    data={
      "schema":"structural.NEON_2026_authenticated_file_catalog_source_gate.v1",
      "original_NEON_release":"RELEASE-2026",
      "fixed_original_product":"DP1.10022.001",
      "strict_forest_site_context":"BART",
      "three_products_shared_source_month":"2015-08",
      "authentication_secret_input_name":"NEON_API_TOKEN",
      "source_api_authentication_verified":False,
      "original_file_catalog_n":None,
      "original_beetle_data_files_downloaded":0,
      "raw_token_or_signed_URL_or_taxa_never_saved":True,
      "original_forest_plot_level_membership_verified":False,
      "forest_beetle_temperature_or_movement_effect_scored":False,
      "access_status":"NOT_ATTEMPTED"
    }
    if not token or not str(token).strip():
        data["access_status"]="SCIENTIFIC_SOURCE_STOP_SECRET_NOT_CONFIGURED"
        return data
    # Do not use token in URL (query strings can enter logs).
    req=urllib.request.Request(URL,headers={
        "User-Agent":"Structural-ForestBeetle-NEON-Authenticated-Catalog/1.0",
        "X-API-Token":token.strip(),
        "Accept":"application/json"})
    try:
        with opener(req,timeout=45) as resp:
            status=resp.status
            body=resp.read(2_000_001)
        if len(body)>2_000_000:
            data["access_status"]="SOURCE_ORIGINAL_CATALOG_OVERSIZE_STOP"
        elif status!=200:
            data["access_status"]="SOURCE_HTTP_"+str(status)+"_STOP"
        else:
            payload=json.loads(body)
            files=(payload.get("data") or {}).get("files")
            if not isinstance(files,list):
                data["access_status"]="ORIGINAL_NEON_RESPONSE_SCHEMA_STOP"
            else:
                data["source_api_authentication_verified"]=True
                data["access_status"]="ORIGINAL_SOURCE_FILE_CATALOG_ACCESS_GRANTED"
                data["original_file_catalog_n"]=len(files)
                # No name or temporary downloadable URL leaves runner.
                data["file_extension_aggregates"]={
                    ext:sum(str(q.get("name","")).lower().endswith(ext) for q in files)
                    for ext in (".csv",".txt",".zip",".json")
                }
    except urllib.error.HTTPError as e:
        # Don't read error body: may include dynamic/authentication details.
        data["access_status"]="SOURCE_HTTP_"+str(e.code)+"_ACCESS_STOP"
    except urllib.error.URLError:
        data["access_status"]="SOURCE_NETWORK_ACCESS_STOP"
    return data


def run(out):
    token=os.environ.get("NEON_API_TOKEN")
    result=probe(token=token)
    dst=Path(out);dst.mkdir(parents=True,exist_ok=True)
    (dst/"NEON_original_secret_backed_access_manifest.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    run(args.out)
