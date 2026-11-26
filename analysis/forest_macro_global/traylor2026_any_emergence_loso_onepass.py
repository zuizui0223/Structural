#!/usr/bin/env python3
"""ONE frozen 4-study heldout resource prediction, Traylor et al. 2026.

Do not rerun source outcome after first score/STOP. Original source remains in
private transient CI runner only; only study-anonymous aggregates are archived.
"""
import argparse
import csv
import io
import itertools
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import traylor2026_original_firstheader_methodonly as parent

SOURCE_COLUMNS=("study","volume_m3","time_months","origin","type",
                "abd.native.amb","abd.exotic.amb","tot.amb","native.pres","exotic.pres")
SEED=20261123
PRE_N=356
STUDY_SIZE=[48,64,100,144]


class ScientificStop(ValueError):
    pass


def integer(v,name):
    s=str(v or "").strip()
    if s.lower() in ("","na","nan","null"):
        raise ScientificStop("SOURCE_MISSING_"+name)
    try:
        a=float(s)
    except (TypeError,ValueError):
        raise ScientificStop("SOURCE_NONNUMERIC_"+name)
    if not math.isfinite(a) or a<0 or a!=int(a):
        raise ScientificStop("SOURCE_COUNT_NOT_NONNEGATIVE_INTEGER_"+name)
    return int(a)


def read_original_source():
    original=parent.source()  # exact 3 original public file MD5/size/record/version
    source=original.get("ambrosia per deadwood object data.csv")
    if source is None:
        raise ScientificStop("SOURCE_EXACT_CSV_FILE_MISSING")
    reader=csv.DictReader(io.StringIO(source.decode("utf-8-sig",errors="replace")),delimiter=",")
    head=reader.fieldnames
    if not head or len(head)!=15 or len(set(head))!=15 or not set(SOURCE_COLUMNS).issubset(head):
        raise ScientificStop("SOURCE_EXACT_FIELD_SET_OR_CSV_HEADER_STOP")
    d=[]
    for line in reader:
        if line.get(None):
            raise ScientificStop("SOURCE_NONRECTANGULAR_CSV_STOP")
        x={k:(line.get(k) or "").strip() for k in SOURCE_COLUMNS}
        d.append(x)
    if len(d)!=PRE_N:
        raise ScientificStop("SOURCE_ORIGINAL_356_SAMPLED_OBJECTS_STOP")
    study=Counter(row["study"] for row in d)
    if "" in study or len(study)!=4 or sorted(study.values())!=STUDY_SIZE:
        raise ScientificStop("SOURCE_ORIGINAL_FOUR_STUDY_FRAME_STOP")
    for key in ("origin","type"):
        if any(not row[key] or row[key].lower() in ("na","nan","null") for row in d):
            raise ScientificStop("SOURCE_MISSING_TREE_RESOURCE_"+key)
    if len(set(row["origin"] for row in d))!=2:
        raise ScientificStop("SOURCE_ORIGINAL_TREE_ORIGIN_TWO_LEVELS_STOP")
    if len(set(row["type"] for row in d))!=2:
        raise ScientificStop("SOURCE_ORIGINAL_TREE_TYPE_TWO_LEVELS_STOP")
    frames=[]
    for row in d:
        wood={}
        for name in ("volume_m3","time_months"):
            try: v=float(row[name].replace(",","."))
            except (TypeError,ValueError):raise ScientificStop("SOURCE_"+name+"_NONNUMERIC_STOP")
            if not math.isfinite(v) or v<=0:
                raise ScientificStop("SOURCE_"+name+"_NONPOSITIVE_STOP")
            wood[name]=v
        n=integer(row["abd.native.amb"],"NATIVE_ABUNDANCE")
        x=integer(row["abd.exotic.amb"],"EXOTIC_ABUNDANCE")
        t=integer(row["tot.amb"],"TOTAL_AMBROSIA_COUNT")
        n_pres=integer(row["native.pres"],"NATIVE_ORIGINAL_PRESENCE")
        x_pres=integer(row["exotic.pres"],"EXOTIC_ORIGINAL_PRESENCE")
        if (t!=n+x or n_pres!=int(n>0) or x_pres!=int(x>0) or
            n_pres not in (0,1) or x_pres not in (0,1)):
            raise ScientificStop("SOURCE_ORIGINAL_NATIVE_EXOTIC_GROUP_COUNTS_PRESENCE_MISMATCH_STOP")
        frames.append({
            "study":row["study"],"origin":row["origin"],"type":row["type"],
            "log_volume":np.log(wood["volume_m3"]),
            "log_time":np.log1p(wood["time_months"]),
            "Y":int((n+x)>0)
        })
    x=pd.DataFrame(frames)
    if int(x.Y.sum())!=141:
        raise ScientificStop("SOURCE_AUTHOR_PUBLISHED_141_POSITIVE_OF_356_STOP")
    return x


def source_model():
    trans=ColumnTransformer([
        ("num",StandardScaler(),["log_volume","log_time"]),
        ("cat",OneHotEncoder(handle_unknown="ignore",sparse_output=False),["origin","type"]),
    ],remainder="drop")
    model=LogisticRegression(
        penalty="l2", C=1.0, solver="lbfgs", max_iter=4000
    )
    return Pipeline([("features",trans),("model",model)])


def heldstudy_scores(frame):
    study=frame.study.to_numpy()
    y=frame.Y.to_numpy(dtype=int)
    groups=sorted(frame.study.unique())
    if len(groups)!=4:
        raise ScientificStop("SOURCE_FOUR_TRAIN_TEST_STUDIES_STOP")
    scores=[]
    for held in groups:
        idx=study!=held
        hid=~idx
        if len(set(y[idx]))<2 or not hid.any() or int(idx.sum())+int(hid.sum())!=PRE_N:
            raise ScientificStop("SOURCE_TRAINING_Y_CLASS_OR_FOLD_STOP")
        p0=float(np.mean([
            (float(y[idx&(study==g)].sum())+0.5)/(int((idx&(study==g)).sum())+1.0)
            for g in groups if g!=held
        ]))
        predictors=frame[["log_volume","log_time","origin","type"]]
        weights=np.zeros(len(frame),dtype=float)
        ntrain=int(idx.sum())
        for g in groups:
            if g==held:continue
            n=int((idx&(study==g)).sum())
            if n<=0:raise ScientificStop("SOURCE_ZERO_TRAIN_GROUP_WEIGHT_STOP")
            weights[idx&(study==g)]=ntrain/(3.0*n)
        if abs(weights[idx].sum()-ntrain)>1e-7:
            raise ScientificStop("SOURCE_TRAIN_STUDY_EQUAL_WEIGHTS_STOP")
        pipe=source_model()
        pipe.fit(predictors.loc[idx],y[idx],model__sample_weight=weights[idx])
        p1=pipe.predict_proba(predictors.loc[hid])[:,1]
        if not np.isfinite(p1).all():
            raise ScientificStop("SOURCE_NONFINITE_HELD_STUDY_PREDICTIONS_STOP")
        yy=y[hid]
        p0a=np.full_like(p1,p0,dtype=float)
        p0a=np.clip(p0a,1e-12,1-1e-12)
        p1=np.clip(p1,1e-12,1-1e-12)
        loss0=float(np.mean(-yy*np.log(p0a)-(1-yy)*np.log1p(-p0a)))
        loss1=float(np.mean(-yy*np.log(p1)-(1-yy)*np.log1p(-p1)))
        scores.append((loss0,loss1,loss0-loss1,int(hid.sum()),int(yy.sum())))
    return np.asarray(scores,dtype=float)


def summarize(scores):
    if scores.shape!=(4,5):
        raise ScientificStop("SOURCE_ONLY_FOUR_HOLDOUT_STUDY_LOSSES_STOP")
    mean0=float(scores[:,0].mean())
    mean1=float(scores[:,1].mean())
    delta=float(scores[:,2].mean())
    rng=np.random.default_rng(SEED)
    bootstrap=np.asarray([scores[rng.integers(0,4,size=4),2].mean()
                          for _ in range(4000)])
    all_signs=np.asarray(list(itertools.product((-1.0,1.0),repeat=4)))
    signed_means=(all_signs*scores[:,2][None,:]).mean(axis=1)
    p=float(np.mean(np.abs(signed_means)>=abs(delta)-1e-14))
    return {
        "heldstudy_prevalence_only_E0_logloss":mean0,
        "heldstudy_resource_E1_logloss":mean1,
        "primary_E0_minus_E1_study_equal_gain":delta,
        "relative_loss_reduction_pct":100*delta/mean0,
        "four_anonymous_study_gains_sorted":[float(x) for x in sorted(scores[:,2])],
        "four_anonymous_study_sample_counts_sorted":[int(x) for x in sorted(scores[:,3])],
        "four_anonymous_study_any_emergence_positive_counts_sorted":[int(x) for x in sorted(scores[:,4])],
        "positive_original_study_gains":int((scores[:,2]>0).sum()),
        "adverse_original_study_gains":int((scores[:,2]<0).sum()),
        "equal_original_study_gains":int((scores[:,2]==0).sum()),
        "four_study_bootstrap_4000_percentile95":[float(v) for v in np.quantile(bootstrap,[.025,.975])],
        "exact_4study_two_sided_signflip_p":p,
        "n_original_studies":4,
        "signflip_assignments":16,
        "minimum_two_sided_exact_p":.125,
        "interpretation_not_causal_or_geographical_generality":True
    }


def test():
    f=pd.DataFrame({
       "log_volume":[-3,-2,-4,-5, -2,-1,-3,-4],
       "log_time":[1,2,1.5,2,1.7,2.2,1.1,3],
       "origin":["native","exotic"]*4,
       "type":["pine","broadleaf"]*4
    })
    train=pd.Series([0,1,0,1,1,1,0,0])
    model=source_model()
    model.fit(f,train,model__sample_weight=np.ones(8))
    assert model.named_steps["model"].C==1.
    assert np.isfinite(model.predict_proba(f)).all()
    assert integer("1.0","test")==1
    try:
        integer("-1","test")
        raise AssertionError("negative beetle count must stop")
    except ScientificStop:pass
    synthetic=np.array([[.8,.7,.1,10,2],[.6,.5,.1,10,3],
                        [.7,.5,.2,10,4],[.9,.6,.3,10,5]])
    test_result=summarize(synthetic)
    assert test_result["signflip_assignments"]==16
    assert test_result["minimum_two_sided_exact_p"]==.125
    print("TRAYLOR2026_4STUDY_LOSO_PREDECLARED_SYNTHETIC_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="traylor2026_any_emergence_loso_onepass/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    out={
       "schema":"structural.traylor2026_onepass_fourstudy_any_emergence_LOSO.v1",
       "original_publisher_version_DOI":parent.VERSION_DOI,
       "pre_original_response_freeze":"docs/FOREST_TRAYLOR2026_ANY_AMBROSIA_EMERGENCE_LOSO_FROZEN_20261123.md",
       "source_original_study_n":4,
       "source_original_sampled_deadwood_objects":356,
       "source_original_biological_or_site_rows_exported":False,
       "source_original_source_files_uploaded":False,
       "new_original_ecological_predictive_score_count":0,
       "status":"SOURCE_ORIGINAL_BIOLOGY_UNOPENED"
    }
    try:
        frame=read_original_source()
        scores=heldstudy_scores(frame)
        out["result"]=summarize(scores)
        out["source_recorded_any_emergence_positive_total"]=int(frame.Y.sum())
        out["new_original_ecological_predictive_score_count"]=1
        out["status"]="ORIGINAL_FOUR_STUDY_HELDOUT_EMERGENCE_EXPLORATORY_COMPLETED"
    except Exception as e:
        out["status"]="ORIGINAL_SOURCE_OR_OUTCOME_ESTIMABILITY_STOP_NO_SCORE"
        out["scientific_error_type"]=type(e).__name__
        out["scientific_stop_reason"]=str(e)[:160] if isinstance(e,(ValueError,ScientificStop)) else ""
    fp=Path(a.out);fp.parent.mkdir(parents=True,exist_ok=True)
    fp.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("TRAYLOR_ONEPASS_STATUS",out["status"])
    print("NEW_ACTUAL_SCORES",out["new_original_ecological_predictive_score_count"])
    if "result" in out:
        r=out["result"]
        print("FOUR_STUDY_GAIN",r["primary_E0_minus_E1_study_equal_gain"],
              "FOUR_STUDY_EXACT_P",r["exact_4study_two_sided_signflip_p"])
if __name__=="__main__":
    main()
