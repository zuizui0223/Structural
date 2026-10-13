#!/usr/bin/env python3
"""v1.238: archived Dryad public WEB download path, checksum-gated only.

Distinct from API 401 stop of v1.237. Same version 354268; same five
file IDs, bytes and SHA256. No biological record parsed in this gate.
"""
import argparse,csv,hashlib,io,json,urllib.request,urllib.error
from pathlib import Path

def exact_routes(file_id):
    if not isinstance(file_id,int) or file_id<=0:
        raise ValueError("File ID must be a source-verified positive integer")
    return (
        f"https://datadryad.org/downloads/file_stream/{file_id}",
        f"https://datadryad.org/stash/downloads/file_stream/{file_id}"
    )

def interpret_header(raw):
    line=raw.splitlines()[0]
    try:first=line.decode("utf-8-sig")
    except UnicodeDecodeError:first=line.decode("latin-1")
    delim=max(("\t",";",","),key=lambda c:first.count(c))
    parts=next(csv.reader(io.StringIO(first),delimiter=delim))
    cols=[s.strip().strip('"') for s in parts]
    if len(cols)<=1 or len(cols)!=len(set(cols)):
        raise ValueError("Tabular headers not identifiable without source code")
    return {"delimiter":"TAB" if delim=="\t" else delim,"columns":cols,"n_columns":len(cols)}

def get_verified(name,item):
    # Only advertised public UI file_stream endpoints predeclared in contract.
    attempts=[]
    for url in exact_routes(item["file_id"]):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"StructuralEcology/1.238"})
            with urllib.request.urlopen(req,timeout=40) as response:
                body=response.read(item["bytes"]+1)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
            attempts.append({"route":url.split("/file_stream")[0],
                             "error_type":type(e).__name__,
                             "status":getattr(e,"code",None)})
            continue
        if len(body)!=item["bytes"]:
            attempts.append({"route":url.split("/file_stream")[0],
                             "issue":"downloaded byte-size mismatch"})
            continue
        if hashlib.sha256(body).hexdigest()!=item["sha256"]:
            attempts.append({"route":url.split("/file_stream")[0],
                             "issue":"public-route content did not match frozen SHA256"})
            continue
        return body,attempts
    return None,attempts

def main():
    p=argparse.ArgumentParser()
    p.add_argument("contract",type=Path);p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if c["schema"]!="structural.helgeland_pedigree_published_web_download_contract.v1_238":
        raise ValueError("Wrong source contract")
    ids=c["source"]["file_ids"]
    sha=c["source"]["sha256"];size=c["source"]["bytes"]
    if len(ids)!=5 or set(ids)!=set(sha) or set(ids)!=set(size):
        raise ValueError("Pinned file set changed")
    result={
      "schema":"structural.helgeland_public_web_same_bytes_headers.v1_238",
      "status":"SOURCE_ACCESS_NOT_YET_ATTEMPTED",
      "source_DOI":c["source"]["DOI"],
      "source_version_id":c["source"]["version_id"],
      "raw_record_rows_interpreted":0,
      "verified_files":{},
      "download_failures":{},
      "new_confirmatory_systems":0,
      "GEB_scientific_HOLD":True,
      "eBird_used":False
    }
    for name in sorted(ids):
        item={"file_id":ids[name],"sha256":sha[name],"bytes":size[name]}
        raw,attempts=get_verified(name,item)
        if raw is None:
            result["download_failures"][name]=attempts
            result["status"]="STOP_PUBLIC_SOURCE_TRANSPORT_NOT_VERIFIED"
            break
        file_record={"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
                    "public_transport_original_bytes_verified":True}
        if name.endswith(".txt"):
            file_record["header"]=interpret_header(raw)
        else:
            # README is documentation, not user-level observations.
            doc=raw.decode("utf-8-sig")
            terms=("natal.island","adult.island","lastobs.island","dam","sire","recruit")
            file_record["readme_field_terms_present"]=[w for w in terms if w.lower() in doc.lower()]
        result["verified_files"][name]=file_record
    else:
        result["status"]="PASS_SAME_VERSION_FIVE_PUBLIC_FILES_SHA256_HEADERS_ONLY"
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
