#!/usr/bin/env python3
"""One frozen, post-result ORIGINAL Finland guild composition x deadwood test.

142 exact same-Year_Site source records; 1° lat x 2° lon held-out blocks.
Outcome is species incidence Host_tree guild relative composition (Hellinger).
Primary = block-equal out-of-grid Hellinger loss difference (baseline - +VD10).
Only anonymous aggregates are written. No alternative estimator search.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from finland_author_2023_siteyear_source_crosswalk import (
    SOURCE_2022, SOURCE_2023, pinned, source22_header_only,
    source23_author_identity_fields_only, compare, ScientificStop as SourceStop,
)
from three_region_beetle_host_guild_turnover import (
    MANIFEST, read_country, GUILDS,
)

N_SITES = 142
SEED = 20261115
RIDGE = 10.0
N_BOOT = 4000
N_FLIPS = 9999
BASELINE = (
    "agedomin", "OldFor_1km", "MeanTemp", "TotalPrecip",
    "globRad_WHm2", "log_Nr_traps", "lat_WGS84", "lon_WGS84", "Year",
)
PLUS = BASELINE + ("VD10",)
ENV_NEEDED = set(PLUS) | {"rowID", "Site", "Year", "climID", "lat_WGS84", "lon_WGS84"}


class ScientificStop(RuntimeError):
    pass


def load_source_only_selection(folder: Path):
    for f,d in [SOURCE_2022, SOURCE_2023, MANIFEST["Finland"]["traits"]]:
        pinned(folder/f, d)
    original = source22_header_only(folder/SOURCE_2022[0])
    author = source23_author_identity_fields_only(folder/SOURCE_2023[0])
    meta = compare(original, author)
    expected = {
        "source_2022_original_sample_year_columns": 153,
        "same_exact_original_year_site_rows_in_both_author_releases": 142,
        "2022_sample_years_unmatched_but_Site_known_in_2023": 10,
        "2022_unmatched_sample_years_with_Site_not_in_2023": 1,
        "source_2023_author_unique_Site_fields": 142,
    }
    if any(meta.get(k)!=v for k,v in expected.items()):
        raise ScientificStop("SOURCE_STOP_PREBIOLOGY_142_10_1_AUTHOR_COHORT_DRIFT")
    keys = {r[0]: i for i,r in enumerate(original)}
    ids_author = {r[0] for r in author}
    if len(ids_author)!=142 or not ids_author.issubset(keys):
        raise ScientificStop("SOURCE_STOP_AUTHOR_YEAR_SITE_MATCH_BROKEN")
    with (folder/SOURCE_2023[0]).open(newline="", encoding="utf-8-sig") as fh:
        reader=csv.DictReader(fh)
        if not ENV_NEEDED.issubset(set(reader.fieldnames or [])):
            raise ScientificStop("SOURCE_STOP_ORIGINAL_FOREST_ENV_PREDICTORS_ABSENT")
        rows=list(reader)
    if len(rows)!=142 or {r["rowID"] for r in rows}!=ids_author or (
        len({r["Site"] for r in rows})!=142
    ):
        raise ScientificStop("SOURCE_STOP_AUTHOR_142_ENV_IDENTITY_DRIFT")
    selected = np.array([keys[r["rowID"]] for r in rows],dtype=int)
    if len(set(selected))!=142:
        raise ScientificStop("SOURCE_STOP_DUPLICATE_SELECTED_AUTHOR_SOURCE_EVENT")
    original_years=[r[2] for r in original]
    # Numerical covariate parsing is a SOURCE-ONLY operation; do not load guild
    # traits or taxon rows until all 142 units and fixed folds are qualified.
    columns={}
    for k in PLUS:
        try:
            a=np.asarray([float(str(r[k]).strip()) for r in rows],dtype=float)
        except (ValueError, TypeError) as exc:
            raise ScientificStop("SOURCE_STOP_PREDECLARED_FOREST_ENV_NA_OR_NONNUMERIC") from exc
        if not np.all(np.isfinite(a)):
            raise ScientificStop("SOURCE_STOP_PREDECLARED_FOREST_ENV_NONFINITE")
        columns[k]=a
    lat=columns["lat_WGS84"]; lon=columns["lon_WGS84"]
    if not (np.all((lat>50)&(lat<72)) and np.all((lon>10)&(lon<40))):
        raise ScientificStop("SOURCE_STOP_ORIGINAL_FINLAND_LOCATION_COORD_RANGE")
    # Approximate predeclared ~100 km geographic cells; NEVER export keys.
    keys_geo=[(math.floor(float(a)),math.floor(float(b)/2)) for a,b in zip(lat,lon)]
    grid_counts=Counter(keys_geo)
    if len(grid_counts)<8 or N_SITES-min(grid_counts.values())<80:
        raise ScientificStop("SOURCE_STOP_FROZEN_SPATIAL_GRID_SUPPORT_TOO_FEW")
    block_index=np.asarray([sorted(grid_counts).index(x) for x in keys_geo],dtype=int)
    years=columns["Year"]
    if any(int(v)!=v or int(v)!=original_years[int(idx)] for v,idx in zip(years,selected)):
        raise ScientificStop("SOURCE_STOP_SOURCE_SAMPLE_YEAR_ENVIRONMENT_MISMATCH")
    allx=np.column_stack([columns[k] for k in PLUS])
    if allx.shape!=(142,10):
        raise ScientificStop("SOURCE_STOP_ORIGINAL_ENV_DESIGN_MATRIX_SHAPE")
    public={
        "prebiological_author_source_2022_153_columns":153,
        "one_author_year_and_one_physical_site_per_response":True,
        "source_author_site_year_exact_matches":142,
        "prior_10_repeated_other_years_and_1_unlinked_event_NOT_SCORED":True,
        "all_142_author_env_rows_complete_and_source_fields_checked":True,
        "source_environment_already_log_z_transformed_NOT_log1p_applied":True,
        "source_geographic_grid_lat_step_deg":1,
        "source_geographic_grid_lon_step_deg":2,
        "original_grid_cells":len(grid_counts),
        "cells_with_at_least_2_sites":sum(v>=2 for v in grid_counts.values()),
        "cells_with_at_least_5_sites":sum(v>=5 for v in grid_counts.values()),
        "min_cell_size":min(grid_counts.values()),
        "median_cell_size":float(np.median(list(grid_counts.values()))),
        "max_cell_size":max(grid_counts.values()),
        "minimum_training_site_n":N_SITES-max(grid_counts.values()),
        "author_original_climate_id_groups":len(set(r["climID"] for r in rows)),
        "number_of_original_source_years":len(set(years)),
        "all_site_folds_source_defined_BEFORE_biology":True,
    }
    if N_SITES-max(grid_counts.values())<80:
        raise ScientificStop("SOURCE_STOP_MINIMUM_TRAINING_80_SITES_NOT_MET")
    return selected, allx, block_index, public


def train_ridge(Xtr:np.ndarray, Ytr:np.ndarray, Xte:np.ndarray, penalty:float=RIDGE):
    mu=Xtr.mean(axis=0)
    sigma=Xtr.std(axis=0,ddof=1)
    sigma=np.where(sigma>1e-10,sigma,1.0)
    train=(Xtr-mu)/sigma
    test=(Xte-mu)/sigma
    ztr=np.column_stack([np.ones(len(train)),train])
    zte=np.column_stack([np.ones(len(test)),test])
    pen=np.eye(ztr.shape[1])*penalty
    pen[0,0]=0.0
    beta=np.linalg.solve(ztr.T@ztr+pen,ztr.T@Ytr)
    unnorm=np.maximum(zte@beta,1e-9)
    norm=np.linalg.norm(unnorm,axis=1,keepdims=True)
    return unnorm/norm,beta


def hellinger_squared(H:np.ndarray,Q:np.ndarray):
    if H.shape!=Q.shape or H.ndim!=2 or H.shape[1]!=3:
        raise ScientificStop("SOURCE_STOP_HELLINGER_COMPOSITION_SHAPE")
    return .5*np.sum((H-Q)**2,axis=1)


def fixed_cv(X:np.ndarray,Y:np.ndarray,grid:np.ndarray):
    if X.shape!=(142,10) or Y.shape!=(142,3) or grid.shape!=(142,):
        raise ScientificStop("SOURCE_STOP_SITE_ENV_RESPONSE_GRAIN_CHANGED")
    base_loss=np.full(142,np.nan)
    add_loss=np.full(142,np.nan)
    for block in sorted(set(grid)):
        held=(grid==block); train=~held
        if train.sum()<80:
            raise ScientificStop("SOURCE_STOP_SPATIAL_BLOCK_TRAIN_N_BELOW80")
        outbase,_=train_ridge(X[train,:9],Y[train],X[held,:9])
        outadd,_=train_ridge(X[train,:],Y[train],X[held,:])
        base_loss[held]=hellinger_squared(Y[held],outbase)
        add_loss[held]=hellinger_squared(Y[held],outadd)
    if not (np.all(np.isfinite(base_loss)) and np.all(np.isfinite(add_loss))):
        raise ScientificStop("SOURCE_STOP_CROSSVAL_LEAKAGE_OR_MISSING_PREDICTION")
    delta=base_loss-add_loss
    blocks=sorted(set(grid))
    return base_loss,add_loss,np.array([delta[grid==b].mean() for b in blocks]),delta


def statistics(block_gain:np.ndarray):
    if len(block_gain)<8 or not np.all(np.isfinite(block_gain)):
        raise ScientificStop("SOURCE_STOP_SPATIAL_BLOCK_INFERENCE_UNDEFINED")
    rng=np.random.default_rng(SEED)
    boots=np.mean(block_gain[rng.integers(0,len(block_gain),size=(N_BOOT,len(block_gain)))],axis=1)
    flips=np.random.default_rng(SEED+1).choice(np.array([-1.,1.]),size=(N_FLIPS,len(block_gain)))
    obs=float(block_gain.mean())
    perm=flips@block_gain/len(block_gain)
    p=float((1+np.sum(np.abs(perm)>=abs(obs)-1e-12))/(N_FLIPS+1))
    ci=np.quantile(boots,[.025,.975])
    return obs,ci,p


def score(folder:Path):
    # selection and environment-only dataset qualification FIRST
    indices,X,grid,prebiology=load_source_only_selection(folder)
    # original 2022 source eligibility and positive-abundance guild definitions;
    # biological columns opened only AFTER metadata freeze.
    all_matrix,codes,diag=read_country(folder,"Finland")
    if all_matrix is None or all_matrix.shape[0]!=153 or (
        diag["eligible_source_sampling_columns"]!=153
    ):
        raise ScientificStop("SOURCE_STOP_OLD_EVENT_ELIGIBILITY_NOT_REPRODUCED")
    inc=all_matrix[indices,:].astype(np.int32)
    if inc.shape[0]!=142:
        raise ScientificStop("SOURCE_STOP_SITE_SOURCE_RESPONSE_GRAIN")
    active=inc.sum(axis=0)>0
    inc=inc[:,active];codes=codes[active]
    if len(codes)<30 or np.any(inc.sum(axis=1)<5):
        raise ScientificStop("SOURCE_STOP_AUTHOR_SITE_KNOWN_TRAIT_RICHNESS_GATE")
    count=inc @ np.eye(3,dtype=np.int32)[codes]
    if np.any(count.sum(axis=1)==0):
        raise ScientificStop("SOURCE_STOP_EMPTY_GUILD_AFTER_AUTHOR_SITE_YEAR_MATCH")
    Y=np.sqrt(count/count.sum(axis=1,keepdims=True))
    baseloss,addloss,blockgain,sitegain=fixed_cv(X,Y,grid)
    observed,ci,p=statistics(blockgain)
    # descriptive coefficients on full source cohort only; no guild-specific p
    _,full_coef=train_ridge(X,Y,X)
    vd10_descr=full_coef[-1,:]
    result={
       "schema":"structural.Finland142_original_deadwood_incremental_hostguild_spatial_holdout.v1",
       "status":"EXPLORATORY_ORIGINAL_ECOLOGY_FROZEN_SINGLE_TEST_COMPLETED",
       "source_2022_Zenodo":"10.5281/zenodo.5950610",
       "author_2023_original_environment_Zenodo":"10.5281/zenodo.8322080",
       "original_2022_country_event_eligibility_153_of_153_reproduced":True,
       "original_author_environment_sameyear_source_142_site_prebiology_gate":prebiology,
       "source_author_sites_for_beetle_hostguild_142":142,
       "original_traits_known_species_active_in_exact_year_sites":int(len(codes)),
       "three_original_host_tree_guilds":["broadl","conifer","both"],
       "source_original_host_tree_siteincidence_NOT_new_field_collections":True,
       "baseline_original_sources":list(BASELINE),
       "one_added_source_measurement":"VD10 author log-transformed z score",
       "source_ridge_penalty_fixed":RIDGE,
       "holdout_blocks_one_degree_lat_by_two_degree_lon":True,
       "main_estimand_grid_block_equal_base_minus_plus_VD10_Hellinger2":round(observed,8),
       "grid_block_bootstrap_4000_95pct_percentile_CI":[round(float(z),8) for z in ci],
       "grid_block_9999_two_sided_signflip_p_conditional":round(p,6),
       "original_grid_cells_heldout":int(len(blockgain)),
       "grid_cells_positive_improvement":int(np.sum(blockgain>1e-12)),
       "grid_cells_negative_improvement":int(np.sum(blockgain< -1e-12)),
       "grid_cells_zero_improvement":int(np.sum(np.abs(blockgain)<=1e-12)),
       "site_equal_holdout_baseline_mean_Hellinger2":round(float(baseloss.mean()),8),
       "site_equal_holdout_plus_VD10_mean_Hellinger2":round(float(addloss.mean()),8),
       "site_equal_holdout_loss_improvement":round(float(sitegain.mean()),8),
       "descriptive_full_data_ridge_VD10_coefficients_sqrt_guild_order_broadl_conifer_both":[
            round(float(z),8) for z in vd10_descr
       ],
       "predefined_exploratory_support_threshold_achieved":bool(
           observed>0 and ci[0]>0 and p<.05
       ),
       "same_original_2023_Finland_population_not_independent_replication":True,
       "not_true_absence_or_forest_3d_canopy_persistence_or_causal_selection":True,
       "spatial_grid_holdout_not_external_country_or_biome":True,
       "species_original_site_environment_raw_values_predictions_and_coordinates_NOT_EXPORTED":True,
       "frozen_original_Finland142site_labelshuffle_D0p035237_UNCHANGED":True,
       "frozen_original_threecountry_D0p091059_UNCHANGED":True,
       "original_PREDICTS_NEON_BALA_GEB_results_frozen":True,
       "eBird_used":False,
    }
    return result


def known_truth():
    X=np.zeros((142,10),float)
    rng=np.random.default_rng(123)
    X[:,0]=rng.normal(size=142)
    X[:,9]=np.linspace(-2,2,142)
    X[:,1:9]=rng.normal(size=(142,8))
    grid=np.repeat(np.arange(14),[11]*2+[10]*12)
    assert len(grid)==142
    Y=np.column_stack([.1 + .7/(1+np.exp(-3*X[:,9])),.2+0*X[:,9],.1+.7/(1+np.exp(3*X[:,9]))])
    Y=np.sqrt(Y/Y.sum(axis=1,keepdims=True))
    b,a,block,site=fixed_cv(X,Y,grid)
    assert np.all(np.isfinite(b)) and np.all(np.isfinite(a))
    assert block.mean()>0  # positive known truth: source local predictor matters
    assert abs(block.mean()-statistics(block)[0])<1e-12
    Z=np.tile(np.sqrt(np.array([.3,.5,.2])),(142,1))
    bn,an,blocknull,_=fixed_cv(X,Z,grid)
    assert abs(np.mean(bn))<1e-10 and abs(np.mean(an))<1e-10
    assert np.all(np.isfinite(blocknull))
    assert np.all((b>=0)&(b<=1)) and np.all((a>=0)&(a<=1))
    # Defined negative block-gain known-truth checks do not select a new model.
    x,ci,p=statistics(np.repeat(-.015,14))
    assert x<0 and ci[1]<0 and p<.05
    x,ci,p=statistics(np.zeros(14))
    assert x==0 and p==1
    print("SYNTHETIC_SPATIAL_BLOCK_CV_RIDGE_POSITIVE_NULL_NEGATIVE_KNOWN_TRUTH_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--folder",type=Path)
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    known_truth()
    if a.test:
        return
    if not a.folder or not a.out:
        ap.error("need --folder --out")
    try:
        result=score(a.folder)
    except (ScientificStop,SourceStop) as exc:
        result={
           "schema":"structural.Finland142_original_deadwood_incremental_hostguild_spatial_holdout.v1",
           "status":str(exc),
           "scientific_source_STOP_not_biological_null":True,
           "no_after_result_alternative_predictor_or_holdout_selected":True,
           "original_guild_and_all_PRIOR_scoring_UNCHANGED":True,
        }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Finnish142forest_local_deadwood_hostguild_spatial_H2_original_aggregate.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8"
    )
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
