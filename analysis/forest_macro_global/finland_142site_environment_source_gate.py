#!/usr/bin/env python3
"""Source-only Finland 2023 standardized environment, hierarchy and collinearity.

Uses no beetle matrix, species IDs, trait scores or biodiversity responses.
Original per-site records stay private; exports only aggregate numeric diagnostics.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

from finland_author_2023_siteyear_source_crosswalk import (
    SOURCE_2023, pinned, source23_author_identity_fields_only, ScientificStop,
)

PREDICTORS = ("VD10", "agedomin", "OldFor_1km")
SOURCE_COLUMNS_FOR_CONTEXT = re.compile(
    r"latitude|longitude|(^|_)lon|(^|_)lat|coord|utm|east|north|geograph|"
    r"(^|_)x$|(^|_)y$|clim|precip|rain|solar|radia|temperature|temp|"
    r"effort|trap|sampling|year|study|region|plot|area|age|vd10|oldfor",
    re.IGNORECASE,
)


def numeric_summary(values: list[str], name: str):
    parsed = []
    missing = 0
    for raw in values:
        raw = raw.strip()
        if not raw or raw.upper() in {"NA", "NAN", "NULL"}:
            missing += 1
            continue
        try:
            x = float(raw)
        except ValueError as e:
            raise ScientificStop("SOURCE_STOP_NONNUMERIC_PRESELECTED_ENVIRONMENT_FIELD_"+name) from e
        if not math.isfinite(x):
            raise ScientificStop("SOURCE_STOP_NONFINITE_PRESELECTED_ENVIRONMENT_FIELD_"+name)
        parsed.append(x)
    if len(parsed) == 0:
        raise ScientificStop("SOURCE_STOP_ALL_ENVIRONMENT_VALUES_MISSING_"+name)
    a = sorted(parsed)
    def quantile(p):
        z=(len(a)-1)*p
        i=int(z)
        return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(z-i)
    return {
       "source_field_name": name,
       "total_author_sites":len(values),
       "nonmissing_numeric_sites":len(a),
       "missing_sites":missing,
       "zero_values":sum(v==0 for v in a),
       "negative_values":sum(v<0 for v in a),
       "minimum":round(a[0],7),
       "q25":round(quantile(.25),7),
       "median":round(quantile(.5),7),
       "q75":round(quantile(.75),7),
       "maximum":round(a[-1],7),
    }


def spearman(v,w):
    # Average ranks with tied values. No dependency needed for input screening.
    def rank(a):
        indexes=sorted(range(len(a)),key=lambda i:a[i])
        r=[0.0]*len(a)
        k=0
        while k<len(indexes):
            j=k+1
            while j<len(indexes) and a[indexes[j]]==a[indexes[k]]:
                j+=1
            value=(k+1+j)/2
            for i in indexes[k:j]:
                r[i]=value
            k=j
        return r
    v=rank(v);w=rank(w)
    ma=sum(v)/len(v);mb=sum(w)/len(w)
    av=sum((x-ma)*(y-mb) for x,y in zip(v,w))
    aa=sum((x-ma)**2 for x in v);bb=sum((x-mb)**2 for x in w)
    return av/math.sqrt(aa*bb) if aa>0 and bb>0 else float("nan")


def audit(path: Path):
    pinned(path, SOURCE_2023[1])
    author=source23_author_identity_fields_only(path)
    if len(author)!=142 or len(set(s for _,s,_ in author))!=142:
        raise ScientificStop("SOURCE_STOP_AUTHOR_142_INDEPENDENT_SITE_IDENTITY_DRIFT")
    with path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        cols=reader.fieldnames or []
        envrows=[r for r in reader]
    if len(envrows)!=142:
        raise ScientificStop("SOURCE_STOP_AUTHOR_142_COVARIATE_ROW_DRIFT")
    result={
        "schema":"structural.Finland2023_142forest_prebiology_environment_availability.v1",
        "original_author_DOI":"10.5281/zenodo.8322080",
        "author_original_environment_file_md5_verified":True,
        "original_author_sites":142,
        "original_author_yearsite_identity_verified":True,
        "source_header_column_count":len(cols),
        "source_header_names_environment_only":[
            c for c in cols if c not in {"rowID","Site","Year"} and
                re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,70}",c)
        ][:80],
        "candidate_original_method_climate_geography_field_names":[
            c for c in cols if c not in {"Site","rowID"} and
            SOURCE_COLUMNS_FOR_CONTEXT.search(c)
        ][:60],
        "taxon_source_matrix_and_Host_tree_traits_UNOPENED":True,
        "source_original_site_ids_and_covariate_values_NOT_REEXPORTED":True,
        "previous_frozen_Finland142site_D0p035237_UNCHANGED":True,
        "prior_PREDICTS_NEON_BALA_GEB_scoring_UNCHANGED":True,
        "eBird_used":False,
    }
    absent=[x for x in PREDICTORS if x not in cols]
    result["preselected_field_names_missing"]=absent
    if absent:
        result["status"]="SCIENTIFIC_SOURCE_STOP_MISSING_PREDECLARED_FIELD"
        return result
    sources={k:[str(row.get(k,"")) for row in envrows] for k in PREDICTORS}
    results={key:numeric_summary(vals,key) for key,vals in sources.items()}
    result["original_environment_source_anonymous_distribution"]=results
    # Author's published 2023 paper transformed positive source resources
    # (deadwood and old forest) and standardized ALL environmental covariates.
    # The exact released CSV fields are signed z scores: a negative z is not
    # negative raw deadwood volume / age. Never log1p a standardized value.
    result["original_source_environment_values_interpreted_as_author_standardized_zscores"] = True
    result["original_raw_deadwood_m3_ha_NOT_claimed_from_csv"] = True
    completed=[row for row in envrows if all(
        str(row.get(k,"")).strip() not in {"","NA","NaN","nan","NULL"} for k in PREDICTORS
    )]
    result["author_142_sites_all_three_predetermined_numeric_covariates_complete"]=len(completed)
    if len(completed)>=3:
        data={}
        for k in PREDICTORS:
            arr=[float(row[k]) for row in completed]
            data[k]=arr  # already transformed/standardized in original author release
            avg=sum(arr)/len(arr)
            sd=math.sqrt(sum((x-avg)**2 for x in arr)/(len(arr)-1))
            results[k]["mean_author_release_units"]=round(avg,7)
            results[k]["sample_standard_deviation_author_release_units"]=round(sd,7)
        corr={}
        for i,k in enumerate(PREDICTORS):
            for other in PREDICTORS[i+1:]:
                x=spearman(data[k],data[other])
                corr[k+"__"+other]=round(x,6) if math.isfinite(x) else None
        result["original_predictor_only_complete_case_spearman_associations"]=corr
    context=("climID","MeanTemp","TotalPrecip","globRad_WHm2","log_Nr_traps",
             "lat_WGS84","lon_WGS84","Year")
    result["planned_climate_effort_coordinates_field_availability"]={
        k:k in cols for k in context
    }
    if "climID" in cols:
        groups={}
        for row in envrows:
            key=str(row["climID"]).strip()
            if not key:continue
            groups[key]=groups.get(key,0)+1
        result["author_climate_group_anonymous_support"]={
            "unique_groups":len(groups),
            "groups_with_two_or_more_source_sites":sum(v>=2 for v in groups.values()),
            "groups_with_five_or_more_source_sites":sum(v>=5 for v in groups.values()),
            "max_site_count_one_group":max(groups.values(),default=0),
            "min_site_count_one_group":min(groups.values(),default=0),
        }
    for k in context:
        if k not in cols or k in ("climID","Year"):continue
        vals=[]
        for row in envrows:
            raw=str(row[k]).strip()
            if not raw or raw.upper() in ("NA","NULL","NAN"):continue
            try:val=float(raw)
            except ValueError:continue
            if math.isfinite(val):vals.append(val)
        result.setdefault("other_context_numeric_field_nonmissing_only",{})[k]=len(vals)
    result["status"]=(
        "ENVIRONMENT_ONLY_AUTHOR_STANDARDIZED_Z_MEASUREMENTS_AVAILABLE_FOR_NEXT_PRESPEC"
        if len(completed)>=60 else
        "SCIENTIFIC_SOURCE_STOP_TOO_FEW_COMPLETE_ENVIRONMENT_SITES_BELOW_60"
    )
    return result


def synthetic():
    rows=["0","2","NA","4"]
    stats=numeric_summary(rows,"VD10")
    assert stats["nonmissing_numeric_sites"]==3
    assert stats["zero_values"]==1
    assert stats["missing_sites"]==1
    assert abs(spearman([1,2,3],[3,2,1])+1)<1e-12
    assert abs(spearman([10,20,30],[3,2,1])+1)<1e-12
    assert abs(spearman([1,2,3],[1,2,3])-1)<1e-12
    assert math.isfinite(spearman([0,0,1,1],[1,2,2,3]))
    print("SYNTHETIC_ENVIRONMENT_ONLY_SOURCE_QA_AND_RANK_TIES_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--file",type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    synthetic()
    if args.test:return
    if not args.file or not args.out:
        ap.error("--file and --out required")
    try:
        result=audit(args.file)
    except ScientificStop as exc:
        result={
            "schema":"structural.Finland2023_142forest_prebiology_environment_availability.v1",
            "status":str(exc),
            "source_ONLY_failure_NOT_a_beetle_effect":True,
            "no_biology_or_site_environment_coupling_scored":True,
        }
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Finland142_original_author_forest_environment_sourceonly.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8"
    )
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
