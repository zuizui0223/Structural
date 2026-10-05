#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,decimal,hashlib,json,math,random
from collections import defaultdict
from pathlib import Path

from src.structural.boreal_confirmatory_model import (
    BorealConfirmatoryModelError,
    fit_ridge_logistic,
    predict_probability,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_IMPL=ROOT/"development/bala_t2_scoring_implementation_v1_141.json"

class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def dec(raw:bytes)->str:
    try: return raw.decode("utf-8").strip()
    except UnicodeDecodeError as e: raise Stop("UTF-8 decode failed") from e

def qnum(s:str)->decimal.Decimal:
    try: x=decimal.Decimal(s)
    except decimal.InvalidOperation as e: raise Stop(f"nonnumeric organismQuantity: {s!r}") from e
    if not x.is_finite() or x<0: raise Stop(f"invalid organismQuantity: {s!r}")
    return x

def load_event_map(path):
    with path.open("r",encoding="utf-8",newline="") as h: rows=list(csv.DictReader(h))
    out={}
    for r in rows:
        eid=str(r["eventID"]).strip()
        ph=str(r["phase"]).strip()
        island=str(r["lineage"])[:3]
        out[eid]=(ph,island)
    return out

def read_csv(path):
    with path.open("r",encoding="utf-8",newline="") as h: return list(csv.DictReader(h))

def logloss(p,y):
    return -math.log(p) if y==1 else -math.log1p(-p)

def type7(xs,p):
    x=sorted(xs);n=len(x)
    if n<1: raise Stop("empty quantile vector")
    h=(n-1)*p;lo=int(math.floor(h));hi=int(math.ceil(h))
    return x[lo] if lo==hi else x[lo]*(hi-h)+x[hi]*(h-lo)

def ranks(xs):
    order=sorted(range(len(xs)),key=lambda i:(xs[i],i))
    r=[0.0]*len(xs);j=0
    while j<len(order):
        k=j+1
        while k<len(order) and xs[order[k]]==xs[order[j]]: k+=1
        rr=((j+1)+k)/2.0
        for i in order[j:k]: r[i]=rr
        j=k
    return r

def pearson(x,y):
    mx=math.fsum(x)/len(x);my=math.fsum(y)/len(y)
    dx=[a-mx for a in x];dy=[b-my for b in y]
    den=math.sqrt(math.fsum(a*a for a in dx)*math.fsum(b*b for b in dy))
    return math.nan if den==0 else math.fsum(a*b for a,b in zip(dx,dy))/den

def spearman(x,y):
    return pearson(ranks(x),ranks(y))

def design_row(row,stats,dropped,include_E,impl):
    islands=impl["design_columns"]["island_dummies_reference_FAI"]
    vals=[1.0]
    target=row["target_island"]
    vals.extend(1.0 if target==isl else 0.0 for isl in islands)
    names=["intercept"]+[f"island_{isl}" for isl in islands]

    for col in impl["design_columns"]["standardized_R2_continuous"]:
        if col in dropped: continue
        if col not in stats: raise Stop(f"missing standardization constant: {col}")
        m=float(stats[col]["mean"]);sd=float(stats[col]["sd"])
        if not sd>0: raise Stop(f"invalid SD: {col}")
        vals.append((float(row[col])-m)/sd);names.append("z_"+col)

    for col in impl["design_columns"]["R2_binary"]:
        vals.append(float(row[col]));names.append(col)

    if include_E:
        col="E_i_lost_access_fraction"
        if col not in stats: raise Stop("missing E_i standardization")
        m=float(stats[col]["mean"]);sd=float(stats[col]["sd"])
        if not sd>0: raise Stop("invalid E_i SD")
        vals.append((float(row[col])-m)/sd);names.append("z_"+col)
    return tuple(vals),tuple(names)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("t2_surface",type=Path)
    ap.add_argument("features",type=Path)
    ap.add_argument("fold_manifest",type=Path)
    ap.add_argument("fold_standardization",type=Path)
    ap.add_argument("pitfall_position_recovery",type=Path)
    ap.add_argument("--expected-t2-sha",required=True)
    ap.add_argument("--expected-features-sha",required=True)
    ap.add_argument("--expected-fold-manifest-sha",required=True)
    ap.add_argument("--expected-fold-standardization-sha",required=True)
    ap.add_argument("--implementation",type=Path,default=DEFAULT_IMPL)
    ap.add_argument("--outcomes",type=Path,required=True)
    ap.add_argument("--taxon-scores",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        impl=json.loads(a.implementation.read_text())
        if impl["schema"]!="structural.bala_t2_scoring_implementation.v1_141": raise Stop("implementation schema drift")
        checks=((a.t2_surface,a.expected_t2_sha),(a.features,a.expected_features_sha),
                (a.fold_manifest,a.expected_fold_manifest_sha),(a.fold_standardization,a.expected_fold_standardization_sha))
        for p,s in checks:
            if sha(p)!=s: raise Stop(f"SHA drift: {p.name}")

        feature_rows=read_csv(a.features)
        if not feature_rows: raise Stop("empty feature table")
        bytax=defaultdict(list)
        for r in feature_rows: bytax[r["MF_token"]].append(r)
        eligible=set(bytax)
        fold_rows=read_csv(a.fold_manifest)
        fold_info={r["heldout_MF_token"]:r for r in fold_rows}
        if set(fold_info)!=eligible: raise Stop("fold/token set mismatch")
        fold_stats=json.loads(a.fold_standardization.read_text())
        if set(fold_stats)!=eligible: raise Stop("standardization/token set mismatch")

        event_map=load_event_map(a.pitfall_position_recovery)
        raw=a.t2_surface.read_bytes().splitlines()
        if len(raw)<2: raise Stop("t2 surface empty")
        idx={"coreid":0,"organismQuantity":12,"MF":20};nfields=32
        t2_present=defaultdict(set)
        token_rows_decoded=eligible_rows_decoded=quantity_values_decoded=0

        eligible_bytes={tok.encode("utf-8"):tok for tok in eligible}
        for rn,line in enumerate(raw[1:],1):
            fields=line.split(b"\t")
            if len(fields)!=nfields: raise Stop(f"t2 field-count drift row {rn}")
            token_rows_decoded+=1
            tok_raw=fields[idx["MF"]].strip()
            tok=eligible_bytes.get(tok_raw)
            if tok is None:
                continue
            eligible_rows_decoded+=1
            coreid=dec(fields[idx["coreid"]])
            if coreid not in event_map: raise Stop("eligible t2 row outside pitfall map")
            ph,island=event_map[coreid]
            if ph!="BALA3": raise Stop("non-BALA3 row in t2 surface")
            qty=qnum(dec(fields[idx["organismQuantity"]]));quantity_values_decoded+=1
            if qty>0: t2_present[tok].add(island)

        outcome_rows=[]
        for tok in sorted(eligible):
            for r in bytax[tok]:
                target=r["target_island"]
                persistence=int(target in t2_present[tok])
                y=0 if persistence else 1
                rr=dict(r);rr["t2_outcome_contraction"]=y
                outcome_rows.append(rr)

        bytax_out=defaultdict(list)
        for r in outcome_rows: bytax_out[r["MF_token"]].append(r)

        score_rows=[];deltas=[]
        minc=impl["fold_logic"]["minimum_training_contractions"]
        minp=impl["fold_logic"]["minimum_training_persistences"]

        for tok in sorted(eligible):
            fmeta=fold_info[tok];st=fold_stats[tok]
            if str(fmeta["prefeature_estimable"]).lower()!="true" or not st["prefeature_estimable"]:
                score_rows.append({"MF_token":tok,"status":"prefeature_nonestimable","heldout_rows":len(bytax_out[tok]),
                    "heldout_contractions":"","heldout_persistences":"","R2_logloss":"","C_logloss":"","C_minus_R2":""})
                continue
            train=[r for r in outcome_rows if r["MF_token"]!=tok]
            test=bytax_out[tok]
            ytrain=[int(r["t2_outcome_contraction"]) for r in train]
            contractions=sum(ytrain);persistences=len(ytrain)-contractions
            if contractions<minc or persistences<minp:
                score_rows.append({"MF_token":tok,"status":"training_class_nonestimable","heldout_rows":len(test),
                    "heldout_contractions":sum(int(r["t2_outcome_contraction"]) for r in test),
                    "heldout_persistences":len(test)-sum(int(r["t2_outcome_contraction"]) for r in test),
                    "R2_logloss":"","C_logloss":"","C_minus_R2":""})
                continue
            dropped=set(st["dropped_zero_variance_R2"])
            Xr=[];Xc=[];yr=[]
            cols_r=None;cols_c=None
            for r in train:
                xr,cr=design_row(r,st["standardization"],dropped,False,impl)
                xc,cc=design_row(r,st["standardization"],dropped,True,impl)
                if cols_r is None: cols_r,cols_c=cr,cc
                if cr!=cols_r or cc!=cols_c: raise Stop("design column drift")
                Xr.append(xr);Xc.append(xc);yr.append(int(r["t2_outcome_contraction"]))
            fitr=fit_ridge_logistic(Xr,yr,columns=cols_r,ridge_lambda=1.0,max_iterations=100,tolerance=1e-8)
            fitc=fit_ridge_logistic(Xc,yr,columns=cols_c,ridge_lambda=1.0,max_iterations=100,tolerance=1e-8)
            lr=[];lc=[]
            for r in test:
                xr,_=design_row(r,st["standardization"],dropped,False,impl)
                xc,_=design_row(r,st["standardization"],dropped,True,impl)
                y=int(r["t2_outcome_contraction"])
                lr.append(logloss(predict_probability(xr,fitr),y))
                lc.append(logloss(predict_probability(xc,fitc),y))
            mr=math.fsum(lr)/len(lr);mc=math.fsum(lc)/len(lc);delta=mc-mr
            deltas.append(delta)
            hc=sum(int(r["t2_outcome_contraction"]) for r in test)
            score_rows.append({"MF_token":tok,"status":"estimable","heldout_rows":len(test),
                "heldout_contractions":hc,"heldout_persistences":len(test)-hc,
                "R2_logloss":repr(mr),"C_logloss":repr(mc),"C_minus_R2":repr(delta)})

        minclusters=impl["fold_logic"]["minimum_primary_estimable_taxa"]
        if len(deltas)<minclusters: raise Stop(f"primary not estimable: {len(deltas)} taxon clusters")

        point=math.fsum(deltas)/len(deltas)
        rng=random.Random(int(impl["primary"]["seed"]));boot=[]
        for _ in range(10000):
            vals=[deltas[rng.randrange(len(deltas))] for __ in deltas]
            boot.append(math.fsum(vals)/len(vals))
        low=type7(boot,0.025);high=type7(boot,0.975)

        # Non-rescuing directional summaries.
        contractions=[r for r in outcome_rows if int(r["t2_outcome_contraction"])==1]
        persists=[r for r in outcome_rows if int(r["t2_outcome_contraction"])==0]
        meanE1=math.fsum(float(r["E_i_lost_access_fraction"]) for r in contractions)/len(contractions) if contractions else math.nan
        meanE0=math.fsum(float(r["E_i_lost_access_fraction"]) for r in persists)/len(persists) if persists else math.nan

        event_rows=[]
        for tok in sorted(eligible):
            rs=bytax_out[tok]
            d=float(rs[0]["event_delta_N_eff"])
            frac=sum(int(r["t2_outcome_contraction"]) for r in rs)/len(rs)
            event_rows.append((d,frac))
        rho=spearman([x for x,_ in event_rows],[y for _,y in event_rows]) if len(event_rows)>=3 else math.nan

        # Full-data E coefficient, secondary only.
        yall=[int(r["t2_outcome_contraction"]) for r in outcome_rows]
        full_coef=math.nan
        if sum(yall)>=5 and len(yall)-sum(yall)>=5:
            # Compute full-data standardization from frozen feature rows, not outcomes.
            cont=impl["design_columns"]["standardized_R2_continuous"]+["E_i_lost_access_fraction"]
            stats={}
            for col in cont:
                xs=[float(r[col]) for r in outcome_rows]
                m=math.fsum(xs)/len(xs);sd=math.sqrt(math.fsum((x-m)**2 for x in xs)/len(xs))
                if sd>0: stats[col]={"mean":m,"sd":sd}
            dropped={col for col in impl["design_columns"]["standardized_R2_continuous"] if col not in stats}
            if "E_i_lost_access_fraction" in stats:
                X=[];cols=None
                for r in outcome_rows:
                    xr,cc=design_row(r,stats,dropped,True,impl)
                    if cols is None: cols=cc
                    X.append(xr)
                ff=fit_ridge_logistic(X,yall,columns=cols,ridge_lambda=1.0,max_iterations=100,tolerance=1e-8)
                full_coef=ff.coefficients[list(ff.columns).index("z_E_i_lost_access_fraction")]

        a.outcomes.parent.mkdir(parents=True,exist_ok=True)
        fields=list(outcome_rows[0].keys())
        with a.outcomes.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(outcome_rows)
        with a.taxon_scores.open("w",encoding="utf-8",newline="") as h:
            fields2=["MF_token","status","heldout_rows","heldout_contractions","heldout_persistences","R2_logloss","C_logloss","C_minus_R2"]
            w=csv.DictWriter(h,fieldnames=fields2,lineterminator="\n");w.writeheader();w.writerows(score_rows)

        result={
          "schema":"structural.bala_t2_scoring_result.v1_141",
          "status":"BALA_SOURCE_LOSS_PRIMARY_SCORED_ONCE",
          "eligible_taxa":len(eligible),
          "target_rows":len(outcome_rows),
          "t2_contractions":sum(int(r["t2_outcome_contraction"]) for r in outcome_rows),
          "t2_persistences":len(outcome_rows)-sum(int(r["t2_outcome_contraction"]) for r in outcome_rows),
          "estimable_taxon_clusters":len(deltas),
          "primary_C_minus_R2":point,
          "bootstrap_ci95_low":low,
          "bootstrap_ci95_high":high,
          "primary_supported":point<0 and high<0,
          "secondary_mean_E_i_contraction":meanE1,
          "secondary_mean_E_i_persistence":meanE0,
          "secondary_full_data_standardized_E_i_coefficient":full_coef,
          "secondary_event_delta_N_eff_vs_contraction_fraction_spearman":rho,
          "secondary_may_rescue_primary":False,
          "t2_rows_scanned_for_token_only":token_rows_decoded,
          "eligible_t2_rows_semantically_decoded":eligible_rows_decoded,
          "eligible_t2_quantity_values_decoded":quantity_values_decoded,
          "noneligible_t2_quantity_values_decoded":0,
          "raw_t2_surface_retained":False,
          "rerun_authorized":False,
          "outcomes_sha256":sha(a.outcomes),
          "taxon_scores_sha256":sha(a.taxon_scores),
          "counts_as_confirmatory_evidence":True
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,decimal.InvalidOperation,BorealConfirmatoryModelError,Stop) as e:
        result={
          "schema":"structural.bala_t2_scoring_result.v1_141",
          "status":"STOP",
          "reason":str(e),
          "noneligible_t2_quantity_values_decoded":0,
          "rerun_authorized":False,
          "counts_as_confirmatory_evidence":False
        };code=2
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
