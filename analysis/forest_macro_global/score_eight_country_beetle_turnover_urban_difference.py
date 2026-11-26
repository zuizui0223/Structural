#!/usr/bin/env python3
"""Forest beetle trap-pair Simpson turnover versus urbanization difference.

One source-frozen EXPLORATORY contrast after previous 13-landscape native/exotic
study already ran. Original Nardi 2026 (Zenodo 17044394 v3); no independent
confirmation. The estimate is the equal-landscape mean of within-landscape
turnover ~ absolute urbanization difference (units = local pop SD).

Permute exposure labels among complete traps *within the same landscape*;
never permute individual pair rows. This keeps trap richness, taxon occurrence,
all pair dependencies and each source landscape's observed exposure distribution.
Export aggregate ranks/counts only, no raw taxon, trap or landscape IDs.
"""
from __future__ import annotations
import argparse, json, math, random, statistics
from collections import Counter, defaultdict
from pathlib import Path
from qualify_eight_country_beetle_joins import parse, build, key

DOI = "10.5281/zenodo.17044394"
SEED = 20261108
N_PERM = 9999
N_BOOT = 10000


def simpson_turnover(a,b):
    """Abundance-free turnover beta_sim; distinct from richness/nestedness."""
    a,b=set(a),set(b)
    shared=len(a & b)
    unique_small=min(len(a-b),len(b-a))
    denom=shared+unique_small
    return unique_small/denom if denom else None


def jaccard(a,b):
    a,b=set(a),set(b)
    union=len(a|b)
    return 1-len(a&b)/union if union else None


def slope(pairs):
    if len(pairs)<10:
        raise ValueError("insufficient_within_landscape_original_pairs")
    xm=statistics.mean(x for x,y in pairs)
    ym=statistics.mean(y for x,y in pairs)
    denom=sum((x-xm)**2 for x,y in pairs)
    if denom<1e-12:
        raise ValueError("no_observed_urban_difference_range")
    return sum((x-xm)*(y-ym) for x,y in pairs)/denom


def source_study(traps):
    """traps: [(within_landscape_urbanization, frozenset(plant_pest_species)), ...]."""
    if len(traps) not in (15,16):
        raise ValueError("source_15_or_16_original_trap_cells_required")
    urban=[u for u,_ in traps]
    if not all(math.isfinite(u) for u in urban):
        raise ValueError("nonfinite_source_urbanization_index")
    richness=[len(s) for _,s in traps]
    if any(r<=0 for r in richness):
        raise ValueError("source_trap_with_no_detected_taxa_outside_prespec")
    m=statistics.mean(urban)
    sd=math.sqrt(sum((u-m)**2 for u in urban)/len(urban))
    if sd<1e-10:
        raise ValueError("source_original_landscape_no_urbanization_variation")
    y=[]
    desc=[]
    with_labels=[]
    for i in range(len(traps)):
        for j in range(i+1,len(traps)):
            sim=simpson_turnover(traps[i][1],traps[j][1])
            jac=jaccard(traps[i][1],traps[j][1])
            if sim is None or jac is None:
                raise ValueError("simpson_turnover_undefined_for_positive_traps")
            y.append(sim)
            desc.append(jac)
            with_labels.append((i,j,sim,jac))
    def rep(u_values):
        return [
            (abs(u_values[i]-u_values[j])/sd, v)
            for (i,j,v,jacc) in with_labels
        ]
    pairs=rep(urban)
    return {
        "source_traps":len(traps),
        "turnover_pairs":len(pairs),
        "mean_family_free_species_Simpson_turnover":statistics.mean(y),
        "mean_Jaccard_dissimilarity_secondary":statistics.mean(desc),
        "mean_exposure_difference_in_local_SD":statistics.mean(x for x,v in pairs),
        "main_slope":slope(pairs),
        "_private_urban":urban,
        "_private_pair_cells":with_labels,
        "_private_SD":sd,
    }


def permuted_slope(source, randomizer):
    xs=source["_private_urban"].copy()
    randomizer.shuffle(xs)
    sd=source["_private_SD"]
    matches=source["_private_pair_cells"]
    return slope([(abs(xs[i]-xs[j])/sd,val) for i,j,val,jac in matches])


def inference(sources, *, permutations=N_PERM, bootstraps=N_BOOT,seed=SEED):
    if len(sources)!=13:
        raise ValueError("not_13_original_landscapes_no_auto_dropping")
    orig=[sources[x]["main_slope"] for x in sorted(sources)]
    effect=statistics.mean(orig)
    rng=random.Random(seed)
    n_extreme=0
    sorted_source=[sources[k] for k in sorted(sources)]
    for _ in range(permutations):
        mean_perm=statistics.mean(permuted_slope(s,rng) for s in sorted_source)
        if abs(mean_perm)>=abs(effect)-1e-12:
            n_extreme+=1
    boots=[]
    for _ in range(bootstraps):
        picked=[orig[rng.randrange(len(orig))] for _ in orig]
        boots.append(statistics.mean(picked))
    boots.sort()
    lo=boots[int((len(boots)-1)*.025)]
    hi=boots[int((len(boots)-1)*.975)]
    loo=[statistics.mean([v for j,v in enumerate(orig) if j!=i]) for i in range(len(orig))]
    p=(n_extreme+1)/(permutations+1)
    return {
        "status":"EXPLORATORY_13_LANDSCAPE_ESTIMATE_COMPUTED",
        "estimable_landscapes":len(sources),
        "equal_landscape_mean_Simpson_turnover_slope_per_SD_urban_difference":effect,
        "landscape_bootstrap_95CI":[lo,hi],
        "within_landscape_complete_exposure_label_permutation_two_sided_p_conditional":p,
        "single_predeclared_exploratory_support_criterion_met":effect>0 and lo>0 and p<=.05,
        "positive_landscape_slopes":sum(v>0 for v in orig),
        "negative_landscape_slopes":sum(v<0 for v in orig),
        "zero_landscape_slopes":sum(v==0 for v in orig),
        "leave_one_landscape_out_mean_same_sign_n":sum(v*effect>0 for v in loo),
        "all_trap_pairwise_dependence_preserved_within_label_permutation":True,
        "no_pooled_trap_pair_independence_claim":True,
        "permutations":permutations,"landscape_bootstrap":bootstraps,
    }


def calculate(original_wide,original_long,site_env,trap_env,
              *, permutations=N_PERM,bootstraps=N_BOOT):
    eligibility=build(original_wide,original_long,site_env,trap_env)
    if not eligibility["source_bio_wide_0_1_incidence_matrix_semantics_confirmed"]:
        raise ValueError("original_taxa_incidence_not_frozen")
    if not eligibility["landscape_env_plot_id_and_biological_SITE_values_exact_match"]:
        raise ValueError("original_13_landscape_identity_not_verified")
    wide,columns=original_wide
    env,_=trap_env
    labels=columns[2:]
    if len(labels)!=301:raise ValueError("original_301_species_names_changed")
    species_sets={}
    for r in wide:
        cell=(key(r["SITE"]),key(r["CELL_ID"]))
        present=set()
        for label in labels:
            value=r.get(label,"")
            if value not in ("0","0.0","1","1.0"):
                try:v=float(value)
                except (TypeError,ValueError):raise ValueError("source_nonbinary_incidence")
                if v not in (0,1):raise ValueError("source_nonbinary_incidence")
            else:
                v=float(value)
            if v:present.add(label)
        if not present:raise ValueError("original_trap_empty_niche_source_not_prespecified")
        if cell in species_sets:raise ValueError("duplicate_source_beetle_trap_cell")
        species_sets[cell]=frozenset(present)
    urban={}
    for r in env:
        cell=(key(r["SITE"]),key(r["CELL_ID"]))
        try:v=float(r["urbanization_index"])
        except (TypeError,ValueError):raise ValueError("original_urbanization_index_missing")
        if not math.isfinite(v):raise ValueError("source_nonfinite_urbanization")
        if cell in urban:raise ValueError("duplicate_environment_index")
        urban[cell]=v
    if species_sets.keys()!=urban.keys():raise ValueError("source_env_and_taxa_cells_do_not_match")
    if len(species_sets)!=207:raise ValueError("source_original_cell_count_changed")
    by_landscape=defaultdict(list)
    for site,trap in sorted(species_sets):
        cell=(site,trap)
        by_landscape[site].append((urban[cell],species_sets[cell]))
    if len(by_landscape)!=13:raise ValueError("not_source_13_landscapes")
    source_summary={site:source_study(vals) for site,vals in by_landscape.items()}
    main=inference(source_summary,permutations=permutations,bootstraps=bootstraps)
    masked=[]
    for i,(site,row) in enumerate(sorted(source_summary.items())):
        masked.append({
            "anonymous_landscape_index":i+1,
            "original_trap_count":row["source_traps"],
            "dependent_within_landscape_pair_count":row["turnover_pairs"],
            "mean_source_Simpson_taxon_turnover":row["mean_family_free_species_Simpson_turnover"],
            "mean_source_Jaccard_secondary":row["mean_Jaccard_dissimilarity_secondary"],
            "slope_Simpson_turnover_per_local_urbanization_difference_SD":row["main_slope"]
        })
    return {
        "schema":"structural.forest_beetle_turnover_absolute_urbanization_difference.v1",
        "source_Zenodo_v3_DOI":DOI,
        "original_sampling_landscape_n":13,
        "original_species_by_trap_incidence_matrix_traps":207,
        "original_taxa_columns":301,
        "source_original_positive_incidence_counts":3215,
        "published_species_Coleoptera_surveillance_2019":True,
        "study_original_exposure":"trap_local_urbanization_index_differenced_within_landscape",
        "study_original_response":"pairwise_Simpson_species_turnover_not_nestedness",
        "primary_original_trap_pair_count_nonindependent":sum(s["turnover_pairs"] for s in source_summary.values()),
        "target_predeclared_in_analysis_specific_protocol_after_previous_source_analysis":True,
        "existing_2026_Nardi_study_analyzed_species_turnover":True,
        "previous_negative_exotic_share_urban_test_not_relabelled":True,
        "main_result":main,
        "anonymous_landscape_results":masked,
        "no_environmental_causal_claim":True,
        "species_detection_not_dispersal_or_natural_colonization":True,
        "trap_lures_and_spatial_autocorrelation_not_removed":True,
        "regional_or_forest_canopy_vertical_response_not_tested":True,
        "no_original_site_taxa_trap_IDs_individuals_or_coordinates_exported":True,
        "eBird_used":False,
    }


def run(wide,long,site,trap,out):
    inputs=[
        parse(wide,"bio_cast"),
        parse(long,"bio_data_trapscale"),
        parse(site,"env_data_sitescale"),
        parse(trap,"env_data_trapscale")
    ]
    report=calculate(*inputs)
    dest=Path(out);dest.mkdir(parents=True,exist_ok=True)
    (dest/"forest_beetles_pairwise_turnover_urban_difference.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    for n in ("wide","long","site","trap","out"):
        p.add_argument("--"+n,required=True)
    a=p.parse_args()
    run(a.wide,a.long,a.site,a.trap,a.out)
