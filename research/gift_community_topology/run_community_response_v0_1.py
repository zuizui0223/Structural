#!/usr/bin/env python3
"""One-shot execution of the frozen GIFT community-richness topology study.

This script MUST NOT be run until an exact pre-response lock has been committed.
It opens only the frozen community response surfaces, computes no H2 result, and
fits only the frozen H1/H3 clade-specific models with the frozen bootstrap draw set.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np

BASE="https://gift.uni-goettingen.de/api/extended/"
VERSION="3.2"
CLADES=("Angiospermae","Pteridophyta","Gymnospermae")
CLIMATE_MAP={
    "bio1":"wc2.0_bio_30s_01",
    "bio5":"wc2.0_bio_30s_05",
    "bio6":"wc2.0_bio_30s_06",
    "bio12":"wc2.0_bio_30s_12",
    "bio15":"wc2.0_bio_30s_15",
}
LOCK_SCHEMA="structural.gift_community_topology_pre_response_lock.v0_5"

def sha(value)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path:Path)->dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value

def as01(value):
    try:
        return int(float(value))
    except (TypeError,ValueError):
        return None

def fetch_checklist(clade:str,list_id:str,taxon_id:str,attempts:int=5):
    params={
        "query":"checklists",
        "listid":str(list_id),
        "taxonid":str(taxon_id),
        "namesmatched":"0",
        "filter":"native",
    }
    url=BASE+"index3.2.php?"+urlencode(params)
    last=None
    for attempt in range(attempts):
        try:
            req=Request(url,headers={"User-Agent":"Structural-GIFT-community-response/0.1"})
            with urlopen(req,timeout=180) as response:
                raw=response.read()
            rows=json.loads(raw)
            if not isinstance(rows,list):
                raise RuntimeError(f"{clade} list {list_id}: expected JSON list")
            return rows,{
                "clade":clade,
                "list_ID":str(list_id),
                "taxon_ID":str(taxon_id),
                "url":url,
                "bytes":len(raw),
                "sha256":hashlib.sha256(raw).hexdigest(),
                "rows":len(rows),
            }
        except (HTTPError,URLError,TimeoutError,json.JSONDecodeError) as exc:
            last=exc
            if attempt+1<attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"failed checklist query {clade} list {list_id}: {last}")

def raw_predictors(island):
    climate=island["climate"]
    return {
        "bio1":float(climate[CLIMATE_MAP["bio1"]]),
        "bio5":float(climate[CLIMATE_MAP["bio5"]]),
        "bio6":float(climate[CLIMATE_MAP["bio6"]]),
        "bio12":float(climate[CLIMATE_MAP["bio12"]]),
        "bio15":float(climate[CLIMATE_MAP["bio15"]]),
        "log_area":math.log(max(float(island["area_km2"]),1e-12)),
        "log1p_dist":math.log1p(float(island["dist_km"])),
        "SLMP":float(island["SLMP"]),
        "GMMC":float(island["GMMC"]),
        "log1p_nearest_other":math.log1p(float(island["nearest_other_island_km"])),
        "surrounding_island_pressure":float(island["surrounding_island_pressure"]),
        "surrounding_landmass_pressure":float(island["surrounding_landmass_pressure"]),
        "step_isolation_gain_log":float(island["step_isolation_gain_log"]),
        "extreme":float(bool(island["extreme_q75"])),
    }

def build_model_rows(panel,protocol,richness):
    scaling=protocol["predictor_semantics"]["frozen_continuous_scaling"]
    island_scaling={
        k:v for k,v in scaling.items() if k!="log1p_list_count_by_clade"
    }
    list_scaling=scaling["log1p_list_count_by_clade"]

    rows={clade:[] for clade in CLADES}
    for group in panel["groups"]:
        arch=group["archipelago_id"]
        for island in group["islands"]:
            eid=str(island["entity_ID"])
            raw=raw_predictors(island)
            scaled=dict(raw)
            for col,spec in island_scaling.items():
                scaled[col]=(float(raw[col])-float(spec["mean"]))/float(spec["sd"])
            for clade in CLADES:
                key=(clade,eid)
                if key not in richness:
                    raise RuntimeError(f"missing frozen response for {clade} island {eid}")
                list_count=len(island["list_ids"][clade])
                if list_count<1:
                    raise RuntimeError(f"empty list surface for {clade} island {eid}")
                ls=list_scaling[clade]
                row={
                    "archipelago_id":arch,
                    "entity_ID":eid,
                    "clade":clade,
                    **scaled,
                    "log1p_list_count":(
                        math.log1p(list_count)-float(ls["mean"])
                    )/float(ls["sd"]),
                    "y":math.log1p(int(richness[key]["richness"])),
                }
                row["step_gain_x_extreme"]=row["step_isolation_gain_log"]*row["extreme"]
                rows[clade].append(row)
    return rows

def demean_clade(rows,columns):
    X=np.asarray([[row[c] for c in columns] for row in rows],dtype=float)
    y=np.asarray([row["y"] for row in rows],dtype=float)
    labels=[row["archipelago_id"] for row in rows]
    groups=defaultdict(list)
    for i,label in enumerate(labels):
        groups[label].append(i)
    Xc=X.copy(); yc=y.copy()
    for idxs in groups.values():
        idx=np.asarray(idxs,dtype=int)
        Xc[idx,:]-=X[idx,:].mean(axis=0,keepdims=True)
        yc[idx]-=y[idx].mean()
    if np.linalg.matrix_rank(Xc,tol=1e-10)!=Xc.shape[1]:
        raise RuntimeError("full response design lost rank despite frozen predictor audit")
    blocks={}
    for arch,idxs in groups.items():
        idx=np.asarray(idxs,dtype=int)
        blocks[arch]=(Xc[idx,:],yc[idx])
    return Xc,yc,blocks

def beta_from_xy(X,y):
    beta,_,rank,_=np.linalg.lstsq(X,y,rcond=None)
    if rank!=X.shape[1]:
        raise RuntimeError("OLS design rank failure")
    return beta

def replay_bootstrap(protocol,clade_blocks,columns):
    frozen=protocol["model"]["bootstrap_design"]
    archipelagos=frozen["archipelagos"]
    reps=int(frozen["accepted_replicates"])
    seed=int(frozen["seed"])
    rng=np.random.default_rng(seed)
    accepted=[]
    betas={clade:[] for clade in CLADES}
    h1=[]
    h3=[]
    attempted=0
    max_attempts=reps*10
    target_index=columns.index(protocol["H1_primary"]["per_clade_target_column"])

    while len(accepted)<reps and attempted<max_attempts:
        attempted+=1
        draw=[
            archipelagos[int(i)]
            for i in rng.integers(0,len(archipelagos),size=len(archipelagos))
        ]
        matrices={}
        vectors={}
        valid=True
        for clade in CLADES:
            X=np.vstack([clade_blocks[clade][arch][0] for arch in draw])
            y=np.concatenate([clade_blocks[clade][arch][1] for arch in draw])
            if np.linalg.matrix_rank(X,tol=1e-10)!=X.shape[1]:
                valid=False
                break
            matrices[clade]=X; vectors[clade]=y
        if not valid:
            continue
        accepted.append(draw)
        cb={}
        for clade in CLADES:
            b=beta_from_xy(matrices[clade],vectors[clade])[target_index]
            cb[clade]=float(b)
            betas[clade].append(float(b))
        h1.append(float(sum(cb.values())/3.0))
        h3.append(float(cb["Pteridophyta"]-(cb["Angiospermae"]+cb["Gymnospermae"])/2.0))

    if len(accepted)!=reps:
        raise RuntimeError(f"bootstrap replay accepted {len(accepted)} != {reps}")
    if attempted!=int(frozen["candidate_draws_attempted"]):
        raise RuntimeError(
            f"bootstrap attempted-draw drift {attempted} != {frozen['candidate_draws_attempted']}"
        )
    digest=sha(accepted)
    if digest!=frozen["accepted_draws_sha256"]:
        raise RuntimeError(
            f"bootstrap accepted-draw SHA drift {digest} != {frozen['accepted_draws_sha256']}"
        )
    return {
        "clade_target_bootstrap":betas,
        "H1_bootstrap":h1,
        "H3_bootstrap":h3,
        "accepted_draws_sha256":digest,
        "candidate_draws_attempted":attempted,
    }

def interval(values):
    arr=np.asarray(values,dtype=float)
    q=np.quantile(arr,[0.025,0.975],method="linear")
    return [float(q[0]),float(q[1])]

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--panel",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--lock",type=Path,required=True)
    ap.add_argument("--raw-output",type=Path,required=True)
    args=ap.parse_args()

    panel=load(args.panel); protocol=load(args.protocol); lock=load(args.lock)
    if lock.get("schema")!=LOCK_SCHEMA:
        raise RuntimeError("unexpected pre-response lock schema")
    if lock.get("status")!="FROZEN_QUALIFIED_BEFORE_RESPONSE":
        raise RuntimeError("pre-response lock is not qualified")
    if lock.get("response_values_accessed") is not False:
        raise RuntimeError("lock already records response access")
    if lock.get("response_open_authorized") is not True:
        raise RuntimeError("lock does not authorize one-shot response access")
    if panel.get("panel_fingerprint")!=lock.get("panel_fingerprint"):
        raise RuntimeError("panel fingerprint drift")
    if protocol.get("protocol_fingerprint")!=lock.get("protocol_fingerprint"):
        raise RuntimeError("protocol fingerprint drift")
    if protocol.get("status")!="QUALIFIED_TO_OPEN_COMMUNITY_RESPONSE":
        raise RuntimeError("protocol is not qualified to open response")
    if protocol.get("response_open_authorized") is not True:
        raise RuntimeError("protocol response authorization absent")
    if protocol["H2"].get("status")!="TERMINAL_PRE_RESPONSE_NON_ESTIMABLE_NOT_TESTED":
        raise RuntimeError("H2 terminal boundary drift")
    if lock.get("bootstrap_draws_sha256")!=protocol["model"]["bootstrap_design"]["accepted_draws_sha256"]:
        raise RuntimeError("bootstrap draw-set drift")
    for clade in CLADES:
        if panel["response_surfaces"][clade]["surface_sha256"]!=lock["response_surface_sha256"][clade]:
            raise RuntimeError(f"response surface drift for {clade}")
        if panel["response_surfaces"][clade]["opened"] is not False:
            raise RuntimeError(f"panel already marks {clade} response open")

    # Build exact query universe and guarantee each list maps to one frozen island.
    query_map={}
    expected_query_counts={}
    for group in panel["groups"]:
        for island in group["islands"]:
            eid=str(island["entity_ID"])
            for clade in CLADES:
                taxon_id=str(panel["response_surfaces"][clade]["taxon_ID"])
                for lid in island["list_ids"][clade]:
                    key=(clade,str(lid),taxon_id)
                    if key in query_map and query_map[key]!=eid:
                        raise RuntimeError(f"list surface maps to multiple islands: {key}")
                    query_map[key]=eid
    for clade in CLADES:
        expected_query_counts[clade]=sum(key[0]==clade for key in query_map)

    results={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={
            pool.submit(fetch_checklist,clade,lid,taxon):(clade,lid,taxon)
            for clade,lid,taxon in sorted(query_map,key=lambda x:(x[0],int(x[1])))
        }
        for fut in as_completed(futures):
            key=futures[fut]
            results[key]=fut.result()

    if set(results)!=set(query_map):
        raise RuntimeError("not every frozen checklist query returned")

    present=defaultdict(set)
    uncertain=defaultdict(set)
    raw_rows=[]
    source_receipts=[]
    for key in sorted(results,key=lambda x:(x[0],int(x[1]))):
        clade,lid,taxon=key
        eid=query_map[key]
        rows,receipt=results[key]
        source_receipts.append(receipt)
        for row in rows:
            row_eid=row.get("entity_ID")
            if row_eid not in (None,""):
                try:
                    observed_eid=str(int(float(row_eid)))
                except (TypeError,ValueError):
                    raise RuntimeError(f"non-numeric entity_ID in {clade} list {lid}")
                if observed_eid!=eid:
                    raise RuntimeError(
                        f"response entity mismatch for {clade} list {lid}: {observed_eid} != {eid}"
                    )
            wid=row.get("work_ID")
            if wid in (None,""):
                continue
            wid=str(int(float(wid)))
            native=as01(row.get("native"))
            questionable=as01(row.get("questionable"))
            quest_native=as01(row.get("quest_native"))
            raw_rows.append((clade,lid,eid,wid,native,questionable,quest_native))
            if native==1 and questionable!=1 and quest_native!=1:
                present[(clade,eid)].add(wid)
            elif native==1:
                uncertain[(clade,eid)].add(wid)

    raw_rows.sort(key=lambda r:(r[0],int(r[1]),int(r[2]),int(r[3])))
    args.raw_output.parent.mkdir(parents=True,exist_ok=True)
    with args.raw_output.open("w",encoding="utf-8",newline="") as handle:
        w=csv.writer(handle)
        w.writerow(["clade","list_ID","entity_ID","work_ID","native","questionable","quest_native"])
        w.writerows(raw_rows)

    richness={}
    all_islands={
        str(island["entity_ID"])
        for group in panel["groups"] for island in group["islands"]
    }
    for clade in CLADES:
        for eid in all_islands:
            p=present[(clade,eid)]
            u=uncertain[(clade,eid)]-p
            richness[(clade,eid)]={
                "richness":len(p),
                "uncertain_only_work_ids":len(u),
            }

    model_rows=build_model_rows(panel,protocol,richness)
    columns=protocol["H1_primary"]["per_clade_model_columns"]
    target=protocol["H1_primary"]["per_clade_target_column"]
    target_index=columns.index(target)

    point={}
    blocks={}
    for clade in CLADES:
        X,y,b=demean_clade(model_rows[clade],columns)
        beta=beta_from_xy(X,y)
        point[clade]=float(beta[target_index])
        blocks[clade]=b

    h1_point=float(sum(point.values())/3.0)
    h3_point=float(
        point["Pteridophyta"]-(point["Angiospermae"]+point["Gymnospermae"])/2.0
    )
    boot=replay_bootstrap(protocol,blocks,columns)
    h1_ci=interval(boot["H1_bootstrap"])
    h3_ci=interval(boot["H3_bootstrap"])
    clade_ci={
        clade:interval(boot["clade_target_bootstrap"][clade])
        for clade in CLADES
    }

    richness_rows=sorted(
        [
            {
                "clade":clade,
                "entity_ID":eid,
                **value,
            }
            for (clade,eid),value in richness.items()
        ],
        key=lambda row:(row["clade"],int(row["entity_ID"])),
    )
    query_set=sorted((clade,lid,taxon,eid) for (clade,lid,taxon),eid in query_map.items())
    output={
        "schema":"structural.gift_community_topology_outcome.v0_1",
        "status":"ONE_SHOT_COMMUNITY_RESPONSE_SCORED",
        "gift_version":VERSION,
        "pre_response_lock_sha256":sha(lock),
        "panel_fingerprint":panel["panel_fingerprint"],
        "protocol_fingerprint":protocol["protocol_fingerprint"],
        "response_access":{
            "species_composition_opened":True,
            "query_count_total":len(query_map),
            "query_count_by_clade":expected_query_counts,
            "query_set_sha256":sha(query_set),
            "all_frozen_surfaces_queried":True,
            "prior_pilot_archipelagos_queried":False,
        },
        "raw_response":{
            "rows":len(raw_rows),
            "sha256":sha(raw_rows),
            "source_receipts_sha256":sha(source_receipts),
            "species_names_reported":False,
        },
        "richness":{
            "rows":len(richness_rows),
            "sha256":sha(richness_rows),
            "zero_richness_rows":sum(row["richness"]==0 for row in richness_rows),
            "uncertain_only_total":sum(row["uncertain_only_work_ids"] for row in richness_rows),
        },
        "H1_primary":{
            "estimate":h1_point,
            "bootstrap_95_ci":h1_ci,
            "prediction":"positive",
            "supported":h1_ci[0]>0,
            "clade_component_estimates":point,
            "clade_component_bootstrap_95_ci":clade_ci,
        },
        "H2":{
            "status":"NOT_TESTED_TERMINAL_PRE_RESPONSE_NON_ESTIMABLE",
            "estimate":None,
            "bootstrap_95_ci":None,
        },
        "H3_primary":{
            "estimate":h3_point,
            "bootstrap_95_ci":h3_ci,
            "prediction":"negative",
            "supported":h3_ci[1]<0,
        },
        "bootstrap":{
            "accepted_replicates":len(boot["H1_bootstrap"]),
            "accepted_draws_sha256":boot["accepted_draws_sha256"],
            "candidate_draws_attempted":boot["candidate_draws_attempted"],
            "H1_estimates_sha256":sha(boot["H1_bootstrap"]),
            "H3_estimates_sha256":sha(boot["H3_bootstrap"]),
        },
        "claim_boundaries":[
            "richness is checklist-derived native richness under the frozen GIFT quality filters, not perfect census richness",
            "step-isolation gain is a response-independent geometric bottleneck metric, not a dispersal or colonization probability",
            "H2 geological-history moderation was terminally non-estimable before response and is not tested",
            "prior burned-pilot archipelagos are excluded from this response surface",
        ],
    }
    output["outcome_fingerprint"]=sha(output)
    print(json.dumps(output,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
