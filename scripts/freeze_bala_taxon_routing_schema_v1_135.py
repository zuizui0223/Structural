#!/usr/bin/env python3
"""Freeze BALA Occurrence schema and deterministic MF taxon partition rule.

Reads only the previously frozen meta_manifest.json. It does not open or decode
any occurrence.txt data row.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_taxon_routing_contract_v1_135.json"

class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def field_map(ext:dict)->dict[str,int]:
    return {str(x["name"]):int(x["index"]) for x in ext["fields"]}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--meta-manifest",type=Path,required=True)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--partition-spec",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.bala_taxon_routing_contract.v1_135":
            raise Stop("contract schema drift")
        src=c["frozen_schema_source"]
        if sha(a.meta_manifest)!=src["meta_manifest_sha256"]:
            raise Stop("meta manifest SHA drift")
        meta=json.loads(a.meta_manifest.read_text())
        exts=[x for x in meta.get("extensions",[]) if str(x.get("rowType","")).endswith("/Occurrence")]
        if len(exts)!=1: raise Stop("Occurrence extension resolution failed")
        ext=exts[0]
        if ext.get("location")!=src["occurrence_location"]: raise Stop("Occurrence location drift")
        if ext.get("rowType")!=src["rowType"]: raise Stop("Occurrence rowType drift")
        if ext.get("encoding")!=src["encoding"]: raise Stop("Occurrence encoding drift")
        if ext.get("fieldsTerminatedBy")!="\\t": raise Stop("Occurrence delimiter drift")
        if int(ext.get("ignoreHeaderLines",-1))!=1: raise Stop("Occurrence header-line rule drift")
        if int(ext.get("coreid_index",-1))!=0: raise Stop("Occurrence coreid index drift")

        fmap=field_map(ext)
        required=c["required_occurrence_fields_from_meta_xml"]
        for name,spec in required.items():
            if name=="event_core_link":
                continue
            if name not in fmap: raise Stop(f"missing required Occurrence field: {name}")
            if fmap[name]!=int(spec["index"]):
                raise Stop(f"Occurrence field index drift: {name}")

        p=c["deterministic_partition"]
        if p["hash"]!="SHA-256": raise Stop("unexpected hash")
        if p["pilot_buckets"]!=[0] or p["confirmatory_buckets"]!=[1,2,3]:
            raise Stop("partition bucket drift")
        spec={
          "schema":"structural.bala_taxon_partition_spec.v1_135",
          "status":"MF_TAXON_PARTITION_RULE_FROZEN_BEFORE_OCCURRENCE_ROW_ACCESS",
          "candidate_id":c["candidate_id"],
          "routing_field":"identificationRemarks",
          "routing_field_index":fmap["identificationRemarks"],
          "coreid_index":0,
          "hash":"SHA-256",
          "salt":p["salt"],
          "hash_input":p["hash_input"],
          "bucket_rule":p["bucket_rule"],
          "pilot_buckets":[0],
          "confirmatory_buckets":[1,2,3],
          "normalization":c["taxon_token_normalization"],
          "authorized_decode_during_opaque_routing":["identificationRemarks"],
          "forbidden_decode_during_opaque_routing":[
            "coreid/eventID link","organismQuantity","eventID","scientificName",
            "order","family","taxonRank"
          ],
          "occurrence_data_rows_decoded":0,
          "taxon_tokens_opened":0
        }
        a.partition_spec.parent.mkdir(parents=True,exist_ok=True)
        a.partition_spec.write_text(json.dumps(spec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        result={
          "schema":"structural.bala_taxon_routing_schema_result.v1_135",
          "status":"BALA_OCCURRENCE_SCHEMA_AND_MF_PARTITION_RULE_FROZEN_RESPONSE_UNOPENED",
          "occurrence_extension_location":ext["location"],
          "occurrence_field_count":len(ext["fields"]),
          "routing_field":"identificationRemarks",
          "routing_field_index":fmap["identificationRemarks"],
          "eventID_index":fmap["eventID"],
          "organismQuantity_index":fmap["organismQuantity"],
          "scientificName_index":fmap["scientificName"],
          "order_index":fmap["order"],
          "family_index":fmap["family"],
          "taxonRank_index":fmap["taxonRank"],
          "partition_spec_sha256":sha(a.partition_spec),
          "occurrence_data_rows_decoded":0,
          "taxon_tokens_opened":0,
          "event_by_taxon_rows_parsed":0,
          "taxon_occurrence_values_opened":0,
          "source_loss_effects_computed":0,
          "confirmatory_eligible":False,
          "next_gate":"execute one opaque MF-only row routing pass; persist pilot row bytes and a sealed confirmatory byte surface without decoding confirmatory event/quantity/taxonomy fields"
        }
        code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={
          "schema":"structural.bala_taxon_routing_schema_result.v1_135",
          "status":"STOP","reason":str(e),
          "occurrence_data_rows_decoded":0,"taxon_tokens_opened":0,
          "event_by_taxon_rows_parsed":0,"taxon_occurrence_values_opened":0,
          "source_loss_effects_computed":0,"confirmatory_eligible":False
        }
        code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
