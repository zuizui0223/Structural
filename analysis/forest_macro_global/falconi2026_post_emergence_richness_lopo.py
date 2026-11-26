#!/usr/bin/env python3
"""Author-SHA gated Ecuador saproxylic beetle *conditional richness* LOPO.

Retrospective exploratory; freeze:
docs/FOREST_FALCONI2026_POST_EMERGENCE_RICHNESS_LOPO_FREEZE_20261122.md
docs/FOREST_FALCONI2026_POST_EMERGENCE_RICHNESS_LOPO_SOURCE_LABEL_ERRATUM_20261122.md

No raw plot IDs, morphospecies, specimen lines, raw ZIP or observations are
committed or output. Source file supplied locally with --source; GitHub CI is
source-free synthetic only.
"""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SHA = "8c6e822866207a3398d6ce32fd35b6786713472ea87c2c1f3267984ebb79500d"
SIZE = 11201
HOSTS = ("CACAO", "FERNAN SANCHEZ", "GUABA", "MASCAREI", "SAPANILLO")
STAGES = ("Agri", "Reg1", "Reg2", "Old")
MEMBERS = {
    "R skript for Saproxylic beetle analyses_2024_12_22.R",
    "PlotLogSpeciesAbundancesDensity.csv", "PlotKat4HostSpecIndiv_3.csv",
    "a_Agri_3.csv", "a_Old_3.csv", "a_Reg1_3.csv", "a_Reg2_3.csv",
    "HostBeetleIndiv_3.csv", "PlotSpeciesIndiv_3.csv",
}
META_HEADER = [
    "Plot_ID","Plot","Species","Individuals","Latitude","Longitude","Elevation",
    "Treatment1","Regeneration_year","Succession","Treatment2","Category7",
    "Category4","History"
]
LOG_HEADER = ["Plot","Host","Indiv","Spec","WoodDensity"]
SEED = 20261122


class SourceSTOP(ValueError):
    pass


def as_int(x, name):
    n = pd.to_numeric(x,errors="coerce")
    if n.isna().any() or not np.isfinite(n).all() or (n<0).any() or (n!=np.floor(n)).any():
        raise SourceSTOP(name+" nonnegative-integer source domain STOP")
    return n.astype(int)


def source(path):
    b=Path(path).read_bytes()
    if len(b)!=SIZE or hashlib.sha256(b).hexdigest()!=SHA:
        raise SourceSTOP("exact source fingerprint STOP")
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        if set(z.namelist())!=MEMBERS or len(z.namelist())!=len(MEMBERS):
            raise SourceSTOP("author ZIP roster STOP")
        m=pd.read_csv(io.BytesIO(z.read("PlotSpeciesIndiv_3.csv")),
                      sep=";",dtype=str,keep_default_na=False)
        w=pd.read_csv(io.BytesIO(z.read("PlotLogSpeciesAbundancesDensity.csv")),
                      sep=";",dtype=str,keep_default_na=False)
    if list(m.columns)!=META_HEADER or list(w.columns)!=LOG_HEADER:
        raise SourceSTOP("original CSV header STOP")
    if (len(m)!=61 or m.Plot.nunique()!=61 or m.Plot_ID.nunique()!=61 or
        m.Plot.duplicated().any() or not m.Plot.equals(m.Plot_ID)):
        raise SourceSTOP("61 exact source Plot keys STOP")
    if (len(w)!=300 or w[["Plot","Host"]].duplicated().any() or
        not w.Plot.isin(m.Plot).all() or set(w.Host)!=set(HOSTS)):
        raise SourceSTOP("300 original physical Plot x Host keys STOP")
    support=w.groupby("Plot").Host.nunique()
    if support.value_counts().to_dict()!={5:59,4:1,1:1}:
        raise SourceSTOP("original full/partial log opportunity STOP")
    complete=support[support==5].index
    if any(set(w.loc[w.Plot==i,"Host"])!=set(HOSTS) for i in complete):
        raise SourceSTOP("full five-Host support STOP")
    if set(m.Category4)!=set(STAGES) or m.Category4.eq("").any():
        raise SourceSTOP("source recovery class STOP")
    w=w.copy()
    w["Indiv"]=as_int(w.Indiv,"Indiv")
    w["Spec"]=as_int(w.Spec,"Spec")
    if w.Spec.gt(w.Indiv).any() or not np.array_equal(w.Spec.gt(0),w.Indiv.gt(0)):
        raise SourceSTOP("original source Spec/Indiv consistency STOP")
    mw=w[w.Plot.isin(complete)].copy()
    if len(mw)!=295 or int(mw.Indiv.gt(0).sum())!=169:
        raise SourceSTOP("59x5 original binary source frame STOP")
    meta=m[["Plot","Category4","History","Latitude","Longitude","Elevation"]].copy()
    meta.History=meta.History.mask(meta.History.str.strip()=="","__UNRECORDED__")
    missing_history=int(meta.History.eq("__UNRECORDED__").sum())
    for field in ["Latitude","Longitude","Elevation"]:
        n=pd.to_numeric(meta[field].str.replace(",",".",regex=False),errors="coerce")
        if n.isna().any() or not np.isfinite(n).all():
            raise SourceSTOP("original geographic covariate STOP")
        meta[field]=n.astype(float)
    merged=mw.merge(meta,on="Plot",how="left",indicator=True,validate="many_to_one")
    if not merged._merge.eq("both").all() or any(
        merged[k].isna().any() for k in ["Category4","History","Latitude","Longitude","Elevation"]
    ):
        raise SourceSTOP("original plot metadata crosswalk STOP")
    pos=merged[merged.Indiv>0].copy()
    if len(pos)!=169 or pos.Plot.nunique()!=59:
        raise SourceSTOP("59 heldout physical plots do not all have positive source logs")
    pos["log_indiv"]=np.log1p(pos.Indiv.astype(float))
    pos["y"]=np.log1p(pos.Spec.astype(float))
    return merged,pos,missing_history


def pipeline(with_host):
    cats=["Category4","History"]+(["Host"] if with_host else [])
    nums=["Latitude","Longitude","Elevation","log_indiv"]
    trans=ColumnTransformer([
        ("categorical",OneHotEncoder(handle_unknown="ignore"),cats),
        ("numeric",StandardScaler(),nums)
    ])
    return Pipeline([("features",trans),("ridge",Ridge(alpha=10.0,fit_intercept=True))])


def fold_losses(pos):
    x=pos[["Category4","History","Latitude","Longitude","Elevation","log_indiv","Host"]]
    y=pos.y.to_numpy()
    g=pos.Plot.to_numpy()
    unique=sorted(pos.Plot.unique())
    if len(unique)!=59:
        raise SourceSTOP("heldout fold count STOP")
    rows=[]
    for p in unique:
        keep=g!=p
        test=~keep
        if not keep.any() or not test.any():
            raise SourceSTOP("source fold empty")
        errors=[]
        for extra in [False,True]:
            m=pipeline(extra)
            m.fit(x.loc[keep],y[keep])
            pred=m.predict(x.loc[test])
            if not np.isfinite(pred).all():
                raise SourceSTOP("nonfinite model prediction")
            errors.append(float(np.mean((y[test]-pred)**2)))
        rows.append((errors[0],errors[1],errors[0]-errors[1]))
    return np.asarray(rows,dtype=float)


def inference(d):
    rng=np.random.default_rng(SEED)
    mean=float(d.mean())
    boots=np.asarray([d[rng.integers(len(d),size=len(d))].mean()
                      for _ in range(4000)])
    ge=0
    for _ in range(9999):
        s=rng.choice([-1,1],size=len(d))
        if abs(float((d*s).mean()))>=abs(mean)-1e-14:
            ge+=1
    return {
        "bootstrap95":list(np.quantile(boots,[.025,.975])),
        "plot_signflip_MC_p_two_sided":(ge+1)/10000,
        "plot_signflip_ge":ge,
        "n_improved":int((d>0).sum()),
        "n_worsened":int((d<0).sum()),
        "n_equal":int((d==0).sum()),
        "bootstrap_reps":4000,"signflip_reps":9999,"seed":SEED
    }


def run(path):
    logs,pos,n_unrec=source(path)
    folds=fold_losses(pos)
    e0=float(folds[:,0].mean())
    e1=float(folds[:,1].mean())
    delta=e0-e1
    err=inference(folds[:,2])
    host={}
    for h in HOSTS:
        whole=logs[logs.Host==h]
        emerged=whole[whole.Indiv>0]
        if len(whole)!=59 or len(emerged)==0:
            raise SourceSTOP("within-source offered host denominator STOP")
        prob=len(emerged)/59
        conditional=float(emerged.Spec.mean())
        overall=float(whole.Spec.mean())
        if abs(prob*conditional-overall)>1e-12:
            raise SourceSTOP("two-part observed richness arithmetic STOP")
        host[h]={
            "offered_logs":len(whole),
            "positive_logs":len(emerged),
            "emergence_observed_fraction":prob,
            "mean_Spec_given_positive":conditional,
            "mean_Spec_per_offered_log":overall,
            "mean_Indiv_given_positive":float(emerged.Indiv.mean())
        }
    return {
        "schema":"structural.falconi2026_conditional_richness_LOPO.v1",
        "evidence_class":"retrospective_single_study_exploratory",
        "original_zip_sha256":SHA,
        "source_original_plot_rows":61,
        "source_original_log_rows":300,
        "matched_physical_plots":59,
        "matched_offered_logs":295,
        "positive_logs_scored":169,
        "plot_metadata_history_missing":n_unrec,
        "score":"equal-plot LOPO squared error of log1p(Spec), conditional Indiv>0",
        "baseline_E0":"Category4, History, Latitude, Longitude, Elevation, log1p(Indiv)",
        "extended_E1":"E0 plus literal Host, Ridge alpha10",
        "E0_loss":e0,"E1_loss":e1,
        "gain_E0_minus_E1":delta,"relative_loss_reduction_percent":100*delta/e0,
        "inference":err,
        "fixed_support_gate_pass":bool(delta>0 and err["bootstrap95"][0]>0 and
                                       err["plot_signflip_MC_p_two_sided"]<.05),
        "host_descriptive_two_part_richness":host,
        "original_plot_taxa_composition_inferred":False,
        "causal_or_generalizable_mechanism_claim":False,
        "raw_source_rows_or_plot_names_archived":False
    }


def test():
    assert pipeline(False).named_steps["ridge"].alpha==10.0
    assert pipeline(True).named_steps["ridge"].alpha==10.0
    assert list(as_int(pd.Series([0,2,6]),"fixture"))==[0,2,6]
    try:
        as_int(pd.Series([-1]),"bad")
        raise AssertionError("must STOP on negative")
    except SourceSTOP:
        pass
    a=inference(np.zeros(59))
    assert a["plot_signflip_MC_p_two_sided"]==1 and a["n_equal"]==59
    print("SYNTHETIC_ONLY_KNOWN_TRUTH_PASS")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source")
    parser.add_argument("--out")
    parser.add_argument("--test",action="store_true")
    args=parser.parse_args()
    if args.test:
        test()
    else:
        if not args.source or not args.out:
            parser.error("provide exact local original ZIP via --source and aggregate JSON via --out")
        try:
            output=run(args.source)
        except SourceSTOP as e:
            output={"schema":"structural.falconi2026_conditional_richness_LOPO.v1",
                    "status":"SCIENTIFIC_SOURCE_STOP_NO_SCORE","cause":str(e),
                    "new_effects_scored":0}
        p=Path(args.out)
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2,default=float)+"\n")
        print("SOURCE_SCORED",output.get("status","EXPLORATORY_COMPLETED"))
        if "gain_E0_minus_E1" in output:
            print("E0",output["E0_loss"],"E1",output["E1_loss"],"GAIN",output["gain_E0_minus_E1"],
                  "SUPPORT",output["fixed_support_gate_pass"])
