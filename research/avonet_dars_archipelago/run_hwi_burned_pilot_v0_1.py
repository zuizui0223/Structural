#!/usr/bin/env python3
"""Spend only the frozen DARs bird burned-pilot matrices on estimability checks.

This runner deliberately does NOT calculate HWI-occupancy Spearman rho, fit the
second-stage model, inspect confirmatory matrices, or contribute predictive
evidence. Any failed pilot consumes protocol v0.1.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

DARS_REPO="txm676/DARs"
DARS_COMMIT="8b381ff26e3d6f4da17730dda0c5ab7dbad12eed"
TRAIT_PATH="Data/Species_datasets/Traits_all_species_PublVer.csv"

def sha(value)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return x

def fetch_raw(path:str)->bytes:
    url=f"https://raw.githubusercontent.com/{DARS_REPO}/{DARS_COMMIT}/"+quote(path,safe="/")
    req=Request(url,headers={"User-Agent":"Structural-AVONET-DARs-burned-pilot/0.1"})
    with urlopen(req,timeout=180) as response:
        return response.read()

def parse_number(x):
    try:
        return float(x)
    except (TypeError,ValueError):
        return None

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--partition",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--trait",type=Path,required=True)
    ap.add_argument("--lock",type=Path,required=True)
    ap.add_argument("--raw-dir",type=Path,required=True)
    args=ap.parse_args()

    part=load(args.partition); protocol=load(args.protocol)
    trait_receipt=load(args.trait); lock=load(args.lock)

    if lock.get("schema")!="structural.avonet_dars_hwi_pre_response_lock.v0_1":
        raise RuntimeError("unexpected bird lock schema")
    if lock.get("status")!="FROZEN_QUALIFIED_BEFORE_PILOT_RESPONSE":
        raise RuntimeError("bird lock not qualified")
    if lock.get("response_values_accessed") is not False:
        raise RuntimeError("bird lock already records response access")
    if lock.get("pilot_response_authorized") is not True:
        raise RuntimeError("bird lock does not authorize exact pilot response")
    if lock.get("confirmatory_response_authorized") is not False:
        raise RuntimeError("bird lock unexpectedly authorizes confirmatory response")
    if protocol.get("protocol_fingerprint")!=lock.get("protocol_fingerprint"):
        raise RuntimeError("protocol fingerprint drift")
    if part.get("partition_fingerprint")!=lock.get("partition_fingerprint"):
        raise RuntimeError("partition fingerprint drift")
    if trait_receipt.get("trait_fingerprint")!=lock.get("trait_fingerprint"):
        raise RuntimeError("trait fingerprint drift")
    if protocol.get("status")!="FROZEN_BEFORE_BURNED_PILOT_RESPONSE":
        raise RuntimeError("protocol not frozen")
    if protocol.get("pilot_response_opened") is not False:
        raise RuntimeError("protocol already records pilot response")
    if protocol.get("confirmatory_response_opened") is not False:
        raise RuntimeError("confirmatory response already opened")
    if protocol["burned_pilot_gate"].get("effect_or_rho_computation_allowed") is not False:
        raise RuntimeError("pilot evidence ceiling drift")
    if protocol["burned_pilot_gate"].get("model_fit_allowed") is not False:
        raise RuntimeError("pilot model-fit ceiling drift")

    # Reacquire the exact response-independent trait predictor.
    trait_raw=fetch_raw(TRAIT_PATH)
    if hashlib.sha256(trait_raw).hexdigest()!=trait_receipt["source"]["sha256"]:
        raise RuntimeError("trait predictor SHA drift")
    if git_blob_sha(trait_raw)!=trait_receipt["source"]["git_blob_sha"]:
        raise RuntimeError("trait predictor Git blob drift")
    trait_rows=list(csv.DictReader(io.StringIO(trait_raw.decode("utf-8-sig"))))
    hwi={}
    for row in trait_rows:
        name=(row.get("Species 2") or "").strip()
        value=parse_number(row.get("Hand-Wing Index"))
        if name and value is not None:
            if name in hwi:
                raise RuntimeError(f"duplicate direct HWI species name: {name}")
            hwi[name]=value

    pilot={r["dataset"]:r for r in part["pilot"]}
    confirm={r["dataset"]:r for r in part["confirmatory"]}
    expected=set(protocol["burned_pilot_gate"]["pilot_datasets"])
    if set(pilot)!=expected:
        raise RuntimeError("pilot membership drift")
    if set(pilot)&set(confirm):
        raise RuntimeError("pilot/confirmatory dataset overlap")

    minimum=protocol["archipelago_endpoint"]["minimum_requirements"]
    args.raw_dir.mkdir(parents=True,exist_ok=True)
    audits=[]
    raw_receipts=[]
    for dataset in sorted(pilot):
        meta=pilot[dataset]
        raw=fetch_raw(meta["response_path"])
        observed_blob=git_blob_sha(raw)
        if observed_blob!=meta["response_blob_sha"]:
            raise RuntimeError(
                f"{dataset}: response blob drift {observed_blob} != {meta['response_blob_sha']}"
            )
        if len(raw)!=int(meta["response_size_bytes"]):
            raise RuntimeError(f"{dataset}: response size drift")
        (args.raw_dir/dataset).write_bytes(raw)

        table=list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
        if len(table)<4 or len(table[0])<2:
            raise RuntimeError(f"{dataset}: malformed matrix")
        width=len(table[0])
        if any(len(row)!=width for row in table):
            raise RuntimeError(f"{dataset}: ragged CSV matrix")
        labels=[row[0].strip() for row in table[1:]]
        if labels[-2:]!=["Area (ha)","sp.r"]:
            raise RuntimeError(
                f"{dataset}: expected terminal rows Area (ha), sp.r; observed {labels[-2:]}"
            )
        species_rows=table[1:-2]
        island_names=[x.strip() for x in table[0][1:]]
        n_islands=len(island_names)
        if len(set(island_names))!=n_islands or any(not x for x in island_names):
            raise RuntimeError(f"{dataset}: invalid/duplicate island labels")

        species_names=[]
        matched=[]
        variable=0
        occ_values=set()
        unique_hwi=set()
        nonbinary_cells=0
        duplicate_species=0
        seen=set()
        for row in species_rows:
            name=row[0].strip()
            if not name:
                raise RuntimeError(f"{dataset}: blank species row label")
            if name in seen:
                duplicate_species+=1
            seen.add(name)
            species_names.append(name)
            values=[]
            for cell in row[1:]:
                v=parse_number(cell)
                if v not in (0.0,1.0):
                    nonbinary_cells+=1
                values.append(v)
            if any(v not in (0.0,1.0) for v in values):
                continue
            if name in hwi:
                occupancy=sum(values)/n_islands
                matched.append(name)
                occ_values.add(occupancy)
                unique_hwi.add(hwi[name])
                if 0.0<occupancy<1.0:
                    variable+=1

        if nonbinary_cells:
            raise RuntimeError(f"{dataset}: nonbinary species-incidence cells={nonbinary_cells}")
        if duplicate_species:
            raise RuntimeError(f"{dataset}: duplicate species rows={duplicate_species}")

        total_species=len(species_rows)
        coverage=(len(matched)/total_species) if total_species else 0.0
        checks={
            "islands":n_islands>=int(minimum["islands"]),
            "HWI_matched_species":len(matched)>=int(minimum["HWI_matched_species"]),
            "HWI_match_coverage":coverage>=float(minimum["HWI_match_coverage"]),
            "variable_occupancy_species":variable>=int(minimum["variable_occupancy_species"]),
            "distinct_occupancy_fractions":len(occ_values)>=int(minimum["distinct_occupancy_fractions"]),
            "unique_HWI_values":len(unique_hwi)>=int(minimum["unique_HWI_values"]),
        }
        passed=all(checks.values())
        audits.append({
            "dataset":dataset,
            "Type_V_fine":meta["Type_V_fine"],
            "extreme_isolation_q75":bool(meta["extreme_isolation_q75"]),
            "response_path":meta["response_path"],
            "response_blob_sha":observed_blob,
            "response_bytes":len(raw),
            "n_islands":n_islands,
            "n_species_rows":total_species,
            "HWI_matched_species":len(matched),
            "HWI_match_coverage":coverage,
            "variable_occupancy_species":variable,
            "distinct_occupancy_fractions":len(occ_values),
            "unique_HWI_values":len(unique_hwi),
            "checks":checks,
            "dataset_pass":passed,
            "rho":None,
            "effect_size":None,
        })
        raw_receipts.append({
            "dataset":dataset,
            "git_blob_sha":observed_blob,
            "bytes":len(raw),
            "sha256":hashlib.sha256(raw).hexdigest(),
        })

    passing=[x for x in audits if x["dataset_pass"]]
    oceanic_pass=any(x["dataset_pass"] and x["Type_V_fine"]=="Oceanic" for x in audits)
    shelf_pass=any(x["dataset_pass"] and x["Type_V_fine"]=="C.Shelf" for x in audits)
    study_pass=len(passing)>=4 and oceanic_pass and shelf_pass

    out={
        "schema":"structural.avonet_dars_hwi_burned_pilot.v0_1",
        "status":"PILOT_PASS_ESTIMABILITY_ONLY" if study_pass else "TERMINAL_STOP_NON_ESTIMABLE",
        "protocol_fingerprint":protocol["protocol_fingerprint"],
        "partition_fingerprint":part["partition_fingerprint"],
        "trait_fingerprint":trait_receipt["trait_fingerprint"],
        "pre_response_lock_sha256":sha(lock),
        "response_access":{
            "pilot_response_opened":True,
            "pilot_matrix_queries":len(audits),
            "confirmatory_response_opened":False,
            "confirmatory_matrix_queries":0,
        },
        "evidence_ceiling":{
            "rho_computed":False,
            "model_fits":0,
            "effect_size":None,
            "prediction_score":None,
            "predictive_denominator_contribution":0,
        },
        "pilot_audits":audits,
        "passing_datasets":len(passing),
        "oceanic_pilot_passed":oceanic_pass,
        "continental_shelf_pilot_passed":shelf_pass,
        "pilot_pass":study_pass,
        "confirmatory_response_authorized":study_pass,
        "raw_pilot_receipts":raw_receipts,
        "raw_pilot_receipts_sha256":sha(raw_receipts),
        "terminal_rule":(
            "if pilot_pass=false: do not retune HWI, endpoint, minimum requirements, "
            "pilot membership, q75 or confirmatory panel; never open confirmatory matrices under v0.1"
        ),
    }
    out["pilot_receipt_sha256"]=sha(out)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if study_pass else 2

if __name__=="__main__":
    raise SystemExit(main())
