#!/usr/bin/env python3
"""Pilot-only feasibility test for a hierarchical multi-species GIFT model.

Consumes only the already-frozen burned-pilot artifact. It may fit R3 and C
models to establish numerical/row support, but it deliberately does not compute
or emit predictive loss, C-R3 direction, H1/H2/H3 effects, or any confirmatory
statistic.
"""
from __future__ import annotations

from collections import defaultdict
import argparse, csv, hashlib, json, math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
from sklearn.linear_model import LogisticRegression

BASE="https://gift.uni-goettingen.de/api/extended/"
VERSION="3.2"
SCALES=(25.0,50.0,125.0,250.0)
CLIMATE=(
    "wc2.0_bio_30s_01","wc2.0_bio_30s_05","wc2.0_bio_30s_06",
    "wc2.0_bio_30s_12","wc2.0_bio_30s_15",
)
MISC=("area","dist","SLMP","GMMC","longitude","latitude")
MAX_ITER=2000

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def load(path):
    x=json.loads(Path(path).read_text())
    if not isinstance(x,dict): raise RuntimeError(f"{path} must contain object")
    return x

def fetch(query,**extra):
    url=BASE+f"index{VERSION}.php?"+urlencode({"query":query,**{k:str(v) for k,v in extra.items()}})
    req=Request(url,headers={"User-Agent":"Structural-GIFT-hierarchical-feasibility/0.1"})
    with urlopen(req,timeout=180) as r: raw=r.read()
    rows=json.loads(raw)
    if not isinstance(rows,list): raise RuntimeError(f"{query}: expected list")
    return rows,{"url":url,"rows":len(rows),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def s(x): return "" if x is None else str(x)

def as01(x):
    try:return int(float(x))
    except (TypeError,ValueError):return None

def explicit_true(x): return as01(x)==1

def hav(lon1,lat1,lon2,lat2):
    R=6371.0088
    a1,a2=map(math.radians,(lat1,lat2))
    da=a2-a1;dl=math.radians(lon2-lon1)
    z=math.sin(da/2)**2+math.cos(a1)*math.cos(a2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1,math.sqrt(z)))

def balanced_blocks(ids,lon,lat,k=4):
    ids=sorted(ids,key=int);pairs=[]
    for j,a in enumerate(ids):
        for b in ids[j+1:]:
            pairs.append((hav(float(lon[a]),float(lat[a]),float(lon[b]),float(lat[b])),-int(a),-int(b),a,b))
    _,_,_,a,b=max(pairs)
    scored=[]
    for eid in ids:
        da=hav(float(lon[eid]),float(lat[eid]),float(lon[a]),float(lat[a]))
        db=hav(float(lon[eid]),float(lat[eid]),float(lon[b]),float(lat[b]))
        scored.append((da-db,int(eid),eid))
    ordered=[r[2] for r in sorted(scored)]
    base,rem=divmod(len(ordered),k); sizes=[base+(1 if j<rem else 0) for j in range(k)]
    out={};cur=0
    for j,size in enumerate(sizes,1):
        for eid in ordered[cur:cur+size]: out[eid]=f"B{j}"
        cur+=size
    return out,sizes

def adjacency_components(ids,distmat,radius):
    ids=list(ids); n=len(ids)
    adj=[[] for _ in range(n)]
    for i in range(n):
        for j in range(i+1,n):
            if distmat[i,j] <= radius:
                adj[i].append(j);adj[j].append(i)
    comp=[None]*n; comps=[]
    for i in range(n):
        if comp[i] is not None: continue
        stack=[i]; members=[]; cid=len(comps); comp[i]=cid
        while stack:
            x=stack.pop();members.append(x)
            for y in adj[x]:
                if comp[y] is None:
                    comp[y]=cid;stack.append(y)
        comps.append(members)
    return comp,comps

def canonical_raw_hash(rows):
    vals=[]
    for r in rows:
        vals.append((
            str(r["list_ID"]),str(r["entity_ID"]),str(r["work_ID"]),
            as01(r.get("native")),as01(r.get("questionable")),as01(r.get("quest_native"))
        ))
    vals.sort(key=lambda x:(int(x[0]),int(x[2]),int(x[1])))
    return sha(vals)

def prepare_presence(raw_rows):
    present=defaultdict(set); uncertain=defaultdict(set)
    for r in raw_rows:
        eid=str(r["entity_ID"]); wid=str(r["work_ID"])
        native=as01(r.get("native"))
        if native==1 and not explicit_true(r.get("questionable")) and not explicit_true(r.get("quest_native")):
            present[eid].add(wid)
        elif native==1:
            uncertain[eid].add(wid)
    return present,uncertain

def feature_cache(ids,misc):
    ids=list(ids);n=len(ids)
    lon=np.asarray([float(misc["longitude"][eid]) for eid in ids])
    lat=np.asarray([float(misc["latitude"][eid]) for eid in ids])
    dm=np.zeros((n,n),float)
    for i in range(n):
        for j in range(i+1,n):
            d=hav(lon[i],lat[i],lon[j],lat[j]);dm[i,j]=dm[j,i]=d
    comps={}
    for radius in SCALES:
        comps[radius]=adjacency_components(ids,dm,radius)
    nearest_other=[]
    for i in range(n):
        vals=[dm[i,j] for j in range(n) if j!=i]
        nearest_other.append(min(vals))
    area=np.asarray([float(misc["area"][eid]) for eid in ids])
    mainland=np.asarray([float(misc["dist"][eid]) for eid in ids])
    surrounding_island=[]
    surrounding_land=[]
    unanchored=[]
    mainland_step=[]
    for i in range(n):
        sp=[];sl=[];ue=[];ms=[]
        for radius in SCALES:
            sp.append(math.log1p(sum(math.exp(-dm[i,j]/radius) for j in range(n) if j!=i)))
            sl.append(math.log1p(sum(area[j]*math.exp(-dm[i,j]/radius) for j in range(n) if j!=i)))
            comp,cc=comps[radius]
            members=cc[comp[i]]
            ue.append((len(members)-1)/(n-1))
            ms.append(1.0 if any(mainland[j] <= radius for j in members) else 0.0)
        surrounding_island.append(float(np.mean(sp)))
        surrounding_land.append(float(np.mean(sl)))
        unanchored.append(float(np.mean(ue)))
        mainland_step.append(float(np.mean(ms)))
    return {
        "ids":ids,"index":{eid:i for i,eid in enumerate(ids)},"dm":dm,"comps":comps,
        "nearest_other":np.asarray(nearest_other),"surrounding_island":np.asarray(surrounding_island),
        "surrounding_land":np.asarray(surrounding_land),"unanchored":np.asarray(unanchored),
        "mainland_step":np.asarray(mainland_step),
    }

def row_features(eid,wid,train_ids,present,cache,misc,climate,is_training_row):
    i=cache["index"][eid]
    anchors=[a for a in train_ids if wid in present[a] and (not is_training_row or a!=eid)]
    if not anchors: return None
    aidx=[cache["index"][a] for a in anchors]
    dists=[cache["dm"][i,j] for j in aidx]
    nearest=min(dists)
    source=[];source_area=[]
    for radius in SCALES:
        source.append(math.log1p(sum(math.exp(-cache["dm"][i,j]/radius) for j in aidx)))
        source_area.append(math.log1p(sum(float(misc["area"][anchors[k]])*math.exp(-cache["dm"][i,j]/radius) for k,j in enumerate(aidx))))
    eog=[]
    for radius in SCALES:
        comp,cc=cache["comps"][radius]
        members=set(cc[comp[i]])
        eog.append(1.0 if any(j in members for j in aidx) else 0.0)
    r3=[
        *[float(climate[layer][eid]) for layer in CLIMATE],
        math.log(max(float(misc["area"][eid]),1e-12)),
        math.log1p(float(misc["dist"][eid])),
        nearest,
        float(np.mean(source)),
        float(np.mean(source_area)),
        float(misc["SLMP"][eid]),
        float(misc["GMMC"][eid]),
        float(cache["nearest_other"][i]),
        float(cache["surrounding_island"][i]),
        float(cache["surrounding_land"][i]),
        float(cache["unanchored"][i]),
        float(cache["mainland_step"][i]),
    ]
    return np.asarray(r3,float),float(np.mean(eog))

def build_matrix(ids,train_ids,species,present,uncertain,cache,misc,climate,training):
    X=[];E=[];Y=[];S=[]
    for si,wid in enumerate(species):
        for eid in ids:
            if wid in uncertain[eid] and wid not in present[eid]:
                continue
            target=1 if wid in present[eid] else 0
            feats=row_features(eid,wid,train_ids,present,cache,misc,climate,training)
            if feats is None: continue
            r3,eog=feats
            X.append(r3);E.append(eog);Y.append(target);S.append(si)
    if not X:
        return None
    return np.vstack(X),np.asarray(E,float),np.asarray(Y,int),np.asarray(S,int)

def design(train,test,n_species,include_eog):
    Xtr,Etr,Ytr,Str=train; Xte,Ete,Yte,Ste=test
    mu=Xtr.mean(axis=0); sd=Xtr.std(axis=0)
    keep=sd>1e-12
    Ztr=(Xtr[:,keep]-mu[keep])/sd[keep]
    Zte=(Xte[:,keep]-mu[keep])/sd[keep]
    eog_sd=float(Etr.std())
    if include_eog and eog_sd>1e-12:
        em=float(Etr.mean())
        Ztr=np.column_stack([Ztr,(Etr-em)/eog_sd])
        Zte=np.column_stack([Zte,(Ete-em)/eog_sd])
        eog_retained=True
    else:
        eog_retained=False
    one_tr=np.zeros((len(Str),n_species),float); one_tr[np.arange(len(Str)),Str]=1.0
    one_te=np.zeros((len(Ste),n_species),float); one_te[np.arange(len(Ste)),Ste]=1.0
    return np.column_stack([one_tr,Ztr]),np.column_stack([one_te,Zte]),Ytr,Yte,eog_retained,int(keep.sum())

def fit_check(Xtr,Ytr,Xte):
    if len(set(Ytr.tolist()))<2: return False,False,None
    model=LogisticRegression(C=1.0,penalty="l2",solver="lbfgs",fit_intercept=False,max_iter=MAX_ITER)
    model.fit(Xtr,Ytr)
    converged=bool(np.max(model.n_iter_)<MAX_ITER)
    pr=model.predict_proba(Xte)[:,1]
    finite=bool(np.isfinite(pr).all() and np.all((pr>=0)&(pr<=1)))
    return converged,finite,(float(pr.min()),float(pr.max()))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw",type=Path,required=True)
    ap.add_argument("--universe",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--terminal",type=Path,required=True)
    a=ap.parse_args()

    u=load(a.universe); p=load(a.protocol); t=load(a.terminal)
    taxon=p["taxon_name"]
    if t["status"]!="TERMINAL_STOP_NON_ESTIMABLE": raise RuntimeError("v1 terminal STOP required")
    if t["taxon_name"]!=taxon or t["universe_fingerprint"]!=u["universe_fingerprint"] or t["protocol_fingerprint"]!=p["protocol_fingerprint"]:
        raise RuntimeError("v1 provenance drift")
    raw_rows=list(csv.DictReader(a.raw.open(encoding="utf-8",newline="")))
    if canonical_raw_hash(raw_rows)!=t["raw_response_sha256"]: raise RuntimeError("frozen pilot raw-response hash mismatch")

    misc={}; meta={}
    for var in MISC:
        rows,m=fetch("geoentities_env_misc",envvar=var); misc[var]={s(r["entity_ID"]):r.get(var) for r in rows};meta[var]=m
        if m["sha256"]!=u["source_sha256"]["misc"][var]: raise RuntimeError(f"safe predictor drift: {var}")
    climate={}
    for layer in CLIMATE:
        rows,m=fetch("geoentities_env_raster",layername=layer,sumstat="mean");climate[layer]={s(r["entity_ID"]):r.get("mean") for r in rows};meta[layer]=m
        if m["sha256"]!=u["source_sha256"]["climate"][layer]: raise RuntimeError(f"safe predictor drift: {layer}")

    present,uncertain=prepare_presence(raw_rows)
    groups={g["archipelago_id"]:g for g in u["groups"]}
    pilot_ids=p["pilot_selection"]["pilot_archipelagos"]
    audits=[]
    for gid in pilot_ids:
        g=groups[gid]; ids=[str(x) for x in g["entity_ids"]]
        blocks,sizes=balanced_blocks(ids,misc["longitude"],misc["latitude"],4)
        if sizes!=g["block_sizes"] or sha(sorted((eid,blocks[eid]) for eid in ids))!=g["block_assignment_sha256"]:
            raise RuntimeError(f"block replay drift: {gid}")
        cache=feature_cache(ids,misc)
        folds=[]
        for block in ("B1","B2","B3","B4"):
            train_ids=[eid for eid in ids if blocks[eid]!=block]
            test_ids=[eid for eid in ids if blocks[eid]==block]
            # Development rule: species needs >=2 training presences so every
            # positive training row has at least one self-excluded source, and
            # >=1 training absence so prevalence is not structurally all-one.
            species=sorted({
                wid for eid in train_ids for wid in present[eid]
                if sum(wid in present[x] for x in train_ids)>=2
                and sum((wid not in present[x]) and (wid not in uncertain[x]) for x in train_ids)>=1
            },key=int)
            train=build_matrix(train_ids,train_ids,species,present,uncertain,cache,misc,climate,True)
            test=build_matrix(test_ids,train_ids,species,present,uncertain,cache,misc,climate,False)
            if train is None or test is None:
                folds.append({"block":block,"valid":False,"reason":"empty_matrix"})
                continue
            ref=design(train,test,len(species),False)
            cand=design(train,test,len(species),True)
            r_conv,r_fin,_=fit_check(ref[0],ref[2],ref[1])
            c_conv,c_fin,_=fit_check(cand[0],cand[2],cand[1])
            eog_retained=cand[4]
            valid=(
                len(species)>=10 and len(ref[3])>=50
                and r_conv and r_fin and c_conv and c_fin and eog_retained
            )
            folds.append({
                "block":block,"train_species":len(species),
                "train_rows":len(ref[2]),"test_rows":len(ref[3]),
                "train_positive":int(ref[2].sum()),"train_negative":int(len(ref[2])-ref[2].sum()),
                "reference_numeric_predictors_retained":ref[5],
                "candidate_eog_retained":eog_retained,
                "reference_converged":r_conv,"candidate_converged":c_conv,
                "reference_predictions_finite":r_fin,"candidate_predictions_finite":c_fin,
                "valid":valid,
            })
        valid_folds=sum(x.get("valid",False) for x in folds)
        audits.append({
            "archipelago_id":gid,"support_class":g["support_class"],
            "valid_folds":valid_folds,"archipelago_pass":valid_folds>=3,
            "folds":folds,
        })

    passing=[x for x in audits if x["archipelago_pass"]]
    has_extreme=any(x["support_class"] in {"extreme_only","paired"} for x in passing)
    has_nonextreme=any(x["support_class"] in {"nonextreme_only","paired"} for x in passing)
    passed=len(passing)>=2 and has_extreme and has_nonextreme
    out={
        "schema":"structural.gift_multispecies_hierarchical_feasibility.v0_2",
        "status":"HIERARCHICAL_FEASIBILITY_PASS" if passed else "HIERARCHICAL_FEASIBILITY_STOP",
        "taxon_name":taxon,
        "development_data":"frozen v1 burned-pilot response only",
        "confirmatory_response_opened":False,
        "confirmatory_query_count":0,
        "v1_terminal_receipt_sha256":t["terminal_receipt_sha256"],
        "v1_protocol_fingerprint":p["protocol_fingerprint"],
        "universe_fingerprint":u["universe_fingerprint"],
        "model_family":{
            "response":"species x island native checklist incidence",
            "species_effect":"L2-penalized species one-hot intercepts",
            "shared_slopes":"frozen R3 island/source features",
            "candidate_addition":"species-conditioned EOG connected frequency",
            "lambda":1.0,
            "training_species_rule":">=2 training presences and >=1 unambiguous training absence",
            "effect_direction_inspected":False,
            "loss_difference_computed":False,
        },
        "fold_gate":{
            "minimum_training_species":10,
            "minimum_test_rows":50,
            "reference_and_candidate_must_converge":True,
            "candidate_eog_must_be_nonconstant":True,
        },
        "archipelago_gate":"at least 3 of 4 folds valid",
        "study_gate":"at least 2 of 3 pilot archipelagos pass, with >=1 extreme contributor and >=1 non-extreme contributor",
        "archipelago_audits":audits,
        "feasibility_pass":passed,
        "confirmatory_response_authorized":False,
        "effect_size":None,
        "prediction_score":None,
        "predictive_denominator_contribution":0,
    }
    out["receipt_sha256"]=sha(out)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if passed else 2

if __name__=="__main__":
    raise SystemExit(main())
