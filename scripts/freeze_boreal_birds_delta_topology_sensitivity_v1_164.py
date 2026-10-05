#!/usr/bin/env python3
"""Freeze actual-minus-null topology-residual sensitivity for boreal birds."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NULL_SCRIPT=ROOT/"scripts/freeze_boreal_birds_topology_nulls_v1_161.py"
DESIGN=ROOT/"development/boreal_birds_delta_topology_preintake_v1_164.json"

class DeltaTopologyError(RuntimeError):
    pass

def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise DeltaTopologyError(f"cannot load {path.name}")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_json(path:Path)->dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise DeltaTopologyError("JSON object required")
    return value

def edge_set(rows)->set[tuple[str,str]]:
    out=set()
    for row in rows:
        left=str(row["left"]);right=str(row["right"])
        if left==right:
            raise DeltaTopologyError("self edge")
        out.add(tuple(sorted((left,right))))
    return out

def graph_H(mod,ids,edges,dist,target,sources,lam):
    adjacency=mod.adj(ids,edges,dist)
    shortest=mod.dijkstra(target,adjacency)
    q=[]
    for source in sources:
        d_graph=shortest[source]
        d_euclid=float(dist[tuple(sorted((target,source)))])
        if d_graph+1e-10<d_euclid:
            raise DeltaTopologyError("graph path shorter than Euclidean distance")
        q.append(math.exp(-(d_graph-d_euclid)/lam))
    mu=math.fsum(q)/len(q)
    sigma2=math.fsum((x-mu)**2 for x in q)/len(q)
    if mu<=0.0:
        raise DeltaTopologyError("nonpositive topology-residual mean")
    return sigma2/(mu*mu)

def render(rows:list[dict])->str:
    cols=["target","n","M","H_actual_hex","H_null_mean_hex","delta_H_hex","delta_S_topo_hex"]
    return ",".join(cols)+"\n"+"\n".join(",".join(str(r[c]) for c in cols) for r in rows)+"\n"

def freeze(design_path:Path=DESIGN):
    design=load_json(design_path)
    if design.get("schema")!="structural.boreal_birds_delta_topology_preintake.v1_164":
        raise DeltaTopologyError("unexpected v1.164 design schema")
    if design["response_boundary"]["bird_response_values_opened"]!=0:
        raise DeltaTopologyError("bird response boundary drift")

    mod=load_module(NULL_SCRIPT,"birdnull161_delta")
    ensemble_text,_,_=mod.run(
        mod.CONTRACT,
        mod.GEOMETRY,
        mod.GEOMETRY_FREEZE,
        mod.SPATIAL_FREEZE,
        mod.OPERATOR_FREEZE,
    )
    ensemble=json.loads(ensemble_text)
    expected_parent=design["parent_hash_freeze"]
    if hashlib.sha256(ensemble_text.encode("utf-8")).hexdigest()!=expected_parent["null_ensemble_expected_sha256"]:
        raise DeltaTopologyError("null ensemble exact replay SHA mismatch")
    if ensemble.get("ensemble_fingerprint")!="ec482ecd2cc359dc09ef4bff0f0ae7bee1c9a418776237d2aa8c77e90b9fd1fe":
        raise DeltaTopologyError("null ensemble fingerprint mismatch")

    xy=mod.geometry(mod.GEOMETRY)
    ids=tuple(sorted(xy))
    dist=mod.pairwise_distances(xy)
    sources=tuple(json.loads(mod.CONTRACT.read_text())["configuration_sensitivity"]["possible_sources"])
    targets=tuple(json.loads(mod.CONTRACT.read_text())["configuration_sensitivity"]["targets"])
    lam=float.fromhex(ensemble["kernel_scale_km_hex"])
    actual=edge_set(ensemble["actual_edges"])
    nulls=[edge_set(row["edges"]) for row in ensemble["nulls"]]

    rows=[];audit=[]
    for target in targets:
        H_actual=graph_H(mod,ids,actual,dist,target,sources,lam)
        H_null=[graph_H(mod,ids,g,dist,target,sources,lam) for g in nulls]
        H_null_mean=math.fsum(H_null)/len(H_null)
        delta_H=H_actual-H_null_mean
        audit.append({
            "target":target,
            "H_actual_hex":H_actual.hex(),
            "H_null_mean_hex":H_null_mean.hex(),
            "delta_H_hex":delta_H.hex(),
            "actual_greater_than_null_mean":delta_H>0.0,
        })
        M=len(sources)
        for n in range(1,M+1):
            factor=(M-n)/(n*(M-1))
            rows.append({
                "target":target,
                "n":n,
                "M":M,
                "H_actual_hex":H_actual.hex(),
                "H_null_mean_hex":H_null_mean.hex(),
                "delta_H_hex":delta_H.hex(),
                "delta_S_topo_hex":(factor*delta_H).hex(),
            })

    text=render(rows)
    observed_sha=hashlib.sha256(text.encode("utf-8")).hexdigest()
    expected_sha=design["response_free_identifiability"]["expected_surface_sha256"]
    if observed_sha!=expected_sha:
        raise DeltaTopologyError("delta topology surface SHA drift")

    delta=[float.fromhex(x["delta_H_hex"]) for x in audit]
    positives=sum(x>0.0 for x in delta)
    if positives!=design["response_free_identifiability"]["targets_with_delta_H_positive"]:
        raise DeltaTopologyError("positive-target count drift")
    if min(delta).hex()!=design["response_free_identifiability"]["delta_H_min_hex"]:
        raise DeltaTopologyError("delta_H minimum drift")
    if max(delta).hex()!=design["response_free_identifiability"]["delta_H_max_hex"]:
        raise DeltaTopologyError("delta_H maximum drift")

    receipt={
        "schema":"structural.boreal_birds_delta_topology_sensitivity_freeze.v1_164",
        "status":"DELTA_TOPOLOGY_SENSITIVITY_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id":design["candidate_id"],
        "surface_sha256":observed_sha,
        "row_count":len(rows),
        "target_count":len(targets),
        "n_values":[1,2,3,4,5,6],
        "targets_with_delta_H_positive":positives,
        "delta_H_min_hex":min(delta).hex(),
        "delta_H_max_hex":max(delta).hex(),
        "target_audit":audit,
        "parent_null_ensemble_sha256":expected_parent["null_ensemble_expected_sha256"],
        "bird_file_opened":False,
        "bird_header_opened":False,
        "bird_response_values_opened":0,
        "pilot_response_authorized":False,
        "confirmatory_response_authorized":False,
        "counts_as_empirical_evidence":False,
        "next_action":"bind the one-shot bird pilot router to this surface SHA and the v1.163 canonical hash freeze",
    }
    return text,json.dumps(receipt,indent=2,sort_keys=True)+"\n"

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--design",type=Path,default=DESIGN)
    ap.add_argument("--surface",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    args=ap.parse_args()
    try:
        surface,receipt=freeze(args.design)
    except Exception as exc:
        result={
            "schema":"structural.boreal_birds_delta_topology_sensitivity_freeze.v1_164",
            "status":"STOP",
            "reason":str(exc),
            "bird_response_values_opened":0,
            "pilot_response_authorized":False,
            "confirmatory_response_authorized":False,
            "counts_as_empirical_evidence":False,
        }
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        args.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2,sort_keys=True))
        return 2
    for path,text in ((args.surface,surface),(args.receipt,receipt)):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding="utf-8")
    print(receipt,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
