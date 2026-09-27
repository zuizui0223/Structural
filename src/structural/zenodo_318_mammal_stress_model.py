"""Deterministic pre-heldout model freeze for the 318-island mammal stress test.

This module consumes only:
- the already-consumed 65-island burned-pilot surface + frozen species list;
- the response-independent safe island design.

It must be run before any 244-island heldout occurrence value is opened.
NumPy is imported lazily only by the one-shot fitting function.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import io
import math
from collections import defaultdict
from typing import Iterable, Mapping, Sequence


class MammalStressModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class FrozenFit:
    columns: tuple[str, ...]
    coefficients: tuple[float, ...]
    iterations: int
    final_max_abs_delta: float


CONTINUOUS = (
    "Anntemp_promedio",
    "Annprec_promedio",
    "Elev_max",
)
LOG1P_CONTINUOUS = (
    "Area_km2",
    "dContinent_km",
    "distance_biggerLandmass",
)


def parse_safe_design(csv_text: str) -> list[dict[str, str]]:
    rows=list(csv.DictReader(io.StringIO(csv_text)))
    if not rows:
        raise MammalStressModelError("safe design is empty")
    ids=[r["ID"] for r in rows]
    if len(ids)!=len(set(ids)):
        raise MammalStressModelError("duplicate safe-design ID")
    return rows


def parse_burned_pilot(
    csv_text: str,
    *,
    pilot_order: Sequence[str],
    species: Sequence[str],
) -> dict[str, tuple[int, ...]]:
    rows=list(csv.DictReader(io.StringIO(csv_text)))
    if not rows or tuple(rows[0].keys())!=("partition_unit","block","target"):
        raise MammalStressModelError("unexpected burned-pilot schema")
    n_species=len(species)
    out: dict[str,list[int]]={str(i):[] for i in pilot_order}
    for row in rows:
        iid=row["block"]
        if row["partition_unit"]!=iid or iid not in out:
            raise MammalStressModelError("pilot row outside frozen island order")
        if row["target"] not in {"0","1"}:
            raise MammalStressModelError("pilot target is not binary")
        out[iid].append(int(row["target"]))
    if any(len(out[i])!=n_species for i in out):
        raise MammalStressModelError("pilot island does not have full fixed species universe")
    return {i:tuple(out[i]) for i in pilot_order}


def matrix_bitstrings(
    matrix: Mapping[str, Sequence[int]],
    *,
    pilot_order: Sequence[str],
) -> dict[str,str]:
    result={}
    for iid in pilot_order:
        bits="".join(str(int(v)) for v in matrix[str(iid)])
        if set(bits)-{"0","1"}:
            raise MammalStressModelError("nonbinary compact pilot matrix")
        result[str(iid)]=format(int(bits or "0",2), f"0{(len(bits)+3)//4}x")
    return result


def matrix_from_bitstrings(
    bitstrings: Mapping[str,str],
    *,
    pilot_order: Sequence[str],
    species_count: int,
) -> dict[str,tuple[int,...]]:
    out={}
    width=(species_count+3)//4
    for iid in pilot_order:
        h=bitstrings[str(iid)]
        if len(h)!=width:
            raise MammalStressModelError("pilot bitstring hex width mismatch")
        bits=bin(int(h,16))[2:].zfill(width*4)[-species_count:]
        out[str(iid)]=tuple(int(ch) for ch in bits)
    return out


def raw_surface_text(
    matrix: Mapping[str, Sequence[int]],
    *,
    pilot_order: Sequence[str],
) -> str:
    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow(["partition_unit","block","target"])
    for iid in pilot_order:
        for y in matrix[str(iid)]:
            w.writerow([str(iid),str(iid),str(int(y))])
    return out.getvalue()


def population_mean_sd(values: Sequence[float]) -> tuple[float,float]:
    n=len(values)
    if not n:
        raise MammalStressModelError("empty standardization vector")
    mean=sum(values)/n
    var=sum((x-mean)**2 for x in values)/n
    sd=math.sqrt(var)
    if not math.isfinite(sd) or sd<=0:
        raise MammalStressModelError("zero/nonfinite pilot population SD")
    return mean,sd


def _logit(p: float) -> float:
    if not 0<p<1:
        raise MammalStressModelError("logit input outside (0,1)")
    return math.log(p/(1-p))


def _sigmoid(x: float) -> float:
    if x>=0:
        return 1/(1+math.exp(-x))
    e=math.exp(x)
    return e/(1+e)


def freeze_transform_spec(
    safe_rows: Sequence[Mapping[str,str]],
    *,
    pilot_order: Sequence[str],
) -> dict:
    by_id={str(r["ID"]):r for r in safe_rows}
    pilot=[by_id[str(i)] for i in pilot_order]
    levels=tuple(sorted({r["Archipielago"] for r in pilot}))
    if not levels:
        raise MammalStressModelError("no pilot archipelago levels")
    transforms={}
    for col in CONTINUOUS:
        vals=[float(r[col]) for r in pilot]
        mu,sd=population_mean_sd(vals)
        transforms[col]={"mean":mu,"sd":sd,"transform":"identity"}
    for col in LOG1P_CONTINUOUS:
        vals=[math.log1p(float(r[col])) for r in pilot]
        mu,sd=population_mean_sd(vals)
        transforms[col]={"mean":mu,"sd":sd,"transform":"log1p"}
    return {
        "archipelago_levels":list(levels),
        "continuous":transforms,
        "type_encoding":{"Connected":0.0,"Isolated":1.0},
        "categorical_encoding":"full_one_hot_sorted_levels",
        "intercept_penalized":False,
        "all_nonintercept_coefficients_penalized":True,
    }


def island_base_vector(row: Mapping[str,str], spec: Mapping) -> tuple[float,...]:
    values=[1.0]
    arch=row["Archipielago"]
    levels=spec["archipelago_levels"]
    if arch not in levels:
        raise MammalStressModelError(f"unseen archipelago level: {arch}")
    values.extend(1.0 if arch==a else 0.0 for a in levels)
    for col in CONTINUOUS:
        t=spec["continuous"][col]
        values.append((float(row[col])-t["mean"])/t["sd"])
    for col in LOG1P_CONTINUOUS:
        t=spec["continuous"][col]
        values.append((math.log1p(float(row[col]))-t["mean"])/t["sd"])
    typ=row["Type"]
    if typ not in spec["type_encoding"]:
        raise MammalStressModelError(f"unexpected Type: {typ}")
    values.append(float(spec["type_encoding"][typ]))
    return tuple(values)


def base_column_names(spec: Mapping) -> tuple[str,...]:
    return (
        ("intercept",)
        + tuple(f"Archipielago={x}" for x in spec["archipelago_levels"])
        + tuple(f"z_{x}" for x in CONTINUOUS)
        + tuple(f"z_log1p_{x}" for x in LOG1P_CONTINUOUS)
        + ("Type_Isolated",)
    )


def source_metrics(
    matrix: Mapping[str,Sequence[int]],
    safe_rows: Sequence[Mapping[str,str]],
    *,
    pilot_order: Sequence[str],
    species_count: int,
) -> dict:
    by_id={str(r["ID"]):r for r in safe_rows}
    global_counts=[0]*species_count
    arch_ids: dict[str,list[str]]=defaultdict(list)
    for iid in pilot_order:
        vals=matrix[str(iid)]
        if len(vals)!=species_count:
            raise MammalStressModelError("species count mismatch")
        for j,y in enumerate(vals):
            global_counts[j]+=int(y)
        arch_ids[by_id[str(iid)]["Archipielago"]].append(str(iid))
    arch_counts={}
    for arch,ids in arch_ids.items():
        c=[0]*species_count
        for iid in ids:
            for j,y in enumerate(matrix[iid]):
                c[j]+=int(y)
        arch_counts[arch]=c
    return {
        "global_counts":global_counts,
        "archipelago_pilot_island_ids":{k:list(v) for k,v in sorted(arch_ids.items())},
        "archipelago_counts":{k:arch_counts[k] for k in sorted(arch_counts)},
    }


def _training_rows(
    matrix: Mapping[str,Sequence[int]],
    safe_rows: Sequence[Mapping[str,str]],
    *,
    pilot_order: Sequence[str],
    transform_spec: Mapping,
    extreme_threshold: float,
):
    by_id={str(r["ID"]):r for r in safe_rows}
    species_count=len(next(iter(matrix.values())))
    metrics=source_metrics(
        matrix,safe_rows,pilot_order=pilot_order,species_count=species_count
    )
    global_counts=metrics["global_counts"]
    arch_counts=metrics["archipelago_counts"]
    arch_ids=metrics["archipelago_pilot_island_ids"]
    rows_r3=[]
    rows_c=[]
    y=[]
    for iid in pilot_order:
        row=by_id[str(iid)]
        base=island_base_vector(row,transform_spec)
        arch=row["Archipielago"]
        n_arch=len(arch_ids[arch])
        for j,target in enumerate(matrix[str(iid)]):
            g=_logit((global_counts[j]-target+0.5)/(len(pilot_order)))
            w=_logit((arch_counts[arch][j]-target+0.5)/(n_arch))
            extreme=1.0 if float(row["dContinent_km"])>=extreme_threshold else 0.0
            rows_r3.append(base+(g,))
            rows_c.append(base+(g,w,w*extreme))
            y.append(int(target))
    return rows_r3,rows_c,y,metrics


def fit_ridge_logistic_numpy(
    X_rows: Sequence[Sequence[float]],
    y_values: Sequence[int],
    *,
    columns: Sequence[str],
    ridge_lambda: float=1.0,
    max_iterations: int=100,
    tolerance: float=1e-8,
) -> FrozenFit:
    import numpy as np

    X=np.asarray(X_rows,dtype=np.float64)
    y=np.asarray(y_values,dtype=np.float64)
    if X.ndim!=2 or X.shape[0]!=y.shape[0] or X.shape[1]!=len(columns):
        raise MammalStressModelError("fit matrix shape mismatch")
    beta=np.zeros(X.shape[1],dtype=np.float64)
    penalty=np.ones(X.shape[1],dtype=np.float64)
    penalty[0]=0.0
    final_delta=float("inf")
    for iteration in range(1,max_iterations+1):
        eta=X@beta
        mu=np.empty_like(eta)
        pos=eta>=0
        mu[pos]=1.0/(1.0+np.exp(-eta[pos]))
        ex=np.exp(eta[~pos])
        mu[~pos]=ex/(1.0+ex)
        weights=mu*(1.0-mu)
        grad=X.T@(y-mu)-ridge_lambda*penalty*beta
        hessian=(X.T*weights)@X+ridge_lambda*np.diag(penalty)
        try:
            delta=np.linalg.solve(hessian,grad)
        except np.linalg.LinAlgError as exc:
            raise MammalStressModelError("IRLS linear solve failed") from exc
        beta=beta+delta
        final_delta=float(np.max(np.abs(delta)))
        if final_delta<=tolerance:
            return FrozenFit(
                columns=tuple(columns),
                coefficients=tuple(float(x) for x in beta),
                iterations=iteration,
                final_max_abs_delta=final_delta,
            )
    raise MammalStressModelError("IRLS did not converge")


def build_and_fit(
    *,
    matrix: Mapping[str,Sequence[int]],
    safe_rows: Sequence[Mapping[str,str]],
    pilot_order: Sequence[str],
    extreme_threshold: float,
):
    transform=freeze_transform_spec(safe_rows,pilot_order=pilot_order)
    base=base_column_names(transform)
    r3_rows,c_rows,y,metrics=_training_rows(
        matrix,safe_rows,pilot_order=pilot_order,
        transform_spec=transform,extreme_threshold=extreme_threshold
    )
    r3_cols=base+("pilot_global_occupancy_logit",)
    c_cols=r3_cols+(
        "pilot_within_archipelago_source_logit",
        "pilot_within_archipelago_source_logit_x_extreme_q75",
    )
    r3=fit_ridge_logistic_numpy(r3_rows,y,columns=r3_cols)
    c=fit_ridge_logistic_numpy(c_rows,y,columns=c_cols)
    return transform,metrics,r3,c


def prediction_surface(
    *,
    species: Sequence[str],
    safe_rows: Sequence[Mapping[str,str]],
    pilot_matrix: Mapping[str,Sequence[int]],
    pilot_order: Sequence[str],
    heldout_order: Sequence[str],
    transform_spec: Mapping,
    metrics: Mapping,
    r3_fit: FrozenFit,
    c_fit: FrozenFit,
    extreme_threshold: float,
    probability_clip: tuple[float,float]=(1e-12,0.999999999999),
) -> str:
    by_id={str(r["ID"]):r for r in safe_rows}
    global_counts=metrics["global_counts"]
    arch_counts=metrics["archipelago_counts"]
    arch_ids=metrics["archipelago_pilot_island_ids"]
    n_global=len(pilot_order)
    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow([
        "island_id","species","p_R3_hex","p_C_hex",
        "extreme_q75","archipelago","type"
    ])
    lo,hi=probability_clip
    for iid in heldout_order:
        row=by_id[str(iid)]
        base=island_base_vector(row,transform_spec)
        arch=row["Archipielago"]
        if arch not in arch_ids:
            raise MammalStressModelError(f"heldout archipelago lacks pilot source: {arch}")
        n_arch=len(arch_ids[arch])
        extreme=1.0 if float(row["dContinent_km"])>=extreme_threshold else 0.0
        for j,sp in enumerate(species):
            g=_logit((global_counts[j]+0.5)/(n_global+1))
            source=_logit((arch_counts[arch][j]+0.5)/(n_arch+1))
            xr3=base+(g,)
            xc=base+(g,source,source*extreme)
            eta3=sum(a*b for a,b in zip(xr3,r3_fit.coefficients))
            etac=sum(a*b for a,b in zip(xc,c_fit.coefficients))
            p3=min(hi,max(lo,_sigmoid(eta3)))
            pc=min(hi,max(lo,_sigmoid(etac)))
            w.writerow([
                str(iid),sp,float(p3).hex(),float(pc).hex(),
                int(extreme),arch,row["Type"]
            ])
    return out.getvalue()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def float_hex_mapping(x):
    if isinstance(x,float):
        return x.hex()
    if isinstance(x,dict):
        return {k:float_hex_mapping(v) for k,v in x.items()}
    if isinstance(x,list):
        return [float_hex_mapping(v) for v in x]
    if isinstance(x,tuple):
        return [float_hex_mapping(v) for v in x]
    return x
