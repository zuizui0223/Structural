#!/usr/bin/env python3
"""Correct the already-frozen v1.68 header manifest using frozen row-name evidence.

No response file is downloaded or read. The v1.68 header has 5,394 species
names; v1.20 independently established that a data row has 5,395 fields:
one source-local row ID plus 5,394 binary occurrence values.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_corrected_physical_schema_contract_v1_69.json"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def species_fp(names:list[str])->str:
    h=hashlib.sha256()
    for name in names:
        h.update(name.encode("utf-8")); h.update(b"\n")
    return h.hexdigest()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("v168_manifest",type=Path)
    ap.add_argument("v168_receipt",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output-manifest",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_corrected_physical_schema_contract.v1_69":
            raise Stop("contract schema drift")
        ev=c["frozen_evidence"]["v168_header_artifact"]
        if sha(a.v168_manifest)!=ev["header_manifest_sha256"]: raise Stop("v1.68 manifest SHA drift")
        if sha(a.v168_receipt)!=ev["header_receipt_sha256"]: raise Stop("v1.68 receipt SHA drift")
        old=json.loads(a.v168_receipt.read_text())
        if old.get("total_header_fields")!=5394: raise Stop("v1.68 header field-count drift")
        if old.get("data_record_routing_fields_decoded")!=0: raise Stop("v1.68 exceeded header-only boundary")
        with a.v168_manifest.open("r",encoding="utf-8",newline="") as h:
            rows=list(csv.DictReader(h))
        if len(rows)!=5394: raise Stop("v1.68 manifest row-count drift")
        names=[str(r["header_string"]) for r in rows]
        if any(not n.strip() for n in names): raise Stop("blank species header")
        if len(set(names))!=len(names): raise Stop("duplicate species header")
        if names[0]!="Cephalophus.adersi": raise Stop("first header identity drift")
        fp=species_fp(names)
        if fp!=c["physical_schema"]["corrected_species_order_sha256"]:
            raise Stop("corrected species-order fingerprint drift")

        a.output_manifest.parent.mkdir(parents=True,exist_ok=True)
        with a.output_manifest.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n")
            w.writerow(["species_index","data_column_index","species_name"])
            for j,name in enumerate(names):
                w.writerow([j,j+2,name])

        result={
          "schema":"structural.global_mammals_corrected_physical_schema_result.v1_69",
          "status":"CORRECTED_ROWNAME_SCHEMA_FROZEN_WITHOUT_RESPONSE_ACCESS",
          "header_fields":len(names),
          "species_count":len(names),
          "data_record_fields":len(names)+1,
          "routing_data_column_index":1,
          "first_species_data_column_index":2,
          "last_species_data_column_index":len(names)+1,
          "first_species_name":names[0],
          "last_species_name":names[-1],
          "species_order_sha256":fp,
          "corrected_manifest_sha256":sha(a.output_manifest),
          "response_downloaded":False,
          "data_record_fields_decoded":0,
          "occurrence_values_decoded":0,
          "same_v165_protocol_retry_authorized":False,
          "new_exploratory_lineage_may_continue":True,
          "counts_as_empirical_evidence":False
        }; code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.global_mammals_corrected_physical_schema_result.v1_69",
          "status":"STOP",
          "reason":str(e),
          "response_downloaded":False,
          "occurrence_values_decoded":0,
          "same_v165_protocol_retry_authorized":False,
          "counts_as_empirical_evidence":False
        }; code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__": raise SystemExit(main())
