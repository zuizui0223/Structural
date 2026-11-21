#!/usr/bin/env python3
"""ONE original Piccini 2026 German forest-floor guild-composition site-heldout test.

Frozen protocol:
docs/FOREST_BEETLE_PICCINI2026_FLOOR_GUILD_HELDOUT_SINGLE_TEST_PRESPEC_20261117.md
Original 17-column GRO source fetched to private runner RAM and MD5 verified.
Method-only gate always precedes source species/guild/abundance access.
Only anonymous aggregate output. Never reuses original old scorers.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from piccini2026_gro_original_method_unit_gate import (
    DOI, metadata_source_files, head_shape, get_one_original_publisher_file, MethodStop
)
from piccini2026_gro_original_header_only_gate import normalized

SOURCE_ROWS=22414
BOOT=4000
SEED=20261117
SHRINK=5.
STAND_COUNT=5
SITE_COUNT=8
PLOTS=40
FIELD_NAMES=("site","stand","plot","stratum","period")
TAXON_NAMES={"species","speciesname","speciesid","taxon","taxonid"}
ABUND_NAMES={"abundance","individuals","count"}
GUILD_NAME="feedingguild"

class ScientificStop(Exception):
    pass

def find_one(normal,choices,why):
    p=[i for i,z in enumerate(normal) if z in choices]
    if len(p)!=1:
        raise ScientificStop("SOURCE_STOP_"+why+"_HEADER_AMBIGUOUS")
    return p[0]

def source_design_before_biology(raw:bytes):
    try:
        text=raw.decode("utf-8-sig")
        reader=csv.reader(io.StringIO(text,newline=""),delimiter=";",strict=True)
        header=next(reader)
    except (UnicodeError,StopIteration,csv.Error) as e:
        raise ScientificStop("SOURCE_STOP_CSV_HEADER") from e
    norm=[normalized(x) for x in header]
    if len(norm)!=17:
        raise ScientificStop("SOURCE_STOP_ORIGINAL_17_FIELD_WIDTH")
    ix={k:find_one(norm,{k},"CORE_"+k.upper()) for k in FIELD_NAMES}
    trap_positions=[i for i,name in enumerate(header) if name.strip()=="trapID"]
    if len(trap_positions)!=1 or trap_positions[0]!=7:
        raise ScientificStop("SOURCE_STOP_EXACT_SOURCE_TRAPID_8TH_COLUMN")
    ix["trapID"]=trap_positions[0]
    # HEADER-only identification here; biological values not yet touched.
    ix["species"]=find_one(norm,TAXON_NAMES,"SPECIES")
    ix["guild"]=find_one(norm,{GUILD_NAME},"GUILD")
    ix["abundance"]=find_one(norm,ABUND_NAMES,"ABUNDANCE")
    core={k:ix[k] for k in (*FIELD_NAMES,"trapID")}
    rowtext=[]
    site_stands=defaultdict(set)
    plot_site=defaultdict(set)
    plot_stand=defaultdict(set)
    plot_layer_traps=defaultdict(set)
    plot_layer_periods=defaultdict(set)
    traps_context=defaultdict(set)
    layer_plots=defaultdict(set)
    for j,row in enumerate(reader,1):
        if j>SOURCE_ROWS or len(row)!=17:
            raise ScientificStop("SOURCE_STOP_ORIGINAL_ROW_SHAPE_OR_SIZE")
        # Index into method fields ONLY until all source-design gates pass.
        site,stand,plot,layer,period,trap=(row[core[k]].strip()
            for k in (*FIELD_NAMES,"trapID"))
        if not all((site,stand,plot,layer,period,trap)):
            raise ScientificStop("SOURCE_STOP_METHOD_CORE_BLANK")
        site_stands[site].add(stand)
        plot_site[plot].add(site)
        plot_stand[plot].add(stand)
        plot_layer_traps[(plot,layer)].add(trap)
        plot_layer_periods[(plot,layer)].add(period)
        traps_context[trap].add((plot,layer))
        layer_plots[layer].add(plot)
        # Source rows kept private, biological cols not accessed yet.
        rowtext.append(row)
    if len(rowtext)!=SOURCE_ROWS:
        raise ScientificStop("SOURCE_STOP_22414_SOURCE_ROW_DRIFT")
    if (len(site_stands)!=SITE_COUNT or
        len({s for v in site_stands.values() for s in v})!=STAND_COUNT or
        any(len(v)!=STAND_COUNT for v in site_stands.values()) or
        len(plot_site)!=PLOTS or
        any(len(v)!=1 for v in plot_site.values()) or
        any(len(v)!=1 for v in plot_stand.values()) or
        len(layer_plots)!=3 or
        any(len(v)!=PLOTS for v in layer_plots.values()) or
        len(plot_layer_traps)!=120):
        raise ScientificStop("SOURCE_STOP_8SITE_FIVE_STAND_FORTY_PLOT_LAYER_GRAIN")
    if any(len(v)!=1 for v in traps_context.values()) or len(traps_context)!=557:
        raise ScientificStop("SOURCE_STOP_trapID_NONCOLLISION_557_CHECK")
    shapes=defaultdict(int)
    for plot in plot_site:
        per=[len(v) for (p,layer),v in plot_layer_traps.items() if p==plot]
        shapes[tuple(sorted(per))]+=1
    if shapes!={(3,3,8):37,(2,3,8):3}:
        raise ScientificStop("SOURCE_STOP_NOMINAL_8_3_3_SHAPE_DRIFT")
    choices=[layer for layer,plots in layer_plots.items()
             if len(plots)==PLOTS and all(
                 len(plot_layer_traps[(plot,layer)])==8 for plot in plot_site)]
    if len(choices)!=1:
        raise ScientificStop("SOURCE_STOP_FLOOR_EIGHT_ID_STRATUM_NOT_UNIQUE")
    floor=choices[0]
    if any(len(plot_layer_periods[(p,floor)])<2 for p in plot_site):
        raise ScientificStop("SOURCE_STOP_FLOOR_PERIOD_COVERAGE_BELOW_TWO")
    # Every site×stand is one plot, never 40 independent parent sites.
    pairs={(next(iter(plot_site[p])),next(iter(plot_stand[p]))) for p in plot_site}
    if len(pairs)!=40:
        raise ScientificStop("SOURCE_STOP_ONE_PLOT_PER_SITE_STAND")
    return ix,rowtext,floor,plot_site,plot_stand,{
        "original_source_rows":len(rowtext),
        "source_parent_sites":len(site_stands),
        "source_stand_categories":STAND_COUNT,
        "source_plot_labels":PLOTS,
        "source_layer_labels":len(layer_plots),
        "source_floor_8_recorded_ID_plots":PLOTS,
        "source_global_trapID_labels":len(traps_context),
        "source_floor_8_ID_panel_period_tokens_per_plot_SORTED_RANGE":[
            min(len(plot_layer_periods[(p,floor)]) for p in plot_site),
            max(len(plot_layer_periods[(p,floor)]) for p in plot_site)
        ],
        "source_8_3_3_full_nominal_plots":shapes[(3,3,8)],
        "source_8_3_2_partial_nominal_plots":shapes[(2,3,8)],
        "original_source_biological_columns_UNTOUCHED_until_this_gate":True,
        "no_source_site_stand_plot_layer_IDs_exported":True,
        "source_period_not_converted_to_calendar_year":True,
        "source_zero_capture_and_trap_days_NOT_INFERRED":True,
    }

def selected_floor_guild_matrix(ix,rows,floor,plot_site,plot_stand):
    # FIRST and ONLY biological response read; rows retained after DESIGN gate.
    all_species_guilds=defaultdict(set)
    plot_species=defaultdict(set)
    original_guild_missing_species=set()
    species_in_floor=set()
    source_nonpositive=0
    for row in rows:
        layer=row[ix["stratum"]].strip()
        if layer!=floor:
            continue
        species=row[ix["species"]].strip()
        guild=row[ix["guild"]].strip()
        abund=row[ix["abundance"]].strip()
        if not species or not abund:
            raise ScientificStop("BIOLOGY_STOP_SOURCE_SPECIES_OR_COUNT_MISSING")
        try:
            n=float(abund)
        except ValueError as e:
            raise ScientificStop("BIOLOGY_STOP_NONNUMERIC_ABUNDANCE") from e
        if not np.isfinite(n) or n<0:
            raise ScientificStop("BIOLOGY_STOP_NEGATIVE_OR_NONFINITE_ABUNDANCE")
        if n==0:
            source_nonpositive+=1
            continue
        plot=row[ix["plot"]].strip()
        species_in_floor.add(species)
        plot_species[plot].add(species)
        if guild:
            all_species_guilds[species].add(guild)
        else:
            original_guild_missing_species.add(species)
    # Validate ORIGINAL trait ontology: zero ambiguous nonempty species labels.
    conflicts=sum(len(g)>1 for g in all_species_guilds.values())
    if conflicts:
        raise ScientificStop("BIOLOGY_STOP_SOURCE_SPECIES_GUILD_CONFLICT")
    active_known={s:next(iter(g)) for s,g in all_species_guilds.items() if len(g)==1}
    guilds=sorted(set(active_known.values()))
    if not 2<=len(guilds)<=12:
        raise ScientificStop("BIOLOGY_STOP_SOURCE_GUILD_COUNT_NOT_2_TO_12")
    if len(species_in_floor)==0 or (
       len(active_known)/len(species_in_floor)<0.80):
        raise ScientificStop("BIOLOGY_STOP_SOURCE_GUILD_COVERAGE_BELOW_80PCT")
    if len(plot_species)!=40:
        raise ScientificStop("BIOLOGY_STOP_FLOOR_PLOT_SPECIES_DETECTION_MISSING")
    site_keys=sorted({next(iter(v)) for v in plot_site.values()})
    stand_keys=sorted({next(iter(v)) for v in plot_stand.values()})
    plots=sorted(plot_site)
    ys=[];sites=[];stands=[];per_plot_coverage=[]
    for plot in plots:
        spp=plot_species[plot]
        known=[s for s in spp if s in active_known]
        coverage=len(known)/len(spp) if spp else 0
        if len(known)<5 or coverage<.70:
            raise ScientificStop("BIOLOGY_STOP_PLOT_TAXON_OR_GUILD_COVERAGE")
        counts=np.zeros(len(guilds),dtype=float)
        guild_ix={g:i for i,g in enumerate(guilds)}
        for sp in known:
            counts[guild_ix[active_known[sp]]]+=1.
        counts/=counts.sum()
        ys.append(np.sqrt(counts))
        sites.append(site_keys.index(next(iter(plot_site[plot]))))
        stands.append(stand_keys.index(next(iter(plot_stand[plot]))))
        per_plot_coverage.append(coverage)
    return (np.asarray(ys),np.asarray(sites),np.asarray(stands),
            {"source_original_floor_species_detected":len(species_in_floor),
             "source_floor_guild_known_active_species":len(active_known),
             "source_original_guild_categories":len(guilds),
             "source_source_species_conflicting_guild_count":conflicts,
             "source_floor_record_lines_abundance_zero_skipped":source_nonpositive,
             "source_floor_plot_guild_coverage_MIN":round(min(per_plot_coverage),6),
             "source_floor_plot_guild_coverage_MAX":round(max(per_plot_coverage),6),
             "feedingguild_label_text_and_species_names_NOT_EXPORTED":True,
             "abundance_used_for_presence_gt_zero_ONLY":True,
             "no_abundance_weights_or_trap_exposure_imputation":True})

def unit_normalize(x):
    norm=np.linalg.norm(x,axis=-1,keepdims=True)
    if np.any(norm<1e-12):
        raise ScientificStop("BIOLOGY_STOP_ZERO_PREDICTED_GUILD_VECTOR")
    return x/norm

def fixed_heldout(Y,site,stand):
    if Y.ndim!=2 or Y.shape[0]!=40 or not 2<=Y.shape[1]<=12:
        raise ScientificStop("MODEL_STOP_GUILD_COMPOSITION_MATRIX")
    if site.shape!=(40,) or stand.shape!=(40,):
        raise ScientificStop("MODEL_STOP_SITE_STAND_SHAPE")
    if not np.allclose(np.sum(Y*Y,axis=1),1.,atol=1e-9):
        raise ScientificStop("MODEL_STOP_OBSERVED_HELLINGER_NORM")
    l0=np.full(40,np.nan);l1=np.full(40,np.nan)
    for held in range(8):
        tr=site!=held;te=site==held
        if tr.sum()!=35 or te.sum()!=5 or (
            sorted(stand[te].tolist())!=[0,1,2,3,4]):
            raise ScientificStop("MODEL_STOP_SITE_HOLDOUT_LEAKAGE_OR_DESIGN")
        global_mean=Y[tr].mean(axis=0)
        pb=unit_normalize(global_mean[None,:])[0]
        for i in np.flatnonzero(te):
            match=tr & (stand==stand[i])
            if match.sum()!=7:raise ScientificStop("MODEL_STOP_STAND_TRAIN_COUNT_NOT7")
            ext=(np.sum(Y[match],axis=0)+SHRINK*global_mean)/(7.+SHRINK)
            pe=unit_normalize(ext[None,:])[0]
            l0[i]=.5*np.sum((Y[i]-pb)**2)
            l1[i]=.5*np.sum((Y[i]-pe)**2)
    if not np.all(np.isfinite(l0)) or not np.all(np.isfinite(l1)):
        raise ScientificStop("MODEL_STOP_NONFINITE_LOSS")
    site_delta=np.array([np.mean((l0-l1)[site==i]) for i in range(8)])
    return l0,l1,site_delta

def summarize(l0,l1,d):
    obs=float(np.mean(d))
    rng=np.random.default_rng(SEED)
    boot=np.mean(d[rng.integers(0,8,size=(BOOT,8))],axis=1)
    ci=np.quantile(boot,[.025,.975])
    flips=np.array([[(1. if (state>>j)&1 else -1.) for j in range(8)]
                    for state in range(256)])
    perm=np.mean(flips*d[None,:],axis=1)
    p=float(np.sum(np.abs(perm)>=abs(obs)-1e-12)/256)
    return {
        "single_primary_site_equal_delta_Hellinger2_baseline_minus_stand":round(obs,8),
        "site_equal_heldout_baseline_H2":round(float(np.mean(l0)),8),
        "site_equal_heldout_plus_stand_H2":round(float(np.mean(l1)),8),
        "site_equal_heldout_H2_relative_reduction_percent":
            round(float(100*(np.mean(l0)-np.mean(l1))/np.mean(l0)),5)
            if np.mean(l0)>0 else None,
        "site_block_bootstrap_4000_95pct_percentile_CI":[round(float(a),8) for a in ci],
        "site_256_exact_signflip_two_sided_p":round(p,8),
        "positive_site_block_gain_count":int(np.sum(d>1e-12)),
        "negative_site_block_gain_count":int(np.sum(d< -1e-12)),
        "zero_site_block_gain_count":int(np.sum(np.abs(d)<=1e-12)),
        "site_block_gain_min":round(float(d.min()),8),
        "site_block_gain_max":round(float(d.max()),8),
        "original_parent_sites_in_cv":8,
        "train_plots_per_fold":35,
        "heldout_plots_per_fold":5,
        "precommitted_shrinkage_lambda":SHRINK,
        "exploratory_positive_criterion_met":
             bool(obs>0 and ci[0]>0 and p<.05),
        "not_an_independent_biome_or_causal_effect":True,
    }

def known_truth():
    site=np.repeat(np.arange(8),5)
    stand=np.tile(np.arange(5),8)
    # In-sample guild mixture tied to stand. Held-out transfer should help.
    rng=np.random.default_rng(99)
    dense=np.array([[7.,1.,1.],[1.,7.,1.],[1.,1.,7.],
                    [5.,3.,1.],[1.,3.,5.]])
    y0=np.stack([dense[s]+rng.uniform(.02,.2,3)
                 for s in stand])
    y=np.sqrt(y0/y0.sum(axis=1,keepdims=True))
    b,a,d=fixed_heldout(y,site,stand)
    assert d.mean()>0
    stats=summarize(b,a,d)
    assert stats["single_primary_site_equal_delta_Hellinger2_baseline_minus_stand"]>0
    # Null exactly identical positive-guild mix in every plot.
    z=np.sqrt(np.tile(np.array([[.2,.3,.5]]),(40,1)))
    bn,an,dn=fixed_heldout(z,site,stand)
    assert abs(dn.mean())<1e-12
    assert summarize(bn,an,dn)["site_256_exact_signflip_two_sided_p"]==1.
    assert np.all((b>=0)&(b<=1)) and np.all((a>=0)&(a<=1))
    # Source-only method reader known truth cannot accidentally read species.
    h=["site","stand","plot","stratum","period","Species","trap",
       "trapID","feedingguild","Abundance"]+["X"+str(i) for i in range(7)]
    assert len(h)==17
    i={x:find_one([normalized(t) for t in h],{x},"TEST")
       for x in FIELD_NAMES}
    assert i["site"]==0 and i["stratum"]==3
    print("SYNTHETIC_ONE_GUILD_SITE_HOLDOUT_POSITIVE_NULL_METHOD_GATE_PASS")

def single_source_score():
    status={"status":"SOURCE_UNSCORED",
            "original_source_DOI":DOI,
            "original_2024_canopy_archive_UNOPENED":True,
            "original_old_BALA_GEB_PREDICTS_NEON_Finland_Thai_UNOPENED":True,
            "eBird_used":False,"TinyFish_used":False}
    try:
        files=metadata_source_files()
        h=[head_shape(f["file_id"]) for f in files]
        main=[f for f,x in zip(files,h) if x["header_column_count"]==17
              and x["header_delimiter_category"]=="semicolon"]
        other=[f for f,x in zip(files,h) if x["header_column_count"]==3
               and x["header_delimiter_category"]=="tab"]
        if len(main)!=1 or len(other)!=1:
            raise ScientificStop("SOURCE_STOP_MAIN_AND_SECOND_HEADER_ARCHITECTURE")
        f=main[0]
        raw=get_one_original_publisher_file(f["file_id"],f["expected_size"])
        check=f.get("published_checksum")
        if not (isinstance(check,dict) and check.get("type","").lower()=="md5"
                and hashlib.md5(raw).hexdigest()==str(check.get("value","")).lower()):
            raise ScientificStop("SOURCE_STOP_ORIGINAL_PUBLISHER_MD5")
        ix,rows,floor,site_map,stand_map,gate=source_design_before_biology(raw)
        status["prebiology_method_gate"]=gate
        # FIRST taxa/guild/positive-abundance access starts strictly HERE.
        Y,site,stand,qa=selected_floor_guild_matrix(
            ix,rows,floor,site_map,stand_map)
        status["original_floor_guild_eligibility"]=qa
        l0,l1,d=fixed_heldout(Y,site,stand)
        status["result"]=summarize(l0,l1,d)
        status["status"]="ONE_EXPLORATORY_SOURCE_OBSERVED_GUILD_PREDICTION_COMPLETE"
    except (ScientificStop,MethodStop) as exc:
        status["status"]=str(exc)
        status["SCIENTIFIC_OR_METHOD_STOP_NOT_ECOLOGICAL_NULL"]=True
        status["new_biological_estimator_NOT_COMPLETED"]=True
    return status

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    opts=ap.parse_args()
    known_truth()
    if opts.test:return
    if not opts.out:ap.error("--out required")
    result={"schema":"structural.Piccini2026_floor_guild_8site_holdout_one_original_test.v1",
      "prebiology_protocol":
       "docs/FOREST_BEETLE_PICCINI2026_FLOOR_GUILD_HELDOUT_SINGLE_TEST_PRESPEC_20261117.md",
      "single_original_evaluation":single_source_score(),
      "no_raw_taxon_site_trap_guild_records_uploaded":True,
      "old_frozen_originals_NOT_RESCORED":True,
      "postresult_variant_selection_NOT_ALLOWED":True}
    opts.out.mkdir(parents=True,exist_ok=True)
    (opts.out/"Piccini2026_floor_guild_site_holdout_original_onepass.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
