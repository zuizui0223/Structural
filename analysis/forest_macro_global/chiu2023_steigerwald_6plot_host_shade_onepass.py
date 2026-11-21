#!/usr/bin/env python3
"""ONE preregistered retrospective six-plot original host×shade composition transfer.

One pinned author-original Git blob, new species response only after source grain
and original sample support. Six PLOT leave-one-out blocks, no post-hoc options.
Only anonymous aggregate values are saved, never source species/site IDs.
"""
from __future__ import annotations
import argparse, csv, io, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np
from chiu2023_steigerwald_6plot_source_grain_gate import (
    original_pub,method_only,SourceStop,SIZE,BLOB)

PRE="docs/FOREST_BEETLE_CHIU2023_STEIGERWALD_SIXPLOT_HOST_SHADE_SITE_HELDOUT_ONEPASS_PRESPEC_20261117.md"
RIDGE=5.
BOOT=4000
SEED=20261117
N_SITES=6
N_TREATMENTS=3
N_HOSTS=6
N_ROWS=3891
N_POSITIVE_YEAR_CONTEXTS=430
N_PLOT_HOST_TREATMENT=108
EXPECTED_SHAPE=(3,6,6)
class ScientificStop(Exception):pass

def validate_new_prebiology_gate(raw):
    m=method_only(raw)  # source-only reader ignores original species and abundance columns
    needed={
      "status":"SOURCE_METHOD_OPPORTUNITY_COVERAGE_NOT_FULL_STOP",
      "original_author_file_bytes":SIZE,
      "source_method_records_NOT_unique_traps_or_individuals":N_ROWS,
      "source_author_distinct_original_ID_labels":430,
      "source_author_ID_cross_context_collisions":0,
      "source_host_code_tree_spec_vs_tree_species_conflicts":0,
      "source_distinct_parent_plots":N_SITES,
      "source_distinct_treatment_levels":N_TREATMENTS,
      "source_distinct_original_host_types":N_HOSTS,
      "source_distinct_collection_years":4,
      "source_positive_recorded_plot_treat_host_contexts":N_PLOT_HOST_TREATMENT,
      "source_positive_recorded_plot_treat_host_year_contexts":N_POSITIVE_YEAR_CONTEXTS,
    }
    for k,v in needed.items():
        if m.get(k)!=v:
            raise ScientificStop("SOURCE_STOP_PINNED_CHIU_ORIGINAL_METHOD_DRIFT")
    if m.get("source_year_support_count_per_positive_cell_MIN_MAX") != [3,4]:
        raise ScientificStop("SOURCE_STOP_3_4_YEAR_SUPPORT_SCOPE_CHANGED")
    return m

def build_observed_comp(raw):
    # SINGLE original biological source read; conducted ONLY after above gate.
    try:
        rdr=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
        cells=defaultdict(set)
        all_taxa=set()
        per_id_species=set()
        duplicated_id_species=0
        zero_counts=0
        n=0
        for row in rdr:
            n+=1
            sp=row["species"].strip()
            if not sp:raise ScientificStop("BIOLOGY_STOP_MISSING_SPECIES")
            try:
                x=float(row["abundance"])
            except (ValueError,TypeError) as exc:
                raise ScientificStop("BIOLOGY_STOP_NONNUMERIC_OR_NA_ABUNDANCE") from exc
            if not math.isfinite(x) or x<0 or x!=int(x):
                raise ScientificStop("BIOLOGY_STOP_INVALID_OR_NONDINITE_ABUNDANCE")
            if x==0:
                zero_counts+=1
                continue
            site,treat,host=(row["plot"].strip(),row["treatment"].strip(),
                             row["tree_spec"].strip())
            cells[(site,treat,host)].add(sp)
            all_taxa.add(sp)
            unique=(row["ID"].strip(),sp)
            if unique in per_id_species:
                duplicated_id_species+=1
            per_id_species.add(unique)
    except csv.Error as exc:
        raise ScientificStop("BIOLOGY_STOP_ORIGINAL_CSV_SPECIES_PARSE") from exc
    if n!=N_ROWS or len(cells)!=108 or not (2<=len(all_taxa)<=500):
        raise ScientificStop("BIOLOGY_STOP_ORIGINAL_RESPONSE_COHORT_SHAPE")
    sites=sorted({k[0] for k in cells})
    shades=sorted({k[1] for k in cells})
    hosts=sorted({k[2] for k in cells})
    taxa=sorted(all_taxa)
    if len(sites)!=6 or len(shades)!=3 or len(hosts)!=6:
        raise ScientificStop("BIOLOGY_STOP_ORIGINAL_HOST_SHADE_LEVELS")
    indexed={s:i for i,s in enumerate(taxa)}
    obs=[];plot=[];treat=[];host=[];num_detected=[]
    for s in sites:
        for t in shades:
            for h in hosts:
                sp=cells[(s,t,h)]
                if not sp:raise ScientificStop("BIOLOGY_STOP_EMPTY_SOURCE_POSITIVE_CELL")
                vec=np.zeros(len(taxa),dtype=float)
                for species in sp:vec[indexed[species]]=1.
                vec/=len(sp)
                obs.append(np.sqrt(vec))
                plot.append(sites.index(s))
                treat.append(shades.index(t))
                host.append(hosts.index(h))
                num_detected.append(len(sp))
    y=np.asarray(obs,dtype=float)
    qa={
        "source_historical_beetle_species_in_original":len(taxa),
        "source_original_positive_record_lines":n-zero_counts,
        "source_original_zero_count_record_lines_skipped":zero_counts,
        "source_source_ID_species_duplicate_positive_rows_unweighted":duplicated_id_species,
        "source_tree_shade_cells_used":len(cells),
        "source_cell_detected_species_count_min":min(num_detected),
        "source_cell_detected_species_count_median":float(np.median(num_detected)),
        "source_cell_detected_species_count_max":max(num_detected),
        "original_species_names_and_site_treatment_host_codes_NOT_EXPORTED":True,
        "original_abundance_used_to_validate_presence_ONLY":True,
        "source_years_POOLED_not_hypothesis_or_zero_imputed":True,
    }
    return y,np.asarray(plot),np.asarray(treat),np.asarray(host),qa

def l2_normalize(v):
    z=np.linalg.norm(v)
    if not (np.isfinite(z) and z>1e-12):
        raise ScientificStop("MODEL_STOP_PROJECTION_ZERO_OR_NONFINITE")
    return v/z

def sixplot_heldout(y,plots,shade,host):
    if y.shape[0]!=108 or not 2<=y.shape[1]<=500 or any(
        a.shape!=(108,) for a in (plots,shade,host)):
        raise ScientificStop("MODEL_STOP_ORIGINAL_SITE_HOST_RESPONSE_SHAPE")
    if not np.allclose(np.einsum("ij,ij->i",y,y),1.,atol=1e-10):
        raise ScientificStop("MODEL_STOP_SOURCE_HELLINGER_RESPONSE_NORM")
    b=np.full(108,np.nan);a=np.full(108,np.nan)
    for held in range(6):
        train=plots!=held;test=plots==held
        if train.sum()!=90 or test.sum()!=18:
            raise ScientificStop("MODEL_STOP_LOPO_TRAIN_TEST_GRAIN")
        if len(set(zip(shade[test],host[test])))!=18:
            raise ScientificStop("MODEL_STOP_HELDOUT_CONDITIONS_NOT_18")
        for j in np.flatnonzero(test):
            mask=train&(shade==shade[j])
            if mask.sum()!=30:raise ScientificStop("MODEL_STOP_SHADE_TRAIN_NOT_30")
            avg=y[mask].mean(axis=0)
            pb=l2_normalize(avg)
            match=mask&(host==host[j])
            if match.sum()!=5:raise ScientificStop("MODEL_STOP_HOST_SHADE_TRAIN_NOT5")
            ext=(np.sum(y[match],axis=0)+RIDGE*avg)/(5.+RIDGE)
            pe=l2_normalize(ext)
            b[j]=.5*np.dot(y[j]-pb,y[j]-pb)
            a[j]=.5*np.dot(y[j]-pe,y[j]-pe)
    if not np.all(np.isfinite(b)) or not np.all(np.isfinite(a)):
        raise ScientificStop("MODEL_STOP_NONFINITE_SITE_TRANSFER_LOSS")
    delta=np.array([float(np.mean((b-a)[plots==site])) for site in range(6)])
    return b,a,delta

def summary(b,a,d):
    mean=float(d.mean())
    rng=np.random.default_rng(SEED)
    boot=np.mean(d[rng.integers(0,6,size=(BOOT,6))],axis=1)
    ci=np.quantile(boot,[.025,.975])
    flips=np.array([[1 if (n>>k)&1 else -1 for k in range(6)]
                    for n in range(64)],dtype=float)
    null=np.mean(flips*d[None,:],axis=1)
    p=float(np.sum(np.abs(null)>=abs(mean)-1e-12)/64)
    baseline=float(b.mean());extended=float(a.mean())
    return {
      "primary_sixplot_equal_gain_Hellinger2_baseline_minus_plus_host":round(mean,9),
      "original_site_equal_baseline_Hellinger2":round(baseline,9),
      "original_site_equal_plus_host_Hellinger2":round(extended,9),
      "relative_heldout_error_reduction_percent":
          round(100*(baseline-extended)/baseline,5) if baseline>0 else None,
      "sixplot_bootstrap_4000_95pct_percentile_CI":[round(float(v),9) for v in ci],
      "sixplot_exact_64_signflip_two_sided_p":round(p,8),
      "positive_plot_gain_count":int((d>1e-12).sum()),
      "negative_plot_gain_count":int((d < -1e-12).sum()),
      "zero_plot_gain_count":int((np.abs(d)<=1e-12).sum()),
      "plot_gain_min":round(float(d.min()),9),
      "plot_gain_max":round(float(d.max()),9),
      "original_geographic_parent_plot_blocks":6,
      "heldout_cells_per_plot":18,
      "train_cells_per_fold":90,
      "precommitted_ridge_lambda":RIDGE,
      "precommitted_support_gate_met":bool(mean>0 and ci[0]>0 and p<.05),
      "one_german_forest_observational_within_source_ONLY":True,
      "not_external_independent_countries_or_guilds":True,
      "no_missing_year_contexts_filled_as_zero":True,
    }

def synthetic():
    sites=np.repeat(np.arange(6),18)
    shades=np.tile(np.repeat(np.arange(3),6),6)
    hosts=np.tile(np.arange(6),18)
    raw=np.array([
      [10.,1.,1.],[1.,10.,1.],[1.,1.,10.],
      [5.,3.,1.],[1.,3.,5.],[2.,6.,2.],
    ])
    vals=np.stack([raw[h]+.03*np.asarray([1.,2.,3.]) for h in hosts])
    y=np.sqrt(vals/vals.sum(axis=1,keepdims=True))
    a,b,d=sixplot_heldout(y,sites,shades,hosts)
    assert float(d.mean())>0 and summary(a,b,d)["precommitted_support_gate_met"]
    const=np.sqrt(np.tile(np.array([[.2,.3,.5]]),(108,1)))
    a,b,d=sixplot_heldout(const,sites,shades,hosts)
    assert abs(d.mean())<1e-12
    assert summary(a,b,d)["sixplot_exact_64_signflip_two_sided_p"]==1.0
    assert all(a.shape==(108,) for a in [a,b])
    print("SYNTHETIC_CHIU_SIXPLOT_OBSERVED_HOST_IDENTITY_TRANSFER_POSITIVE_NULL_LEAKAGE_PASS")

def original_once():
    obj={"status":"NOT_EXECUTED",
         "prior_Piccini_Finland_BALA_GEB_responders_NOT_REOPENED":True}
    try:
        raw=original_pub()
        gate=validate_new_prebiology_gate(raw)
        obj["prebiology_method_gate"]={
            "original_gitblob_sha_VERIFIED":gate["original_author_git_blob_sha1_VERIFIED"],
            "source_method_records":gate["source_method_records_NOT_unique_traps_or_individuals"],
            "source_parent_plots":gate["source_distinct_parent_plots"],
            "source_plot_shade_host_contexts":gate["source_positive_recorded_plot_treat_host_contexts"],
            "source_positive_year_contexts":gate["source_positive_recorded_plot_treat_host_year_contexts"],
            "original_source_2_years_without_positive_rows_NOT_imputed":True,
            "source_species_abundance_NOT_USED_FOR_COHORT_SELECTION":True}
        y,site,shade,host,qa=build_observed_comp(raw)
        obj["original_observed_species_response_eligibility"]=qa
        baseline,extended,site_d=sixplot_heldout(y,site,shade,host)
        obj["result"]=summary(baseline,extended,site_d)
        obj["status"]="ONE_RETROSPECTIVE_STEIGERWALD_SIXPLOT_OBSERVED_HOST_PORTABILITY_TEST_COMPLETE"
    except (ScientificStop,SourceStop) as exc:
        obj["status"]=str(exc)
        obj["SCIENTIFIC_STOP_NOT_ECOLOGICAL_NEGATIVE"]=True
        obj["new_biological_estimator_NOT_COMPLETED"]=True
    return obj

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out required")
    output={"schema":"structural.ChiuVogel2023_sixplot_host_shade_onepass_predicted_species_composition.v1",
            "precommit":PRE,
            "one_original_observational_evaluation":original_once(),
            "old_Piccini_Finland_Burner_PREDICTS_NEON_BALA_mammals_GEB_SEALED":True,
            "no_original_species_sample_identity_or_abundance_cells_REEXPORTED":True,
            "no_postresult_exposure_tree_host_parameter_selection":True,
            "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Chiu2023_6plot_host_shade_observed_species_LOPO_onepass.json").write_text(
        json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(output,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
