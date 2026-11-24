#!/usr/bin/env python3
"""One frozen retrospective within-Sihlwald endpoint. Aggregate output only."""
import argparse,csv,datetime,hashlib,io,json,re
from pathlib import Path
import numpy as np
import haeler2023_envidat455_four_csv_header_only as source
import haeler2023_envidat455_plot_bundle_nonresponse_gate as prior
import haeler2023_envidat455_species_matrix_ID_crosswalk_only as keys

ENV="Forest and environmental variables"
MAT="Community matrix (saproxylic beetles)"
DOC="Variable description"
class Stop(ValueError): pass

def require(x,msg):
    if not x: raise Stop(msg)

def numeric(v):
    x=float(str(v).strip())
    require(np.isfinite(x),"NONFINITE_ORIGINAL_VALUE")
    return x

def date(s):
    for f in ("%Y-%m-%d","%d.%m.%Y","%d/%m/%Y","%Y/%m/%d"):
        try: return datetime.datetime.strptime(s.strip(),f)
        except ValueError: pass
    raise Stop("ORIGINAL_DATE_FORMAT_NOT_FROZEN")

def amount_name(header,book):
    pat=re.compile(r"(?i)(.*?)[_. ]?40$")
    opts=[]
    for h in header:
        m=pat.fullmatch(h)
        if not m:continue
        stem=m.group(1).rstrip("_. ")
        if not re.search(r"(?i)(amount|dead.?wood|length|^dw$)",stem) or "isol" in stem.lower():continue
        # Require the complete 19-radius parallel source family.
        fam=[z for z in header if re.fullmatch(re.escape(stem)+r"[_. ]?(?:[2-9]0|1[0-9]0|200)",z,re.I)]
        if len(fam)!=19:continue
        defs=[v for k,v in book.items() if stem.casefold() in k.casefold() or k==h]
        if any(re.search(r"(?i)(dead.?wood|dead wood|wood pieces)",v) and re.search(r"(?i)(length|amount|sum|meter|metre)",v) for v in defs):
            opts.append(h)
    require(len(opts)==1,"AMOUNT40_SOURCE_CODEBOOK_UNRESOLVED")
    return opts[0]

def env_input(raw):
    rows,header=prior.reader(raw[ENV],ENV)
    codes,_=prior.reader(raw[DOC],DOC)
    book={str(list(r.values())[0]).strip():str(list(r.values())[1]) for r in codes}
    amount=amount_name(header,book)
    iso="Isolation_40"
    require(iso in header,"ORIGINAL_ISOLATION40_MISSING")
    # Source definition of isolation is independently stated in original paper.
    req=["Bundle_Surface_total_cm2","Plot_Temp_Summer_high95_celsius","Bundle_SWR_direct",
         "Date_start_forest","Date_stop_forest","Date_start_emergence_trap","Date_stop_emergence_trap",
         "Plot_ID","Bundle_ID",amount,iso]
    require(set(req).issubset(header),"ORIGINAL_ENV_FIELDS_MISSING")
    ids=[]; groups=[]; X=[]
    for row in rows:
        bid=row["Bundle_ID"].strip(); pid=row["Plot_ID"].strip()
        s=numeric(row[req[0]]); t=numeric(row[req[1]]); light=numeric(row[req[2]])
        a=numeric(row[amount]); i=numeric(row[iso])
        f=(date(row[req[4]])-date(row[req[3]])).days
        e=(date(row[req[6]])-date(row[req[5]])).days
        require(s>0 and a>=0 and i>=0 and f>0 and e>0,"INVALID_ORIGINAL_EXPOSURE_OR_AMOUNT")
        ids.append(bid);groups.append(pid)
        X.append([np.log1p(s),t,light,np.log1p(a),f,e,i])
    require(len(ids)==244 and len(set(ids))==244 and len(set(groups))==62,"SOURCE_244_62_FRAME_DRIFT")
    require(all(ids) and all(groups),"BLANK_SOURCE_ID")
    return ids,np.array(groups),np.array(X,dtype=float),amount

def response(blob,ids):
    rr=csv.reader(io.StringIO(blob.decode("utf-8-sig")),delimiter=";")
    h=next(rr)
    require(len(h)==44 and len(set(h[1:]))==43 and all(s.strip() for s in h[1:]),"TAXON_HEADER_ROLE_STOP")
    require(h[0].strip().casefold() in keys.ID_NAMES,"MATRIX_ID_ROLE_STOP")
    y={}
    for r in rr:
        if not r:continue
        require(len(r)==44 and r[0].strip() not in y,"MATRIX_ROW_DUPLICATE_OR_WIDTH")
        z=np.array([numeric(s) for s in r[1:]])
        require(np.all(z>=0) and np.all(z==np.floor(z)),"COUNTS_NOT_NONNEGATIVE_INTEGER")
        y[r[0].strip()]=z
    require(set(y)==set(ids),"RESPONSE_EXACT_KEYS_DRIFT")
    a=np.stack([y[i] for i in ids])
    n=a.sum(axis=1)
    b=np.sqrt(np.divide(a,n[:,None],out=np.zeros_like(a),where=n[:,None]>0))
    return np.column_stack([b,(n==0).astype(float)]),int((n==0).sum())

def fit_predict(x,y,g,train,test):
    _,i,n=np.unique(g[train],return_inverse=True,return_counts=True)
    w=1/n[i]
    tr=x[train]; te=x[test]
    mu=np.average(tr,axis=0,weights=w)
    sd=np.sqrt(np.average((tr-mu)**2,axis=0,weights=w))
    sd[sd==0]=1
    a=np.column_stack([np.ones(len(tr)),(tr-mu)/sd])
    b=np.column_stack([np.ones(len(te)),(te-mu)/sd])
    penalty=np.diag([0]+[10]*x.shape[1])
    beta=np.linalg.solve(a.T@(w[:,None]*a)+penalty,a.T@(w[:,None]*y[train]))
    return b@beta

def evaluate(x,y,g):
    out=[]
    for group in np.unique(g):
        test=g==group;train=~test
        a=fit_predict(x[:,:-1],y,g,train,test)
        b=fit_predict(x,y,g,train,test)
        out.append([np.mean(np.sum((a-y[test])**2,axis=1)),np.mean(np.sum((b-y[test])**2,axis=1))])
    z=np.array(out);d=z[:,0]-z[:,1];base,plus=z.mean(axis=0)
    return {"plot_equal_baseline_loss":float(base),"plot_equal_plus_isolation_loss":float(plus),
            "delta":float(base-plus),"relative_error_reduction":float((base-plus)/base),
            "plots_improved":int((d>1e-12).sum()),"plots_tied":int((abs(d)<=1e-12).sum()),
            "plots_worse":int((d<-1e-12).sum()),"plot_count":len(z),"population_p_value":None}

def fixture():
    rng=np.random.default_rng(7)
    g=np.repeat(np.arange(30),4)
    x=rng.normal(size=(120,7));y=np.column_stack([x[:,-1],-x[:,-1]])
    s=evaluate(x,y,g)
    assert s["delta"]>0 and s["plot_count"]==30
    tr=g!=0;te=~tr
    a=fit_predict(x,y,g,tr,te); y[te]+=1000
    assert np.array_equal(a,fit_predict(x,y,g,tr,te))
    print("SYNTHETIC_FIXED_LOPO_GAIN_AND_HELDOUT_RESPONSE_LEAKAGE_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="swiss244_isolation/receipt.json")
    args=p.parse_args();fixture()
    if args.test:return
    result={"schema":"structural.swiss244.frozen_heldplot_isolation40.v1","status":"SOURCE_UNOPENED","original_rows_exported":False,"old_outcomes_reopened":False}
    try:
        rr=source.exact_public_urls();raw={}
        for t,digest in prior.PINNED_SHA.items():
            raw[t]=source.one_download(rr[t]["url"],rr[t]["size"])
            require(hashlib.sha256(raw[t]).hexdigest()==digest,"ORIGINAL_SHA_DRIFT")
        ids,g,x,amount=env_input(raw)
        result["environment_gate"]={"n_bundles":len(ids),"n_plots":len(set(g)),"amount_field":amount,"isolation_field":"Isolation_40","all_finite":True}
        result["status"]="ENVIRONMENT_PASS_RESPONSE_NOT_SCORED"
        y,nzero=response(raw[MAT],ids)
        result["response_gate"]={"n_recorded_rows":len(y),"n_explicit_all_zero_rows":nzero,"n_response_channels_including_empty":y.shape[1]}
        result["result"]=evaluate(x,y,g)
        result["status"]="ONE_FROZEN_WITHIN_FOREST_HELD_PLOT_SCORE_COMPLETE"
    except Stop as e:
        result["status"]="SOURCE_OR_SCHEMA_STOP";result["reason"]=str(e)
    except Exception as e:
        result["status"]="SOURCE_OR_EXECUTION_STOP";result["error_class"]=type(e).__name__
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
