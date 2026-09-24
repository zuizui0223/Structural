#!/usr/bin/env python3
"""Freeze DARs bird archipelago evidence partitions before species matrices open."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SALT="structural-avonet-dars-pilot-v1"

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise RuntimeError(f"{path} must contain object")
    return x

def sha(x)->str:
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def h(path):
    return hashlib.sha256(f"{SALT}|{path}".encode()).hexdigest()

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--census",type=Path,required=True)
    a=p.parse_args()
    x=load(a.census)

    if x.get("response_values_accessed") is not False:
        raise RuntimeError("response already accessed")
    if x["true_island_response_surface"].get("content_opened") is not False:
        raise RuntimeError("true-island matrices were opened")

    files={row["path"].split("/")[-1]:row for row in x["true_island_response_surface"]["files"]}
    pred=x["response_blind_predictor_surface"]["predictor_content"]["rows"]
    rows=[]
    for row in pred:
        name=row["Dataset"]
        if name not in files:
            raise RuntimeError(f"predictor row has no frozen response file: {name}")
        rows.append({
            "dataset":name,
            "response_path":files[name]["path"],
            "response_blob_sha":files[name]["blob_sha"],
            "response_size_bytes":files[name]["size"],
            "Type_V_fine":row["Type_V_fine"],
            "Type_fine2":row["Type_fine2"],
            "Iso":float(row["Iso"]),
            "MeanDist":float(row["MeanDist"]),
            "Bio1_m":float(row["Bio1_m"]),
            "Bio12_m":float(row["Bio12_m"]),
            "pilot_hash":h(files[name]["path"]),
        })

    marine=[r for r in rows if r["Type_fine2"]=="Marine"]
    inland=[r for r in rows if r["Type_fine2"]!="Marine"]
    oceanic=sorted([r for r in marine if r["Type_V_fine"]=="Oceanic"],key=lambda r:r["pilot_hash"])
    shelf=sorted([r for r in marine if r["Type_V_fine"]=="C.Shelf"],key=lambda r:r["pilot_hash"])
    hybrid=sorted([r for r in marine if r["Type_V_fine"]=="C.Shelf / Atoll"],key=lambda r:r["pilot_hash"])

    if len(oceanic)!=10 or len(shelf)!=10 or len(hybrid)!=1 or len(inland)!=4:
        raise RuntimeError(
            f"unexpected response-blind type counts: oceanic={len(oceanic)} "
            f"shelf={len(shelf)} hybrid={len(hybrid)} inland={len(inland)}"
        )

    pilot=oceanic[:2]+shelf[:2]+hybrid
    pilot_names={r["dataset"] for r in pilot}
    confirm=[r for r in marine if r["dataset"] not in pilot_names and r["Type_V_fine"] in {"Oceanic","C.Shelf"}]
    out_scope=inland

    if sum(r["Type_V_fine"]=="Oceanic" for r in confirm)!=8:
        raise RuntimeError("confirmatory Oceanic count not 8")
    if sum(r["Type_V_fine"]=="C.Shelf" for r in confirm)!=8:
        raise RuntimeError("confirmatory C.Shelf count not 8")

    ranked=sorted(marine,key=lambda r:(-r["Iso"],r["dataset"]))
    n_extreme=math.ceil(0.25*len(ranked))
    extreme={r["dataset"] for r in ranked[:n_extreme]}
    for r in rows:
        r["extreme_isolation_q75"]=r["dataset"] in extreme

    pilot=sorted(pilot,key=lambda r:r["dataset"])
    confirm=sorted(confirm,key=lambda r:r["dataset"])
    out_scope=sorted(out_scope,key=lambda r:r["dataset"])
    confirm_extreme=sum(r["extreme_isolation_q75"] for r in confirm)
    confirm_nonextreme=len(confirm)-confirm_extreme

    payload={
        "schema":"structural.avonet_dars_partition.v0_1",
        "status":"RESPONSE_SEALED_PARTITIONS_FROZEN",
        "source_fingerprint":x["source_fingerprint"],
        "response_values_accessed":False,
        "response_matrix_content_opened":False,
        "eligibility":{
            "primary_scope":"marine true-island datasets only",
            "marine_rule":"Type_fine2 == Marine",
            "H2_primary_classes":["Oceanic","C.Shelf"],
            "hybrid_role":"burned pilot geometry/schema stress only; not confirmatory H2",
            "inland_role":"out of scope for the marine-island primary; remains unopened",
        },
        "isolation":{
            "metric":"DARs predictor Iso at archipelago/dataset level",
            "primary_rule":"upper 25% of the 21 frozen marine archipelago Iso values",
            "n_eligible_archipelagos":len(marine),
            "n_extreme_archipelagos":n_extreme,
            "extreme_dataset_names":sorted(extreme),
            "threshold_is_rank_based":True,
        },
        "pilot_selection":{
            "rule":"two lowest deterministic SHA256 ranks within Oceanic + two within C.Shelf + the single C.Shelf/Atoll hybrid",
            "salt":SALT,
            "uses_response_values":False,
            "pilot_count":len(pilot),
        },
        "pilot":pilot,
        "confirmatory":confirm,
        "out_of_scope_unopened":out_scope,
        "confirmatory_counts":{
            "total":len(confirm),
            "Oceanic":sum(r["Type_V_fine"]=="Oceanic" for r in confirm),
            "C.Shelf":sum(r["Type_V_fine"]=="C.Shelf" for r in confirm),
            "extreme_q75":confirm_extreme,
            "nonextreme_q75":confirm_nonextreme,
        },
        "response_surface_fingerprints":{
            "pilot":sha([(r["response_path"],r["response_blob_sha"]) for r in pilot]),
            "confirmatory":sha([(r["response_path"],r["response_blob_sha"]) for r in confirm]),
            "out_of_scope":sha([(r["response_path"],r["response_blob_sha"]) for r in out_scope]),
        },
        "pilot_response_authorized":False,
        "confirmatory_response_authorized":False,
    }
    payload["partition_fingerprint"]=sha(payload)
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
