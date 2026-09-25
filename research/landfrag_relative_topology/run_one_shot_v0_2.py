#!/usr/bin/env python3
"""One-shot LandFrag abundance scoring under the frozen v0.2 protocol.

The monolithic abundance CSV is fetched exactly once from the frozen Git commit.
Any post-fetch schema or response-quality failure emits a terminal outcome and
must not be rerun under v0.2.
"""
from __future__ import annotations

from collections import defaultdict
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

SOURCE_REPO="mauriciovancine/landfrag"
SOURCE_COMMIT="5fd540048a6e60c641c9c1d6e7f26e7b5eece137"
ABUNDANCE_PATH="data/00_landfrag_metadata/landfrag_abundances_jun2024_final_version.csv"
ABUNDANCE_BLOB="abfdd21712b7f221207e25e62b623e8a8a901a55"
EXPECTED_CENSUS="8d4ad7a00775a77bef231b2f5842c1dbcbd959315c0410843528c0828db2784b"
EXPECTED_PRECISION="9c7fce34c2b9d027caa489ffbaad436241d518854bd2d6300265470a1e81e638"
EXPECTED_PROTOCOL="102b3f7700ac2bc072ee5abb9370c2473cd2473fda44e7d8d79fd2eb9686282c"
AUTH_SCHEMA="structural.landfrag_relative_topology_one_shot_authorization.v0_2"
EXPECTED_COLUMNS=[
    "id","refshort","fragment_id","plot_id","scientific_name","abundance","tsn","taxon"
]
TARGET="direct_x_gain"

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

def fetch_raw()->bytes:
    url=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/"+quote(
        ABUNDANCE_PATH,safe="/"
    )
    req=Request(url,headers={"User-Agent":"Structural-LandFrag-one-shot/0.1"})
    with urlopen(req,timeout=180) as response:
        return response.read()

def decode_csv(raw:bytes):
    try:
        return raw.decode("utf-8-sig"),"utf-8-sig"
    except UnicodeDecodeError:
        return raw.decode("cp1252"),"cp1252"

def parse_count(x):
    if x is None:
        return None
    s=str(x).strip()
    if not s or s.lower() in {"na","nan"}:
        return None
    try:
        v=float(s)
    except ValueError:
        return None
    if not math.isfinite(v) or v<0 or abs(v-round(v))>1e-9:
        return None
    return int(round(v))

def log_choose(n,k):
    if k<0 or n<0 or k>n:
        return float("-inf")
    return math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)

def rarefied_expected_richness(species_counts,m):
    N=sum(species_counts.values())
    if N<m:
        raise RuntimeError("rarefaction reference effort exceeds fragment abundance")
    denom=log_choose(N,m)
    total=0.0
    for n in species_counts.values():
        if n<=0:
            continue
        remaining=N-n
        if remaining<m:
            p_absent=0.0
        else:
            logp=log_choose(remaining,m)-denom
            p_absent=math.exp(logp)
            p_absent=min(1.0,max(0.0,p_absent))
        total+=1.0-p_absent
    return total

def design_audit(X):
    rank=int(np.linalg.matrix_rank(X,tol=1e-10))
    sv=np.linalg.svd(X,compute_uv=False)
    cond=float(sv[0]/sv[-1]) if sv[-1]>1e-15 else float("inf")
    return {
        "rank":rank,
        "n_columns":int(X.shape[1]),
        "full_rank":rank==X.shape[1],
        "condition_number":cond,
    }

def validate_pre_response(census,precision,protocol,lock,auth):
    if census.get("census_fingerprint")!=EXPECTED_CENSUS:
        raise RuntimeError("census fingerprint drift")
    if precision.get("precision_fingerprint")!=EXPECTED_PRECISION:
        raise RuntimeError("precision fingerprint drift")
    if protocol.get("protocol_fingerprint")!=EXPECTED_PROTOCOL:
        raise RuntimeError("protocol fingerprint drift")
    if lock.get("schema")!="structural.landfrag_relative_topology_pre_response_lock.v0_2":
        raise RuntimeError("unexpected lock schema")
    if lock.get("status")!="FROZEN_QUALIFIED_BEFORE_MONOLITHIC_ABUNDANCE_ACCESS":
        raise RuntimeError("pre-response lock not qualified")
    if lock.get("response_values_accessed") is not False or lock.get("abundance_file_opened") is not False:
        raise RuntimeError("lock already records response access")
    if lock.get("census_fingerprint")!=EXPECTED_CENSUS:
        raise RuntimeError("lock/census drift")
    if lock.get("precision_fingerprint")!=EXPECTED_PRECISION:
        raise RuntimeError("lock/precision drift")
    if lock.get("protocol_fingerprint")!=EXPECTED_PROTOCOL:
        raise RuntimeError("lock/protocol drift")
    if lock["response_surface"]["git_blob_sha"]!=ABUNDANCE_BLOB:
        raise RuntimeError("lock abundance blob drift")
    if auth.get("schema")!=AUTH_SCHEMA:
        raise RuntimeError("unexpected authorization schema")
    if auth.get("status")!="AUTHORIZED_FOR_EXACT_ONE_SHOT_ABUNDANCE_ACCESS":
        raise RuntimeError("one-shot response access not authorized")
    if auth.get("response_values_accessed") is not False:
        raise RuntimeError("authorization already records response access")
    if auth.get("census_fingerprint")!=EXPECTED_CENSUS:
        raise RuntimeError("authorization/census drift")
    if auth.get("precision_fingerprint")!=EXPECTED_PRECISION:
        raise RuntimeError("authorization/precision drift")
    if auth.get("protocol_fingerprint")!=EXPECTED_PROTOCOL:
        raise RuntimeError("authorization/protocol drift")
    if auth["source"]["git_blob_sha"]!=ABUNDANCE_BLOB:
        raise RuntimeError("authorization abundance blob drift")
    if auth["authorization"]["one_shot_monolithic_access"] is not True:
        raise RuntimeError("monolithic response access not authorized")
    if auth["authorization"]["rerun_after_any_abundance_bytes_opened"] is not False:
        raise RuntimeError("rerun firewall drift")
    if protocol["response_firewall"]["expected_columns"]!=EXPECTED_COLUMNS:
        raise RuntimeError("response schema drift")
    if protocol["study_model"]["target"]!=TARGET:
        raise RuntimeError("target drift")
    if protocol["H1_primary"]["prediction"]!="positive":
        raise RuntimeError("H1 direction drift")

def terminal_base(census,protocol,raw,encoding,row_count,status,details):
    out={
        "schema":"structural.landfrag_relative_topology_outcome.v0_2",
        "status":status,
        "source":{
            "repository":SOURCE_REPO,
            "commit":SOURCE_COMMIT,
            "path":ABUNDANCE_PATH,
            "git_blob_sha":ABUNDANCE_BLOB,
            "sha256":hashlib.sha256(raw).hexdigest(),
            "bytes":len(raw),
            "encoding":encoding,
            "rows_parsed":row_count,
        },
        "census_fingerprint":EXPECTED_CENSUS,
        "protocol_fingerprint":EXPECTED_PROTOCOL,
        "response_access":{
            "monolithic_abundance_opened":True,
            "all_LandFrag_response_family_consumed":True,
            "H1_scored":False,
        },
        "terminal_details":details,
        "H1_primary":None,
        "evidence_boundary":{
            "post_response_retuning_authorized":False,
            "new_LandFrag_hypothesis_authorized":False,
            "rerun_authorized":False,
        },
    }
    out["outcome_fingerprint"]=sha(out)
    return out

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--census",type=Path,required=True)
    ap.add_argument("--precision",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--lock",type=Path,required=True)
    ap.add_argument("--authorization",type=Path,required=True)
    ap.add_argument("--raw-output",type=Path,required=True)
    args=ap.parse_args()

    census=load(args.census)
    precision=load(args.precision)
    protocol=load(args.protocol)
    lock=load(args.lock)
    auth=load(args.authorization)
    validate_pre_response(census,precision,protocol,lock,auth)

    raw=fetch_raw()
    observed_blob=git_blob_sha(raw)
    observed_sha=hashlib.sha256(raw).hexdigest()
    args.raw_output.parent.mkdir(parents=True,exist_ok=True)
    args.raw_output.write_bytes(raw)

    if observed_blob!=ABUNDANCE_BLOB:
        out=terminal_base(
            census,protocol,raw,"unknown",0,
            "TERMINAL_STOP_SOURCE_BLOB_DRIFT",
            {"observed_git_blob_sha":observed_blob,"expected_git_blob_sha":ABUNDANCE_BLOB},
        )
        print(json.dumps(out,indent=2,sort_keys=True))
        return 2

    try:
        text,encoding=decode_csv(raw)
    except Exception as exc:
        out=terminal_base(
            census,protocol,raw,"decode_failed",0,
            "TERMINAL_STOP_RESPONSE_SCHEMA",
            {"error":f"decode failure: {type(exc).__name__}: {exc}"},
        )
        print(json.dumps(out,indent=2,sort_keys=True))
        return 2

    try:
        reader=csv.DictReader(io.StringIO(text))
        observed_columns=reader.fieldnames or []
        if observed_columns!=EXPECTED_COLUMNS:
            raise RuntimeError(
                f"column mismatch: observed={observed_columns} expected={EXPECTED_COLUMNS}"
            )
        response_rows=list(reader)
    except Exception as exc:
        out=terminal_base(
            census,protocol,raw,encoding,0,
            "TERMINAL_STOP_RESPONSE_SCHEMA",
            {"error":f"CSV schema failure: {type(exc).__name__}: {exc}"},
        )
        print(json.dumps(out,indent=2,sort_keys=True))
        return 2

    selected={s["refshort"]:s for s in census["studies"]}
    focal_ids={
        sid:{r["fragment_id"] for r in s["focal_rows"]}
        for sid,s in selected.items()
    }

    abund=defaultdict(lambda:defaultdict(lambda:defaultdict(int)))
    focal_rows_seen=defaultdict(int)
    study_invalid=defaultdict(lambda:defaultdict(int))
    selected_response_rows=0

    for row in response_rows:
        sid=str(row.get("refshort","")).strip()
        if sid not in selected:
            continue
        fragment=str(row.get("fragment_id","")).strip()
        if fragment not in focal_ids[sid]:
            continue
        selected_response_rows+=1
        focal_rows_seen[(sid,fragment)]+=1
        species=str(row.get("scientific_name","")).strip()
        if not species:
            study_invalid[sid]["blank_species_name"]+=1
            continue
        count=parse_count(row.get("abundance"))
        if count is None:
            study_invalid[sid]["invalid_abundance"]+=1
            continue
        abund[sid][fragment][species]+=count

    study_audits={}
    study_coefficients={}
    cols=protocol["study_model"]["columns"]
    target_idx=cols.index(TARGET)

    for sid in sorted(selected):
        s=selected[sid]
        reasons=[]
        frozen_rows={r["fragment_id"]:r for r in s["focal_rows"]}
        missing=[
            fid for fid in sorted(frozen_rows)
            if focal_rows_seen[(sid,fid)]==0
        ]
        if missing:
            reasons.append("missing_frozen_focal_response")
        if study_invalid[sid]:
            reasons.append("invalid_selected_response_rows")

        totals={}
        for fid in frozen_rows:
            totals[fid]=sum(abund[sid][fid].values())
        low=[fid for fid,n in totals.items() if n<2]
        if low:
            reasons.append("focal_total_abundance_lt_2")
        m=min(totals.values()) if totals else 0
        if m<2:
            reasons.append("study_reference_effort_lt_2")

        rarefied={}
        if not reasons:
            try:
                for fid in frozen_rows:
                    rarefied[fid]=rarefied_expected_richness(abund[sid][fid],m)
            except Exception:
                reasons.append("rarefaction_failure")

        response_sd=None
        beta=None
        design=None
        if not reasons:
            ordered=[r["fragment_id"] for r in s["focal_rows"]]
            ylog=np.log1p(np.asarray([rarefied[fid] for fid in ordered],dtype=float))
            response_sd=float(ylog.std(ddof=0))
            if not math.isfinite(response_sd) or response_sd<=1e-12:
                reasons.append("response_sd_not_positive")
            X=np.asarray([r["design"] for r in s["focal_rows"]],dtype=float)
            design=design_audit(X)
            if len(ordered)<int(protocol["study_response_gate"]["minimum_model_rows"]):
                reasons.append("fewer_than_minimum_model_rows")
            if not design["full_rank"]:
                reasons.append("response_design_not_full_rank")
            if design["condition_number"]>float(
                protocol["study_response_gate"]["maximum_frozen_predictor_condition_number"]
            ):
                reasons.append("response_design_condition_gt_100")
            if not reasons:
                yz=(ylog-ylog.mean())/response_sd
                beta,_,rank,_=np.linalg.lstsq(X,yz,rcond=None)
                if int(rank)!=X.shape[1]:
                    reasons.append("ols_rank_failure")
                    beta=None

        passed=not reasons and beta is not None
        audit={
            "refshort":sid,
            "geography_cluster":s["geography_cluster"],
            "n_frozen_focals":len(frozen_rows),
            "selected_response_rows":sum(focal_rows_seen[(sid,fid)] for fid in frozen_rows),
            "missing_focal_count":len(missing),
            "invalid_response_counts":dict(study_invalid[sid]),
            "minimum_fragment_total_abundance":min(totals.values()) if totals else None,
            "study_reference_effort":m,
            "response_log1p_sd":response_sd,
            "design_audit":design,
            "pass":passed,
            "failure_reasons":reasons,
        }
        study_audits[sid]=audit
        if passed:
            study_coefficients[sid]={
                "geography_cluster":s["geography_cluster"],
                "target":float(beta[target_idx]),
                "coefficients":{
                    col:float(beta[i]) for i,col in enumerate(cols)
                },
                "n_focals":len(frozen_rows),
                "reference_effort":m,
            }

    by_cluster=defaultdict(list)
    for sid,row in study_coefficients.items():
        by_cluster[row["geography_cluster"]].append(row["target"])
    cluster_coefficients={
        cid:float(np.mean(vals)) for cid,vals in sorted(by_cluster.items())
    }
    qualified_clusters=len(cluster_coefficients)
    minimum_clusters=int(
        protocol["geography_aggregation"]["minimum_response_qualified_geography_clusters"]
    )

    if qualified_clusters<minimum_clusters:
        out=terminal_base(
            census,protocol,raw,encoding,len(response_rows),
            "TERMINAL_STOP_RESPONSE_QUALITY",
            {
                "selected_response_rows":selected_response_rows,
                "response_qualified_studies":len(study_coefficients),
                "response_qualified_geography_clusters":qualified_clusters,
                "minimum_required_geography_clusters":minimum_clusters,
                "study_audits":study_audits,
            },
        )
        print(json.dumps(out,indent=2,sort_keys=True))
        return 2

    cluster_ids=sorted(cluster_coefficients)
    values=np.asarray([cluster_coefficients[c] for c in cluster_ids],dtype=float)
    estimate=float(values.mean())
    reps=int(protocol["bootstrap"]["replicates"])
    seed=int(protocol["bootstrap"]["seed"])
    rng=np.random.default_rng(seed)
    boot=np.empty(reps,dtype=float)
    m=len(values)
    for i in range(reps):
        idx=rng.integers(0,m,size=m)
        boot[i]=values[idx].mean()
    ci=np.quantile(boot,[0.025,0.975],method="linear")
    loo={}
    if m>1:
        for i,cid in enumerate(cluster_ids):
            loo[cid]=float(np.delete(values,i).mean())

    taxon_by_study={
        s["refshort"]:s["taxa"] for s in census["studies"]
    }
    taxon_cluster_values=defaultdict(lambda:defaultdict(list))
    for sid,row in study_coefficients.items():
        for taxon in taxon_by_study[sid]:
            taxon_cluster_values[taxon][row["geography_cluster"]].append(row["target"])
    taxon_summaries={}
    for taxon,clusters in sorted(taxon_cluster_values.items()):
        vals=[
            float(np.mean(v)) for _,v in sorted(clusters.items())
        ]
        taxon_summaries[taxon]={
            "geography_clusters":len(vals),
            "mean_target":float(np.mean(vals)) if vals else None,
            "fraction_positive":float(np.mean(np.asarray(vals)>0)) if vals else None,
        }

    out={
        "schema":"structural.landfrag_relative_topology_outcome.v0_2",
        "status":"ONE_SHOT_LANDFRAG_H1_SCORED",
        "source":{
            "repository":SOURCE_REPO,
            "commit":SOURCE_COMMIT,
            "path":ABUNDANCE_PATH,
            "git_blob_sha":observed_blob,
            "sha256":observed_sha,
            "bytes":len(raw),
            "encoding":encoding,
            "rows":len(response_rows),
        },
        "census_fingerprint":EXPECTED_CENSUS,
        "precision_fingerprint":EXPECTED_PRECISION,
        "protocol_fingerprint":EXPECTED_PROTOCOL,
        "response_access":{
            "monolithic_abundance_opened":True,
            "all_LandFrag_response_family_consumed":True,
            "H1_scored":True,
        },
        "response_quality":{
            "selected_response_rows":selected_response_rows,
            "qualified_studies":len(study_coefficients),
            "qualified_geography_clusters":qualified_clusters,
            "minimum_required_geography_clusters":minimum_clusters,
            "study_audits":study_audits,
        },
        "H1_primary":{
            "estimate":estimate,
            "bootstrap_95_ci":[float(ci[0]),float(ci[1])],
            "prediction":"positive",
            "supported":bool(ci[0]>0),
            "cluster_coefficients":cluster_coefficients,
            "study_coefficients":study_coefficients,
            "study_target_fraction_positive":float(np.mean(
                np.asarray([v["target"] for v in study_coefficients.values()])>0
            )),
            "cluster_target_fraction_positive":float(np.mean(values>0)),
            "leave_one_geography_out_mean":loo,
            "bootstrap_estimates_sha256":sha([float(x) for x in boot]),
        },
        "secondary_nonrescuing":{
            "taxon_summaries":taxon_summaries,
            "cannot_rescue_H1":True,
        },
        "evidence_boundary":{
            "post_response_retuning_authorized":False,
            "new_LandFrag_hypothesis_authorized":False,
            "rerun_authorized":False,
            "landscape_metric_rescue_authorized":False,
        },
    }
    out["outcome_fingerprint"]=sha(out)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
