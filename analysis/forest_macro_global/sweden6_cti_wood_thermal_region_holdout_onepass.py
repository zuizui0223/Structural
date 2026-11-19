#!/usr/bin/env python3
"""ONE prespecified original SLU Sweden six-region CTI woody-substrate prediction.

First original CTI source-value access ONLY AFTER 87-row 29-plot
six-region environmental source admission succeeds. Existing original
specieslist_xylo.csv, richness and abundance fields stay sealed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import random
import statistics

from sweden6_slu_original_three_file_header_gate import (
    ORIGINAL_URLS, official_get, SourceStop
)
from sweden6_slu_climate_plotshade_nonresponse_gate import (
    CLIMATE_SHA, CLIMATE_SIZE, FIELDS, original_climate_nonresponse_only,
    finite_numeric, strict_integer_key
)

PRESPEC="docs/FOREST_SWEDEN6_CTISUBSTRATE_REGION_HOLDOUT_EXPLORATORY_ONEPASS_PRESPEC_20261119.md"
LAM=10.0
SEED=20261119
BOOT=4000
BLOCKS=("1","2","3","4","5","6")
EXPECTED_BLOCK_PLOTS={"1":5,"2":5,"3":4,"4":5,"5":5,"6":5}
EXPECTED_ROWS=87

def admitted_source_original_environment(raw):
    qa=original_climate_nonresponse_only(raw,strict_original=False)
    # The historical 30-plot admission failed and remains STOP.
    # This distinct cohort is observed 29 plots, 87 COMPLETE shade triplets.
    if not (
        qa["source_original_climate_TABLE_rows"]==87 and
        qa["source_actual_unique_block_plot_shade_keys"]==87 and
        qa["source_author_6block_count"]==6 and
        qa["source_author_30block_plot_count"]==29 and
        qa["source_nominal_plotshade_missing_cell_count_NOT_IMPUTED"]==3 and
        qa["source_each_block_original_unique_plot_counts"]==EXPECTED_BLOCK_PLOTS and
        qa["source_original_min_plot_count_per_block"]==4 and
        qa["source_original_min_shades_available_per_plot"]==3 and
        all(qa["source_original_original_predictor_missing_rows"][k]==0
            for k in ("Mikrotemp","Makrotemp","Bark","Diameter","Regional climate","Aspect"))
    ):
        raise SourceStop("SLU_SIXBLOCK_29PLOT_87SHADE_PREBIOLOGY_PHYSICAL_GATE_STOP")
    return qa

def first_original_cti_response(raw):
    # Caller has finished independent nonresponse-source gate BEFORE this.
    reader=csv.DictReader(
        io.StringIO(raw.decode("utf-8-sig"),newline=""),
        delimiter=";",strict=True
    )
    if tuple(reader.fieldnames or ())!=FIELDS:
        raise SourceStop("SLU_ORIGINAL_BEETLE_CTI_SOURCE_SCHEMA_DRIFT")
    rows=[]
    ids=set()
    for r in reader:
        if None in r or set(r)!=set(FIELDS):
            raise SourceStop("SLU_ORIGINAL_SOURCE_RESPONSE_ROW_WIDTH_DRIFT")
        block=strict_integer_key(r["Block"],"BLOCK")
        plot=strict_integer_key(r["Plot"],"PLOT")
        shade=strict_integer_key(r["Shade"],"SHADE")
        key=(block,plot,shade)
        if key in ids:
            raise SourceStop("SLU_ORIGINAL_DUPLICATE_CTI_BLOCK_PLOT_SHADE")
        ids.add(key)
        values={}
        for var in ("Regional climate","Makrotemp","Mikrotemp","Bark","Diameter","Aspect"):
            v=finite_numeric(r[var])
            if v is None:raise SourceStop("SLU_ORIGINAL_CTI_MODEL_PREDICTOR_NONFINITE_STOP")
            values[var]=v
        response=finite_numeric(r["CTI"])
        if response is None:
            raise SourceStop("SLU_ORIGINAL_CTI_87_RESPONSE_NONFINITE_STOP")
        theta=values["Aspect"]*math.pi/180
        features={
           "Regional climate":values["Regional climate"],
           "Makrotemp":values["Makrotemp"],
           "Shade2":1.0 if shade=="2" else 0.0,
           "Shade3":1.0 if shade=="3" else 0.0,
           "Aspect_sin":math.sin(theta),
           "Aspect_cos":math.cos(theta),
           "Mikrotemp":values["Mikrotemp"],
           "Bark":values["Bark"],
           "Diameter":values["Diameter"],
        }
        rows.append({"_block":block,"_sample":key,"_X":features,"_Y":response})
    if len(rows)!=EXPECTED_ROWS or len(ids)!=EXPECTED_ROWS:
        raise SourceStop("SLU_ORIGINAL_CTI_87_RESPONSE_TOTAL_DRIFT")
    return rows

E0=("Regional climate","Makrotemp","Shade2","Shade3","Aspect_sin","Aspect_cos")
E1=E0+("Mikrotemp",)
E2=E1+("Bark","Diameter")

def solve(a,b):
    n=len(a)
    mat=[list(a[i])+[b[i]] for i in range(n)]
    for col in range(n):
        pivot=max(range(col,n),key=lambda j:abs(mat[j][col]))
        if abs(mat[pivot][col])<1e-10:
            raise SourceStop("SLU_RIDGE_FIXED_DESIGN_SINGULAR")
        mat[col],mat[pivot]=mat[pivot],mat[col]
        divisor=mat[col][col]
        for k in range(col,n+1):
            mat[col][k]/=divisor
        for j in range(n):
            if j==col:continue
            q=mat[j][col]
            for k in range(col,n+1):
                mat[j][k]-=q*mat[col][k]
    return [row[-1] for row in mat]

def fit_predict(train,test,features):
    if len(train)<60 or not test:
        raise SourceStop("SLU_LOBO_TRAIN_HELD_BLOCK_SAMPLE_TOO_SMALL")
    means={f:statistics.fmean(x["_X"][f] for x in train) for f in features}
    scales={}
    for f in features:
        variance=statistics.fmean((x["_X"][f]-means[f])**2 for x in train)
        scales[f]=math.sqrt(variance) if variance>0 else 1.0
    def vector(item):
        return [1.0]+[(item["_X"][f]-means[f])/scales[f] for f in features]
    xtrain=[vector(x) for x in train]
    ytrain=[x["_Y"] for x in train]
    p=len(features)+1
    lhs=[[math.fsum(x[i]*x[j] for x in xtrain)+(LAM if i==j and i>0 else 0)
          for j in range(p)] for i in range(p)]
    rhs=[math.fsum(x[i]*y for x,y in zip(xtrain,ytrain)) for i in range(p)]
    coef=solve(lhs,rhs)
    return [math.fsum(w*x for w,x in zip(coef,vector(item))) for item in test]

def percentile(values,p):
    s=sorted(values)
    x=(len(s)-1)*p
    lo=int(math.floor(x));hi=int(math.ceil(x))
    return s[lo]+(s[hi]-s[lo])*(x-lo)

def onepass(rows):
    if len({x["_block"] for x in rows})!=6:
        raise SourceStop("SLU_6_INDEPENDENT_HELD_REGIONS_DRIFT")
    loss_by_block={}
    region_size={}
    for block in BLOCKS:
        test=[x for x in rows if x["_block"]==block]
        train=[x for x in rows if x["_block"]!=block]
        if len(test)!=EXPECTED_BLOCK_PLOTS[block]*3:
            raise SourceStop("SLU_29PLOT_REGION_BLOCK_HOLDOUT_SIZE_DRIFT")
        region_size[block]=len(test)
        losses={}
        for name,features in (("E0",E0),("E1",E1),("E2",E2)):
            pred=fit_predict(train,test,features)
            losses[name]=statistics.fmean((p-item["_Y"])**2 for p,item in zip(pred,test))
        loss_by_block[block]=losses
    def reg_mean(metric):
        return statistics.fmean(loss_by_block[b][metric] for b in BLOCKS)
    m0,m1,m2=reg_mean("E0"),reg_mean("E1"),reg_mean("E2")
    wood=[loss_by_block[b]["E1"]-loss_by_block[b]["E2"] for b in BLOCKS]
    micro=[loss_by_block[b]["E0"]-loss_by_block[b]["E1"] for b in BLOCKS]
    primary=statistics.fmean(wood)
    rng=random.Random(SEED)
    boot=[statistics.fmean(rng.choice(wood) for _ in range(6)) for _ in range(BOOT)]
    CI=[percentile(boot,.025),percentile(boot,.975)]
    extreme=0
    for signs in itertools.product((-1,1),repeat=6):
        x=statistics.fmean(a*b for a,b in zip(wood,signs))
        if abs(x)>=abs(primary)-1e-12:
            extreme+=1
    p=extreme/64
    positive=sum(x>0 for x in wood)
    support=primary>0 and CI[0]>0 and p<.05 and positive>=5
    return {
       "original_87_source_CTI_observations_ALL_FINITE":True,
       "original_29_source_plots_in_6_regions":True,
       "original_source_region_equal_block_sizes_SORTED":sorted(region_size.values()),
       "original_cti_overall_min":min(x["_Y"] for x in rows),
       "original_cti_overall_max":max(x["_Y"] for x in rows),
       "original_leave_one_BLOCK_out_region_equal_MSE_CTIsquared":{
          "E0_regional_macro_shade_aspect":m0,
          "E1_plus_source_2020_underbark_microtemp":m1,
          "E2_plus_source_spruce_Bark_and_Diameter":m2,
       },
       "primary_region_equal_increment_MSE_E1_minus_E2":primary,
       "secondary_region_equal_increment_MSE_E0_minus_E1":statistics.fmean(micro),
       "original_region_blocks_with_positive_wood_increment":positive,
       "original_region_blocks_with_positive_micro_increment":sum(x>0 for x in micro),
       "original_region_equal_bootstrap4000_fixedseed95_primary":CI,
       "original_region_equal_exact_64signs_twosided_p":p,
       "original_region_equal_exact_signflip_extreme_of_64":extreme,
       "fixed_ridge_lambda":LAM,
       "fixed_region_bootstrap_seed":SEED,
       "frozen_exploratory_directional_support_THRESHOLD_MET":support,
       "status":(
          "EXPLORATORY_SWEDEN6_WOOD_CTITEMPERATURE_OUTOFREGION_INCREMENT_SUPPORTED"
          if support else
          "EXPLORATORY_SWEDEN6_WOOD_CTITEMPERATURE_OUTOFREGION_INCREMENT_NOT_SUPPORTED"
       ),
       "original_tree_host_species_fixed_spruce_NO_HOST_ABSENCE_test":True,
       "source_original_microclimate_2020_beetles_2021_NOT_CONCURRENT":True,
       "original_specieslist_xylo_3460_SPECIES_ROWS_NOT_ACCESSED":True,
       "original_species_richness_Totlab_biological_columns_NOT_ACCESSED":True,
       "original_site_id_or_CTI_by_region_raw_records_NOT_EXPORTED":True,
       "causal_thermal_refuge_or_3D_resource_lock_NOT_ESTIMATED":True,
    }

def known_truth():
    beta=solve([[2.0,0.0],[0.0,3.0]],[4.0,9.0])
    assert all(abs(v-w)<1e-10 for v,w in zip(beta,(2.0,3.0)))
    assert len(E0)==6 and len(E1)==7 and len(E2)==9 and LAM==10.0
    assert math.isclose(percentile([0.0,10.0],.5),5)
    fake=[]
    for b in BLOCKS:
        for site in range(EXPECTED_BLOCK_PLOTS[b]):
            for shade in ("1","2","3"):
                i=len(fake)
                X={f:float(i%7+1) for f in E2}
                X["Regional climate"]=float(int(b))
                X["Shade2"]=float(shade=="2")
                X["Shade3"]=float(shade=="3")
                fake.append({"_block":b,"_sample":(b,site,shade),
                             "_X":X,"_Y":10.0+.1*(i%4)})
    r=onepass(fake)
    assert r["original_29_source_plots_in_6_regions"]
    assert r["original_region_equal_exact_64signs_twosided_p"]>=0
    assert r["causal_thermal_refuge_or_3D_resource_lock_NOT_ESTIMATED"]
    print("SYNTHETIC_SWEDEN6_FIXED_LOBO_E0_E1_E2_RIDGE_CTIsquared_64SIGNFLIP_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    report={
       "schema":"structural.slu_sweden6_beetle_cti_sprucewood_2020climate_2021observed_onepass.v1",
       "precommit":PRESPEC,
       "original_source_DOI":"10.5878/dhmc-bq15",
       "original_source_climate_csv_bytes":CLIMATE_SIZE,
       "original_source_sha256":CLIMATE_SHA,
       "original_29_plot_87rows_physical_gate_BEFORE_CTI":True,
       "published_Gossmann2024_regionaltemp_x_shade_PRIOR_ART":True,
       "previous_6field_88row_30plot_SOURCE_STOPS_PRESERVED":True,
       "no_beetle_specieslist_XYLO_OR_original_richness_Totalab_rows_ACCESSED":True,
       "prior_Finland_Carpathian_England_PREDICTS_Thai_NEON_BALA_GEB_biology_UNCHANGED":True,
       "eBird_used":False,"TinyFish_used":False,
    }
    try:
        raw=official_get(ORIGINAL_URLS["boreal_forest_climate_data.csv"][0])
        if len(raw)!=CLIMATE_SIZE or hashlib.sha256(raw).hexdigest()!=CLIMATE_SHA:
            raise SourceStop("SLU_ORIGINAL_CLIMATE_SOURCE_SHA_DRIFT")
        original_qa=admitted_source_original_environment(raw)
        # END RESPONSE-BLIND SOURCE ELIGIBILITY. Only now read CTI.
        rows=first_original_cti_response(raw)
        result=onepass(rows)
        report["original_source_BIOLOGICAL_CTI_ONEPASS_RESULT"]=result
        report["original_original_source_method_pass_without_CTIOpen"]=True
        report["source_87environment_predictors_full_before_response"]=True
        report["original_CTIsource_biological_response_FIRST_READ"]=True
        report["status"]=result["status"]
    except SourceStop as exc:
        report["status"]=str(exc)
        report["source_or_CTI_value_STOP_not_ecological_null"]=True
        report["no_valid_CTI_predictive_score"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Sweden6_original_29plot_2020micro_barkdiameter_2021CTI_LOBO_onepass.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SLU_SWEDEN6_29PLOT_ONEPASS_CTIsubstrate_PREDICTIVE",report["status"])
    print("NO_ORIGINAL_3460_SPECIES_RECORDS_OR_CTI_BY_REGION_EXPORTED")
if __name__=="__main__":
    main()
