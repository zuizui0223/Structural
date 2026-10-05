#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_confirmatory_preaccess_contract_v1_138.json"
class Stop(RuntimeError): pass
PHASES=("BALA1","BALA2","BALA3")
ISLANDS=("FAI","FLO","PIC","SJG","SMG","SMR","TER")
DUMMY_ISLANDS=("FLO","PIC","SJG","SMG","SMR","TER")
CONT=("t0_other_source_count","nearest_surviving_source_euclidean_km","diffuse_surviving_source_euclidean_pressure")

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def clean(x): return str(x or "").strip()

def read_csv(path:Path,delimiter=","):
    with path.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h,delimiter=delimiter))

def event_map(path:Path):
    out={}
    for r in read_csv(path):
        eid=clean(r["eventID"]);phase=clean(r["phase"]);lineage=clean(r["lineage"]);island=lineage[:3]
        if phase not in PHASES or island not in ISLANDS:raise Stop("event-map identity drift")
        if eid in out and out[eid]!=(phase,island):raise Stop("eventID conflict")
        out[eid]=(phase,island)
    return out

def eligible_taxon(info):
    def u(field):return sorted({clean(x) for x in info[field] if clean(x)})
    sci,order,family,rank=(u("scientificName"),u("order"),u("family"),u("taxonRank"))
    if any(len(x)>1 for x in (sci,order,family,rank)):return False,"taxonomy_conflict"
    if len(order)!=1:return False,"order_missing"
    o=order[0].casefold();f=family[0].casefold() if len(family)==1 else ""
    mentions=" ".join(sci+order+family+rank).casefold()
    if "acari" in mentions or "collembola" in mentions:return False,"metadata_excluded_group"
    if o=="diptera":return False,"diptera_not_morphospecies_resolved"
    if o=="hymenoptera" and f!="formicidae":return False,"non_formicidae_hymenoptera_not_morphospecies_resolved"
    return True,"eligible"

def qty(x):
    try:v=float(clean(x))
    except ValueError as e:raise Stop(f"nonnumeric quantity: {x!r}") from e
    if not math.isfinite(v) or v<0:raise Stop("invalid quantity")
    return v

def hav(lat1,lon1,lat2,lon2):
    r=6371.0088;p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1);dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1.0,math.sqrt(a)))

def load_distances(geometry_path,edges_path,contract):
    if sha(geometry_path)!=contract["source_operator_parent"]["geometry_sha256"]:raise Stop("geometry SHA drift")
    if sha(edges_path)!=contract["source_operator_parent"]["edges_sha256"]:raise Stop("edge SHA drift")
    g=read_csv(geometry_path);coords={r["island"]:(float(r["latitude"]),float(r["longitude"])) for r in g}
    if set(coords)!=set(ISLANDS):raise Stop("island geometry drift")
    eu={(a,b):hav(*coords[a],*coords[b]) for a in ISLANDS for b in ISLANDS}
    inf=float("inf");gd={(a,b):(0.0 if a==b else inf) for a in ISLANDS for b in ISLANDS}
    for r in read_csv(edges_path):
        a,b=clean(r["from_island"]),clean(r["to_island"]);w=float(r["haversine_km"])
        gd[(a,b)]=gd[(b,a)]=min(gd[(a,b)],w)
    for k in ISLANDS:
        for i in ISLANDS:
            for j in ISLANDS:
                gd[(i,j)]=min(gd[(i,j)],gd[(i,k)]+gd[(k,j)])
    if any(not math.isfinite(gd[(i,j)]) for i in ISLANDS for j in ISLANDS):raise Stop("graph disconnected")
    return eu,gd

def feature_row(p0,p1,target,eu,gd,lam):
    lost=p0-p1
    if len(lost)!=1 or target not in p1:raise Stop("feature row outside exactly-one-loss route")
    lost_source=next(iter(lost))
    t0_other=p0-{target};surv=p1-{target}
    if not t0_other:raise Stop("target has no other t0 source")
    den=sum(math.exp(-gd[(target,s)]/lam) for s in t0_other)
    num=math.exp(-gd[(target,lost_source)]/lam)
    E=num/den
    if surv:
        nearest=min(eu[(target,s)] for s in surv)
        pressure=sum(math.exp(-eu[(target,s)]/lam) for s in surv)
        empty=0.0
    else:
        nearest=0.0;pressure=0.0;empty=1.0
    return {
      "target_island":target,
      "t0_other_source_count":float(len(t0_other)),
      "nearest_surviving_source_euclidean_km":nearest,
      "diffuse_surviving_source_euclidean_pressure":pressure,
      "surviving_source_empty":empty,
      "E_i":E,
      "lost_source":lost_source
    }

def parse_pilot_presence(path:Path,expected_sha:str):
    if sha(path)!=expected_sha:raise Stop("pilot presence SHA drift")
    rows=read_csv(path);by=defaultdict(lambda:defaultdict(set))
    for r in rows:
        if int(r["present"]) not in (0,1):raise Stop("pilot presence domain drift")
        if int(r["present"])==1:by[r["MF_token"]][r["phase"]].add(r["island"])
        else:by[r["MF_token"]][r["phase"]]|=set()
    return by

def parse_confirmatory_t01(path:Path,emap):
    rows=read_csv(path,delimiter="\t")
    info=defaultdict(lambda:defaultdict(list));obs=defaultdict(lambda:defaultdict(set))
    for r in rows:
        token=clean(r["identificationRemarks"]);eid=clean(r["eventID"]);core=clean(r["id"])
        if eid!=core:raise Stop("confirmatory t0/t1 eventID-coreid mismatch")
        if core not in emap:raise Stop("confirmatory t0/t1 row outside frozen pitfall map")
        phase,island=emap[core]
        if phase not in {"BALA1","BALA2"}:raise Stop("t2 row entered t0/t1 semantic surface")
        for f in ("scientificName","order","family","taxonRank"):info[token][f].append(clean(r[f]))
        if clean(r["organismQuantityType"]).casefold()!="individuals":raise Stop("quantity type drift")
        if qty(r["organismQuantity"])>0:obs[token][phase].add(island)
    return info,obs,len(rows)

def standardize(train_rows):
    stats={}
    for key in CONT:
        vals=np.array([r[key] for r in train_rows],dtype=float)
        m=float(vals.mean());sd=float(np.sqrt(np.mean((vals-m)**2)))
        if not sd>0:raise Stop(f"zero variance continuous predictor: {key}")
        stats[key]=(m,sd)
    return stats

def design(rows,stats,include_E):
    cols=["intercept"]+[f"island_{x}" for x in DUMMY_ISLANDS]+[f"z_{x}" for x in CONT]+["surviving_source_empty"]
    if include_E:cols+=["E_i"]
    X=[]
    for r in rows:
        v=[1.0]+[1.0 if r["target_island"]==x else 0.0 for x in DUMMY_ISLANDS]
        v += [(r[k]-stats[k][0])/stats[k][1] for k in CONT]
        v += [r["surviving_source_empty"]]
        if include_E:v += [r["E_i"]]
        X.append(v)
    return np.asarray(X,dtype=float),cols

def sigmoid(z):
    z=np.asarray(z,dtype=float)
    out=np.empty_like(z);pos=z>=0
    out[pos]=1/(1+np.exp(-z[pos]));ez=np.exp(z[~pos]);out[~pos]=ez/(1+ez)
    return out

def fit_ridge(X,y,lam,maxiter,tol):
    beta=np.zeros(X.shape[1],dtype=float);pen=np.ones(X.shape[1]);pen[0]=0.0
    for it in range(maxiter):
        p=sigmoid(X@beta);w=np.maximum(p*(1-p),1e-12)
        grad=X.T@(p-y)+lam*pen*beta
        H=X.T@(X*w[:,None])+np.diag(lam*pen)
        try:step=np.linalg.solve(H,grad)
        except np.linalg.LinAlgError as e:raise Stop("ridge Hessian solve failed") from e
        beta2=beta-step
        if float(np.max(np.abs(beta2-beta)))<tol:return beta2,it+1
        beta=beta2
    raise Stop("ridge model did not converge")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pilot_presence",type=Path)
    ap.add_argument("confirmatory_t0t1_surface",type=Path)
    ap.add_argument("pitfall_position_recovery",type=Path)
    ap.add_argument("geometry",type=Path)
    ap.add_argument("edges",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--eligibility",type=Path,required=True)
    ap.add_argument("--predictors",type=Path,required=True)
    ap.add_argument("--predictions",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c["schema"]!="structural.bala_confirmatory_preaccess_contract.v1_138":raise Stop("contract schema drift")
        eu,gd=load_distances(a.geometry,a.edges,c);lam=float(c["source_operator"]["graph_kernel_lambda_km"])
        pilot=parse_pilot_presence(a.pilot_presence,c["pilot_parent"]["presence_sha256"])
        emap=event_map(a.pitfall_position_recovery)
        info,obs,nrows=parse_confirmatory_t01(a.confirmatory_t0t1_surface,emap)

        # Pilot training rows.
        train=[]
        for token,ph in pilot.items():
            p0=set(ph.get("BALA1",set()));p1=set(ph.get("BALA2",set()));p2=set(ph.get("BALA3",set()))
            if len(p0)>=2 and len(p0-p1)==1 and len(p1)>=1:
                for target in sorted(p1):
                    fr=feature_row(p0,p1,target,eu,gd,lam)
                    fr.update({"MF_token":token,"y":0 if target in p2 else 1})
                    train.append(fr)
        if len(train)!=22:raise Stop(f"pilot training row count drift: {len(train)}")
        y=np.array([r["y"] for r in train],dtype=float)
        if set(y)!={0.0,1.0}:raise Stop("pilot training endpoint class collapse")

        eligibility=[];predrows=[];qual_taxa=set()
        for token in sorted(info):
            ok,reason=eligible_taxon(info[token]);eligibility.append({"MF_token":token,"eligible":str(ok).lower(),"reason":reason})
            if not ok:continue
            p0=set(obs[token].get("BALA1",set()));p1=set(obs[token].get("BALA2",set()))
            if len(p0)>=2 and len(p0-p1)==1 and len(p1)>=1:
                qual_taxa.add(token)
                for target in sorted(p1):
                    fr=feature_row(p0,p1,target,eu,gd,lam);fr["MF_token"]=token;predrows.append(fr)

        min_taxa=int(c["transition_population"]["minimum_confirmatory_taxon_clusters_before_t2"])
        min_rows=int(c["transition_population"]["minimum_confirmatory_target_rows_before_t2"])
        if len(qual_taxa)<min_taxa or len(predrows)<min_rows:
            raise Stop(f"confirmatory t0/t1 estimability failed: taxa={len(qual_taxa)} rows={len(predrows)}")

        stats=standardize(train)
        X2,cols2=design(train,stats,False);XC,colsC=design(train,stats,True)
        lamridge=float(c["model"]["ridge_lambda"])
        b2,it2=fit_ridge(X2,y,lamridge,int(c["model"]["max_iterations"]),float(c["model"]["coefficient_tolerance"]))
        bC,itC=fit_ridge(XC,y,lamridge,int(c["model"]["max_iterations"]),float(c["model"]["coefficient_tolerance"]))
        Z2,_=design(predrows,stats,False);ZC,_=design(predrows,stats,True)
        cliplo,cliphi=map(float,c["model"]["probability_clip"])
        p2=np.clip(sigmoid(Z2@b2),cliplo,cliphi);pC=np.clip(sigmoid(ZC@bC),cliplo,cliphi)
        diff=int(np.sum(np.abs(pC-p2)>float(c["confirmatory_prediction_freeze"]["difference_threshold"])))
        if diff<int(c["confirmatory_prediction_freeze"]["minimum_probability_difference_cells"]):
            raise Stop("R2/C prediction surfaces are numerically identical")

        a.eligibility.parent.mkdir(parents=True,exist_ok=True)
        with a.eligibility.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=["MF_token","eligible","reason"],lineterminator="\n");w.writeheader();w.writerows(eligibility)
        fields=["MF_token","target_island","lost_source","t0_other_source_count","nearest_surviving_source_euclidean_km","diffuse_surviving_source_euclidean_pressure","surviving_source_empty","E_i"]
        with a.predictors.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader()
            for r in predrows:w.writerow({k:r[k] for k in fields})
        with a.predictions.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["MF_token","target_island","p_R2","p_C"])
            for r,u,v in zip(predrows,p2,pC):w.writerow([r["MF_token"],r["target_island"],format(float(u),".17g"),format(float(v),".17g")])

        receipt={
          "schema":"structural.bala_confirmatory_preaccess_result.v1_138",
          "status":"BALA_CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_T2_ACCESS",
          "pilot_training_rows":len(train),"pilot_training_contractions":int(y.sum()),"pilot_training_persistences":int(len(y)-y.sum()),
          "confirmatory_t0_t1_rows_semantically_opened":nrows,
          "confirmatory_taxa_seen_t0_t1":len(info),"confirmatory_taxonomically_eligible_t0_t1":sum(r["eligible"]=="true" for r in eligibility),
          "confirmatory_exactly_one_loss_taxa":len(qual_taxa),"confirmatory_target_rows":len(predrows),
          "R2_columns":cols2,"C_columns":colsC,
          "standardization":{k:{"mean":stats[k][0],"sd":stats[k][1]} for k in CONT},
          "R2_coefficients":[float(x) for x in b2],"C_coefficients":[float(x) for x in bC],
          "R2_iterations":it2,"C_iterations":itC,
          "prediction_difference_cells_gt_1e_12":diff,
          "eligibility_sha256":sha(a.eligibility),"predictors_sha256":sha(a.predictors),"predictions_sha256":sha(a.predictions),
          "pilot_model_parameters_are_training_only_not_evidence":True,
          "t2_surface_semantically_opened":False,"t2_values_used":False,"t2_scoring_authorized":False,
          "source_loss_effect_claim_authorized":False
        }
        code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        receipt={"schema":"structural.bala_confirmatory_preaccess_result.v1_138","status":"STOP","reason":str(e),
          "t2_surface_semantically_opened":False,"t2_values_used":False,"t2_scoring_authorized":False,
          "source_loss_effect_claim_authorized":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
