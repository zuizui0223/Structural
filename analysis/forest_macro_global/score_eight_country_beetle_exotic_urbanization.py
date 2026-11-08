#!/usr/bin/env python3
"""Frozen exploratory native/exotic BEETLE incidence versus local urbanization.

Source: 2026 Nardi et al. 8-country / 13-landscape original Zenodo v3.
The primary estimand was source-frozen BEFORE this code read real responses:
mean of 13 within-landscape OLS slopes exotic share ~ standardized
urbanization_index, with equal landscape weights. 13 landscapes are NOT 207
independent forests or confirmed independent eight-country replicates.

Does not fit source-network mobility, thermal refugia, canopy structure or
vertical niche. Source species names/locations/trap IDs never exported.
"""
from __future__ import annotations

import argparse,json,math,random,statistics
from collections import Counter,defaultdict
from pathlib import Path

from qualify_eight_country_beetle_joins import parse,build,key,count_n

EXPECTED_SOURCE_DOI="10.5281/zenodo.17044394"
SEED=20261108
B=10000
P=9999

def _slope_standardized_urban(pairs):
    """OLS response fraction per 1 SD of within-landscape urbanization."""
    n=len(pairs)
    if n<10:raise ValueError("insufficient_original_cell_count_for_slope")
    x=[float(t[0]) for t in pairs]
    y=[float(t[1]) for t in pairs]
    xm=statistics.mean(x)
    ym=statistics.mean(y)
    sd=math.sqrt(sum((z-xm)**2 for z in x)/n)
    if sd<1e-10:raise ValueError("no_within_landscape_urbanization_variation")
    z=[(a-xm)/sd for a in x]
    return sum(a*(b-ym) for a,b in zip(z,y))/sum(a*a for a in z)


def _inference(per_landscape, *, p_reps=P,b_reps=B,seed=SEED):
    eligible={k:v for k,v in per_landscape.items() if v["eligible"]}
    if len(eligible)<8:
        return {
            "status":"SCIENTIFIC_STOP_FEWER_THAN_8_LANDSCAPES_WITH_ESTIMABLE_LOCAL_URBANIZATION",
            "eligible_landscapes":len(eligible),
            "main_mean_slope":None,
            "bootstrap_CI":None,"permutation_two_sided_p":None,
            "predeclared_support_criterion_met":False
        }
    ids=sorted(eligible)
    base=[eligible[k]["slope"] for k in ids]
    mean=statistics.mean(base)
    r=random.Random(seed)
    extrema=0
    for _ in range(p_reps):
        shuffled=[]
        for sid in ids:
            pairs=eligible[sid]["pairs"]
            shuffled_x=[t[0] for t in pairs]
            r.shuffle(shuffled_x)
            shuffled.append(_slope_standardized_urban(list(zip(
                shuffled_x,[q[1] for q in pairs]))))
        value=statistics.mean(shuffled)
        if abs(value)>=abs(mean)-1e-12:extrema+=1
    boot=[]
    for _ in range(b_reps):
        sample=[base[r.randrange(len(base))] for _ in base]
        boot.append(statistics.mean(sample))
    boot.sort()
    lo,hi=boot[int(.025*(b_reps-1))],boot[int(.975*(b_reps-1))]
    signs=[]
    for i in range(len(ids)):
        signs.append(statistics.mean(v for j,v in enumerate(base) if i!=j))
    return {
        "status":"EXPLORATORY_ESTIMATE_COMPUTED",
        "eligible_landscapes":len(ids),
        "main_mean_slope_exotic_incidence_share_per_within_landscape_urban_SD":mean,
        "bootstrap_landscape_95CI":[lo,hi],
        "within_landscape_urbanization_permutation_two_sided_p_CONDITIONAL":(extrema+1)/(p_reps+1),
        "predeclared_support_criterion_met":mean>0 and lo>0,
        "positive_original_landscape_slope_count":sum(x>0 for x in base),
        "negative_original_landscape_slope_count":sum(x<0 for x in base),
        "zero_original_landscape_slope_count":sum(x==0 for x in base),
        "leave_one_landscape_out_maintains_main_slope_sign_count":sum(
            v*mean>0 for v in signs),
        "landscape_bootstrap_reps":b_reps,
        "within_landscape_permutation_reps":p_reps,
        "permutation_inference_does_not_remove_spatial_autocorrelation":True,
        "only_13_original_landscapes_not_207_independent_forests":True
    }


def calculate(raw_wide,raw_long,raw_site_env,raw_trap_env, *, p_reps=P,b_reps=B):
    gate=build(raw_wide,raw_long,raw_site_env,raw_trap_env)
    if not gate["source_bio_wide_0_1_incidence_matrix_semantics_confirmed"]:
        raise ValueError("unverified_original_species_incidence_response")
    if not gate["landscape_env_plot_id_and_biological_SITE_values_exact_match"]:
        raise ValueError("original_source_forest_landscape_identity_not_matched")
    wide,_=raw_wide
    long,_=raw_long
    env,_=raw_trap_env
    groups=defaultdict(set)
    contexts=defaultdict(set)
    every_cell=set((key(r["SITE"]),key(r["CELL_ID"])) for r in wide)
    if len(every_cell)!=207:raise ValueError("source_original_207_beetle_cells_not_unique")
    for r in long:
        sid=key(r["SITE"])
        label=r["SPECIES"].strip()
        status=r["STATUS"].strip()
        n=count_n(r["N"])
        if status not in ("Native","Exotic"):
            raise ValueError("original_source_taxon_nativity_status_unrecognized")
        if not label or n is None or n<=0:
            raise ValueError("source_presence_row_missing_species_or_positive_N")
        cell=(sid,key(r["CELL_ID"]))
        if cell not in every_cell:raise ValueError("source_occurrence_has_no_environment_sampling_cell")
        groups[cell,status].add(label)
        contexts[sid,label].add(status)
    if any(len(values)>1 for values in contexts.values()):
        raise ValueError("original_native_exotic_status_conflicts_within_landscape")
    exposure={}
    for r in env:
        cell=(key(r["SITE"]),key(r["CELL_ID"]))
        try:u=float(r["urbanization_index"])
        except ValueError:u=float("nan")
        exposure[cell]=u if math.isfinite(u) else None
    if set(exposure)!=every_cell:raise ValueError("original_exposure_cell_join_mismatch")
    bysite=defaultdict(list)
    site_source_species=defaultdict(lambda:{"Native":set(),"Exotic":set()})
    for cell in sorted(every_cell):
        n=len(groups[cell,"Native"]);e=len(groups[cell,"Exotic"])
        site=cell[0]
        site_source_species[site]["Native"].update(groups[cell,"Native"])
        site_source_species[site]["Exotic"].update(groups[cell,"Exotic"])
        denominator=n+e
        u=exposure[cell]
        bysite[site].append({
            "u":u,"n":n,"e":e,
            "denominator":denominator,
            "exotic_share":e/denominator if denominator else None})
    if len(bysite)!=13:raise ValueError("source_landscape_count_drift")
    landscape={}
    for site,items in sorted(bysite.items()):
        valid=[(t["u"],t["exotic_share"]) for t in items
               if t["u"] is not None and t["exotic_share"] is not None]
        unique_u=len({round(u,12) for u,y in valid})
        can_score=(len(valid)>=10 and unique_u>=8 and
                   max((u for u,y in valid),default=0)-min((u for u,y in valid),default=0)>1e-10)
        slope=_slope_standardized_urban(valid) if can_score else None
        landscape[site]={
            "source_cell_count":len(items),
            "source_cell_with_both_exposure_and_any_beetle_detection":len(valid),
            "no_beetle_detected_cells":sum(t["denominator"]==0 for t in items),
            "missing_urban_exposure_cells":sum(t["u"] is None for t in items),
            "distinct_urbanization_index_values":unique_u,
            "number_of_native_taxon_labels_detected":len(site_source_species[site]["Native"]),
            "number_of_exotic_taxon_labels_detected":len(site_source_species[site]["Exotic"]),
            "mean_exotic_detected_label_share_per_sampled_cell":(
                statistics.mean(y for x,y in valid) if valid else None),
            "eligible":can_score,
            "slope":slope,
            "pairs":valid
        }
    result=_inference(landscape,p_reps=p_reps,b_reps=b_reps)
    anon=[]
    for i,(sid,q) in enumerate(sorted(landscape.items())):
        anon.append({
            "anonymous_landscape_index":i+1,
            **{k:v for k,v in q.items() if k!="pairs"}
        })
    return {
        "schema":"structural.forest_beetle_within_landscape_exotic_share_urbanization.v1",
        "source_Zenodo_v3_DOI":EXPECTED_SOURCE_DOI,
        "source_original_landscapes":13,
        "source_original_cell_count":207,
        "source_original_cell_taxon_incidence_count":3215,
        "source_original_taxon_label_count":301,
        "source_exotic_and_native_STATUS_is_landscape_specific":True,
        "source_301_taxa_binary_incidence_matrix_verified":True,
        "source_original_N_sum_minus_published_61755":gate["source_version3_N_minus_published_summary_count"],
        "absolute_individual_abundance_not_used_due_to_published_source_difference":True,
        "main_predictor":"original_urbanization_index_within_landscape_z",
        "main_response":"exotic_label_richness/(exotic+native_label_richness)_per_trap",
        "independent_study_sampling_unit":"landscape_SITE_not_CELL_ID_or_taxon",
        "predeclared_eligible_landscape_rule":"at least 10 detected/exposed cells and 8 distinct original urbanization_index values",
        "same_landscape_fixed_context_removed_from_main_slope":True,
        "forest_2000_spatial_amount_NOT_scored_this_test":True,
        "main_result":result,
        "original_landscape_descriptive":anon,
        "confounder_country_biogeographic_pool_not_resolved":True,
        "reproduction_of_existing_2026_monitoring_study_possible":True,
        "original_source_geometry_not_dispersal_or_species_source_network":True,
        "not_thermal_movement_or_canopy_understorey_layer_test":True,
        "no_original_site_IDS_taxa_names_trap_records_reexported":True,
        "eBird_used":False
    }


def run(bio_wide,bio_long,site_env,trap_env,out):
    parsed=[
        parse(bio_wide,"bio_cast"),
        parse(bio_long,"bio_data_trapscale"),
        parse(site_env,"env_data_sitescale"),
        parse(trap_env,"env_data_trapscale")]
    result=calculate(*parsed)
    d=Path(out);d.mkdir(parents=True,exist_ok=True)
    (d/"forest_beetle_exotic_incidence_urbanization_study_sites.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("bio_wide","bio_long","site_env","trap_env","out"):
        p.add_argument("--"+name,required=True)
    x=p.parse_args()
    run(x.bio_wide,x.bio_long,x.site_env,x.trap_env,x.out)
