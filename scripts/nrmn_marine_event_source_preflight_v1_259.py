#!/usr/bin/env python3
"""Read ONLY AODN/IMOS RLS + ATRC public Arrow _common_metadata schemas.

Network feasibility first; no fish observations, survey rows, human contacts,
original global mammal response, eBird or later holdout probabilities.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import io
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow import fs

FROZEN_SCHEMA="structural.nrmn_marine_event_source_preflight.v1_259"
DATASET_IDS=("survey","fish")
MAX_LEN=5_000_000

class SourceStop(Exception):
    """If source identity/schema not verified, never proceed to outcomes."""


def check_schema(blob:bytes, expected:list[str]) -> dict:
    if not 0 < len(blob)<=MAX_LEN:
        raise SourceStop("Original AODN _common_metadata is empty or exceeds frozen 5MB cap")
    try:
        schema=pq.read_schema(pa.BufferReader(blob))
    except (ValueError,pa.ArrowInvalid,pa.ArrowIOError) as e:
        raise SourceStop(f"Original public source metadata not Arrow parquet schema: {type(e).__name__}") from e
    observed=list(schema.names)
    if len(observed)!=len(set(observed)):
        raise SourceStop("Nonunique source field names")
    absent=sorted(set(expected)-set(observed))
    if absent:
        raise SourceStop(f"Missing schema fields needed for future protected survey join: {absent}")
    if "survey_id" not in observed:
        raise SourceStop("No original survey_id join")
    return {
        "n_fields":len(observed),
        "field_names":observed,
        "field_types":{f.name:str(f.type) for f in schema},
        "expected_fields_all_present":True,
        "join_field":"survey_id",
        "metadata_sidecar_sha256":hashlib.sha256(blob).hexdigest(),
        "metadata_sidecar_bytes":len(blob)
    }


def inspect_one_s3(s3, bucket:str, dataset:str, fields:list[str]):
    # The original publisher notebook explicitly uses this dataset path and
    # sidecar. Access only a small Arrow footer with no biological data rows.
    key=f"{bucket}/{dataset}/_common_metadata"
    info=s3.get_file_info(key)
    if info.type!=fs.FileType.File or not 0<info.size<=MAX_LEN:
        raise SourceStop(f"Unavailable or oversized canonical public S3 parquet _common_metadata: {dataset}")
    with s3.open_input_file(key) as f:
        payload=f.read(MAX_LEN+1)
    out=check_schema(payload,fields)
    out.update({"dataset":dataset,"public_s3_object":f"s3://{bucket}/{dataset}/_common_metadata",
                "declared_sidecar_size":info.size})
    if len(payload)!=info.size:
        raise SourceStop(f"Sidecar changed in transit: {dataset}")
    return out


def audit(contract:dict, inspector=None):
    if contract.get("schema")!=FROZEN_SCHEMA:
        raise SourceStop("Protocol unrecognised")
    authority=contract["authority"]
    if (
        authority["upstream_source_tree_sha"]!="2409b27a9c85d6db5db2885fdc0e48596b448b78"
        or authority["region"]!="ap-southeast-2"
        or authority["s3_endpoint"]!="https://s3.ap-southeast-2.amazonaws.com"
        or authority["bucket"]!="aodn-cloud-optimised"
        or authority["survey_dataset"]!="diver_survey_metadata_qc.parquet"
        or authority["fish_dataset"]!="diver_reef_fish_abundance_biomass_qc.parquet"
    ):
        raise SourceStop("Frozen upstream AODN dataset identity changed")
    if not contract["limits"]["ecological_response_rows_accessed"]==0:
        raise SourceStop("Pre-response firewall modified")
    if inspector is None:
        inspector=fs.S3FileSystem(
            region=authority["region"],
            endpoint_override=authority["s3_endpoint"],
            anonymous=True,
            request_timeout=35)
    d={}
    for kind in DATASET_IDS:
        dataset=authority[f"{kind}_dataset"]
        expected=contract[f"expected_{kind}_fields"]
        d[kind]=inspect_one_s3(inspector,authority["bucket"],dataset,expected)
    if d["survey"]["field_types"]["survey_id"] != d["fish"]["field_types"]["survey_id"]:
        raise SourceStop("Future survey_id linking field has discordant Arrow types")
    return {
        "schema":"structural.nrmn_marine_event_source_attestation.v1_259",
        "status":"PASS_PUBLISHER_PUBLIC_METADATA_ONLY",
        "review_utc":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "upstream_aodn_repo_tree_sha":authority["upstream_source_tree_sha"],
        "source_authority_metadata_uuids":{
            "survey":authority["survey_metadata_uuid"],
            "fish":authority["fish_metadata_uuid"]
        },
        "datasets":d,
        "strict_shared_survey_id_type":d["survey"]["field_types"]["survey_id"],
        "actual_event_date_coverage_from_live_rows":"UNOPENED",
        "actual_multi_island_repeat_networks":"UNESTIMATED",
        "biological_records_opened":0,
        "survey_event_rows_opened":0,
        "fish_species_abundance_rows_opened":0,
        "eBird_used":False,
        "GEB_scientific_HOLD":True,
        "next_stage":"Source-locked survey metadata only: physical event/date/site/program frame before fish species response"
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--contract",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    receipt={
        "schema":"structural.nrmn_marine_event_source_attestation.v1_259",
        "status":"FAIL_CLOSED_BEFORE_BIOLOGICAL_RESPONSE",
        "biological_records_opened":0,
        "survey_event_rows_opened":0,
        "GEB_scientific_HOLD":True
    }
    try:
        receipt=audit(contract)
    except Exception as e:
        receipt["stop_reason"]=f"{type(e).__name__}: {str(e)[:500]}"
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":receipt["status"],
                      "stop_reason":receipt.get("stop_reason"),
                      "schemas_seen":sorted(receipt.get("datasets",{}))},sort_keys=True))
    if receipt["status"]!="PASS_PUBLISHER_PUBLIC_METADATA_ONLY":
        raise SystemExit(2)


if __name__=="__main__":main()
