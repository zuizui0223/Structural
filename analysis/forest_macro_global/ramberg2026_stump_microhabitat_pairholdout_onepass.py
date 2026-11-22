#!/usr/bin/env python3
"""ONE frozen exploratory species-composition score from original Swedish stumps.

Original SHA and source keys, see frozen protocol document. NO biological
source is carried in GitHub or archived: source file lives only in CI job
memory, and output consists exclusively of anonymous 5-pair aggregates.
"""
import argparse
import collections
import io
import itertools
import json
import math
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import ramberg2026_zenodo_xlsx_firstheader_only as original
import ramberg2026_original_sample_identity_only as prior

MAIN="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SEED=20261122
CATS0=["Type"]
CATS1=["Type","bark_coverage","ground_moisture","sunexposure_stump"]
NUMS1=["stump_diameter","stump_height"]
METHOD_FIELDS={"Lop_nummer","sample id","Pair_number","Site_code","Type",
               "tree_species","stump_diameter","stump_height",
               "bark_coverage","ground_moisture","sunexposure_stump"}
PROTOCOL="docs/FOREST_BEETLE_RAMBERG2026_STUMP_MICROHABITAT_PAIRED_HOLDOUT_FROZEN_20261122.md"


class ScienceStop(ValueError):
    pass


def full_source_data():
    """Read one exact original publisher file; verify and admit source identities."""
    blob=original.original_file()   # exact official Zenodo SHA/MD5/size
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        paths=original.sheet_paths(z)
        sh=prior.original_row1(z,paths["Samples"])
        bh=prior.original_row1(z,paths["Species"])
        if len(sh)!=18 or len(bh)!=153:
            raise ScienceStop("SOURCE_HEADER_DIMS_STOP")
        refs={v for _,t,v in sh if t=="s"}
        shared=original.selected_sharedstrings(z,refs)
        names={col:prior.to_label((typ,val),shared) for col,typ,val in sh}
        cols={c:name for c,name in names.items() if name in METHOD_FIELDS}
        if not METHOD_FIELDS.issubset(cols.values()):
            raise ScienceStop("SOURCE_REQUIRED_METHOD_PREDICTOR_HEADER_STOP")
        if len(cols)!=len(set(cols.values())):
            raise ScienceStop("SOURCE_NONUNIQUE_METHOD_NAMES_STOP")
        if any(t!="n" for _,t,_ in bh[3:]):
            raise ScienceStop("SOURCE_SPECIES_HEADER_ID_TYPES_STOP")
        s_headers={col:prior.to_label((t,v),{}) for col,t,v in bh[3:]}
        if len(s_headers)!=150 or len(set(s_headers.values()))!=150 or not all(s_headers.values()):
            raise ScienceStop("SOURCE_SPECIES_UNIQUE_NUMERIC_HEADERS_STOP")

        rows,nxml=prior.read_samples_allowlisted_values(z,paths["Samples"],cols)
        sst_idx={v for row in rows for typ,v in row.values() if typ=="s"}
        strings=original.selected_sharedstrings(z,sst_idx)
        fields=[{k:prior.to_label(row.get(k,("str","")),strings)
                 for k in cols.values()} for row in rows]
        eligible=[row for row in fields if row.get("sample id","").strip()]
        if len(eligible)!=150:
            raise ScienceStop("SOURCE_150_ORIGINAL_STUMP_OPPORTUNITY_STOP")
        by_serial={v["Lop_nummer"]:v for v in eligible if v["Lop_nummer"]}
        if len(by_serial)!=150 or set(by_serial)!=set(s_headers.values()):
            raise ScienceStop("SOURCE_GLOBAL_LOP_NUMMER_HEADER_ID_STOP")
        by_stand=collections.Counter(x["Site_code"] for x in eligible)
        by_pair=collections.Counter(x["Pair_number"] for x in eligible)
        sitepair=collections.defaultdict(set)
        pairtype=collections.defaultdict(set)
        for r in eligible:
            sitepair[r["Site_code"]].add(r["Pair_number"])
            pairtype[r["Pair_number"]].add(r["Type"])
        if (len(by_stand)!=10 or set(by_stand.values())!={15} or
            len(by_pair)!=5 or set(by_pair.values())!={30} or
            any(len(v)!=1 for v in sitepair.values()) or
            any(len(v)!=2 for v in pairtype.values()) or
            len({r["tree_species"] for r in eligible})!=1):
            raise ScienceStop("SOURCE_FIVE_PAIR_TEN_STAND_STRUCTURE_STOP")

        # Original environmental variables only (no age with 48 missing).
        for r in eligible:
            for key in CATS1:
                if not r.get(key,"").strip() or r[key].strip().lower() in ("na","nan","null"):
                    raise ScienceStop("SOURCE_MICROHABITAT_CATEGORICAL_MISSING_STOP")
            for key in NUMS1:
                raw=r.get(key,"")
                try: val=float(raw.replace(",","."))
                except (TypeError,ValueError): raise ScienceStop("SOURCE_NUMERIC_STUMP_PREDICTOR_MISSING_STOP")
                if not np.isfinite(val):
                    raise ScienceStop("SOURCE_NUMERIC_STUMP_PREDICTOR_NONFINITE_STOP")
                r[key]=val

        # FIRST opening of species response rows, only after source admission.
        seen_cols=set(s_headers)
        matrix=[]
        taxon_ids=[]
        native_missing=0
        present_zero=0
        observed_nonzero=0
        with z.open(paths["Species"]) as fh:
            for event,element in ET.iterparse(fh,events=("end",)):
                if element.tag!=MAIN+"row":
                    continue
                n=element.attrib.get("r","")
                if not n.isdigit():
                    raise ScienceStop("SOURCE_SPECIES_EXCEL_ROW_ID_STOP")
                if int(n)==1:
                    element.clear()
                    continue
                tax_label=None
                values={}
                for cell in element.findall(MAIN+"c"):
                    coord=cell.attrib.get("r","")
                    col=prior.col_letters(coord)
                    if col=="A":
                        t=cell.attrib.get("t","n")
                        v=cell.find(MAIN+"v")
                        if t=="s":
                            if v is None or not (v.text or "").isdigit():
                                raise ScienceStop("SOURCE_TAXON_HEADER_REF_STOP")
                            # Keep index for exact name resolution once.
                            tax_label=("s",int(v.text))
                        elif t=="inlineStr":
                            tax_label=("i","".join(a.text or "" for a in cell.iter(MAIN+"t")))
                        elif t=="str":
                            tax_label=("i",v.text or "" if v is not None else "")
                        else:
                            raise ScienceStop("SOURCE_TAXON_LABEL_MISSING_STOP")
                    elif col in seen_cols:
                        v=cell.find(MAIN+"v")
                        t=cell.attrib.get("t","n")
                        if t!="n" or v is None or v.text is None:
                            raise ScienceStop("SOURCE_SPECIES_COUNT_BLANK_OR_TEXT_STOP")
                        try:
                            x=float(v.text)
                        except ValueError:
                            raise ScienceStop("SOURCE_SPECIES_COUNT_NOT_NUMBER_STOP")
                        if not np.isfinite(x) or x<0 or x!=int(x):
                            raise ScienceStop("SOURCE_SPECIES_COUNT_INVALID_DOMAIN_STOP")
                        values[col]=int(x)
                        if x==0:present_zero+=1
                        else:observed_nonzero+=1
                if tax_label is None:
                    raise ScienceStop("SOURCE_TAXON_ID_ABSENT_STOP")
                if len(values)!=150:
                    native_missing+=150-len(values)
                    raise ScienceStop("SOURCE_SPECIES_EXPLICIT_67X150_CELL_COVERAGE_STOP")
                taxon_ids.append(tax_label)
                matrix.append([values[col] for col in s_headers])
                element.clear()
        if len(matrix)!=67:
            raise ScienceStop("SOURCE_SPECIES_67_TAXA_ROW_COUNT_STOP")
        shared_tax_idx={i for typ,i in taxon_ids if typ=="s"}
        tax_sst=original.selected_sharedstrings(z,shared_tax_idx)
        names=[tax_sst[i].strip() if typ=="s" else i.strip() for typ,i in taxon_ids]
        if len(set(names))!=67 or any(not s for s in names):
            raise ScienceStop("SOURCE_SPECIES_NAMES_UNIQUE_NONBLANK_STOP")
    # Workbook already closed; raw names remain private in job.
    abundance=np.asarray(matrix,dtype=np.float64)
    if abundance.shape!=(67,150):
        raise ScienceStop("SOURCE_SPECIES_MATRIX_SHAPE_STOP")
    totals=abundance.sum(axis=0)
    if not np.all(totals>0):
        raise ScienceStop("SOURCE_ZERO_CATCH_STUMP_COMPOSITION_NOT_ESTIMABLE_STOP")
    keys=[s_headers[c] for c in s_headers]
    features=pd.DataFrame([by_serial[k] for k in keys])
    features["stump_diameter"]=features["stump_diameter"].astype(float)
    features["stump_height"]=features["stump_height"].astype(float)
    y=np.sqrt((abundance/totals).T)
    if not np.allclose((y*y).sum(axis=1),1.,atol=1e-12):
        raise ScienceStop("SOURCE_HELLINGER_UNIT_VECTORS_STOP")
    return features,y,{"taxon_rows":67,"stump_cols":150,
                       "explicit_species_cells":int(present_zero+observed_nonzero),
                       "explicit_zero_species_cells":int(present_zero),
                       "source_species_numeric_missing_cells":native_missing}


def design(extra):
    cats=CATS1 if extra else CATS0
    transforms=[("cats",OneHotEncoder(handle_unknown="ignore",sparse_output=False),cats)]
    if extra:transforms.append(("stump",StandardScaler(),NUMS1))
    col=ColumnTransformer(transforms)
    return Pipeline([("features",col),
                     ("model",Ridge(alpha=10.0,fit_intercept=True))])


def safe_predict(raw,train_y):
    pred=np.maximum(np.asarray(raw,dtype=float),0.0)
    norms=np.linalg.norm(pred,axis=1)
    fallback=np.mean(train_y,axis=0)
    fallback=np.maximum(fallback,0.)
    fallback/=max(np.linalg.norm(fallback),1e-30)
    result=np.zeros_like(pred)
    good=norms>1e-12
    result[good]=pred[good]/norms[good,None]
    result[~good]=fallback
    return result


def fivepair_score(features,y):
    pairs=features.Pair_number.to_numpy()
    values=sorted(set(pairs))
    if len(values)!=5:return None
    out=[]
    for pair in values:
        train=pairs!=pair
        test=~train
        if int(test.sum())!=30 or int(train.sum())!=120:
            raise ScienceStop("SOURCE_HELD_PAIR_30_STUMPS_STOP")
        losses=[]
        for extra in (False,True):
            model=design(extra)
            model.fit(features.loc[train],y[train])
            pred=safe_predict(model.predict(features.loc[test]),y[train])
            errors=np.sum((y[test]-pred)**2,axis=1)/2
            if not np.isfinite(errors).all():
                raise ScienceStop("SOURCE_PREDICTION_NONFINITE_STOP")
            losses.append(float(errors.mean()))
        out.append([losses[0],losses[1],losses[0]-losses[1]])
    return np.asarray(out,dtype=float)


def infer(folds):
    base=float(folds[:,0].mean())
    alt=float(folds[:,1].mean())
    delta=float(folds[:,2].mean())
    rng=np.random.default_rng(SEED)
    boots=np.asarray([np.mean(folds[rng.integers(5,size=5),2])
                      for i in range(4000)])
    signs=np.asarray(list(itertools.product((-1.,1.),repeat=5)))
    vals=np.mean(signs*folds[:,2][None,:],axis=1)
    p=float(np.mean(np.abs(vals)>=abs(delta)-1e-14))
    return {
       "E0_stand_type_pair_equal_Hellinger2":base,
       "E1_plus_local_stump_microhabitat_pair_equal_Hellinger2":alt,
       "primary_E0_minus_E1_mean_gain":delta,
       "five_anonymous_source_pair_gains":sorted(float(x) for x in folds[:,2]),
       "positive_pair_gains":int((folds[:,2]>0).sum()),
       "negative_pair_gains":int((folds[:,2]<0).sum()),
       "equal_pair_gains":int((folds[:,2]==0).sum()),
       "pair_bootstrap_4000_percentile95":list(np.quantile(boots,[0.025,0.975])),
       "five_pair_exact_two_sided_signed_flips_p":p,
       "fixed_n_pairs":5,"n_exact_sign_vectors":32,
       "minimum_attainable_two_sided_p":0.0625,
       "one_study_geographical_portability_claim":False}


def synthetic():
    rs=np.random.default_rng(19)
    y=rs.random((14,7))
    y=y/np.linalg.norm(y,axis=1,keepdims=True)
    out=safe_predict(y,y)
    assert np.allclose(np.linalg.norm(out,axis=1),1)
    x=np.zeros((2,7))
    assert np.isclose(np.linalg.norm(safe_predict(x,y)[0]),1)
    artificial=np.array([[0.2,0.1,0.1],[0.3,0.2,0.1],
                         [0.1,0.2,-0.1],[-0.2,-0.1,-0.1],[0.3,0.35,-.05]])
    r=infer(artificial)
    assert r["n_exact_sign_vectors"]==32 and 0<=r["five_pair_exact_two_sided_signed_flips_p"]<=1
    assert design(True).named_steps["model"].alpha==10
    print("SWEDEN2026_FIVEPAIR_SOURCEFREE_KNOWN_TRUTH_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="ramberg2026_microhabitat_onepass/receipt.json")
    a=ap.parse_args()
    synthetic()
    if a.test:return
    output={
       "schema":"structural.ramberg2026_stump_microhabitat_pairholdout_onepass.v1",
       "source_original_publisher_SHA256":original.SHA,
       "frozen_protocol":PROTOCOL,
       "original_study_count":1,"fixed_original_geographic_pair_n":5,
       "original_beetle_source_rows_exported":False,
       "original_taxon_ids_or_sample_ids_exported":False,
       "new_species_composition_effect_scored":0,
       "status":"SOURCE_ORIGINAL_BIOLOGY_UNOPENED"}
    try:
        predictors,y,diag=full_source_data()
        result=infer(fivepair_score(predictors,y))
        output["source_anonymous_eligibility"]=diag
        output["observed_original_heldpair_predictive_result"]=result
        output["new_species_composition_effect_scored"]=1
        output["status"]="ORIGINAL_ONEPASS_EXPLORATORY_COMPLETE"
    except Exception as e:
        output["status"]="ORIGINAL_SOURCE_OR_SPECIES_ESTIMABILITY_STOP"
        output["error_class"]=type(e).__name__
        output["scientific_stop_reason"]=str(e)[:170] if isinstance(e,(ValueError,ScienceStop)) else ""
    dest=Path(a.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("RAMBERG2026_ONEPASS_STATUS",output["status"])
    print("NEW_PRIMARY_SCORE_COUNT",output["new_species_composition_effect_scored"])
    if "observed_original_heldpair_predictive_result" in output:
        r=output["observed_original_heldpair_predictive_result"]
        print("HELDPAIR_E0_E1_GAIN",r["primary_E0_minus_E1_mean_gain"],
              "EXACT_PAIR_P",r["five_pair_exact_two_sided_signed_flips_p"])


if __name__=="__main__":
    main()
