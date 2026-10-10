#!/usr/bin/env python3
"""v1.230 SOURCE-BLIND git blob and header audit, no biology rows semantically parsed.

Author repo is checked out at an exact commit. Read bytes to verify immutable
git-blob SHA-1, then decode ONLY the first header line (never biological rows).
"""
import argparse
import hashlib
import json
from pathlib import Path

def git_blob_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

def inspect_one(path,manifest):
    raw=path.read_bytes()
    if len(raw)!=manifest["bytes"]:
        raise ValueError("File size mismatch, scientific STOP")
    digest=git_blob_sha(raw)
    if digest!=manifest["git_blob_sha1"]:
        raise ValueError("Frozen Git source blob mismatch")
    # The header only: do not split or decode the remainder of the file.
    first=raw[:4096].splitlines()[0]
    fields=[x.strip().strip('"').lstrip("\ufeff")
            for x in first.decode("utf-8-sig").split(";")]
    if not set(manifest["required_header_fields"]).issubset(set(fields)):
        raise ValueError("Declared source schema missing critical fields")
    if len(fields)!=len(set(fields)):
        raise ValueError("Duplicate header field")
    return {
        "git_blob_sha1":digest,"bytes":len(raw),
        "header_fields":fields,
        "required_fields_verified":list(manifest["required_header_fields"]),
        "response_rows_decoded":0,
        "natal_identity_confirmed_from_header":False,
        "observed_directed_migrant_events_confirmed":False
    }

def run(base,contract):
    if contract["schema"]!="structural.helgeland_direct_movement_provenance_preflight.v1_230":
        raise ValueError("Wrong contract")
    if contract["guards"]["biological_response_rows_decoded_in_v230"]!=0:
        raise ValueError("No biological rows authorized")
    results={}
    for spec in contract["authority"]["source_files"]:
        p=base/spec["path"]
        if not p.is_file():
            raise ValueError("Missing exact original author file")
        results[spec["path"]]=inspect_one(p,spec)
    if len(results)!=2:
        raise ValueError("Unexpected source expansion")
    return {
        "schema":"structural.helgeland_source_header_receipt.v1_230",
        "status":"PASS_IMMUTABLE_PUBLISHED_HEADERS_ONLY_NO_EMPIRICAL_ADMISSION",
        "author_repo":contract["authority"]["author_github_repository"],
        "author_commit":contract["authority"]["commit"],
        "files":results,
        "prior_study_overlap":"Ranke et al. 2021 same archipelago as Hansson Frank et al. 2026, not independent replication",
        "island_number_from_published_methods_not_observation_rows":11,
        "archipelago_count":1,
        "potential_individual_ID_and_natal_migration_linkage_only":True,
        "island_level_colonization_events_verified":0,
        "directed_recruitment_success_versus_simple_migrant_presence_unverified":True,
        "source_outcome_rows_decoded":0,
        "estimability_pilot_executed":False,
        "fresh_confirmatory_admission":False,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("checkout",type=Path)
    p.add_argument("contract",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=run(a.checkout,json.loads(a.contract.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
