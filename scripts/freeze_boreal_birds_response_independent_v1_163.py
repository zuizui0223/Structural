#!/usr/bin/env python3
"""Canonical response-independent freeze for the boreal-bird sparse-topology test."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NULL_SCRIPT=ROOT/"scripts/freeze_boreal_birds_topology_nulls_v1_161.py"
TOPO_SCRIPT=ROOT/"scripts/freeze_boreal_birds_topology_residual_sensitivity_v1_162.py"

class Freeze163Error(RuntimeError):
    pass

def sha_text(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise Freeze163Error(f"cannot load {path.name}")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def freeze(*,freeze_parent_sha:str,request_commit_sha:str):
    for label,value in (("freeze_parent_sha",freeze_parent_sha),("request_commit_sha",request_commit_sha)):
        value=str(value).strip()
        if len(value)!=40 or any(c not in "0123456789abcdef" for c in value.lower()):
            raise Freeze163Error(f"invalid {label}")

    nullmod=load_module(NULL_SCRIPT,"boreal_bird_null_v161")
    topomod=load_module(TOPO_SCRIPT,"boreal_bird_topo_v162")

    ensemble_text,raw_surface_text,null_receipt_text=nullmod.run(
        nullmod.CONTRACT,
        nullmod.GEOMETRY,
        nullmod.GEOMETRY_FREEZE,
        nullmod.SPATIAL_FREEZE,
        nullmod.OPERATOR_FREEZE,
    )
    topo_surface_text,topo_receipt_text=topomod.freeze(
        topomod.DESIGN,
        topomod.GEOMETRY,
    )

    ensemble=json.loads(ensemble_text)
    null_receipt=json.loads(null_receipt_text)
    topo_receipt=json.loads(topo_receipt_text)

    if ensemble.get("status")!="RESPONSE_INDEPENDENT_NULL_ENSEMBLE_FROZEN":
        raise Freeze163Error("null ensemble did not freeze")
    if null_receipt.get("bird_response_values_opened")!=0:
        raise Freeze163Error("null response boundary violated")
    if topo_receipt.get("status")!="TOPOLOGY_RESIDUAL_SENSITIVITY_FROZEN_RESPONSE_INDEPENDENTLY":
        raise Freeze163Error("topology-residual surface did not freeze")
    if topo_receipt.get("bird_response_values_opened")!=0:
        raise Freeze163Error("topology-residual response boundary violated")
    if len(ensemble.get("nulls",[]))!=20:
        raise Freeze163Error("null count drift")
    if topo_receipt.get("row_count")!=78 or topo_receipt.get("H_topo_unique_count")!=13:
        raise Freeze163Error("topology-residual support drift")

    children={
        "null_ensemble":{
            "path":"development/boreal_birds_topology_null_ensemble_v1_163.json",
            "sha256":sha_text(ensemble_text),
            "ensemble_fingerprint":ensemble["ensemble_fingerprint"],
            "null_count":20,
        },
        "raw_configuration_surface":{
            "path":"development/boreal_birds_configuration_sensitivity_v1_163.csv",
            "sha256":sha_text(raw_surface_text),
            "role":"nonprimary response-free diagnostic after v1.162",
        },
        "topology_residual_surface":{
            "path":"development/boreal_birds_topology_residual_sensitivity_v1_163.csv",
            "sha256":sha_text(topo_surface_text),
            "role":"primary pre-response mechanism surface",
            "H_topo_min_hex":topo_receipt["H_topo_min_hex"],
            "H_topo_max_hex":topo_receipt["H_topo_max_hex"],
            "H_topo_unique_count":topo_receipt["H_topo_unique_count"],
        },
        "null_child_receipt":{
            "sha256":sha_text(null_receipt_text),
        },
        "topology_child_receipt":{
            "sha256":sha_text(topo_receipt_text),
        },
    }
    fingerprint_payload={
        "candidate_id":"lac_la_ronge_boreal_19island_birds_sparse_topology_2026",
        "freeze_parent_sha":freeze_parent_sha,
        "request_commit_sha":request_commit_sha,
        "children":children,
    }
    freeze_fingerprint=hashlib.sha256(
        json.dumps(fingerprint_payload,sort_keys=True,separators=(",",":")).encode("utf-8")
    ).hexdigest()

    receipt={
        "schema":"structural.boreal_birds_response_independent_freeze.v1_163",
        "status":"CANONICAL_RESPONSE_INDEPENDENT_FREEZE",
        **fingerprint_payload,
        "freeze_fingerprint":freeze_fingerprint,
        "generation":{
            "null_contract":"development/boreal_birds_topology_null_contract_v1_161.json",
            "null_generator":"scripts/freeze_boreal_birds_topology_nulls_v1_161.py",
            "topology_residual_design":"development/boreal_birds_topology_residual_preintake_v1_162.json",
            "topology_residual_generator":"scripts/freeze_boreal_birds_topology_residual_sensitivity_v1_162.py",
            "legacy_moving_branch_v1_161_run_is_canonical":False,
        },
        "response_boundary":{
            "bird_file_opened":False,
            "bird_header_opened":False,
            "bird_response_values_opened":0,
            "beetle_response_used":False,
            "plant_response_used":False,
            "pilot_response_authorized":False,
            "confirmatory_response_authorized":False,
            "counts_as_empirical_evidence":False,
        },
        "next_action":"build a separately committed one-shot bird pilot router exact-bound to this freeze fingerprint",
    }
    return (
        ensemble_text,
        raw_surface_text,
        topo_surface_text,
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",
    )

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--freeze-parent-sha",required=True)
    ap.add_argument("--request-commit-sha",required=True)
    ap.add_argument("--ensemble",type=Path,required=True)
    ap.add_argument("--raw-surface",type=Path,required=True)
    ap.add_argument("--topology-surface",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        outputs=freeze(
            freeze_parent_sha=a.freeze_parent_sha,
            request_commit_sha=a.request_commit_sha,
        )
    except Exception as exc:
        result={
            "schema":"structural.boreal_birds_response_independent_freeze.v1_163",
            "status":"STOP",
            "reason":str(exc),
            "bird_response_values_opened":0,
            "pilot_response_authorized":False,
            "confirmatory_response_authorized":False,
            "counts_as_empirical_evidence":False,
        }
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2,sort_keys=True))
        return 2

    for path,text in zip((a.ensemble,a.raw_surface,a.topology_surface,a.receipt),outputs):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding="utf-8")
    print(outputs[-1],end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
