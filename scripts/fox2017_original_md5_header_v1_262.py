#!/usr/bin/env python3
"""Fox 2017 original pinned Dryad MD5 byte source / headers only.

Try exactly original publisher-owned URLs. No imitation data, alternate version,
precomputed biological scores or treatment-level semantic response reading.
"""
import argparse,csv,hashlib,io,json,urllib.error,urllib.request
from pathlib import Path

ORIGINAL={
    "README_for_data_for_Fox_et_el_2017_nature_ee.txt":
        {"id":29821,"bytes":1440,"md5":"b25b2ddd88e046ac58849a20a549e9e7"},
    "data_for_Fox_et_el_2017_nature_ee.csv":
        {"id":29820,"bytes":323814,"md5":"a39aec4a41c5fcb301203ee56f922b89"},
}
DOI="10.5061/dryad.2rs23"
VERSION=5720
def approved_urls(file_id):
    if not isinstance(file_id,int) or file_id<=0:raise ValueError("Invalid source file ID")
    return (
        f"https://datadryad.org/api/v2/files/{file_id}/download",
        f"https://datadryad.org/downloads/file_stream/{file_id}",
        f"https://datadryad.org/stash/downloads/file_stream/{file_id}",
    )
def fetched_bytes(name,meta):
    attempts=[]
    for url in approved_urls(meta["id"]):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"StructuralEcology/1.262"})
            with urllib.request.urlopen(req,timeout=25) as rsp:
                b=rsp.read(meta["bytes"]+1)
        except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError) as e:
            attempts.append({"original_publisher_route":url,"http_status":getattr(e,"code",None),
                             "exception_type":type(e).__name__})
            continue
        digest=hashlib.md5(b).hexdigest()
        if len(b)!=meta["bytes"] or digest!=meta["md5"]:
            attempts.append({"original_publisher_route":url,"verified":False,
                             "reason":"published_Md5_or_byte_size_mismatch"})
            continue
        return b,attempts
    return None,attempts
def header_only(b):
    line=b.splitlines()[0].decode("utf-8-sig",errors="replace")
    delim=max(("\t",";",","),key=lambda d:line.count(d))
    fields=next(csv.reader(io.StringIO(line),delimiter=delim))
    if not fields or len(fields)!=len(set(fields)):
        raise ValueError("Source header unavailable or duplicated")
    return {"fields":[x.strip().strip('"') for x in fields],
            "delimiter":"tab" if delim=="\t" else delim,
            "numerical_rows_parsed":0}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result={
        "schema":"structural.fox2017_hydra_exact_original_headers.v1_262",
        "source_DOI":DOI,"source_version_ID":VERSION,
        "status":"STOP_NO_ORIGINAL_BYTES_AVAILABLE",
        "file_IDs_and_MD5":ORIGINAL,"original_validated_file_headers":{},
        "original_public_source_access_failures":{},
        "numeric_biological_response_rows_decoded":0,
        "data_not_equivalent_to_independent_mechanism_confirmation":True,
        "GEB_scientific_HOLD":True,"eBird_used":False
    }
    for name,meta in sorted(ORIGINAL.items()):
        raw,failures=fetched_bytes(name,meta)
        if raw is None:
            result["original_public_source_access_failures"][name]=failures
            continue
        if name.endswith(".csv"):
            result["original_validated_file_headers"][name]=header_only(raw)
        else:
            doc=raw.decode("utf-8-sig",errors="replace")
            result["original_validated_file_headers"][name]={
                "readme_documentation":doc,
                "no_experimental_rows_decoded":True
            }
    if len(result["original_validated_file_headers"])==len(ORIGINAL):
        result["status"]="PASS_TWO_EXACT_MD5_ORIGINAL_FILES_README_AND_CSV_HEADER_ONLY"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
