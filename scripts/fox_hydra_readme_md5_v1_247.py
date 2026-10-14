#!/usr/bin/env python3
"""Fox et al (2017) source README MD5 gate, never accesses biological CSV."""
import argparse,hashlib,json,urllib.request,urllib.error
from pathlib import Path
SOURCE_ID=29821
LENGTH=1440
MD5="b25b2ddd88e046ac58849a20a549e9e7"
def candidate_urls():
    return [
      f"https://datadryad.org/api/v2/files/{SOURCE_ID}/download",
      f"https://datadryad.org/downloads/file_stream/{SOURCE_ID}",
      f"https://datadryad.org/stash/downloads/file_stream/{SOURCE_ID}"
    ]
def verify_source(raw):
    if len(raw)!=LENGTH or hashlib.md5(raw).hexdigest()!=MD5:
        raise ValueError("Original published README MD5 or byte-size mismatch")
    return raw.decode("utf-8-sig",errors="replace")
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    receipt={"schema":"structural.fox_spatial_hydra_original_readme_gate.v1_247",
      "status":"TECHNICAL_STOP_ORIGINAL_README_TRANSPORT",
      "original_Dryad_DOI":"10.5061/dryad.2rs23","source_file_id":SOURCE_ID,
      "source_MD5":MD5,"source_expected_bytes":LENGTH,
      "verified_source_readme":False,"source_readme_documentation":None,
      "source_access_attempts":[],"experimental_observation_rows_opened":0,
      "new_confirmatory_systems":0,"GEB_scientific_HOLD":True,"eBird_used":False}
    for url in candidate_urls():
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"StructuralEcology/1.247"})
            with urllib.request.urlopen(req,timeout=30) as resp:
                raw=resp.read(LENGTH+1)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as exc:
            receipt["source_access_attempts"].append({
                "publisher_route":url,"http_status":getattr(exc,"code",None),
                "error_type":type(exc).__name__})
            continue
        try:
            content=verify_source(raw)
        except ValueError:
            receipt["source_access_attempts"].append({
                "publisher_route":url,"issue":"ORIGINAL_SOURCE_MD5_OR_SIZE_MISMATCH"})
            continue
        receipt["status"]="PASS_ORIGINAL_README_MD5_AND_METHOD_DESCRIPTIONS_ONLY"
        receipt["verified_source_readme"]=True
        lines=content.splitlines()
        receipt["source_readme_documentation"]={
            "n_lines":len(lines),
            "brief_first_lines":[line[:160] for line in lines[:5]],
            "field_related_lines":[{"line":i,"excerpt":line.strip()[:190]}
                for i,line in enumerate(lines,1)
                if any(word in line.lower() for word in
                   ("treatment","patch","replicate","dispers","extinct","day","habitat","column"))
            ][:20]}
        break
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
if __name__=="__main__":main()
