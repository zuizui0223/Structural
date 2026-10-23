#!/usr/bin/env python3
"""Pico v1.282: fixed two-covariate descriptive robustness of the v1.281 signal.

The 2013 MOVECLIM published source is previously outcome-exposed. This is
retrospective reanalysis of the EXACT original source, not a confirmatory,
causal, invasive-treatment, historical survival, donor or rescue test.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
import urllib.request

from azores_MOVECLIM_2013_refugia_v1_278 import (
    MURL, MSHA, SURL, SSHA, NATIVE, original_event_occurrence_records
)
from azores_MOVECLIM_introduced_pressure_v1_281 import audit_introduced_pressure, _loss_taxa, _norm
from azores2016_s1_loss_presence_crosswalk_v1_268 import canonical_binomial, normalized_locality
from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
from macaronesia_extirpation_source_profile_v1_263 import download_original


def fixed_ridge_residual(y, x1, x2, lam=1.0):
    """24-plot deterministic ridge correction, intercept unpenalized.

    y is introduced species richness; x1 rank elevation; x2 total native
    species richness. No focal species response enters the ridge fit.
    """
    if not (len(y) == len(x1) == len(x2)) or len(y) < 4 or lam != 1.0:
        raise ValueError("Fixed design and ridge penalty required")
    n = len(y)
    mu_y = sum(y) / n
    z_cols = []
    for x in (x1, x2):
        mu = sum(x) / n
        sigma = math.sqrt(sum((v - mu) ** 2 for v in x) / n)
        z_cols.append([(v-mu)/sigma for v in x] if sigma > 0 else [0.0]*n)
    z1, z2 = z_cols
    a = sum(v*v for v in z1) + lam
    b = sum(u*v for u,v in zip(z1,z2))
    d = sum(v*v for v in z2) + lam
    c1 = sum(z*(v-mu_y) for z,v in zip(z1,y))
    c2 = sum(z*(v-mu_y) for z,v in zip(z2,y))
    det = a*d-b*b
    if det <= 0:
        raise ValueError("Fixed ridge matrix not positive definite")
    beta1, beta2 = (c1*d-c2*b)/det, (a*c2-c1*b)/det
    residuals = [v-mu_y-beta1*u-beta2*w for v,u,w in zip(y,z1,z2)]
    if abs(sum(residuals)) > 1e-8:
        raise AssertionError("Ridge model intercept centering error")
    return residuals, {
        "intercept_mean_introduced_richness": mu_y,
        "slope_standardized_elevation": beta1,
        "slope_standardized_native_richness": beta2,
        "lambda": lam,
        "residual_RMS_introduced_taxa": math.sqrt(sum(v*v for v in residuals)/n),
    }


def audit_adjusted(events, observations, losses, *, expected_plots=58, expected_events=232):
    old = audit_introduced_pressure(events, observations, losses,
                                    expected_plots=expected_plots,
                                    expected_events=expected_events)
    focal, pairs = _loss_taxa(losses)
    core_to_site = {}
    site_elev = defaultdict(list)
    for e in events:
        site=(normalized_locality(e.get("island")),str(e.get("locationID","")).strip())
        core=str(e.get("coreid","")).strip()
        if core in core_to_site or not core:
            raise ValueError("Invalid author event coreid")
        core_to_site[core]=site
        site_elev[site].append(float(e.get("minimumElevationInMeters")))
    status = defaultdict(set)
    seen = defaultdict(set)
    for o in observations:
        core=str(o.get("coreid","")).strip()
        if core not in core_to_site:
            raise ValueError("Occurrence without original author event")
        if _norm(o.get("taxonRank")) != "species":
            continue
        name=canonical_binomial(o.get("scientificName"))
        if name is None:
            continue
        try:cov=float(o.get("organismQuantity"))
        except (ValueError,TypeError):continue
        if not math.isfinite(cov) or not (1<=cov<=9):
            continue
        site=core_to_site[core]
        origin=_norm(o.get("establishmentMeans"))
        kind="native" if origin in NATIVE else "introduced" if origin=="introduced" else "unknown"
        status[(site[0],name)].add(kind)
        seen[(site[0],name)].add(site)

    pico_sites=sorted((s for s in site_elev if s[0]=="Pico"),
                      key=lambda s:(statistics.median(site_elev[s]),s[1]))
    if expected_plots==58 and len(pico_sites)!=24:
        raise ValueError("Original Pico plot denominator changed")
    native_by_taxon={}
    alien_by_taxon={}
    for (island,name),sites in seen.items():
        if island!="Pico":continue
        cls=status[(island,name)]
        if cls=={"native"}:native_by_taxon[name]=sites
        elif cls=={"introduced"}:alien_by_taxon[name]=sites
    native_species_by_site=defaultdict(set)
    for species,sites in native_by_taxon.items():
        for site in sites:native_species_by_site[site].add(species)
    alien_species_by_site=defaultdict(set)
    for species,sites in alien_by_taxon.items():
        for site in sites:alien_species_by_site[site].add(species)

    focal_names=[s for s in native_by_taxon if s in focal]
    reference_names=[s for s in native_by_taxon if s not in focal]
    old_pico=old["by_island"]["Pico"]
    if (len(focal_names)!=old_pico["focal_native_taxa"]
        or len(reference_names)!=old_pico["reference_native_taxa"]
        or sum(len(v) for v in native_by_taxon.values())!=
           old_pico["focal_taxon_plot_positives"]+old_pico["reference_taxon_plot_positives"]
        or sum(len(v) for v in alien_by_taxon.values())!=old_pico["introduced_taxon_plot_positives"]):
        raise ValueError("Original v1.281 Pico native/introduced incidence mismatched")
    elevations=[statistics.median(site_elev[s]) for s in pico_sites]
    ranks=[]
    for z in elevations:
        less=sum(v<z for v in elevations)
        equal=sum(v==z for v in elevations)
        ranks.append((less+(equal-1)/2)/(len(elevations)-1) if len(elevations)>1 else 0.5)
    y=[len(alien_species_by_site[s]) for s in pico_sites]
    native=[len(native_species_by_site[s]) for s in pico_sites]
    residuals,model=fixed_ridge_residual(y,ranks,native)
    site_residual=dict(zip(pico_sites,residuals))
    site_pressure=dict(zip(pico_sites,y))
    def taxon_avg(names,values):
        return sum(sum(values[s] for s in native_by_taxon[name])/len(native_by_taxon[name])
                   for name in names)/len(names) if names else None
    f_unadj=taxon_avg(focal_names,site_pressure)
    r_unadj=taxon_avg(reference_names,site_pressure)
    if f_unadj is None or r_unadj is None or abs(
        f_unadj-r_unadj-old_pico["primary_focal_minus_reference_intro_richness"])>1e-9:
        raise ValueError("v1.281 original primary changed during v1.282")
    f_adj=taxon_avg(focal_names,site_residual)
    r_adj=taxon_avg(reference_names,site_residual)
    focal_present=[s for s in pico_sites if any(s in native_by_taxon[t] for t in focal_names)]
    focal_absent=[s for s in pico_sites if s not in focal_present]
    if expected_plots==58 and (len(focal_present)!=19 or len(focal_absent)!=5):
        raise ValueError("v1.281 plot-group denominator changed")
    def mean_at(sites,values):
        return sum(values[s] for s in sites)/len(sites) if sites else None
    raw_native= dict(zip(pico_sites,native))
    raw_resid=site_residual
    return {
        "schema":"structural.azores_MOVECLIM_native_richness_adjustment_result.v1_282",
        "status":"RETROSPECTIVE_RICHNESS_ELEVATION_STRESS_TEST_COMPLETED",
        "plot_frame":"Pico, 24 original 2013 indigenous-vegetation 10x10m plots",
        "independent_plots":len(pico_sites),
        "focal_native_taxa":len(focal_names),
        "reference_native_taxa":len(reference_names),
        "focal_positive_plots":len(focal_present),
        "focal_negative_plots":len(focal_absent),
        "focal_species_plot_positives":sum(len(native_by_taxon[t]) for t in focal_names),
        "other_native_species_plot_positives":sum(len(native_by_taxon[t]) for t in reference_names),
        "introduced_species_plot_positives":sum(y),
        "original_v281_primary_focal_minus_reference":f_unadj-r_unadj,
        "elevation_half_difference_from_v281":old_pico["elevation_half_adjusted_focal_minus_reference_intro"],
        "fixed_ridge":model,
        "focal_mean_introduced_count_residual":f_adj,
        "reference_mean_introduced_count_residual":r_adj,
        "focal_minus_reference_richness_elevation_adjusted":f_adj-r_adj,
        "focal_positive_mean_adjusted_intro_residual":mean_at(focal_present,raw_resid),
        "focal_negative_mean_adjusted_intro_residual":mean_at(focal_absent,raw_resid),
        "focal_positive_minus_negative_adjusted_intro":mean_at(focal_present,raw_resid)-mean_at(focal_absent,raw_resid),
        "focal_positive_mean_native_taxa":mean_at(focal_present,raw_native),
        "focal_negative_mean_native_taxa":mean_at(focal_absent,raw_native),
        "not_a_causal_effect_or_true_refuge":True,
        "not_independent_fresh_confirmatory":True,
        "not_observed_dispersal_colonization_rescue":True,
        "no_taxon_or_plot_id_export":True,
        "other_protected_biological_endpoints_opened":0,
        "GEB_scientific_HOLD":True,
        "confirmatory_systems_admitted":0,
        "eBird_used":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.azores_moveclim_native_richness_adjusted_falsification.v1_282"
        or c.get("status")!="RETROSPECTIVE_SENSITIVITY_PROTOCOL_FROZEN_BEFORE_REOPENING_2013_ROWS"
        or c["sources"]["MOVECLIM_SHA256"]!=MSHA
        or c["sources"]["S1_SHA256"]!=SSHA
        or c["analysis"]["ridge"].find("lambda=1.0")<0):
        raise ValueError("Unfrozen v1.282 source/stress-test configuration")
    result={
       "schema":"structural.azores_MOVECLIM_native_richness_adjustment_result.v1_282",
       "status":"SOURCE_STOP_NO_NEW_ADJUSTMENT",
       "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,
       "other_protected_biological_endpoints_opened":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(MURL,headers={
             "User-Agent":"Structural-retrospective-native-richness-adjustment-v1.282"})
        with urllib.request.urlopen(req,timeout=60) as f:
            move=f.read(15_000_001)
        if len(move)!=111299 or hashlib.sha256(move).hexdigest()!=MSHA:
            raise ValueError("Publisher 2013 source fingerprint mismatch")
        csic=download_original(SURL,332776,5_000_000)
        if hashlib.sha256(csic).hexdigest()!=SSHA:
            raise ValueError("Publisher S1 source fingerprint mismatch")
        events,obs=original_event_occurrence_records(move)
        if len(events)!=232 or len(obs)!=2539:
            raise ValueError("Original 2013 source denominator changed")
        result=audit_adjusted(events,obs,parse_sheet_s1(csic))
    except Exception as ex:
        result["stop_reason"]=str(ex)[:350]
        result["stop_type"]=type(ex).__name__
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "Pico_plot_count":result.get("independent_plots"),
        "original_v281":result.get("original_v281_primary_focal_minus_reference"),
        "richness_and_elevation_adjusted":result.get("focal_minus_reference_richness_elevation_adjusted"),
        "focal_positive_minus_absent_adjusted":result.get("focal_positive_minus_negative_adjusted_intro"),
        "mean_native_richness_on_positive":result.get("focal_positive_mean_native_taxa"),
        "mean_native_richness_on_negative":result.get("focal_negative_mean_native_taxa"),
        "stop_reason":result.get("stop_reason"),
    },sort_keys=True))
    if result["status"]!="RETROSPECTIVE_RICHNESS_ELEVATION_STRESS_TEST_COMPLETED":
        raise SystemExit(2)


if __name__=="__main__":
    main()
