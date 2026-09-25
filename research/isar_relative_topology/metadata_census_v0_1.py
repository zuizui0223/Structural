#!/usr/bin/env python3
"""Freeze response-blind geometry and H1 design for a fresh ISAR synthesis system.

Only the published environmental/metadata table is fetched. No species-abundance
matrix is opened. The final response paths are identified by source commit/path
only and remain sealed.
"""
from __future__ import annotations

from collections import defaultdict, deque
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import numpy as np

SOURCE_REPO="chase-lab/ISAR_synthesis"
SOURCE_COMMIT="4b79a9e0c7fc4b29a6efca534d129a4e4da59fc0"
ENV_PATH="data/env_file_UTF-8.csv"
ENV_GIT_BLOB_SHA="b8d81bff6bcdfbc9da221a08fda95741161af980"
MARINE_TYPES={"True Island","Atoll","Barrier Island"}
MIN_ISLANDS=8
OVERLAP_THRESHOLD=0.80
ROUND_DECIMALS=5
BOOTSTRAP_REPS=10000
BOOTSTRAP_SEED=20260925
MAX_CONDITION=1000.0

def canonical_sha(value)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def fetch_raw(path:str)->bytes:
    url=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/"+quote(path,safe="/")
    req=Request(url,headers={"User-Agent":"Structural-ISAR-relative-topology/0.1"})
    with urlopen(req,timeout=180) as r:
        return r.read()

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return x

def num(x):
    if x in (None,"","NA"):
        return None
    try:
        v=float(x)
    except (TypeError,ValueError):
        return None
    return v if math.isfinite(v) else None

def hav(a,b):
    R=6371.0088
    p1=math.radians(a[0]);p2=math.radians(b[0])
    dp=math.radians(b[0]-a[0]);dl=math.radians(b[1]-a[1])
    z=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1.0,math.sqrt(z)))

def zscore(values):
    a=np.asarray(values,dtype=float)
    mu=float(a.mean());sd=float(a.std(ddof=0))
    if sd<=1e-12:
        raise RuntimeError("response-blind predictor is constant within dataset")
    return (a-mu)/sd,{"mean":mu,"sd":sd}

def geometry(rows):
    ids=[r["island_code"] for r in rows]
    coords=[(float(r["island_lat"]),float(r["island_lon"])) for r in rows]
    n=len(rows)
    D=np.zeros((n,n),dtype=float)
    for i in range(n):
        for j in range(i+1,n):
            D[i,j]=D[j,i]=hav(coords[i],coords[j])
    sums=D.sum(axis=1)
    core=min(range(n),key=lambda i:(float(sums[i]),ids[i]))

    bottleneck=D[core,:].copy()
    bottleneck[core]=0.0
    used=np.zeros(n,dtype=bool)
    for _ in range(n):
        candidates=[i for i in range(n) if not used[i]]
        u=min(candidates,key=lambda i:(float(bottleneck[i]),ids[i]))
        used[u]=True
        for v in range(n):
            if used[v]: continue
            cand=max(float(bottleneck[u]),float(D[u,v]))
            if cand < bottleneck[v]:
                bottleneck[v]=cand

    nn=[];direct=[];gain=[]
    for i in range(n):
        nn.append(min(float(D[i,j]) for j in range(n) if j!=i))
        d=float(D[core,i])
        b=float(bottleneck[i])
        direct.append(d)
        gain.append(max(0.0,math.log1p(d)-math.log1p(b)))

    log_area=[math.log(float(r["island_area_ha"])) for r in rows]
    log_nn=[math.log1p(x) for x in nn]
    log_core=[math.log1p(x) for x in direct]
    z_area,scale_area=zscore(log_area)
    z_nn,scale_nn=zscore(log_nn)
    z_core,scale_core=zscore(log_core)
    z_gain,scale_gain=zscore(gain)
    interaction=z_nn*z_gain
    return {
        "core_island_code":ids[core],
        "scale":{
            "log_area":scale_area,
            "log1p_nearest_neighbor_km":scale_nn,
            "log1p_core_distance_km":scale_core,
            "step_gain_log":scale_gain,
        },
        "rows":[
            {
                "island_code":ids[i],
                "nearest_neighbor_km":nn[i],
                "core_distance_km":direct[i],
                "step_bottleneck_km":float(bottleneck[i]),
                "step_gain_log":gain[i],
                "z_log_area":float(z_area[i]),
                "z_relative_isolation":float(z_nn[i]),
                "z_core_distance":float(z_core[i]),
                "z_step_gain":float(z_gain[i]),
                "topology_x_relative_isolation":float(interaction[i]),
            }
            for i in range(n)
        ],
    }

def coord_set(rows):
    return {
        (round(float(r["island_lat"]),ROUND_DECIMALS),round(float(r["island_lon"]),ROUND_DECIMALS))
        for r in rows
    }

def geography_components(studies):
    ids=sorted(studies)
    sets={sid:coord_set(studies[sid]) for sid in ids}
    adj={sid:set() for sid in ids}
    edges=[]
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            inter=len(sets[a]&sets[b])
            denom=min(len(sets[a]),len(sets[b]))
            frac=inter/denom if denom else 0.0
            if frac>=OVERLAP_THRESHOLD:
                adj[a].add(b);adj[b].add(a)
                edges.append({"a":a,"b":b,"matched_coordinates":inter,"fraction_of_smaller":frac})
    comps=[]
    seen=set()
    for sid in ids:
        if sid in seen: continue
        q=deque([sid]);seen.add(sid);members=[]
        while q:
            u=q.popleft();members.append(u)
            for v in sorted(adj[u]):
                if v not in seen:
                    seen.add(v);q.append(v)
        comps.append(sorted(members))
    comps.sort(key=lambda x:x[0])
    return comps,edges

def weighted_design(final_studies,component_by_study,geometries):
    cols=["z_log_area","z_core_distance","z_relative_isolation","z_step_gain","topology_x_relative_isolation"]
    raw=[];labels=[];datasets=[]
    component_members=defaultdict(list)
    for sid,cid in component_by_study.items():
        component_members[cid].append(sid)
    for sid in sorted(final_studies):
        grows=geometries[sid]["rows"]
        for row in grows:
            raw.append([row[c] for c in cols])
            labels.append(component_by_study[sid])
            datasets.append(sid)
    X=np.asarray(raw,dtype=float)

    # Dataset fixed effects: demean every final predictor column within dataset.
    Xc=X.copy()
    weights=np.zeros(X.shape[0],dtype=float)
    offset=0
    for sid in sorted(final_studies):
        n=len(geometries[sid]["rows"])
        idx=np.arange(offset,offset+n)
        Xc[idx,:]-=X[idx,:].mean(axis=0,keepdims=True)
        cid=component_by_study[sid]
        # Each geography total weight 1; split equally across datasets in that geography,
        # then equally across islands within dataset.
        weights[idx]=1.0/(len(component_members[cid])*n)
        offset+=n
    Xw=Xc*np.sqrt(weights)[:,None]
    rank=int(np.linalg.matrix_rank(Xw,tol=1e-10))
    sv=np.linalg.svd(Xw,compute_uv=False)
    cond=float(sv[0]/sv[-1]) if sv[-1]>1e-15 else float("inf")

    blocks={}
    start=0
    for sid in sorted(final_studies):
        n=len(geometries[sid]["rows"])
        cid=component_by_study[sid]
        blocks.setdefault(cid,[]).append(Xw[start:start+n,:])
        start+=n
    blocks={cid:np.vstack(xs) for cid,xs in blocks.items()}
    return cols,Xw,rank,cond,blocks

def freeze_bootstrap(blocks,ncols):
    clusters=sorted(blocks)
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    accepted=[];attempted=0
    while len(accepted)<BOOTSTRAP_REPS and attempted<BOOTSTRAP_REPS*20:
        attempted+=1
        draw=[clusters[int(i)] for i in rng.integers(0,len(clusters),size=len(clusters))]
        X=np.vstack([blocks[c] for c in draw])
        if np.linalg.matrix_rank(X,tol=1e-10)!=ncols:
            continue
        accepted.append(draw)
    if len(accepted)!=BOOTSTRAP_REPS:
        raise RuntimeError(f"could freeze only {len(accepted)} full-rank cluster draws")
    return {
        "clusters":clusters,
        "replicates":BOOTSTRAP_REPS,
        "seed":BOOTSTRAP_SEED,
        "rng":"numpy.default_rng(PCG64)",
        "candidate_draws_attempted":attempted,
        "accepted_draws_sha256":canonical_sha(accepted),
        "replay_rule":"sample frozen geographic archipelago cluster IDs with replacement; accept only full-rank frozen predictor design; use first 10,000 accepted draws",
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contamination",type=Path,required=True)
    args=ap.parse_args()
    contamination=load(args.contamination)
    if contamination.get("status")!="FROZEN_BEFORE_FRESH_RESPONSE":
        raise RuntimeError("contamination boundary not frozen")
    if contamination.get("response_values_used_for_hypothesis_design") is not False:
        raise RuntimeError("response values entered fresh-system design")

    raw=fetch_raw(ENV_PATH)
    if git_blob_sha(raw)!=ENV_GIT_BLOB_SHA:
        raise RuntimeError("environment metadata Git blob drift")
    try:
        text=raw.decode("utf-8-sig")
        source_encoding="utf-8-sig"
    except UnicodeDecodeError:
        text=raw.decode("cp1252")
        source_encoding="cp1252"
    rows=list(csv.DictReader(io.StringIO(text)))
    if len(rows)!=644:
        raise RuntimeError(f"expected 644 metadata rows, got {len(rows)}")

    by=defaultdict(list)
    for r in rows: by[r["study_ID"]].append(r)

    preeligible={}
    exclusions={}
    for sid,rs in sorted(by.items()):
        reasons=[]
        if not all(r["island_type"] in MARINE_TYPES for r in rs):
            reasons.append("not_all_marine_island_types")
        if len(rs)<MIN_ISLANDS:
            reasons.append("fewer_than_8_islands")
        if not all(num(r["island_lat"]) is not None and num(r["island_lon"]) is not None for r in rs):
            reasons.append("missing_coordinates")
        if not all(num(r["island_area_ha"]) is not None and float(r["island_area_ha"])>0 for r in rs):
            reasons.append("missing_or_nonpositive_area")
        if reasons:
            exclusions[sid]=reasons
        else:
            preeligible[sid]=rs

    components,edges=geography_components(preeligible)
    component_by_study={}
    for idx,members in enumerate(components,1):
        cid=f"G{idx:02d}"
        for sid in members: component_by_study[sid]=cid

    directly=set(contamination["incident"]["directly_opened_study_ids"])
    contaminated_components={
        component_by_study[sid] for sid in directly if sid in component_by_study
    }
    cascade=sorted(
        sid for sid,cid in component_by_study.items()
        if cid in contaminated_components and sid not in directly
    )
    expected=sorted(contamination["expected_cascade_exclusions"])
    if cascade!=expected:
        raise RuntimeError(f"geographic contamination cascade drift: {cascade} != {expected}")

    excluded_response=sorted(
        sid for sid,cid in component_by_study.items()
        if cid in contaminated_components
    )
    final={sid:rs for sid,rs in preeligible.items() if sid not in excluded_response}

    geometries={sid:geometry(rs) for sid,rs in final.items()}
    for sid,g in geometries.items():
        if len(g["rows"])<MIN_ISLANDS:
            raise RuntimeError(f"{sid}: geometry row loss")
        if sum(r["step_gain_log"]>1e-12 for r in g["rows"])<3:
            raise RuntimeError(f"{sid}: insufficient nonzero topology gain")
        if g["scale"]["log1p_nearest_neighbor_km"]["sd"]<=1e-12:
            raise RuntimeError(f"{sid}: no relative-isolation variation")

    final_components=sorted({component_by_study[sid] for sid in final})
    cols,Xw,rank,condition,blocks=weighted_design(final,component_by_study,geometries)
    bootstrap=freeze_bootstrap(blocks,len(cols))
    gates={
        "minimum_10_geographic_archipelagos":len(final_components)>=10,
        "minimum_8_islands_each":all(len(rs)>=8 for rs in final.values()),
        "predictor_design_full_rank":rank==len(cols),
        "condition_number_le_1000":condition<=MAX_CONDITION,
        "bootstrap_10000_full_rank":bootstrap["replicates"]==10000,
    }
    qualified=all(gates.values())

    response_surfaces=[]
    for sid in sorted(final):
        study_names=sorted({r["Study"] for r in final[sid]})
        if len(study_names)!=1:
            raise RuntimeError(f"{sid}: multiple Study file roots")
        root=study_names[0]
        response_surfaces.append({
            "study_ID":sid,
            "geography_cluster":component_by_study[sid],
            "source_path":f"data/ISAR_datasets/{root}.csv",
            "source_commit":SOURCE_COMMIT,
            "opened":False,
        })

    payload={
        "schema":"structural.isar_relative_topology_metadata_census.v0_1",
        "status":"QUALIFIED_RESPONSE_SEALED" if qualified else "STOP_PRE_RESPONSE_NON_ESTIMABLE",
        "source":{
            "repository":SOURCE_REPO,
            "commit":SOURCE_COMMIT,
            "environment_path":ENV_PATH,
            "environment_git_blob_sha":ENV_GIT_BLOB_SHA,
            "environment_sha256":hashlib.sha256(raw).hexdigest(),
            "decoded_as":source_encoding,
            "metadata_rows":len(rows),
        },
        "response_values_accessed":False,
        "abundance_files_opened":False,
        "selection":{
            "marine_types":sorted(MARINE_TYPES),
            "minimum_islands":MIN_ISLANDS,
            "requires_complete_coordinates":True,
            "requires_complete_positive_area":True,
            "preeligible_studies":len(preeligible),
            "preeligible_islands":sum(len(x) for x in preeligible.values()),
            "geography_overlap_threshold":OVERLAP_THRESHOLD,
            "geography_rounding_decimals":ROUND_DECIMALS,
            "direct_response_contaminated_studies":sorted(directly),
            "cascade_response_contaminated_studies":cascade,
            "excluded_response_contaminated_studies":excluded_response,
            "final_studies":len(final),
            "final_islands":sum(len(x) for x in final.values()),
            "final_geographic_archipelagos":len(final_components),
        },
        "geography":{
            "components":[
                {"cluster_id":f"G{i:02d}","studies":members}
                for i,members in enumerate(components,1)
            ],
            "overlap_edges":edges,
            "final_cluster_ids":final_components,
        },
        "predictor_definition":{
            "relative_isolation":"within-dataset z(log1p nearest-neighbor great-circle distance km)",
            "archipelago_core":"geometry medoid: island minimizing summed great-circle distance to all other islands; island_code lexical tie-break",
            "step_bottleneck":"minimum possible largest island-to-island step from the medoid to the focal island in the complete great-circle graph",
            "step_gain":"within-dataset z(log1p direct medoid distance - log1p minimax bottleneck distance), using the nonnegative raw difference before z-scaling",
            "core_distance_control":"within-dataset z(log1p direct distance to geometry medoid km)",
            "area_control":"within-dataset z(log island area ha)",
            "H1_target":"z_step_gain x z_relative_isolation",
            "H1_prediction":"positive",
        },
        "design":{
            "columns":cols,
            "rank":rank,
            "n_columns":len(cols),
            "condition_number":condition,
            "row_count":int(Xw.shape[0]),
            "dataset_fixed_effects":"all final predictor columns demeaned within dataset",
            "geography_weighting":"every geographic archipelago cluster has total weight 1; split equally among datasets in a cluster and equally among islands within each dataset",
            "inference_unit":"geographic archipelago cluster",
            "bootstrap":bootstrap,
        },
        "study_geometry":{
            sid:{
                "geography_cluster":component_by_study[sid],
                "n_islands":len(final[sid]),
                "taxa":sorted({r["Taxa"] for r in final[sid]}),
                "island_type":sorted({r["island_type"] for r in final[sid]}),
                "island_type2":sorted({r["island_type2"] for r in final[sid]}),
                "core_island_code":geometries[sid]["core_island_code"],
                "island_codes":sorted(r["island_code"] for r in final[sid]),
                "fixed_proportional":sorted({r["fixed_proportional"] for r in final[sid]}),
                "nonzero_step_gain_islands":sum(r["step_gain_log"]>1e-12 for r in geometries[sid]["rows"]),
                "scale":geometries[sid]["scale"],
                "geometry_rows":geometries[sid]["rows"],
                "geometry_rows_sha256":canonical_sha(geometries[sid]["rows"]),
            }
            for sid in sorted(final)
        },
        "response_surfaces":response_surfaces,
        "pre_response_gates":gates,
        "response_open_authorized":False,
    }
    payload["fingerprint_semantics"]={
        "identity_excludes":["design.condition_number"],
        "reason":"SVD condition number is a response-blind numerical audit that can vary at machine-precision across BLAS/LAPACK builds; selection, frozen predictors, rank, bootstrap draw set and response surfaces remain identity-bound",
    }
    identity=json.loads(json.dumps(payload))
    identity["design"].pop("condition_number",None)
    payload["census_fingerprint"]=canonical_sha(identity)
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0 if qualified else 2

if __name__=="__main__":
    raise SystemExit(main())
