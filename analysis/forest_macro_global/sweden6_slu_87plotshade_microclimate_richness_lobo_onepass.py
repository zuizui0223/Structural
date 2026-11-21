#!/usr/bin/env python3
"""ONE frozen independent Swedish region-out richness predictive contrast.

New SOURCE-AUTHORED 87-row plot×shade aggregated richness response from the
original SLU climate summary only. We do NOT download/open the original beetle
species/Number/STI table, including its two mismatched Plot keys.

E0 = source regional climate + 2020 macro air temperature + HORIZONTAL shade
     + bark amount + spruce log diameter + circular aspect;
E1 = E0 + measured 2020 under-bark mean microclimate.
Output is a six-region leave-block-out prediction difference on 2021 recorded
plot-shade richness, not a 3D vertical habitat/resource-absence mechanism.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import random
import statistics
import re

from sweden6_slu_original_three_file_header_gate import (
    official_get, ORIGINAL_URLS, first_header_only, SourceStop
)

PRESPEC="docs/FOREST_SWEDEN6_87SOURCE_LOBO_MICROCLIMATE_INCREMENTAL_RICHNESS_ONEPASS_PRESPEC_20261119.md"
SOURCE_NAME="boreal_forest_climate_data.csv"
EXPECTED_BYTES=7019
EXPECTED_SHA256="d546273c352fb2cab97f63f35883f970baea09790348fa4c0dda3e1bc55ba776"
SOURCE_HEADER=(
    "Block","Mikrotemp","Makrotemp","CTI","Plot","Shade",
    "Bark","Diameter","Regional climate","Aspect","Species richness","Totlab"
)
BLOCK_PLOTS={
   1:set(range(11,16)),2:set(range(6,11)),3:set(range(16,21)),
   4:set(range(21,26)),5:set(range(1,6)),6:set(range(26,31))
}
MODEL_LAMBDA=10.0
BOOT_SEED=20261119
BOOT_N=4000
BASELINE_NAMES=(
   "Regional climate","Makrotemp","Shade2","Shade3",
   "Bark","Diameter","Aspect_sin","Aspect_cos"
)
EXPANDED_NAMES=BASELINE_NAMES+("Mikrotemp",)
DELIMITER={ "comma":",", "semicolon":";", "tab":"\t" }
EXACT_UINT=re.compile(r"^[0-9]+$")

def exact_posint(text,low,high,field):
    s=str(text or "").strip()
    if not EXACT_UINT.fullmatch(s):
        raise SourceStop("SLU_LOBO_SOURCE_"+field+"_NOT_LITERAL_INTEGER")
    n=int(s)
    if n<low or n>high:
        raise SourceStop("SLU_LOBO_SOURCE_"+field+"_OUT_OF_PUBLISHED_RANGE")
    return n

def unique_source_header_only(raw):
    first=first_header_only(raw,len(SOURCE_HEADER))
    if tuple(first["original_HEADER_exact_author_field_names"])!=SOURCE_HEADER:
        raise SourceStop("SLU_LOBO_ORIGINAL_12_SOURCE_AUTHOR_FIELD_ORDER_DRIFT")
    return first["original_CSV_header_delimiter"]

def source_response_blind_id_admission(raw,source_delim):
    # CSV transport parses entire rows but examines only Block/Plot/Shade IDs.
    # All numerical ecology values remain text and are not semantically read
    # until all original 87 source identity and independence checks pass.
    stream=io.StringIO(raw.decode("utf-8-sig"),newline="")
    reader=csv.DictReader(stream,delimiter=DELIMITER[source_delim],strict=True)
    if tuple(reader.fieldnames or ())!=SOURCE_HEADER:
        raise SourceStop("SLU_LOBO_ORIGINAL_SOURCE_SCHEMA_CHANGED")
    records=[]
    keys=set()
    plot_keys=set()
    block_plot=defaultdict(set)
    shade_keys=defaultdict(set)
    for r in reader:
        if None in r or set(r)!=set(SOURCE_HEADER):
            raise SourceStop("SLU_LOBO_ORIGINAL_SOURCE_ROW_WIDTH_CHANGED")
        block=exact_posint(r["Block"],1,6,"BLOCK")
        plot=exact_posint(r["Plot"],1,30,"PLOT")
        shade=exact_posint(r["Shade"],1,3,"SHADE")
        if plot not in BLOCK_PLOTS[block]:
            raise SourceStop("SLU_LOBO_CLIMATE_BLOCK_PLOT_AUTHOR_CODEBOOK_INVALID")
        k=(block,plot,shade)
        if k in keys:
            raise SourceStop("SLU_LOBO_DUPLICATE_ORIGINAL_PLOT_SHADE_SOURCE_KEY")
        keys.add(k)
        plot_keys.add((block,plot))
        shade_keys[(block,plot)].add(shade)
        block_plot[block].add(plot)
        records.append({"_b":block,"_p":plot,"_s":shade,"_private_raw":r})
        if len(records)>1000:
            raise SourceStop("SLU_LOBO_UNEXPECTED_SOURCE_ROWS_GT1000")
    if (len(records)!=87 or len(keys)!=87 or len(plot_keys)!=29
        or len(block_plot)!=6 or
        sorted(map(len,block_plot.values()))!=[4,5,5,5,5,5]
        or any(shades!={1,2,3} for shades in shade_keys.values())):
        raise SourceStop("SLU_LOBO_SOURCE_29PLOT_87SHADE_ID_ADMISSION_FAILED")
    return records,{
       "source_original_environment_summary_row_count":len(records),
       "source_original_independent_region_block_count":len(block_plot),
       "source_original_distinct_physical_plot_keys":len(plot_keys),
       "source_original_plot_counts_per_region_SORTED":sorted(map(len,block_plot.values())),
       "source_original_distinct_plot_shade_keys":len(keys),
       "source_original_all_plots_three_horizontal_shades":True,
       "source_original_source_IDs_VALIDATED_before_numeric_environment_or_response":True,
       "source_original_species_richness_or_environment_values_SEMANTICALLY_READ_at_ID_GATE":0,
       "source_taxon_SPECIES_NUMBER_STI_raw_file_NOT_DOWNLOADED":True,
    }

def source_finite(text,field):
    s=str(text or "").strip()
    # Freeze one unambiguous decimal-dot or decimal-comma syntax without
    # thousands separators or scientific-notation remapping.
    if not re.fullmatch(r"[+-]?[0-9]+(?:[.,][0-9]+)?(?:[eE][+-]?[0-9]+)?",s):
        raise SourceStop("SLU_LOBO_ORIGINAL_SOURCE_"+field+"_NOT_FINITE_SIMPLE_NUMERIC")
    if "," in s and "." in s:
        raise SourceStop("SLU_LOBO_SOURCE_AMBIGUOUS_NUMERIC_FORMAT")
    value=float(s.replace(",","."))
    if not math.isfinite(value):
        raise SourceStop("SLU_LOBO_ORIGINAL_"+field+"_NONFINITE")
    return value

def parse_original_87_source_richness_and_predictors(records):
    dataset=[]
    for r in records:
        raw=r["_private_raw"]
        richness=source_finite(raw["Species richness"],"RICHNESS")
        if richness<0 or richness!=math.floor(richness):
            raise SourceStop("SLU_LOBO_ORIGINAL_RICHNESS_NEGATIVE_OR_NONINTEGER")
        reg=source_finite(raw["Regional climate"],"REGIONAL_CLIMATE")
        macro=source_finite(raw["Makrotemp"],"MACROTEMP")
        micro=source_finite(raw["Mikrotemp"],"MICROTEMP")
        bark=source_finite(raw["Bark"],"BARK")
        diameter=source_finite(raw["Diameter"],"DIAMETER")
        aspect=source_finite(raw["Aspect"],"ASPECT")
        if bark<0 or diameter<0:
            raise SourceStop("SLU_LOBO_ORIGINAL_BARK_DIAMETER_NEGATIVE")
        if aspect<0 or aspect>360:
            raise SourceStop("SLU_LOBO_ORIGINAL_ASPECT_NOT_0TO360_DEGREES")
        angle=math.radians(aspect)
        shade2=float(r["_s"]==2)
        shade3=float(r["_s"]==3)
        x=[reg,macro,shade2,shade3,bark,diameter,math.sin(angle),math.cos(angle),micro]
        if len(x)!=len(EXPANDED_NAMES):
            raise SourceStop("SLU_LOBO_FIXED_FEATURES_NOT_9")
        dataset.append({"region":r["_b"],"features":x,"response":math.log1p(int(richness))})
        # Do not inspect or use original CTI / Totlab or raw Species Number STI.
    return dataset

def solve(a,b):
    n=len(a)
    aug=[list(a[i])+[b[i]] for i in range(n)]
    for col in range(n):
        k=max(range(col,n),key=lambda i:abs(aug[i][col]))
        if abs(aug[k][col])<1e-10:
            raise SourceStop("SLU_LOBO_FIXED_RIDGE_LINEAR_SOLVE_ILL_CONDITIONED")
        aug[col],aug[k]=aug[k],aug[col]
        pivot=aug[col][col]
        for z in range(col,n+1):aug[col][z]/=pivot
        for i in range(n):
            if i==col:continue
            multiplier=aug[i][col]
            for z in range(col,n+1):aug[i][z]-=multiplier*aug[col][z]
    return [a[-1] for a in aug]

def fixed_ridge_predict(train,heldout,n_features):
    # Strict training-only feature scaling and intercept unpenalized.
    means=[statistics.fmean(x["features"][j] for x in train) for j in range(n_features)]
    scales=[]
    for j in range(n_features):
        sd=math.sqrt(statistics.fmean((x["features"][j]-means[j])**2 for x in train))
        scales.append(sd if sd>1e-12 else 1.0)
    def row(r):
        return [1.0]+[(r["features"][j]-means[j])/scales[j] for j in range(n_features)]
    X=[row(z) for z in train]
    y=[r["response"] for r in train]
    p=n_features+1
    lhs=[[math.fsum(x[i]*x[j] for x in X)+(MODEL_LAMBDA if i==j and i>0 else 0.0)
          for j in range(p)] for i in range(p)]
    rhs=[math.fsum(X[k][i]*y[k] for k in range(len(X))) for i in range(p)]
    beta=solve(lhs,rhs)
    return [math.fsum(row(r)[i]*beta[i] for i in range(p)) for r in heldout]

def percentile(a,f):
    v=sorted(a)
    x=(len(v)-1)*f
    lo=int(math.floor(x));hi=int(math.ceil(x))
    return v[lo]+(v[hi]-v[lo])*(x-lo)

def one_fixed_original_predictive_test(dataset):
    regions=sorted({r["region"] for r in dataset})
    if regions!=[1,2,3,4,5,6]:
        raise SourceStop("SLU_LOBO_ORIGINAL_SIX_REGION_DESIGN_CHANGED")
    deltas=[]; baseline=[]; expanded=[]; all_baseline=[]; all_expanded=[]; region_sites=[]
    for block in regions:
        train=[r for r in dataset if r["region"]!=block]
        test=[r for r in dataset if r["region"]==block]
        if len(test) not in (12,15) or len(train)+len(test)!=87:
            raise SourceStop("SLU_LOBO_REGION_HOLDOUT_SAMPLE_SIZES_DRIFT")
        y0=fixed_ridge_predict(train,test,len(BASELINE_NAMES))
        y1=fixed_ridge_predict(train,test,len(EXPANDED_NAMES))
        l0=[(v["response"]-p)**2 for v,p in zip(test,y0)]
        l1=[(v["response"]-p)**2 for v,p in zip(test,y1)]
        b=statistics.fmean(l0);e=statistics.fmean(l1)
        baseline.append(b);expanded.append(e)
        deltas.append(b-e)
        all_baseline.extend(l0);all_expanded.extend(l1)
        region_sites.append(len(test))
    primary=statistics.fmean(deltas)
    signed=0
    for mask in range(1<<6):
        trial=math.fsum((-x if mask&(1<<i) else x) for i,x in enumerate(deltas))/6
        if abs(trial)>=abs(primary)-1e-12:signed+=1
    p=signed/64
    rng=random.Random(BOOT_SEED)
    boot=[statistics.fmean(rng.choice(deltas) for _ in deltas) for _ in range(BOOT_N)]
    ci=[percentile(boot,.025),percentile(boot,.975)]
    pos=sum(d>0 for d in deltas)
    bmean=statistics.fmean(baseline)
    emean=statistics.fmean(expanded)
    support=primary>0 and ci[0]>0 and p<.05 and pos>=5
    return {
       "source_original_n_nested_plotshade_richness_units":len(dataset),
       "source_original_six_region_heldout_folds":len(regions),
       "heldout_plotshade_rows_per_original_region_ANONYMOUS_SORTED":sorted(region_sites),
       "model_source_response":"log1p(original_author_Species_richness)",
       "fixed_baseline_eight_source_features":list(BASELINE_NAMES),
       "fixed_expanded_added_only_feature":"Mikrotemp",
       "fixed_training_only_standardized_ridge_lambda":MODEL_LAMBDA,
       "heldout_region_EQUAL_baseline_MSE_logrichness":bmean,
       "heldout_region_EQUAL_plus_micro_MSE_logrichness":emean,
       "heldout_region_EQUAL_add_micro_MSE_IMPROVEMENT":primary,
       "heldout_site_EQUAL_baseline_MSE":statistics.fmean(all_baseline),
       "heldout_site_EQUAL_plus_micro_MSE":statistics.fmean(all_expanded),
       "heldout_region_direction_positive_count":pos,
       "source_original_six_REGION_conditional_exact_2sided_signflip_p":p,
       "source_original_six_REGION_signflip_total":64,
       "source_original_4000_REGION_bootstrap95_improvement":ci,
       "source_frozen_exploratory_directional_support_criterion":support,
       "original_RICHNESS_derived_from_author_summary_not_new_raw_beetle_taxa":True,
       "source_microclimate_2020_vs_richness_2021_LAG":True,
       "source_horizontal_forest_edge_shade_NOT_VERTICAL_height":True,
       "source_all_sites_have_placed_spruce_logs_HOST_PRESENT":True,
       "source_six_regions_one_country_no_globally_general_effect":True,
       "source_published_richness_and_shade_effects_PRIOR_ART":True,
       "status":("EXPLORATORY_SWEDEN6_MICROTEMP_LOBO_RICHNESS_INCREMENTAL_DIRECTIONAL_SUPPORT_ONLY"
                 if support else "EXPLORATORY_SWEDEN6_MICROTEMP_LOBO_RICHNESS_INCREMENTAL_NOT_SUPPORTED"),
    }

def known_truth():
    assert solve([[2,0],[0,3]],[4,9])==[2.0,3.0]
    assert BASELINE_NAMES==EXPANDED_NAMES[:-1]
    assert len(BASELINE_NAMES)==8 and len(EXPANDED_NAMES)==9
    assert BOOT_N==4000 and BOOT_SEED==20261119
    climate=("Block;Mikrotemp;Makrotemp;CTI;Plot;Shade;Bark;Diameter;Regional climate;Aspect;Species richness;Totlab\n"
             "1;15;12;SECRET_CTI;11;1;50;20;10;90;25;SECRET_ABUNDANCE\n").encode()
    header=unique_source_header_only(climate)
    assert header=="semicolon"
    # Exact source checker rejects a synthetic incomplete original source
    # without ever numerically reading richness, CTI, temperature or abundance.
    try:
        source_response_blind_id_admission(climate,header)
        raise AssertionError("incomplete synthetic source wrongly admitted")
    except SourceStop as exc:
        assert "29PLOT_87SHADE" in str(exc)
    assert len(climate.split(b"\n"))>=2
    print("SYNTHETIC_SLU87_SOURCE_GATE_AND_RIDGE_LOBO_ORIGINAL_RESPONSE_FIREWALL_PASS")

def original_once():
    raw=official_get(ORIGINAL_URLS[SOURCE_NAME][0])
    if len(raw)!=EXPECTED_BYTES or hashlib.sha256(raw).hexdigest()!=EXPECTED_SHA256:
        raise SourceStop("SLU_LOBO_ORIGINAL_PUBLISHER_CLIMATE_FILE_SHA_SIZE_DRIFT")
    delim=unique_source_header_only(raw)
    metadata,source_id_receipt=source_response_blind_id_admission(raw,delim)
    # First source numeric environmental/richness semantic read comes only AFTER
    # every original header and physical unit gate above passed.
    data=parse_original_87_source_richness_and_predictors(metadata)
    result=one_fixed_original_predictive_test(data)
    return {"source_original_publisher_climate_file_sha256":EXPECTED_SHA256,
            "source_original_climate_file_size":EXPECTED_BYTES,
            "original_source_verified_87plotshade_identity":source_id_receipt,
            "original_only_one_richness_microclimate_outofregion_test":result,
            "source_original_raw_3459beetle_species_rows_NOT_OPENED":True,
            "source_original_CTI_Totlab_source_fields_NOT_SEMANTICALLY_ACCESSED":True,
            "source_original_raw_plot_or_environment_values_NOT_EXPORTED":True,
            "status":result["status"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:p.error("--out required")
    report={
      "schema":"structural.SLU_Sweden6_source87_microtemp_incremental_LOBO_onepass.v1",
      "precommit":PRESPEC,
      "original_author_data_DOI":"10.5878/dhmc-bq15",
      "original_paper_DOI":"10.1111/ddi.13836",
      "frozen_earlier_species_source_identifier_mismatch_STOP_PRESERVED":True,
      "source_2020_microclimate_predicting_2021_recorded_richness_Not_concurrent":True,
      "original_BEETLE_RAW_SPECIES_NUMBERS_STI_source_data_READ":0,
      "prior_England_Carpathian_Finland_PREDICTS_Thai_NEON_BALA_GEB_effects_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        report["one_original_publisher_source_conditional_test"]=original_once()
        report["status"]=report["one_original_publisher_source_conditional_test"]["status"]
    except (SourceStop,ValueError,UnicodeError,csv.Error,OverflowError,ZeroDivisionError) as e:
        report["status"]=str(e) if isinstance(e,SourceStop) else "SLU_LOBO_ORIGINAL_NUMERIC_OR_MODEL_STOP"
        report["scientific_source_data_quality_STOP_not_ecological_null"]=True
        report["original_onepass_valid_ecological_score_OBTAINED"]=False
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Sweden6_SLU_original87_microclimate_heldout_richness_onepass.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("ORIGINAL_SLU_SWEDEN6_87_MICROCLIMATE_INCREMENTAL_RICHNESS_LOBO",report["status"])
    print("NO_RAW_BEETLE_SPECIES_NUMBERS_OR_STI_SOURCE_READ")
if __name__=="__main__": main()
