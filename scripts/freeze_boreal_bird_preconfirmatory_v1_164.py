#!/usr/bin/env python3
"""Freeze boreal-bird R3/actual-C/20-null-C predictions before confirmation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from scripts.freeze_boreal_19island_topology_sensitivity_v1_162 import (
    edge_fingerprint,
    edge_key,
    generate_null,
    load_geometry,
)
from structural.boreal_beetle_pilot_router import decode_binary_vector_hex
from structural.boreal_confirmatory_model import (
    BorealConfirmatoryModelError,
    apply_standardization,
    fit_mapping,
    fit_ridge_logistic,
    freeze_standardization,
    logit_jeffreys,
    predict_probability,
)
from structural.boreal_dual_isolation_operator import (
    freeze_connected_knn_operator,
    source_features,
)
from structural.boreal_spatial_partition import pairwise_distances, type7_quantile

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/boreal_bird_preconfirmatory_contract_v1_164.json"
DEFAULT_TOPOLOGY=ROOT/"development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
DEFAULT_STATE=ROOT/"development/boreal_19island_state_reference_v0_99.csv"
DEFAULT_STATE_FREEZE=ROOT/"development/boreal_19island_state_reference_freeze_v0_99.json"
DEFAULT_GEOMETRY=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv"
DEFAULT_GEOMETRY_FREEZE=ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"
DEFAULT_SPATIAL=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"


class BirdPreconfirmatoryError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise BirdPreconfirmatoryError(f"{path.name} must contain object")
    return value


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def parse_num(value) -> float:
    s=str(value).strip()
    x=float.fromhex(s) if s.lower().startswith(("0x","+0x","-0x")) else float(s)
    if not math.isfinite(x):
        raise BirdPreconfirmatoryError("nonfinite numeric value")
    return x


def load_state(path: Path, freeze: Mapping) -> tuple[list[str],dict[str,dict[str,float]]]:
    if sha256_file(path) != freeze.get("state_reference_sha256"):
        raise BirdPreconfirmatoryError("state reference SHA mismatch")
    rows=list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    header=("Island","PC1","PC2","PC3","TSF_Z","LOG_AREA_Z","LOG_MAINLAND_DISTANCE_Z")
    if tuple(rows[0].keys()) != header:
        raise BirdPreconfirmatoryError("state header drift")
    order=list(freeze["island_order"])
    if [r["Island"] for r in rows] != order:
        raise BirdPreconfirmatoryError("state island order drift")
    data={}
    for r in rows:
        data[r["Island"]]={k:parse_num(r[k]) for k in header if k!="Island"}
    return order,data


def validate_pilot(execution: Mapping,snapshot: Mapping,contract: Mapping):
    gate=contract["execution_gate"]
    if execution.get("status") != gate["required_pilot_execution_status"]:
        raise BirdPreconfirmatoryError("bird pilot execution did not qualify")
    if execution.get("bird_confirmatory_response_opened") is not False:
        raise BirdPreconfirmatoryError("confirmatory bird response already opened")
    if execution.get("confirmatory_values_parsed") != 0:
        raise BirdPreconfirmatoryError("pilot parsed confirmatory bird values")
    if snapshot.get("schema") != gate["required_pilot_snapshot_schema"]:
        raise BirdPreconfirmatoryError("unexpected pilot snapshot schema")
    if snapshot.get("status") != gate["required_pilot_snapshot_status"]:
        raise BirdPreconfirmatoryError("pilot snapshot did not qualify")
    core=dict(snapshot); fp=core.pop("snapshot_fingerprint",None)
    if fp != canonical_sha256(core):
        raise BirdPreconfirmatoryError("pilot snapshot fingerprint mismatch")
    if execution.get("snapshot_fingerprint") != fp:
        raise BirdPreconfirmatoryError("pilot execution/snapshot mismatch")
    species=list(snapshot["fixed_species"])
    if len(species)!=snapshot["fixed_species_count"] or len(species)!=len(set(species)):
        raise BirdPreconfirmatoryError("invalid fixed species universe")
    pilot=list(snapshot["pilot_island_order"])
    encoded=snapshot["targets_hex_by_island"]
    if set(encoded)!=set(pilot):
        raise BirdPreconfirmatoryError("pilot bit-vector identity drift")
    matrix={island:decode_binary_vector_hex(encoded[island],len(species)) for island in pilot}
    n_map={row["species"]:int(row["n"]) for row in snapshot["n_by_species"]}
    if set(n_map)!=set(species):
        raise BirdPreconfirmatoryError("n-by-species identity drift")
    for j,name in enumerate(species):
        if sum(matrix[i][j] for i in pilot)!=n_map[name]:
            raise BirdPreconfirmatoryError("n-by-species does not match pilot bits")
    smean=float.fromhex(snapshot["S_standardization"]["mean_hex"])
    ssd=float.fromhex(snapshot["S_standardization"]["population_sd_hex"])
    if not math.isfinite(ssd) or ssd<=0:
        raise BirdPreconfirmatoryError("invalid frozen S standard deviation")
    return species,pilot,matrix,n_map,smean,ssd


def reconstruct_operators(coords: Mapping, topology: Mapping, contract162: Mapping|None=None):
    actual=freeze_connected_knn_operator(coords)
    if edge_fingerprint(
        {edge_key(e["left"],e["right"]) for e in actual["edges"]},
        lambda a,b: pairwise_distances(coords)[edge_key(a,b)],
    ) != topology["actual_graph"]["edge_fingerprint"]:
        raise BirdPreconfirmatoryError("actual topology fingerprint drift")

    ids=sorted(coords)
    distances=pairwise_distances(coords)
    def distance(a,b):
        return 0.0 if a==b else float(distances[edge_key(a,b)])
    actual_edges={edge_key(e["left"],e["right"]) for e in actual["edges"]}
    lengths=sorted(distance(*e) for e in actual_edges)
    bounds=[type7_quantile(lengths,p) for p in (0.2,0.4,0.6,0.8)]
    def length_bin(v):
        for idx,b in enumerate(bounds):
            if v<=b+1e-12:return idx
        return 4
    nulls=[]
    meta=topology["null_ensemble"]["nulls"]
    for row in meta:
        edges,accepted,_=generate_null(
            actual_edges=actual_edges,ids=ids,distance=distance,
            length_bin=length_bin,seed=int(row["seed"]),
            accepted_swaps_target=int(topology["null_ensemble"]["accepted_swaps_per_null"]),
        )
        fp=edge_fingerprint(edges,distance)
        if fp!=row["edge_fingerprint"] or accepted!=row["accepted_swaps"]:
            raise BirdPreconfirmatoryError("null topology fingerprint drift")
        nulls.append({
            "operator":"matched_rewired_null",
            "island_order":ids,
            "kernel_scale_km":float.fromhex(topology["actual_graph"]["kernel_scale_km_hex"]),
            "edges":[
                {"left":a,"right":b,"distance_km":distance(a,b)}
                for a,b in sorted(edges)
            ],
        })
    if len(nulls)!=20:
        raise BirdPreconfirmatoryError("null count drift")
    return actual,nulls


def source_raw(target,species_index,pilot,matrix,coords,operator,training):
    positives=[i for i in pilot if matrix[i][species_index]==1]
    if training:
        successes=sum(matrix[i][species_index] for i in pilot if i!=target)
        trials=len(pilot)-1
    else:
        successes=len(positives);trials=len(pilot)
    f=source_features(
        target=target,occupied_sources=positives,
        coordinates=coords,operator=operator,
    )
    return {
        "global_occupancy_logit":logit_jeffreys(successes,trials),
        "log1p_nearest_euclidean_source_km":math.log1p(f.nearest_euclidean_km),
        "log1p_euclidean_source_pressure":math.log1p(f.euclidean_source_pressure),
        "log1p_nearest_graph_path_km":math.log1p(f.nearest_graph_path_km),
        "log1p_graph_source_pressure":math.log1p(f.graph_source_pressure),
    }


def csv_text(header:Sequence[str],rows:Sequence[Sequence[object]])->str:
    out=io.StringIO(newline="");w=csv.writer(out,lineterminator="\n")
    w.writerow(list(header));w.writerows(rows);return out.getvalue()


def constants_hex(c):
    return {k:{"mean_hex":float(v["mean"]).hex(),"sd_hex":float(v["sd"]).hex()} for k,v in c.items()}


def freeze(
    *,
    pilot_execution:Mapping,
    pilot_snapshot:Mapping,
    contract:Mapping,
    topology:Mapping,
    state_path:Path,
    state_freeze:Mapping,
    geometry_path:Path,
    geometry_freeze:Mapping,
    spatial:Mapping,
)->tuple[dict,str]:
    if contract.get("schema")!="structural.boreal_bird_preconfirmatory_contract.v1_164":
        raise BirdPreconfirmatoryError("unexpected v1.164 contract schema")
    species,pilot,matrix,n_map,smean,ssd=validate_pilot(
        pilot_execution,pilot_snapshot,contract
    )
    order,state=load_state(state_path,state_freeze)
    coords=load_geometry(geometry_path,geometry_freeze)
    if set(coords)!=set(order):
        raise BirdPreconfirmatoryError("geometry/state universe mismatch")
    if set(pilot)!=set(spatial["pilot_islands"]):
        raise BirdPreconfirmatoryError("pilot geography drift")
    confirm=list(spatial["confirmatory_islands"])
    actual,nulls=reconstruct_operators(coords,topology)

    base_raw={}
    for island in order:
        node=actual["generic_node_context"][island]
        row=dict(state[island])
        row.update({
            "graph_degree_fraction":float(node["degree_fraction"]),
            "graph_mean_shortest_path_km":float(node["mean_shortest_path_km"]),
            "graph_closeness_per_km":float(node["closeness_per_km"]),
        })
        base_raw[island]=row
    base_cols=(
        "PC1","PC2","PC3","TSF_Z","LOG_AREA_Z","LOG_MAINLAND_DISTANCE_Z",
        "graph_degree_fraction","graph_mean_shortest_path_km","graph_closeness_per_km",
    )
    base_const=freeze_standardization([base_raw[i] for i in order],base_cols)

    common_cols=(
        "global_occupancy_logit",
        "log1p_nearest_euclidean_source_km",
        "log1p_euclidean_source_pressure",
    )
    graph_cols=("log1p_nearest_graph_path_km","log1p_graph_source_pressure")

    train_common=[];train_actual=[];train_null=[[] for _ in nulls];records=[];y=[]
    for island in pilot:
        for j,name in enumerate(species):
            a=source_raw(island,j,pilot,matrix,coords,actual,True)
            train_common.append({k:a[k] for k in common_cols})
            train_actual.append({k:a[k] for k in graph_cols})
            nrows=[]
            for ni,op in enumerate(nulls):
                nr=source_raw(island,j,pilot,matrix,coords,op,True)
                train_null[ni].append({k:nr[k] for k in graph_cols})
                nrows.append(nr)
            records.append((island,j,name,a,nrows))
            y.append(int(matrix[island][j]))
    common_const=freeze_standardization(train_common,common_cols)
    actual_const=freeze_standardization(train_actual,graph_cols)
    null_const=[freeze_standardization(rows,graph_cols) for rows in train_null]

    r3_cols=("intercept",)+tuple(f"z_{k}" for k in base_cols)+tuple(f"z_{k}" for k in common_cols)
    c_cols=r3_cols+tuple(f"z_{k}" for k in graph_cols)
    Xr3=[];Xa=[];Xn=[[] for _ in nulls]
    for island,j,name,a,nrows in records:
        zb=apply_standardization(base_raw[island],columns=base_cols,constants=base_const)
        zc=apply_standardization(a,columns=common_cols,constants=common_const)
        r3=(1.0,)+tuple(zb)+tuple(zc)
        za=apply_standardization(a,columns=graph_cols,constants=actual_const)
        Xr3.append(r3);Xa.append(r3+tuple(za))
        for ni,nr in enumerate(nrows):
            zn=apply_standardization(nr,columns=graph_cols,constants=null_const[ni])
            Xn[ni].append(r3+tuple(zn))

    settings=contract["fitting"]
    kwargs=dict(
        ridge_lambda=float(settings["ridge_lambda"]),
        max_iterations=int(settings["max_iterations"]),
        tolerance=float(settings["tolerance"]),
    )
    fit_r3=fit_ridge_logistic(Xr3,y,columns=r3_cols,**kwargs)
    fit_a=fit_ridge_logistic(Xa,y,columns=c_cols,**kwargs)
    fit_n=[fit_ridge_logistic(Xn[i],y,columns=c_cols,**kwargs) for i in range(20)]
    clip=tuple(float(v) for v in settings["probability_clip"])

    header=contract["preconfirmatory_outputs"]["prediction_columns"]
    rows=[]
    targets=topology["configuration_sensitivity"]["targets"]
    for island in confirm:
        block=spatial["island_to_block"][island]
        zb=apply_standardization(base_raw[island],columns=base_cols,constants=base_const)
        for j,name in enumerate(species):
            a=source_raw(island,j,pilot,matrix,coords,actual,False)
            zc=apply_standardization(a,columns=common_cols,constants=common_const)
            r3=(1.0,)+tuple(zb)+tuple(zc)
            za=apply_standardization(a,columns=graph_cols,constants=actual_const)
            pa=predict_probability(r3+tuple(za),fit_a,clip=clip)
            pr3=predict_probability(r3,fit_r3,clip=clip)
            pnull=[]
            for ni,op in enumerate(nulls):
                nr=source_raw(island,j,pilot,matrix,coords,op,False)
                zn=apply_standardization(nr,columns=graph_cols,constants=null_const[ni])
                pnull.append(predict_probability(r3+tuple(zn),fit_n[ni],clip=clip))
            n=n_map[name]
            S=float.fromhex(targets[island]["S_by_n_hex"][str(n)])
            zS=(S-smean)/ssd
            rows.append([
                island,block,name,n,float(S).hex(),float(zS).hex(),
                float(pr3).hex(),float(pa).hex(),
                *[float(p).hex() for p in pnull],
            ])
    text=csv_text(header,rows)
    expected=13*len(species)
    if len(rows)!=expected:
        raise BirdPreconfirmatoryError("prediction row count drift")
    models={
        "R3":fit_mapping(fit_r3),
        "C_actual":fit_mapping(fit_a),
        "C_null":[fit_mapping(f) for f in fit_n],
    }
    receipt={
        "schema":"structural.boreal_bird_preconfirmatory_freeze.v1_164",
        "status":"BIRD_ACTUAL_AND_NULL_PREDICTIONS_FROZEN_BEFORE_CONFIRMATORY_RESPONSE",
        "candidate_id":contract["candidate_id"],
        "pilot_snapshot_fingerprint":pilot_snapshot["snapshot_fingerprint"],
        "fixed_species_count":len(species),
        "training_row_count":len(y),
        "prediction_row_count":len(rows),
        "S_standardization":{
            "mean_hex":float(smean).hex(),
            "population_sd_hex":float(ssd).hex(),
        },
        "base_standardization":constants_hex(base_const),
        "R3_standardization":constants_hex(common_const),
        "actual_C_standardization":constants_hex(actual_const),
        "null_C_standardization":[constants_hex(x) for x in null_const],
        "models":models,
        "models_fingerprint":canonical_sha256(models),
        "prediction_surface_sha256":sha256_text(text),
        "actual_graph_fingerprint":topology["actual_graph"]["edge_fingerprint"],
        "null_graph_fingerprints":[x["edge_fingerprint"] for x in topology["null_ensemble"]["nulls"]],
        "primary_scoring":contract["primary_scoring"],
        "bird_confirmatory_values_opened":0,
        "bird_confirmatory_response_authorized":False,
        "counts_as_empirical_evidence":False,
    }
    return receipt,text


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("pilot_execution",type=Path)
    p.add_argument("pilot_snapshot",type=Path)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--topology",type=Path,default=DEFAULT_TOPOLOGY)
    p.add_argument("--state",type=Path,default=DEFAULT_STATE)
    p.add_argument("--state-freeze",type=Path,default=DEFAULT_STATE_FREEZE)
    p.add_argument("--geometry",type=Path,default=DEFAULT_GEOMETRY)
    p.add_argument("--geometry-freeze",type=Path,default=DEFAULT_GEOMETRY_FREEZE)
    p.add_argument("--spatial",type=Path,default=DEFAULT_SPATIAL)
    p.add_argument("--predictions",type=Path)
    p.add_argument("--receipt",type=Path)
    a=p.parse_args()
    try:
        receipt,text=freeze(
            pilot_execution=load_json(a.pilot_execution),
            pilot_snapshot=load_json(a.pilot_snapshot),
            contract=load_json(a.contract),
            topology=load_json(a.topology),
            state_path=a.state,
            state_freeze=load_json(a.state_freeze),
            geometry_path=a.geometry,
            geometry_freeze=load_json(a.geometry_freeze),
            spatial=load_json(a.spatial),
        )
    except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError,
            BorealConfirmatoryModelError,BirdPreconfirmatoryError) as exc:
        receipt={
            "schema":"structural.boreal_bird_preconfirmatory_freeze.v1_164",
            "status":"STOP",
            "reason":str(exc),
            "bird_confirmatory_values_opened":0,
            "bird_confirmatory_response_authorized":False,
            "counts_as_empirical_evidence":False,
        }
        text=None;code=2
    else:
        code=0
    if text is not None and a.predictions is not None:
        a.predictions.parent.mkdir(parents=True,exist_ok=True)
        a.predictions.write_text(text,encoding="utf-8")
    rendered=json.dumps(receipt,indent=2,sort_keys=True)+"\n"
    if a.receipt is not None:
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        a.receipt.write_text(rendered,encoding="utf-8")
    print(rendered,end="")
    return code


if __name__=="__main__":
    raise SystemExit(main())
