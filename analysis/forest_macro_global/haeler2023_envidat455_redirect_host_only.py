#!/usr/bin/env python3
"""One verified publisher EnviDat455 first resource: HTTP redirect host only.

No automatic 302 follow, no original file content or site/beetle values.
"""
import argparse,json,urllib.error,urllib.parse,urllib.request
from pathlib import Path
import haeler2023_envidat455_four_csv_header_only as original

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def diagnose():
    ids=original.exact_public_urls()
    x=ids["Community matrix (saproxylic beetles)"]
    opener=urllib.request.build_opener(NoRedirect())
    req=urllib.request.Request(x["url"],headers=original.HEADERS)
    try:
        with opener.open(req,timeout=30) as h:
            status=h.status
            loc=h.headers.get("Location")
    except urllib.error.HTTPError as e:
        status=e.code
        loc=e.headers.get("Location")
    out={"publisher_original_resource_id":x["id"],
         "publisher_original_resource_declared_size":x["size"],
         "publisher_original_request_status":status,
         "source_original_resource_data_bytes_read":0,
         "original_species_or_deadwood_values_read":0,
         "redirect_url_path_or_query_exported":False}
    if status in (301,302,303,307,308) and loc:
        p=urllib.parse.urlparse(urllib.parse.urljoin(x["url"],loc))
        out["redirect_scheme"]=p.scheme
        out["redirect_host_only"]=p.hostname
        out["status"]="SOURCE_ORIGINAL_REDIRECT_HOST_DOCUMENTED_NO_SOURCE_BYTES"
    elif status in (401,403):
        out["status"]="SOURCE_ORIGINAL_PUBLISHER_FILE_ACCESS_DENIED"
    else:
        out["status"]="SOURCE_ORIGINAL_REDIRECT_NOT_VERIFIED"
    return out

def test():
    assert NoRedirect().redirect_request(None,None,302,"",{},"https://example.com") is None
    assert len(original.ORIGINAL)==4
    print("SWISS_ENVIDAT_REDIRECT_HOST_SOURCE_FREE_TEST_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="envidat455_redirect_hostonly/receipt.json")
    a=ap.parse_args()
    test()
    if a.test:return
    out={"schema":"structural.envidat455_exact_original_302_HOST_ONLY_NO_BODY.v1",
         "original_doi":"10.16904/envidat.455",
         "original_beetle_or_resource_data_bytes_read":0,
         "new_original_ecological_scores":0,
         "status":"SOURCE_REDIRECT_HOST_UNCHECKED"}
    try:
        out["source_redirect"]=diagnose()
        out["status"]=out["source_redirect"]["status"]
    except Exception as e:
        out["status"]="SOURCE_REDIRECT_HOST_DIAGNOSTIC_STOP"
        out["error_type"]=type(e).__name__
        out["error_code"]=str(e)[:120] if isinstance(e,ValueError) else ""
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("ENVIDAT_302_REDIRECT_METHOD_STATUS",out["status"])
    print("ORIGINAL_RESPONSE_BYTES_READ",out["original_beetle_or_resource_data_bytes_read"])
if __name__=="__main__":main()
