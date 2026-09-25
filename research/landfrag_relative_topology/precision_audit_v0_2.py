#!/usr/bin/env python3
"""Response-blind precision audit for the frozen LandFrag v0.2 design.

Uses only frozen predictor matrices. No abundance response is opened. The unit-
residual variance calculations are design diagnostics, not power guarantees.
"""
from __future__ import annotations
from collections import defaultdict
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np

TARGET="direct_x_gain"
Z975=1.959963984540054
Z80=0.8416212335729143

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path):
    x=json.loads(Path(path).read_text())
    if not isinstance(x,dict): raise RuntimeError("census must be object")
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--census",type=Path,required=True)
    a=ap.parse_args()
    x=load(a.census)
    if x.get("schema")!="structural.landfrag_relative_topology_metadata.v0_2":
        raise RuntimeError("unexpected census schema")
    if x.get("status")!="QUALIFIED_RESPONSE_SEALED_V0_2":
        raise RuntimeError("v0.2 census not qualified")
    if x.get("response_values_accessed") is not False or x.get("abundance_file_opened") is not False:
        raise RuntimeError("response already opened")

    cols=x["geometry_rules"]["model_columns"]
    target_idx=cols.index(TARGET)
    studies={}
    by_cluster=defaultdict(list)
    for study in x["studies"]:
        X=np.asarray([r["design"] for r in study["focal_rows"]],dtype=float)
        xtx=X.T@X
        inv=np.linalg.inv(xtx)
        var=float(inv[target_idx,target_idx])
        sd=math.sqrt(var)
        row={
            "refshort":study["refshort"],
            "cluster":study["geography_cluster"],
            "n_focals":study["n_focals"],
            "unit_residual_target_variance":var,
            "unit_residual_target_se":sd,
        }
        studies[study["refshort"]]=row
        by_cluster[study["geography_cluster"]].append(row)

    clusters={}
    for cid,rows in sorted(by_cluster.items()):
        k=len(rows)
        # Perfect positive correlation among studies in the same geography is
        # the conservative variance bound for their equal-weight mean.
        se_bound=sum(r["unit_residual_target_se"] for r in rows)/k
        clusters[cid]={
            "studies":[r["refshort"] for r in rows],
            "n_studies":k,
            "perfect_correlation_unit_residual_se_bound":se_bound,
        }

    G=len(clusters)
    global_se=math.sqrt(
        sum(v["perfect_correlation_unit_residual_se_bound"]**2 for v in clusters.values())
    )/G
    halfwidth=Z975*global_se
    mde80=(Z975+Z80)*global_se
    payload={
        "schema":"structural.landfrag_relative_topology_precision.v0_2",
        "status":"RESPONSE_BLIND_DESIGN_PRECISION_AUDIT",
        "response_values_accessed":False,
        "census_fingerprint":x["census_fingerprint"],
        "study_count":len(studies),
        "geography_cluster_count":G,
        "assumption":"within-study standardized response residual SD=1; study target estimates in the same geography treated as perfectly positively correlated; geography clusters treated independent",
        "interpretation":"algebraic design precision proxy only; observed residual/spatial structure may differ and no response-dependent power retuning is authorized",
        "global_unit_residual_target_se_bound":global_se,
        "unit_residual_95pct_halfwidth":halfwidth,
        "unit_residual_two_sided_alpha05_power80_mde":mde80,
        "studies":studies,
        "clusters":clusters,
    }
    fingerprint_core={
        "schema":"structural.landfrag_relative_topology_precision_identity.v0_2",
        "census_fingerprint":x["census_fingerprint"],
        "target":TARGET,
        "study_count":len(studies),
        "geography_cluster_count":G,
        "cluster_membership":{
            cid:clusters[cid]["studies"] for cid in sorted(clusters)
        },
        "algorithm":{
            "study_variance":"target diagonal of inverse(X'X) under unit residual variance",
            "within_geography":"perfect positive correlation conservative SE bound for equal-study mean",
            "across_geography":"independent equal-geography mean",
            "z975":Z975,
            "z80":Z80,
        },
        "rounded_global_summary_12dp":{
            "se_bound":round(global_se,12),
            "halfwidth_95":round(halfwidth,12),
            "mde_alpha05_power80":round(mde80,12),
        },
    }
    payload["precision_fingerprint_semantics"]={
        "excludes":"full-precision per-study/per-cluster floating diagnostics because LAPACK/BLAS may differ at machine precision",
        "includes":"census identity, target, cluster membership, algorithm constants and 12-decimal global design-precision summary",
    }
    payload["precision_fingerprint_core"]=fingerprint_core
    payload["precision_fingerprint"]=sha(fingerprint_core)
    print(json.dumps(payload,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
