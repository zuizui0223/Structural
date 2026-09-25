#!/usr/bin/env python3
"""One-shot fresh response execution for the frozen ISAR relative-topology H1."""
from __future__ import annotations

from collections import defaultdict
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import numpy as np

SOURCE_REPO="chase-lab/ISAR_synthesis"
SOURCE_COMMIT="4b79a9e0c7fc4b29a6efca534d129a4e4da59fc0"
EXPECTED_CENSUS="23d726b895845753006c15529871dce89a38e9c93b94d515628a86b5b4a15ec3"
EXPECTED_PROTOCOL="2aa38abac0c706d639e34135373188628e9e9ec63846aa6926c892a8b3e0c285"
LOCK_SCHEMA="structural.isar_relative_topology_pre_response_lock.v0_1"

class ResponseQualityError(RuntimeError):
    pass

def sha(value)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise RuntimeError(f"{path} must contain JSON object")
    return x

def fetch_raw(path:str,attempts:int=8)->bytes:
    url=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/"+quote(path,safe="/")
    last=None
    for attempt in range(attempts):
        try:
            req=Request(url,headers={"User-Agent":"Structural-ISAR-relative-topology-one-shot/0.1"})
            with urlopen(req,timeout=180) as r:
                return r.read()
        except (HTTPError,URLError,TimeoutError) as exc:
            last=exc
            if attempt+1<attempts:
                time.sleep(min(2**attempt,30))
    raise RuntimeError(f"failed source response fetch {path}: {last}")

def decode(raw:bytes)->tuple[str,str]:
    try:
        return raw.decode("utf-8-sig"),"utf-8-sig"
    except UnicodeDecodeError:
        return raw.decode("cp1252"),"cp1252"

def parse_count(cell:str,study:str,island:str,species:str)->int:
    x=cell.strip()
    if x=="" or x.lower()=="na":
        return 0
    try:
        v=float(x)
    except ValueError as exc:
        raise ResponseQualityError(
            f"{study}: nonnumeric abundance at island={island!r} species={species!r}: {cell!r}"
        ) from exc
    if not math.isfinite(v) or v<0 or not v.is_integer():
        raise ResponseQualityError(
            f"{study}: abundance must be finite nonnegative integer at island={island!r} species={species!r}: {cell!r}"
        )
    return int(v)

def parse_matrix(raw:bytes,study:str,expected_islands:list[str]):
    text,encoding=decode(raw)
    table=list(csv.reader(io.StringIO(text)))
    if len(table)<2:
        raise ResponseQualityError(f"{study}: matrix has fewer than 2 rows")
    header=table[0]
    if len(header)<2 or header[0].strip()!="island_name":
        raise ResponseQualityError(f"{study}: first column must be island_name")
    species=header[1:]
    if any(name=="" for name in species):
        raise ResponseQualityError(f"{study}: blank species column name")
    if len(set(species))!=len(species):
        raise ResponseQualityError(f"{study}: duplicate species column names")
    width=len(header)
    rows={}
    for row_no,row in enumerate(table[1:],start=2):
        if len(row)!=width:
            raise ResponseQualityError(f"{study}: ragged row {row_no}: {len(row)} != {width}")
        island=row[0].strip()
        if not island:
            raise ResponseQualityError(f"{study}: blank island_name at row {row_no}")
        if island in rows:
            raise ResponseQualityError(f"{study}: duplicate island_name {island!r}")
        counts=[
            parse_count(cell,study,island,species[j])
            for j,cell in enumerate(row[1:])
        ]
        rows[island]=counts
    observed=set(rows)
    expected=set(expected_islands)
    if observed!=expected:
        raise ResponseQualityError(
            f"{study}: island row set mismatch; missing={sorted(expected-observed)!r}; extra={sorted(observed-expected)!r}"
        )
    return {
        "encoding":encoding,
        "species":species,
        "rows":rows,
    }

def log_choose(n:int,k:int)->float:
    if k<0 or n<0 or k>n:
        return float("-inf")
    return math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)

def rarefied_richness(counts:list[int],m:int)->float:
    N=sum(counts)
    if m<0 or m>N:
        raise ResponseQualityError(f"invalid rarefaction m={m} for N={N}")
    denom=log_choose(N,m)
    total=0.0
    for ns in counts:
        if ns<=0:
            continue
        remaining=N-ns
        if remaining<m:
            total+=1.0
        else:
            log_abs=log_choose(remaining,m)-denom
            if log_abs>1e-12:
                raise ResponseQualityError("hypergeometric absent probability exceeded one")
            total+=-math.expm1(min(0.0,log_abs))
    if not math.isfinite(total) or total<0:
        raise ResponseQualityError("nonfinite rarefied richness")
    return total

def build_response(parsed:dict,census:dict):
    diagnostics={}
    y_by_study={}
    for sid in sorted(parsed):
        expected=census["study_geometry"][sid]["island_codes"]
        rows=parsed[sid]["rows"]
        totals={island:sum(rows[island]) for island in expected}
        if any(N<2 for N in totals.values()):
            bad={k:v for k,v in totals.items() if v<2}
            raise ResponseQualityError(f"{sid}: islands with total abundance <2: {bad}")
        m=min(totals.values())
        if m<2:
            raise ResponseQualityError(f"{sid}: study rarefaction minimum m_g={m}<2")
        rare={island:rarefied_richness(rows[island],m) for island in expected}
        logs=np.asarray([math.log1p(rare[i]) for i in expected],dtype=float)
        if not np.all(np.isfinite(logs)):
            raise ResponseQualityError(f"{sid}: nonfinite transformed rarefied richness")
        mu=float(logs.mean());sd=float(logs.std(ddof=0))
        if sd<=1e-12:
            raise ResponseQualityError(f"{sid}: z(log1p rarefied richness) SD <= 1e-12")
        y_by_study[sid]={island:(math.log1p(rare[island])-mu)/sd for island in expected}
        diagnostics[sid]={
            "n_islands":len(expected),
            "n_species_columns":len(parsed[sid]["species"]),
            "minimum_total_abundance_m_g":m,
            "total_abundance_min":min(totals.values()),
            "total_abundance_max":max(totals.values()),
            "rarefied_richness_min":min(rare.values()),
            "rarefied_richness_max":max(rare.values()),
            "log1p_rarefied_mean":mu,
            "log1p_rarefied_sd":sd,
            "zero_rarefied_islands":sum(v<=0 for v in rare.values()),
        }
    return y_by_study,diagnostics

def build_weighted_blocks(census:dict,protocol:dict,y_by_study:dict):
    columns=protocol["predictor_model"]["columns"]
    clusters=defaultdict(list)
    study_cluster={r["study_ID"]:r["geography_cluster"] for r in census["response_surfaces"]}
    cluster_studies=defaultdict(list)
    for sid,cid in study_cluster.items():
        cluster_studies[cid].append(sid)

    allX=[];ally=[];blocks={}
    for sid in sorted(y_by_study):
        cid=study_cluster[sid]
        grows=census["study_geometry"][sid]["geometry_rows"]
        pred={r["island_code"]:r for r in grows}
        islands=census["study_geometry"][sid]["island_codes"]
        X=np.asarray([[pred[i][c] for c in columns] for i in islands],dtype=float)
        y=np.asarray([y_by_study[sid][i] for i in islands],dtype=float)
        Xc=X-X.mean(axis=0,keepdims=True)
        yc=y-y.mean()
        weight=1.0/(len(cluster_studies[cid])*len(islands))
        root=math.sqrt(weight)
        Xw=Xc*root;yw=yc*root
        allX.append(Xw);ally.append(yw)
        clusters[cid].append((Xw,yw,sid))
    for cid,parts in clusters.items():
        blocks[cid]=(np.vstack([p[0] for p in parts]),np.concatenate([p[1] for p in parts]))
    X=np.vstack(allX);y=np.concatenate(ally)
    if np.linalg.matrix_rank(X,tol=1e-10)!=len(columns):
        raise ResponseQualityError("response model design lost rank")
    return X,y,blocks

def fit_beta(X:np.ndarray,y:np.ndarray)->np.ndarray:
    beta,_,rank,_=np.linalg.lstsq(X,y,rcond=None)
    if rank!=X.shape[1]:
        raise ResponseQualityError("weighted model rank failure")
    return beta

def replay_bootstrap(protocol:dict,blocks:dict,target_index:int):
    frozen=protocol["bootstrap"]
    cluster_ids=frozen["clusters"]
    reps=int(frozen["replicates"])
    rng=np.random.default_rng(int(frozen["seed"]))
    accepted=[];effects=[];attempted=0
    while len(accepted)<reps and attempted<reps*20:
        attempted+=1
        draw=[cluster_ids[int(i)] for i in rng.integers(0,len(cluster_ids),size=len(cluster_ids))]
        X=np.vstack([blocks[c][0] for c in draw])
        if np.linalg.matrix_rank(X,tol=1e-10)!=X.shape[1]:
            continue
        y=np.concatenate([blocks[c][1] for c in draw])
        accepted.append(draw)
        effects.append(float(fit_beta(X,y)[target_index]))
    if len(accepted)!=reps:
        raise ResponseQualityError(f"bootstrap accepted {len(accepted)} != {reps}")
    if attempted!=int(frozen["candidate_draws_attempted"]):
        raise ResponseQualityError(
            f"bootstrap attempted count drift {attempted} != {frozen['candidate_draws_attempted']}"
        )
    observed=sha(accepted)
    if observed!=frozen["accepted_draws_sha256"]:
        raise ResponseQualityError(
            f"bootstrap draw-set SHA drift {observed} != {frozen['accepted_draws_sha256']}"
        )
    return effects,observed,attempted

def terminal(lock,census,protocol,opened,receipts,failure):
    out={
        "schema":"structural.isar_relative_topology_outcome.v0_1",
        "status":"TERMINAL_STOP_RESPONSE_QUALITY",
        "census_fingerprint":census["census_fingerprint"],
        "protocol_fingerprint":protocol["protocol_fingerprint"],
        "response_access":{
            "abundance_response_opened":bool(opened),
            "opened_studies":opened,
            "opened_study_count":len(opened),
            "fresh_surface_count":len(census["response_surfaces"]),
            "scoring_started":False,
        },
        "source_receipts":receipts,
        "failure":str(failure),
        "H1_primary":{"estimate":None,"bootstrap_95_ci":None,"supported":False},
        "terminal_rule":"do not repair/drop/replace a study and continue; v0.1 is consumed and no rerun is authorized",
    }
    out["outcome_fingerprint"]=sha(out)
    return out

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--census",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--lock",type=Path,required=True)
    ap.add_argument("--raw-dir",type=Path,required=True)
    args=ap.parse_args()
    census=load(args.census);protocol=load(args.protocol);lock=load(args.lock)

    if lock.get("schema")!=LOCK_SCHEMA or lock.get("status")!="FROZEN_QUALIFIED_BEFORE_RESPONSE":
        raise RuntimeError("unexpected or unqualified lock")
    if census.get("census_fingerprint")!=EXPECTED_CENSUS or lock.get("census_fingerprint")!=EXPECTED_CENSUS:
        raise RuntimeError("census lock drift")
    if protocol.get("protocol_fingerprint")!=EXPECTED_PROTOCOL or lock.get("protocol_fingerprint")!=EXPECTED_PROTOCOL:
        raise RuntimeError("protocol lock drift")
    if census.get("response_values_accessed") is not False or census.get("abundance_files_opened") is not False:
        raise RuntimeError("census already records abundance response access")
    if protocol.get("response_values_accessed") is not False:
        raise RuntimeError("protocol already records response access")
    auth=lock.get("authorization",{})
    if auth.get("one_shot_fresh_response_authorized") is not True:
        raise RuntimeError("lock does not authorize one-shot response")
    if auth.get("post_response_study_dropping_authorized") is not False:
        raise RuntimeError("study dropping unexpectedly authorized")
    if auth.get("post_response_retuning_authorized") is not False:
        raise RuntimeError("post-response retuning unexpectedly authorized")
    if auth.get("rerun_after_any_abundance_file_opened") is not False:
        raise RuntimeError("rerun policy drift")
    if protocol["predictor_model"]["target"]!="topology_x_relative_isolation":
        raise RuntimeError("target drift")
    if protocol["H1_primary"]["prediction"]!="positive":
        raise RuntimeError("H1 direction drift")
    if protocol["bootstrap"]["accepted_draws_sha256"]!=lock["bootstrap"]["accepted_draws_sha256"]:
        raise RuntimeError("bootstrap lock drift")

    args.raw_dir.mkdir(parents=True,exist_ok=True)
    opened=[];receipts=[];parsed={}
    try:
        surface_by_study={r["study_ID"]:r for r in census["response_surfaces"]}
        lock_by_study={r["study_ID"]:r for r in lock["response_surfaces"]}
        if set(surface_by_study)!=set(lock_by_study):
            raise RuntimeError("response surface study set drift")
        for sid in sorted(surface_by_study):
            surface=surface_by_study[sid];bound=lock_by_study[sid]
            if surface["source_path"]!=bound["path"] or surface["geography_cluster"]!=bound["cluster"]:
                raise RuntimeError(f"{sid}: response path/cluster drift")
            raw=fetch_raw(surface["source_path"])
            opened.append(sid)
            outpath=args.raw_dir/f"{sid}.csv"
            outpath.write_bytes(raw)
            receipt={
                "study_ID":sid,
                "path":surface["source_path"],
                "bytes":len(raw),
                "sha256":hashlib.sha256(raw).hexdigest(),
                "git_blob_sha":git_blob_sha(raw),
            }
            receipts.append(receipt)
            parsed[sid]=parse_matrix(
                raw,sid,census["study_geometry"][sid]["island_codes"]
            )

        y_by_study,response_diag=build_response(parsed,census)
        X,y,blocks=build_weighted_blocks(census,protocol,y_by_study)
        columns=protocol["predictor_model"]["columns"]
        target=protocol["predictor_model"]["target"]
        target_idx=columns.index(target)
        beta=fit_beta(X,y)
        point=float(beta[target_idx])
        effects,draw_sha,attempted=replay_bootstrap(protocol,blocks,target_idx)
        arr=np.asarray(effects,dtype=float)
        ci=[float(x) for x in np.quantile(arr,[0.025,0.975],method="linear")]
        out={
            "schema":"structural.isar_relative_topology_outcome.v0_1",
            "status":"ONE_SHOT_FRESH_RESPONSE_SCORED",
            "census_fingerprint":census["census_fingerprint"],
            "protocol_fingerprint":protocol["protocol_fingerprint"],
            "response_access":{
                "abundance_response_opened":True,
                "opened_studies":opened,
                "opened_study_count":len(opened),
                "fresh_surface_count":len(census["response_surfaces"]),
                "all_frozen_surfaces_opened":len(opened)==len(census["response_surfaces"]),
                "excluded_contaminated_surfaces_opened":False,
                "scoring_started":True,
            },
            "source_receipts":receipts,
            "response_diagnostics":response_diag,
            "model":{
                "columns":columns,
                "coefficients":{c:float(beta[i]) for i,c in enumerate(columns)},
                "target":target,
                "target_estimate":point,
                "rank":int(np.linalg.matrix_rank(X,tol=1e-10)),
                "rows":int(X.shape[0]),
            },
            "H1_primary":{
                "estimate":point,
                "bootstrap_95_ci":ci,
                "prediction":"positive",
                "supported":ci[0]>0,
                "bootstrap_fraction_gt_zero":float(np.mean(arr>0)),
            },
            "bootstrap":{
                "replicates":len(effects),
                "candidate_draws_attempted":attempted,
                "accepted_draws_sha256":draw_sha,
                "effect_estimates_sha256":sha(effects),
                "quantile_method":"numpy.quantile method=linear",
            },
            "claim_boundary":protocol["H1_primary"]["claim_ceiling"],
            "post_response_retuning_authorized":False,
            "rerun_authorized":False,
        }
        out["outcome_fingerprint"]=sha(out)
        print(json.dumps(out,indent=2,sort_keys=True))
        return 0
    except ResponseQualityError as exc:
        out=terminal(lock,census,protocol,opened,receipts,exc)
        print(json.dumps(out,indent=2,sort_keys=True))
        return 0
    except Exception as exc:
        if opened:
            out=terminal(lock,census,protocol,opened,receipts,f"unexpected after response access: {type(exc).__name__}: {exc}")
            print(json.dumps(out,indent=2,sort_keys=True))
            return 0
        raise

if __name__=="__main__":
    raise SystemExit(main())
