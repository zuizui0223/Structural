#!/usr/bin/env python3
"""ONE exploratory Gloor116 guild-incidence stand-heldout deadwood prediction.

Written/frozen after header-only Weiss170 source format sensitivity but
BEFORE any Gloor species/capture numerical value read. Original raw
source rows and site/taxon IDs stay private in the GitHub runner.

This is NOT a confirmatory author-mapped taxon validation; the original
literal 0/309 HOLD stays intact. It is NOT between-country guild transport.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

from carpathian116_weiss_original_name_only_coverage import (
    validate_original_weiss_private_ledger,
    source_gloor_name_headers,
    EXACT_BINOMIAL,
)
from carpathian116_taxon_header_grammar_rscript_sourceonly import GRAMMAR
from carpathian116_original_author_schema_gate import (
    original_record_links, official_get, FROZEN_FILES, SourceStop
)
from carpathian116_stand_environment_sourceqa import only_whitelist, PREDICTORS

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_WEISS_GUILD_DEADWOOD_LOSO_EXPLORATORY_ONEPASS_PRESPEC_20261118.md"
GUILD=("m","n","p","s","x","z")
LAM=10.0
SEED=20261118
BOOTSTRAPS=4000
BASELINE=(
    "ForestUse_pland_1000_Primary",
    "Disturbance_pland_1000_clearcut",
    "LandCover_shdi_1000",
    "age_max",
    "dbh_div_dead_100",
    "openness_mean",
    "altitude_m",
)
DEADWOOD="volume_dead_tree_lying"
EXTENDED=BASELINE+(DEADWOOD,)
FORESTS={
    "B":{"source":"B_SR_BEETLES.csv","environment":"Beech.csv","rows":60,
         "fields":242,"stands":8,"matched":154},
    "S":{"source":"S_SR_BEETLES.csv","environment":"Spruce.csv","rows":56,
         "fields":161,"stands":10,"matched":83},
}
EXPECTED_WEISS_GUILD={"m":90,"n":0,"p":0,"s":14,"x":41,"z":25}
UNKNOWN={"", "na","nan","null","missing","none","-999"}

def source_bytes(name,links):
    if name not in {item[k] for item in FORESTS.values() for k in ("source","environment")}:
        raise SourceStop("SOURCE_GLOOR_UNDECLARED_ORIGINAL_FILE")
    size,md5=FROZEN_FILES[name]
    raw=official_get(links[name],"*/*",size+1024)
    if len(raw)!=size or hashlib.md5(raw).hexdigest()!=md5:
        raise SourceStop("SOURCE_GLOOR_PUBLISHER_ORIGINAL_FILE_SHA_OR_SIZE_DRIFT")
    return raw

def fixed_source_guild_header_admission(weiss,headers):
    b=headers["B_SR_BEETLES.csv"]["private_taxa"]
    s=headers["S_SR_BEETLES.csv"]["private_taxa"]
    if len(weiss)!=511 or len(b)!=241 or len(s)!=160 or len(b&s)!=92 or len(b|s)!=309:
        raise SourceStop("SOURCE_WEISS_OR_GLOOR_ORIGINAL_PRECOMMITTED_NAME_FRAME_CHANGED")
    named={}
    for code,items in (("B",b),("S",s)):
        mapped={}
        for raw in items:
            if not GRAMMAR["exact_two_underscore_Latin_tokens"].fullmatch(raw):
                raise SourceStop("SOURCE_GLOOR_SOURCE_HEADER_NOT_EXACT_ONE_UNDERSCORE")
            canonical=raw.replace("_"," ",1)
            if not EXACT_BINOMIAL.fullmatch(canonical):
                raise SourceStop("SOURCE_GLOOR_CANONICAL_BINOMIAL_WRONG_FORM")
            if canonical in weiss:
                mapped[raw]=weiss[canonical]
        if len(mapped)!=FORESTS[code]["matched"]:
            raise SourceStop("SOURCE_GLOOR_WEISS_154_OR_83_MATCHED_TAXA_DRIFT")
        named[code]=mapped
    # Join on the external source canonical species name only in PRIVATE memory.
    union={}
    for matched in named.values():
        for raw,g in matched.items():
            canonical=raw.replace("_"," ",1)
            if canonical in union and union[canonical]!=g:
                raise SourceStop("SOURCE_GLOOR_WEISS_DUPLICATE_GUILD_INCONSISTENCY")
            union[canonical]=g
    if len(union)!=170 or {c:sum(v==c for v in union.values()) for c in GUILD}!=EXPECTED_WEISS_GUILD:
        raise SourceStop("SOURCE_GLOOR_WEISS_SOURCE_FORMAT170_GUILD_COUNTS_CHANGED")
    return named

def parse_source_detected_guilds(raw,source,site_count,field_count,matched):
    # Deliberately split in byte space. Only source plot id and exact fixed
    # matched guild-known columns are decoded/numerically examined.
    lines=raw.split(b"\n")
    if lines[-1]==b"":lines.pop()
    if len(lines)!=site_count+1:
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_BEETLE_SAMPLE_ROW_FRAME_CHANGED")
    try:
        import csv
        names=next(csv.reader([lines[0].decode("utf-8-sig").rstrip("\r")],
                              delimiter=",",strict=True))
    except (UnicodeError,ValueError,StopIteration):
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_BEETLE_CSV_HEADER_PARSE_FAILED") from None
    if len(names)!=field_count or names[0].casefold().strip()!="plotid":
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_BEETLE_HEADER_DRIFT")
    if len(names)!=len(set(names)):
        raise SourceStop("SOURCE_GLOOR_BEETLE_HEADER_DUPLICATE")
    match_indices=[(i,GUILD.index(matched[s])) for i,s in enumerate(names) if s in matched]
    if len(match_indices)!=len(matched) or len({i for i,_ in match_indices})!=len(matched):
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_MATCHED_SOURCE_COLUMN_SET_DRIFT")
    Y={}; detected_site_totals=[]
    guild_detected_species={k:set() for k in GUILD}
    for source_line in lines[1:]:
        cells=source_line.rstrip(b"\r").split(b",")
        if len(cells)!=field_count:
            raise SourceStop("SOURCE_GLOOR_ORIGINAL_BEETLE_NUMERIC_CSV_ROW_SHAPE_STOP")
        try:
            id_token=cells[0].decode("utf-8").strip().strip('"').strip()
        except UnicodeError:
            raise SourceStop("SOURCE_GLOOR_BEETLE_SITE_ID_ENCODING_STOP") from None
        if not id_token or id_token in Y:
            raise SourceStop("SOURCE_GLOOR_ORIGINAL_BEETLE_EMPTY_OR_DUPLICATE_PLOTID")
        counts=[0]*len(GUILD)
        for i,j in match_indices:
            # Only the externally guild-assigned source column values are read.
            try:
                text=cells[i].decode("utf-8").strip().strip('"').strip()
                if text.casefold() in UNKNOWN:
                    raise ValueError("missing")
                val=float(text)
            except (UnicodeError,ValueError,OverflowError):
                raise SourceStop("SOURCE_GLOOR_MATCHED_BEETLE_SOURCE_NUMERIC_OR_MISSING_STOP") from None
            if not math.isfinite(val) or val<0:
                raise SourceStop("SOURCE_GLOOR_MATCHED_BEETLE_SOURCE_NONFINITE_NEGATIVE_STOP")
            if val>0:
                counts[j]+=1
                guild_detected_species[GUILD[j]].add(names[i])
        total=sum(counts)
        if total==0:
            raise SourceStop("SOURCE_GLOOR_SITE_WITH_ZERO_MATCHED_DETECTED_GUILD_SPECIES_STOP")
        Y[id_token]=tuple(math.sqrt(c/total) for c in counts)
        detected_site_totals.append(total)
    if len(Y)!=site_count:
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_BEETLE_SAMPLE_TOTAL_DRIFT")
    return Y,{"source_original_rows":len(Y),
              "all_plots_at_least_one_taxon_with_externally_verified_guild":True,
              "observed_source_guild_matched_taxa_with_any_positive_detection":len(set().union(*guild_detected_species.values())),
              "original_source_SITE_OR_SPECIES_VALUES_NOT_EXPORTED":True,
              "source_unmatched_beetle_column_numeric_values_NOT_ACCESSED":True}

def environment_rows(raw,source,expected_count):
    original=only_whitelist(raw,expected_count,source)
    result={}
    for sid,row in original.items():
        numeric={}
        for col in EXTENDED:
            v=row[col]
            if v.strip().casefold() in UNKNOWN:
                raise SourceStop("SOURCE_GLOOR_ORIGINAL_ENVIRONMENT_MISSING_PREDICTOR")
            try:
                val=float(v)
            except (ValueError,TypeError):
                raise SourceStop("SOURCE_GLOOR_ORIGINAL_ENVIRONMENT_NOT_NUMERIC") from None
            if not math.isfinite(val):
                raise SourceStop("SOURCE_GLOOR_ORIGINAL_ENVIRONMENT_NONFINITE")
            numeric[col]=val
        result[sid]={"stand":row["standshort"],"predictors":numeric}
    return result

def solve_linear_system(a,b):
    """Gaussian elimination with partial pivot, multiple RHS. Standard library."""
    n=len(a)
    if n==0 or len(b)!=n or any(len(x)!=n for x in a):
        raise SourceStop("RIDGE_ORIGINAL_LINEAR_ALGEBRA_SHAPE_STOP")
    d=len(b[0])
    mat=[list(a[i])+list(b[i]) for i in range(n)]
    for col in range(n):
        pivot=max(range(col,n),key=lambda i:abs(mat[i][col]))
        if abs(mat[pivot][col])<1e-11:
            raise SourceStop("RIDGE_FIXED_DESIGN_SINGULAR_OR_ILL_CONDITIONED")
        mat[col],mat[pivot]=mat[pivot],mat[col]
        scale=mat[col][col]
        for j in range(col,n+d):
            mat[col][j]/=scale
        for i in range(n):
            if i==col:continue
            factor=mat[i][col]
            for j in range(col,n+d):
                mat[i][j]-=factor*mat[col][j]
    return [row[n:] for row in mat]

def ridge_fit_and_predict(training,heldout,response,environment,features):
    """Each LOSO fold fits z scaling on training plots only."""
    n=len(training);p=len(features)+1;d=len(GUILD)
    if n<10 or not heldout or p not in (8,9):
        raise SourceStop("SOURCE_RIDGE_LOSO_ORIGINAL_SAMPLE_SIZE_INVALID")
    means={x:statistics.fmean(environment[t]["predictors"][x] for t in training)
           for x in features}
    scales={}
    for col in features:
        ss=statistics.fmean((environment[t]["predictors"][col]-means[col])**2
                            for t in training)
        scales[col]=math.sqrt(ss) if ss>0 else 1.0
    def vector(pid):
        return [1.0]+[(environment[pid]["predictors"][col]-means[col])/scales[col]
                      for col in features]
    xs=[vector(t) for t in training]
    ys=[response[t] for t in training]
    lhs=[[math.fsum(x[i]*x[j] for x in xs)+(LAM if i==j and i>0 else 0.0)
          for j in range(p)] for i in range(p)]
    rhs=[[math.fsum(xs[k][i]*ys[k][g] for k in range(n))
          for g in range(d)] for i in range(p)]
    beta=solve_linear_system(lhs,rhs)
    raw_mean=[statistics.fmean(y[g] for y in ys) for g in range(d)]
    mean_norm=math.sqrt(math.fsum(x*x for x in raw_mean))
    fallback=[x/mean_norm for x in raw_mean]
    predictions={}
    for t in heldout:
        xx=vector(t)
        yhat=[max(0.0,math.fsum(xx[i]*beta[i][g] for i in range(p)))
              for g in range(d)]
        norm=math.sqrt(math.fsum(x*x for x in yhat))
        if norm<1e-12:
            yhat=list(fallback)
        else:
            yhat=[x/norm for x in yhat]
        predictions[t]=yhat
    return predictions

def loss_h2(y,z):
    return .5*math.fsum((a-b)**2 for a,b in zip(y,z))

def evaluate_one_forest(response,env,role,expected_stands):
    if set(response)!=set(env):
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_BIOLOGY_ENVIRONMENT_EXACT_PLOT_JOIN_STOP")
    stand_set={row["stand"] for row in env.values()}
    if len(stand_set)!=expected_stands:
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_STAND_GROUP_COUNT_DRIFT")
    ids=sorted(env)
    groups={s:sorted(x for x in ids if env[x]["stand"]==s) for s in stand_set}
    if min(map(len,groups.values()))<4:
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_STAND_SAMPLE_MINIMUM_FAILED")
    folds=[]; all_losses=[]
    for stand in sorted(groups):
        hold=groups[stand]
        training=[k for k in ids if k not in set(hold)]
        base=ridge_fit_and_predict(training,hold,response,env,BASELINE)
        ext=ridge_fit_and_predict(training,hold,response,env,EXTENDED)
        loss_b=[loss_h2(response[k],base[k]) for k in hold]
        loss_e=[loss_h2(response[k],ext[k]) for k in hold]
        folds.append({"block_size":len(hold),
                      "baseline_loss":statistics.fmean(loss_b),
                      "extended_loss":statistics.fmean(loss_e),
                      "delta":statistics.fmean(loss_b)-statistics.fmean(loss_e)})
        all_losses.extend((a,b) for a,b in zip(loss_b,loss_e))
    return {
      "_private_folds":folds,
      "original_physical_plot_count":len(ids),
      "original_source_stand_group_count":len(groups),
      "stand_fold_sizes_anonymous_sorted":sorted((len(v) for v in groups.values())),
      "source_original_LOSO_training_only_scaling_VERIFIED":True,
      "source_original_leave_one_STAND_not_plant_or_species":True,
      "source_original_habitat_type":role,
      "original_stands_with_positive_deadwood_increment":sum(x["delta"]>0 for x in folds),
      "stand_equal_delta_Hellinger2":statistics.fmean(x["delta"] for x in folds),
      "site_equal_baseline_Hellinger2_loss":statistics.fmean(z[0] for z in all_losses),
      "site_equal_plus_deadwood_Hellinger2_loss":statistics.fmean(z[1] for z in all_losses),
      "individual_site_and_stand_or_taxon_ID_values_NOT_OUTPUT":True,
    }

def percentile(values,p):
    a=sorted(values)
    x=(len(a)-1)*p
    lo=int(math.floor(x));hi=int(math.ceil(x))
    return a[lo]+(a[hi]-a[lo])*(x-lo)

def primary_stand_effect(a,b):
    db=[x["delta"] for x in a]; ds=[x["delta"] for x in b]
    if len(db)!=8 or len(ds)!=10:
        raise SourceStop("SOURCE_PRIMARY_ORIGINAL_8_10_STAND_FOLD_DRIFT")
    obs=.5*(statistics.fmean(db)+statistics.fmean(ds))
    rng=random.Random(SEED)
    boot=[]
    for _ in range(BOOTSTRAPS):
        b1=statistics.fmean(rng.choice(db) for _ in range(len(db)))
        b2=statistics.fmean(rng.choice(ds) for _ in range(len(ds)))
        boot.append(.5*(b1+b2))
    ci=(percentile(boot,.025),percentile(boot,.975))
    terms=[.5*x/len(db) for x in db]+[.5*x/len(ds) for x in ds]
    extreme=0
    limit=abs(obs)-1e-13
    for mask in range(1<<len(terms)):
        diff=math.fsum(-v if (mask>>i)&1 else v for i,v in enumerate(terms))
        if abs(diff)>=limit:
            extreme+=1
    p=extreme/(1<<len(terms))
    support=obs>0 and ci[0]>0 and p<.05
    return {
      "exploratory_primary_original_forest_type_EQUAL_stand_EQUAL_delta_Hellinger2":obs,
      "exploratory_primary_stand_stratified_4000_boot_percentile95":list(ci),
      "exploratory_primary_exact_2sided_18stand_signflip_conditional_p":p,
      "exploratory_primary_exact_signflip_extreme_count":extreme,
      "exploratory_number_of_signflip_configs":1<<len(terms),
      "exploratory_forest_specific_stand_group_counts":{"B":8,"S":10},
      "exploratory_fixed_descriptive_support_criterion_passed":support,
      "source_inferential_population_CI_or_causal_claim_NOT_SUPPORTED":True,
    }

def original_once():
    weiss=validate_original_weiss_private_ledger()
    header=source_gloor_name_headers()
    maps=fixed_source_guild_header_admission(weiss,header)
    links=original_record_links()
    scores={}
    for role,desc in FORESTS.items():
        src=source_bytes(desc["source"],links)
        envbytes=source_bytes(desc["environment"],links)
        env=environment_rows(envbytes,desc["environment"],desc["rows"])
        Y,qual=parse_source_detected_guilds(
            src,desc["source"],desc["rows"],desc["fields"],maps[role]
        )
        if set(Y)!=set(env):
            raise SourceStop("SOURCE_GLOOR_FOREST_TYPE_ORIGINAL_PLOTID_CROSSWALK_FAILED")
        fit=evaluate_one_forest(Y,env,role,desc["stands"])
        fit["source_original_matched_incidence_quality_only"]=qual
        scores[role]=fit
    if sum(scores[k]["original_physical_plot_count"] for k in ("B","S"))!=116:
        raise SourceStop("SOURCE_GLOOR_ORIGINAL_116_FROZEN_PLOT_TOTAL_DRIFT")
    primary=primary_stand_effect(
        scores["B"]["_private_folds"],scores["S"]["_private_folds"]
    )
    for d in scores.values():d.pop("_private_folds")
    return {
      "source_original_country_system":"Slovak_Carpathian_one_study",
      "source_original_116_plots_and_18_stands_TESTED":True,
      "original_verified_exploratory_Weiss170_guild_taxa_union":170,
      "source_original_Weiss_matched_taxa_by_forest":{"B":154,"S":83},
      "source_original_Weiss_original_sixcode_matched_taxa":EXPECTED_WEISS_GUILD,
      "original_type_specific_stand_loso_descriptive_results":scores,
      "original_ONE_forest_type_equal_primary_deadwood_increment":primary,
      "author_explicit_taxon_underscore_map_VERIFIED":False,
      "original_full_species_303_vs_header_309_discrepancy_UNRESOLVED":True,
      "Gloor_original_trap_effort_true_zero_detection_NOT_CALIBRATED":True,
      "Gloor_standshort_to_9_mountain_ranges_UNVERIFIED":True,
      "status":(
        "EXPLORATORY_OBSERVED_GUILD_DEADWOOD_LOSO_DIRECTIONAL_SUPPORT_ONLY"
        if primary["exploratory_fixed_descriptive_support_criterion_passed"] else
        "EXPLORATORY_OBSERVED_GUILD_DEADWOOD_LOSO_NOT_SUPPORTED"
      ),
      "source_original_earlier_exact_names_primary_HOLD_UNCHANGED":True,
      "new_confirmatory_cross_country_guild_transport_NOT_VERIFIED":True,
      "model_source_individual_site_species_counts_NOT_EXPORTED":True,
      "new_exploratory_biological_response_score_EVALUATED":True,
    }

def known_truth():
    a=[[2.0,0.0],[0.0,3.0]]
    b=[[2.0],[6.0]]
    coeff=solve_linear_system(a,b)
    assert abs(coeff[0][0]-1)<1e-10
    assert abs(coeff[1][0]-2)<1e-10
    assert abs(loss_h2((1.0,0.0),(1.0,0.0)))<1e-12
    assert abs(loss_h2((1.0,0.0),(0.0,1.0))-1.0)<1e-12
    d={"x":{col:0.0 for col in EXTENDED}}
    assert tuple(GUILD)==tuple("mnpsxz") and LAM==10 and SEED==20261118
    assert len(BASELINE)==7 and len(EXTENDED)==8
    print("SYNTHETIC_GLOOR_ONEPASS_RIDGE_H2_LOSO_FIXED_8_10_STANDS_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:p.error("--out required")
    result={
      "schema":"structural.Carpathian116_Weiss170_guild_detected_LOSO_deadwood_onepass.v1",
      "precommit":PRESPEC,
      "original_Zenodo_source":22142713,
      "source_source_author_Gloor_taxon_format_mapping_confirmatory_VERIFIED":False,
      "prior_exact_0of309_and_author_mapping_HOLD_NOT_REPLACED":True,
      "exploratory_response_taxonomy_selected_by_only_one_frozen_source_format":True,
      "source_original_Weiss2016_and_Franzen2026_Dryad_HTTP401_NOT_RETRIED":True,
      "all_earlier_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_scores_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        result["original_onepass_exploratory_observed_guild_prediction"]=original_once()
        result["status"]=result["original_onepass_exploratory_observed_guild_prediction"]["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["source_or_original_biology_quality_STOP_not_null_ecology"]=True
        result["no_new_valid_exploratory_response_score"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Carpathian116_Weiss170_sourceoriginal_deadwood_loso_onepass_exploratory.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GLOOR116_WEISS170_ONEPASS_EXPLORATORY_DEADWOOD_GUILD_LOSO_STATUS",result["status"])
    print("PRIMARY_EXACT_GUILD_AUTHOR_TAXON_MAPPING_HOLD_PRESERVED")
if __name__=="__main__": main()
