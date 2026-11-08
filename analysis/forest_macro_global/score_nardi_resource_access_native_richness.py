#!/usr/bin/env python3
"""One fixed exploratory test: Native forest beetle richness, tree cover vs access.

Nardi et al. 2026 (Zenodo 17044394 v3): at 207 trap cells within 13 landscapes,
does 250-m unobstructed angular area (configuration) add a positive association
with Native detected taxon-label richness after 250-m tree cover (composition)
and SITE fixed effects? Source-only predictor design audit passed BEFORE seeing
this response: 51.1% residual configuration variance, 11/13 discordant sites.

No urbanization_index composite alongside its components; no posthoc endpoint
switch. Inference uses LANDSCAPES as bootstrap clusters and within-SITE
Freedman–Lane residual shuffles under the composition-only null. Noncausal,
not verified insect movement or habitat patch connectivity. Never writes
original source taxon labels, trap SITE/CELL_ID values or raw observations.
"""
from __future__ import annotations

import argparse,json,math,random,statistics
from collections import Counter,defaultdict
from pathlib import Path

from qualify_eight_country_beetle_joins import parse,build,key,count_n
from audit_nardi_resource_access_identifiability import analyze as audit_predictors

SOURCE_DOI="10.5281/zenodo.17044394"
SEED=20261108
PERM=9999
BOOT=5000

def _rows_by_site(rows):
    out=defaultdict(list)
    for r in rows:out[r["site"]].append(r)
    if len(out)<2:raise ValueError("fewer_than_two_original_landscape_sources")
    return out

def fwl(rows):
    """OLS y ~ landscape fixed intercept + composition + configuration.

    Use within-landscape Frisch-Waugh-Lovell; all original covariates in percent.
    Returns beta per original percent, demeaned x/y and pooled residualized
    configuration with reduced-model source residuals for conditional shuffling.
    """
    blocks=_rows_by_site(rows)
    demeaned=[]
    yhat=[]
    for site,block in blocks.items():
        xc=statistics.mean(r["cover"] for r in block)
        ac=statistics.mean(r["access"] for r in block)
        yc=statistics.mean(r["native"] for r in block)
        for r in block:
            demeaned.append((r["site"],r["cover"]-xc,r["access"]-ac,r["native"]-yc))
    xx=sum(x*x for s,x,z,y in demeaned)
    if xx<=1e-10:raise ValueError("source_within_landscape_tree_cover_has_no_variation")
    xz=sum(x*z for s,x,z,y in demeaned)
    xy=sum(x*y for s,x,z,y in demeaned)
    b_reduced=xy/xx
    z_res=[z-xz/xx*x for s,x,z,y in demeaned]
    y_red=[y-b_reduced*x for s,x,z,y in demeaned]
    zz=sum(z*z for z in z_res)
    if zz<=1e-10:raise ValueError("source_configuration_not_separable_from_tree_cover")
    beta_access=sum(z*y for z,y in zip(z_res,y_red))/zz
    beta_cover=(xy-beta_access*xz)/xx
    residuals=defaultdict(list)
    # The reduced null residual y - fitted (site intercept+cover).
    for (site,x,z,y),r_z,r_y in zip(demeaned,z_res,y_red):
        residuals[site].append((r_z,r_y))
    if len(residuals)!=len(blocks):raise ValueError("original_source_landscape_residual_mismatch")
    return {
        "beta_access_per_1_percentage_point":beta_access,
        "beta_cover_per_1_percentage_point":beta_cover,
        "reduced_model_cover_beta_per_1_percentage_point":b_reduced,
        "residualized_config_ss":zz,
        "within_site_residual_config_and_reduced_y":residuals,
    }


def inference(rows, *, seed=SEED, perm=PERM, boots=BOOT):
    blocks=_rows_by_site(rows)
    if len(blocks)!=13 or len(rows)!=207:
        raise ValueError("requires_original_13_landscapes_207_source_cells")
    fitted=fwl(rows)
    beta=fitted["beta_access_per_1_percentage_point"]
    zz=fitted["residualized_config_ss"]
    residuals=fitted["within_site_residual_config_and_reduced_y"]
    rng=random.Random(seed)
    extreme=0
    for t in range(perm):
        numerator=0.
        for site,q in residuals.items():
            resid=[y for z,y in q]
            rng.shuffle(resid)
            numerator+=sum(item[0]*err for item,err in zip(q,resid))
        randomized=numerator/zz
        if abs(randomized)>=abs(beta)-1e-12:extreme+=1
    boot=[]
    siteids=sorted(blocks)
    for k in range(boots):
        rows_b=[]
        for i in range(len(siteids)):
            selected=siteids[rng.randrange(len(siteids))]
            rows_b.extend({**r,"site":f"resample_{i:02d}"} for r in blocks[selected])
        try:boot.append(fwl(rows_b)["beta_access_per_1_percentage_point"])
        except ValueError:continue
    if len(boot)<0.95*boots:raise ValueError("too_many_singular_source_landscape_bootstrap_draws")
    boot.sort()
    lower=10*boot[int(.025*(len(boot)-1))]
    upper=10*boot[int(.975*(len(boot)-1))]
    same_sign=0
    slopes=[]
    for excluded in siteids:
        q=fwl([r for r in rows if r["site"]!=excluded])["beta_access_per_1_percentage_point"]
        slopes.append(10*q)
        same_sign+=int(q*beta>0)
    return {
        "status":"EXPLORATORY_OBSERVATIONAL_ASSOCIATION_COMPUTED",
        "conditional_access_coefficient_native_detected_labels_per_10pct_unblocked_angle":10*beta,
        "conditional_tree_cover_coefficient_native_detected_labels_per_10pct_tree_cover":10*fitted["beta_cover_per_1_percentage_point"],
        "native_tree_cover_ONLY_slope_per_10pct_cover":10*fitted["reduced_model_cover_beta_per_1_percentage_point"],
        "access_coefficient_13_landscape_cluster_bootstrap_95CI_per10pct":[lower,upper],
        "within_landscape_reduced_model_residual_permutation_two_sided_p":(extreme+1)/(perm+1),
        "predeclared_access_positive_support":10*beta>0 and lower>0 and (extreme+1)/(perm+1)<=0.05,
        "leave_one_landscape_out_same_sign_as_full":same_sign,
        "leave_one_landscape_out_total":len(siteids),
        "bootstrap_effective_landscape_samples":len(boot),
        "permutation_replicates":perm,
        "residual_config_actual_source_variation_preserved_by_FWL":True,
        "within_site_shuffling_does_not_account_for_spatial_autocorrelation":True,
        "not_a_causal_experiment_or_species_movement_measure":True
    }


def analyze(original_wide, original_long, original_site, original_trap, *, perm=PERM,boots=BOOT):
    verified=build(original_wide,original_long,original_site,original_trap)
    if not verified["source_bio_wide_0_1_incidence_matrix_semantics_confirmed"]:
        raise ValueError("source_original_301_taxon_incidence_integrity_failed")
    if verified["source_long_species_field_matches_wide_headers_all"] is not True:
        raise ValueError("source_taxon_identifier_resolution_changed")
    if verified["landscape_env_plot_id_and_biological_SITE_values_exact_match"] is not True:
        raise ValueError("source_original_landscape_ID_crosswalk_failed")
    predictors=audit_predictors(original_trap[0])
    if not predictors["two_covar_separable_in_original_observed_feature_support"]:
        raise ValueError("predictor_only_frozen_gate_did_not_pass")
    if len(original_long[0])!=3215:raise ValueError("original_incidence_count_drift")
    cells={(key(r["SITE"]),key(r["CELL_ID"])) for r in original_wide[0]}
    if len(cells)!=207:raise ValueError("original_207_unique_samples_required")
    native=defaultdict(set)
    seen_species_status=defaultdict(set)
    for r in original_long[0]:
        original_status=r["STATUS"].strip()
        if original_status not in ("Native","Exotic"):
            raise ValueError("source_unrecognized_species_origin")
        label=r["SPECIES"].strip()
        if not label or count_n(r["N"]) is None or count_n(r["N"])<=0:
            raise ValueError("source_original_incidence_N_not_positive")
        sid=key(r["SITE"]);cid=key(r["CELL_ID"])
        seen_species_status[sid,label].add(original_status)
        if original_status=="Native":
            native[sid,cid].add(label)
    if any(len(s)>1 for s in seen_species_status.values()):
        raise ValueError("original_species_origin_conflict_within_landscape")
    sample_rows=[]
    for r in original_trap[0]:
        sid=key(r["SITE"]);cid=key(r["CELL_ID"])
        try:tree=float(r["composition"]);access=float(r["configuration"])
        except ValueError:raise ValueError("source_tree_or_access_missing")
        if not (math.isfinite(tree) and math.isfinite(access) and
                0<=tree<=100 and 0<=access<=100):
            raise ValueError("source_tree_or_access_not_percent_scale")
        sample_rows.append({
            "site":sid,"cover":tree,"access":access,"native":len(native[sid,cid])
        })
    if len(sample_rows)!=207 or {(r["site"],r["cover"],r["access"]) for r in sample_rows} is None:
        raise ValueError("source_cell_count_changed")
    if sum(r["native"] for r in sample_rows)!=2915:
        raise ValueError("original_native_incidence_2915_not_reproduced")
    result=inference(sample_rows,perm=perm,boots=boots)
    blocks=_rows_by_site(sample_rows)
    return {
        "schema":"structural.forest_nardi_native_beetle_resource_access_partial_effect.v1",
        "source_Zenodo_DOI":SOURCE_DOI,
        "source_original_13_landscapes":13,
        "source_original_207_trap_cells":207,
        "source_original_301_taxon_labels":301,
        "source_original_total_positive_incidence":3215,
        "source_original_native_positive_incidence":2915,
        "source_original_exotic_positive_incidence":300,
        "source_predictor_only_13_landscape_gate_passed_before_outcome":True,
        "source_predictor_global_composition_access_correlation":predictors["overall_correlation_composition_configuration"],
        "source_predictor_within_landscape_correlation":predictors["forest_landscape_fixed_effect_centered_covariate_correlation"],
        "source_configuration_independent_fraction_residual_variance":predictors["landscape_centered_configuration_variance_retained_after_cover_regression"],
        "source_native_labels_per_trap_min":min(r["native"] for r in sample_rows),
        "source_native_labels_per_trap_median":statistics.median(r["native"] for r in sample_rows),
        "source_native_labels_per_trap_max":max(r["native"] for r in sample_rows),
        "source_site_native_incidence_counts_ANONYMIZED":[
            {"anonymous_landscape":i+1,
             "trap_cells":len(rows),
             "mean_native_detected_labels_per_cell":statistics.mean(r["native"] for r in rows)}
            for i,(sid,rows) in enumerate(sorted(blocks.items()))],
        "main_result":result,
        "already_published_composite_urbanization_effect_not_new_independent_field_confirmation":True,
        "original_lure_and_sampling_protocol_common_but_detection_not_corrected":True,
        "original_species_specific_source_network_not_observed":True,
        "canopy_upper_lower_and_thermal_escape_not_tested":True,
        "original_site_country_and_site_climate_confounding_not_fully_resolved":True,
        "no_species_names_site_ids_raw_samples_or_coord_exported":True,
        "eBird_used":False
    }


def run(bio_wide,bio_long,site_env,trap_env,out):
    original=(
        parse(bio_wide,"bio_cast"),
        parse(bio_long,"bio_data_trapscale"),
        parse(site_env,"env_data_sitescale"),
        parse(trap_env,"env_data_trapscale")
    )
    result=analyze(*original)
    folder=Path(out);folder.mkdir(parents=True,exist_ok=True)
    (folder/"nardi_beetle_native_richness_resource_vs_access.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("bio_wide","bio_long","site_env","trap_env","out"):
        p.add_argument("--"+name,required=True)
    a=p.parse_args()
    run(a.bio_wide,a.bio_long,a.site_env,a.trap_env,a.out)
