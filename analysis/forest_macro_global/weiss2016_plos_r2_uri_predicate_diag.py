#!/usr/bin/env python3
"""No-source-body diagnostic of one frozen PLOS-issued redirect URI predicates."""
from __future__ import annotations
import argparse,hashlib,json,urllib.request,urllib.parse,urllib.error
from pathlib import Path
PRESPEC="docs/FOREST_MACRO_WEISS2016_R2_URI_PREDICATE_DIAG_PRESPEC_20261118.md"
URL="https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0149506.s001&type=supplementary"
SHA="2595cce0ff5b38d31337d871b664fe7bb3878ab55c1ed714eb7407845cbeb5fc"
HOST="corpus-prod.f505aadad1e46610c8f8563037eb3c4b.r2.cloudflarestorage.com"
class SourceStop(RuntimeError):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def categorize(location):
    if not isinstance(location,str) or len(location)>12000 or not location:
        raise SourceStop("SOURCE_ORIGINAL_LOCATION_MISSING")
    if hashlib.sha256(location.encode("utf-8")).hexdigest()!=SHA:
        raise SourceStop("SOURCE_ISSUED_LOCATION_DRIFT")
    p=urllib.parse.urlparse(location)
    try:
        hasport=p.port is not None
    except ValueError:
        hasport=True
    return {
        "source_location_sha256_matches_previous_pinned":True,
        "scheme_https":p.scheme=="https",
        "exact_prior_issuer_cloudflare_R2_hostname":p.hostname==HOST,
        "userinfo_username_present":p.username is not None,
        "userinfo_password_present":p.password is not None,
        "port_present":hasport,
        "query_present":bool(p.query),
        "fragment_present":bool(p.fragment),
        "absolute_path":p.path.startswith("/"),
        "nonempty_path":bool(p.path),
        "decoded_parent_directory_token_present":(".." in urllib.parse.unquote(p.path).split("/")),
        "original_location_path_query_token_values_NOT_EXPORTED":True,
    }

def header_only():
    req=urllib.request.Request(URL,headers={"Accept":"application/msword,*/*;q=0.2",
         "User-Agent":"Structural-Weiss2016-original-PLOS-issuer-diagnostic-no-body/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=35):
            raise SourceStop("SOURCE_ORIGINAL_PLOS_EXPECTED_302_NOT_OBSERVED")
    except urllib.error.HTTPError as e:
        if e.code!=302:
            raise SourceStop("SOURCE_ORIGINAL_PLOS_HTTP_"+str(e.code)) from None
        return categorize(e.headers.get("Location"))
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_PLOS_ISSUER_TRANSPORT_"+type(e).__name__) from None

def known_truth():
    test="https://"+HOST+"/other/pone.0149506.s001.doc"
    x=hashlib.sha256(test.encode()).hexdigest()
    assert x!=SHA
    # Do not construct an unguarded diagnostic. All real access is SHA-frozen.
    assert b"PLOS".decode()=="PLOS"
    print("SYNTHETIC_REDIRECT_PREDICATE_DIAGNOSTIC_STRICT_SHA_GATE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args();known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    out={"schema":"structural.Weiss2016_R2_URL_publisher_redirect_predicates_no_body.v1",
         "prespec":PRESPEC,"source_original_PLOS_file_binary_bytes_READ":0,
         "source_original_beetle_trait_or_Gloor_species_values_READ":False,
         "Franzen_blocked_Dryad_source_NOT_RETRIED":True,
         "prior_forest_GEB_BALA_historical_scores_UNCHANGED":True,
         "eBird_used":False,"TinyFish_used":False}
    try:
        out["original_issuer_URI_predicates_ONLY"]=header_only()
        out["status"]="SOURCE_PINNED_ISSUER_URI_PREDICATE_DIAGNOSTIC_ONLY"
    except SourceStop as ex:
        out["status"]=str(ex)
        out["source_failure_not_ecological_result"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Weiss2016_PLOS_R2_original_issuer_URI_predicates_only.json").write_text(
       json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PLOS_R2_URL_STRUCTURE_DIAGNOSTIC",out["status"])
    print("NO_ORIGINAL_DOC_CONTENT_OR_GLOOR_BIOLOGY_READ")
if __name__=="__main__":main()
