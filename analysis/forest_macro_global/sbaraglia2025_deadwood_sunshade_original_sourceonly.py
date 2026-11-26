#!/usr/bin/env python3
"""Official Dryad metadata, first community-header line and README only.

No original beetle abundance/taxa rows, environmental RDS values or site values
accessed. Do not infer RDS<->CSV join by matching 800 row counts.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DOI="10.5061/dryad.zcrjdfnpj"
PAPER="10.1111/een.13428"
HOST="https://datadryad.org"
EXPECTED={"env_final.rds","README.md","stickies_final.csv"}
MAX_META=2_000_000
MAX_CSV_HEADER=16_384
MAX_README=8192
USER_AGENT="Structural-Sbaraglia2025-source-only-validation/1.0"
TERM_WORDS=("code","tree_species","treatment","locality","exposure",
            "altitude","tree","run","time_exp","nspec","abu",
            "stickies_final","env_final","sampling","matrix","species",
            "rows","order","merge","join","matched")
IDENTITY_HEADER_WHITELIST={"code","sample","sampleid","trapid","id","site","plot"}

class SourceStop(Exception):pass

def safe_href(href):
    if not isinstance(href,str) or not href.startswith("/api/v2/"):
        raise SourceStop("SOURCE_STOP_NON_NATIVE_DRYAD_API_HREF")
    if any(x in href for x in ("..","//","?","#")):
        raise SourceStop("SOURCE_STOP_INVALID_DRYAD_API_HREF")
    return HOST+href

def one_publisher_json(url):
    if not url.startswith(HOST+"/api/v2/"):
        raise SourceStop("SOURCE_STOP_OUTSIDE_PUBLISHER_API")
    req=urllib.request.Request(url,method="GET",
                               headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=30) as res:
            data=res.read(MAX_META+1)
            status=res.status
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_METADATA_ACCESS_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_METADATA_TRANSPORT_"+type(e).__name__) from e
    if status!=200 or len(data)>MAX_META:
        raise SourceStop("SOURCE_STOP_PUBLISHER_META_HTTP_OR_TOO_LARGE")
    try:obj=json.loads(data.decode("utf-8"))
    except (UnicodeError,ValueError) as e:
        raise SourceStop("SOURCE_STOP_PUBLISHER_INVALID_JSON") from e
    if not isinstance(obj,dict):raise SourceStop("SOURCE_STOP_META_NOT_OBJECT")
    return obj

def extract_file_manifest(dataset,version,files):
    identity=str(dataset.get("identifier","")).casefold()
    if identity not in (DOI, "doi:"+DOI):
        raise SourceStop("SOURCE_STOP_ORIGINAL_DOI_IDENTITY")
    entries=((files.get("_embedded") or {}).get("stash:files"))
    if not isinstance(entries,list) or len(entries)!=3:
        raise SourceStop("SOURCE_STOP_PUBLISHER_THREE_FILE_COUNT_CHANGED")
    if files.get("total") is not None and int(files["total"])!=len(entries):
        raise SourceStop("SOURCE_STOP_PUBLISHER_FILE_PAGINATION")
    lookup={str(x.get("path","")):x for x in entries}
    if set(lookup)!=EXPECTED:
        raise SourceStop("SOURCE_STOP_PUBLISHER_THREE_FILE_MANIFEST_CHANGED")
    output=[]
    for name in sorted(lookup):
        row=lookup[name]
        digest=row.get("digest")
        size=row.get("size")
        if not isinstance(size,int) or size<=0:
            raise SourceStop("SOURCE_STOP_PUBLISHER_FILE_SIZE")
        if not isinstance(digest,str) or not re.fullmatch("[A-Fa-f0-9]{64}",digest):
            raise SourceStop("SOURCE_STOP_PUBLISHER_SHA256_DIGEST")
        href=((row.get("_links") or {}).get("stash:download") or {}).get("href")
        safe_href(href)
        output.append({"name":name,"bytes":size,
              "sha256":digest.lower(),
              "digest_type":row.get("digestType"),
              "original_source_file_retrieved":False})
    return {"publisher_doi":DOI,
            "paper_doi":PAPER,
            "publisher_visibility":dataset.get("visibility"),
            "publisher_license":dataset.get("license"),
            "publisher_version":version.get("versionNumber"),
            "publisher_version_status":version.get(
                "versionStatus",version.get("curationStatus")),
            "original_three_files_sha256_present":True,
            "original_publisher_file_manifest":output},lookup

def metadata():
    endpoint=HOST+"/api/v2/datasets/"+urllib.parse.quote("doi:"+DOI,safe="")
    d=one_publisher_json(endpoint)
    version_link=((d.get("_links") or {}).get("stash:version") or {}).get("href")
    safe_href(version_link)
    m=re.fullmatch(r"/api/v2/versions/([1-9][0-9]*)",version_link)
    if not m:raise SourceStop("SOURCE_STOP_PUBLISHER_VERSION_ID_HREF")
    version=one_publisher_json(safe_href(version_link))
    f=one_publisher_json(safe_href("/api/v2/versions/"+m.group(1)+"/files"))
    manifest,lookup=extract_file_manifest(d,version,f)
    manifest["publisher_version_id_from_native_href"]=int(m.group(1))
    return manifest,lookup

def one_file_small_source(href,filename):
    url=safe_href(href)
    header=filename=="stickies_final.csv"
    cap=MAX_CSV_HEADER if header else MAX_README
    hdr={"User-Agent":USER_AGENT,"Accept":"text/csv,text/plain,*/*"}
    if header:hdr["Range"]="bytes=0-"+str(cap-1)
    req=urllib.request.Request(url,method="GET",headers=hdr)
    try:
        with urllib.request.urlopen(req,timeout=32) as res:
            status=res.status
            raw=res.readline(cap+1) if header else res.read(cap+1)
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_FILE_ACCESS_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_FILE_TRANSPORT_"+type(e).__name__) from e
    if status not in (200,206) or len(raw)>cap:
        raise SourceStop("SOURCE_FILE_UNEXPECTED_HTTP_OR_OVERSIZE")
    if header and not raw.endswith((b"\n",b"\r")):
        raise SourceStop("SOURCE_CSV_FIRSTLINE_NOT_COMPLETE")
    return raw,status

def anonymous_csv_firstline(raw):
    try:line=raw.decode("utf-8-sig").rstrip("\r\n")
    except UnicodeError as e:raise SourceStop("SOURCE_CSV_FIRSTLINE_NOT_UTF8") from e
    sep=max((",", ";","\t"),key=line.count)
    if line.count(sep)==0:raise SourceStop("SOURCE_CSV_DELIMITER_UNKNOWN")
    try:cols=next(csv.reader([line],delimiter=sep,strict=True))
    except csv.Error as e:raise SourceStop("SOURCE_CSV_FIRSTLINE_INVALID") from e
    if len(cols)<20 or len(cols)>400:
        raise SourceStop("SOURCE_CSV_COLUMN_COUNT_OUTSIDE_REPORTED_198PLUS_KEYS")
    x=re.sub("[^a-z0-9]","",str(cols[0]).casefold())
    return {
      "source_original_csv_firstline_column_count":len(cols),
      "original_delimiter_category":{",":"comma",";":"semicolon","\t":"tab"}[sep],
      "first_header_generic_sample_ID_lexeme_if_whitelisted":
         x if x in IDENTITY_HEADER_WHITELIST else None,
      "source_matrix_rows_read":0,
      "original_species_and_taxon_header_labels_NOT_EXPORTED":True,
      "firstline_alone_cannot_prove_800row_RDS_matching":True,
    }

def anonymous_readme(raw):
    try:s=raw.decode("utf-8-sig")
    except UnicodeError as e:raise SourceStop("SOURCE_README_NOT_UTF8") from e
    low=s.casefold()
    return {"readme_utf8_readable":True,
            "readme_lines":len(s.splitlines()),
            "allowed_original_method_word_occurrences":{
                k:len(re.findall(r"(?<!\w)"+re.escape(k)+r"(?!\w)",low))
                for k in TERM_WORDS},
            "original_README_text_NOT_EXPORTED":True,
            "readme_keyword_counts_DO_NOT_PROVE_ROW_ID_JOIN":True}

def original_gate():
    ans={"status":"NOT_OPENED","original_species_abundances_UNSCORED":True,
         "original_env_final_RDS_UNOPENED":True,
         "no_RDS_CSV_rowindex_join_inferred":True,
         "original_2026_Piccini_and_older_scorers_UNTOUCHED":True}
    try:
        manifest,lookup=metadata()
        ans["publisher_provenance"]=manifest
    except SourceStop as e:
        ans["status"]=str(e)
        ans["SOURCE_ACCESS_STOP_not_ecological_null"]=True
        return ans
    attempts=[("stickies_final.csv",anonymous_csv_firstline,"csv_header"),
              ("README.md",anonymous_readme,"readme_method")]
    for filename,parser,key in attempts:
        href=lookup[filename]["_links"]["stash:download"]["href"]
        try:
            raw,status=one_file_small_source(href,filename)
            ans[key]={"http_status":status,**parser(raw)}
        except SourceStop as exc:
            ans[key]={"status":str(exc)}
            ans["status"]="SOURCE_FILE_ACCESS_OR_HEADER_STOP_NOT_ECOLOGICAL_NULL"
            return ans
    ans["status"]="SOURCE_HEADER_README_ONLY_MATRIX_ENV_JOIN_NOT_YET_VERIFIED_NO_BIOLOGY"
    return ans

def known_truth():
    meta={
       "identifier":"doi:"+DOI,"visibility":"public","license":"cc0"}
    f={"_embedded":{"stash:files":[
      {"path":n,"size":30,"digest":"a"*64,
       "digestType":"sha-256",
       "_links":{"stash:download":{"href":"/api/v2/files/123/download"}}}
       for n in sorted(EXPECTED)]},"total":3}
    m,x=extract_file_manifest(meta,{"versionNumber":1},f)
    assert m["original_three_files_sha256_present"] and len(x)==3
    assert m["publisher_visibility"]=="public"
    test=anonymous_csv_firstline(("code,"+(",".join("S"+str(i)
              for i in range(198)))+"\n").encode())
    assert test["source_original_csv_firstline_column_count"]==199
    assert test["first_header_generic_sample_ID_lexeme_if_whitelisted"]=="code"
    assert test["source_matrix_rows_read"]==0
    r=anonymous_readme(b"code, time_exp, locality, run and exposure. Matrix 800 rows.\n")
    assert r["allowed_original_method_word_occurrences"]["code"]==1
    assert not r["readme_keyword_counts_DO_NOT_PROVE_ROW_ID_JOIN"] is False
    try:safe_href("/api/v2/files/../secret")
    except SourceStop:pass
    else:raise AssertionError("unsafe file API href accepted")
    print("SYNTHETIC_SBARAGLIA2025_THREE_FILE_SOURCE_HEADER_AND_ROW_JOIN_FIREWALL_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    out={"schema":"structural.Sbaraglia2025_deadwood_sunshade_10site_source_only.v1",
       "precommit":"docs/FOREST_BEETLE_SBARAGLIA2025_SUN_SHADE_HOST_FUNGAL_ORIGINAL_SOURCE_GATE_PRESPEC_20261117.md",
       "original":original_gate(),
       "original_biodiversity_effect_computed":False,
       "prior_Finland_Burner_Piccini_Thai_PREDICTS_NEON_BALA_GEB_SEALED":True,
       "no_eBird_or_TinyFish":True}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Sbaraglia2025_original_three_file_sourceonly.json").write_text(
        json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
