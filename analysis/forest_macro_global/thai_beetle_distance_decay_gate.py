#!/usr/bin/env python3
"""Distance-decay SUPPORT GATE for Thai beetle vertical niche equivalence.

Primary question: what *observed* horizontal separation is associated with the
same family-composition Bray-Curtis dissimilarity as canopy-versus-understorey?

No horizontal distance is reported if an observed within-stratum distance
range / increasing 4-bin dissimilarity trajectory / target intersection is not
present. Even a supported interpolation is descriptive within two forests, not
a conversion of vertical meters into horizontal meters or proof of dispersal.

Uses in-memory station-level community structure from frozen Thai original
DwC-A source and does not export locations, Event IDs or taxon labels.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import statistics
from pathlib import Path

from thai_beetle_vertical_horizontal_beta import (
    UID, API, EXPECTED_SHA, fetch_json, get_archive_endpoint,
    download_small_archive, original_tables, compare, bray_relative,
    haversine_m,
)


def _quantile_sorted(values, q):
    if not values:
        return None
    x=sorted(values)
    i=(len(x)-1)*q
    a=int(i)
    b=min(a+1,len(x)-1)
    return x[a]+(i-a)*(x[b]-x[a])


def quarter_bins(pairs):
    """Four rank-balanced distance bins; source pairs are nonindependent."""
    if len(pairs)<40:
        raise ValueError("fewer_than_40_horizontal_pair_observations")
    ordered=sorted(pairs,key=lambda p:(p[0],p[1]))
    n=len(ordered)
    bins=[]
    for i in range(4):
        part=ordered[(i*n)//4:((i+1)*n)//4]
        if len(part)<6:raise ValueError("insufficient_observations_per_distance_quartile")
        bins.append({
            "horizontal_pair_comparisons_nonindependent":len(part),
            "median_horizontal_distance_m":statistics.median([q[0] for q in part]),
            "mean_family_relative_BrayCurtis":statistics.mean([q[1] for q in part]),
            "min_horizontal_distance_m":min(q[0] for q in part),
            "max_horizontal_distance_m":max(q[0] for q in part)
        })
    return bins


def distance_gate(vertical_mean,bins, *, min_range=0.05):
    """One conditional interpolation, without unsupported extrapolation."""
    x=[float(b["median_horizontal_distance_m"]) for b in bins]
    y=[float(b["mean_family_relative_BrayCurtis"]) for b in bins]
    target=float(vertical_mean)
    output={
        "status":None,
        "interpolated_horizontal_equivalent_m_NOT_vertical_travel_distance":None,
        "horizontal_bin_beta_span":max(y)-min(y),
        "horizontal_quartiles_monotonic_nondecreasing":
            all(y[i+1]>=y[i]-1e-12 for i in range(3)),
        "vertical_target_within_observed_horizontal_quartile_beta_range":
            min(y)-1e-12<=target<=max(y)+1e-12
    }
    if any(not math.isfinite(z) for z in x+y+[target]):
        output["status"]="NONFINITE_INPUT_STOP"
    elif any(x[i+1]<=x[i] for i in range(3)):
        output["status"]="DUPLICATE_OR_NONINCREASING_DISTANCE_QUARTILE"
    elif max(y)-min(y)<min_range:
        output["status"]="HORIZONTAL_BETA_RANGE_TOO_SMALL"
    elif not output["horizontal_quartiles_monotonic_nondecreasing"]:
        output["status"]="NO_MONOTONIC_HORIZONTAL_DISTANCE_DECAY"
    elif not output["vertical_target_within_observed_horizontal_quartile_beta_range"]:
        output["status"]="VERTICAL_BETA_OUTSIDE_HORIZONTAL_SUPPORT"
    else:
        for i in range(3):
            if y[i]-1e-12<=target<=y[i+1]+1e-12:
                if abs(y[i+1]-y[i])<1e-12:
                    output["status"]="EQUIVALENCE_AMBIGUOUS_FLAT_BIN"
                else:
                    fraction=(target-y[i])/(y[i+1]-y[i])
                    output["interpolated_horizontal_equivalent_m_NOT_vertical_travel_distance"]=(
                        x[i]+(x[i+1]-x[i])*fraction)
                    output["status"]="DESCRIPTIVE_WITHIN_OBSERVED_DISTANCE_SUPPORT"
                break
        if output["status"] is None:output["status"]="INTERPOLATION_NOT_RESOLVED"
    return output


def _slope_per100m(pairs):
    n=len(pairs)
    xm=sum(p[0] for p in pairs)/n
    ym=sum(p[1] for p in pairs)/n
    sx=sum((p[0]-xm)**2 for p in pairs)
    if sx<=1e-12:return None
    return 100*sum((p[0]-xm)*(p[1]-ym) for p in pairs)/sx


def analyze(events,occs):
    baseline,internal=compare(events,occs,return_internal=True)
    forests=internal["forest_names"]
    coords=internal["horizontal_coords"]
    families=internal["station_family_counts"]
    observed_horizontal=[]
    strata=[]
    all_v=[]
    all_h=[]
    for f in forests:
        for season in range(2):
            vs=[]
            hs=[]
            for site in range(9):
                b=bray_relative(families[(f,site),season,"canopy"],
                                families[(f,site),season,"understorey"])
                if b is not None:vs.append(b)
            for layer in ("canopy","understorey"):
                for i,j in itertools.combinations(range(9),2):
                    b=bray_relative(families[(f,i),season,layer],
                                    families[(f,j),season,layer])
                    if b is None:continue
                    d=haversine_m(coords[f,layer,i],coords[f,layer,j])
                    hs.append((d,b))
            if len(vs)!=9 or len(hs)<40:
                raise ValueError("original_family_observations_not_sufficient_in_every_stratum")
            bins=quarter_bins(hs)
            gate=distance_gate(statistics.mean(vs),bins)
            strata.append({
                "anonymous_forest":forests.index(f)+1,
                "campaign":season+1,
                "vertical_paired_station_BC_n":len(vs),
                "horizontal_within_layer_pairwise_BC_n_nonindependent":len(hs),
                "vertical_mean_family_relative_BC":statistics.mean(vs),
                "horizontal_mean_family_relative_BC":statistics.mean(p[1] for p in hs),
                "horizontal_distance_min_m":min(p[0] for p in hs),
                "horizontal_distance_median_m":statistics.median(p[0] for p in hs),
                "horizontal_distance_max_m":max(p[0] for p in hs),
                "horizontal_BC_linear_slope_per100m_NOT_INDEPENDENT":_slope_per100m(hs),
                "distance_quartile_bins":bins,
                "horizontal_equivalent_support_gate":gate
            })
            all_v.extend(vs)
            all_h.extend(p[1] for p in hs)
            observed_horizontal.extend(d for d,b in hs)
    pooledv=statistics.mean(all_v)
    pooledh=statistics.mean(all_h)
    assert abs(pooledv-baseline["pooled_vertical_within_station_family_BrayCurtis_mean"])<1e-12
    assert abs(pooledh-baseline["pooled_horizontal_within_stratum_family_BrayCurtis_mean"])<1e-12
    offsets=internal["paired_horizontal_offsets"]
    report={
       "schema":"structural.thai_beetle_horizontal_distance_decay_support_gate.v1",
       "source_frozen_sha256":EXPECTED_SHA,
       "forest_count":len(forests),
       "physical_station_pairs":18,
       "campaign_rounds_per_forest":2,
       "source_beetle_individuals":1622,
       "vertical_BrayCurtis_pooled_mean":pooledv,
       "horizontal_BrayCurtis_pooled_mean":pooledh,
       "horizontal_min_distance_observed_m":min(observed_horizontal),
       "horizontal_median_distance_observed_m":statistics.median(observed_horizontal),
       "horizontal_max_distance_observed_m":max(observed_horizontal),
       "vertical_canopy_understorey_HORIZ_OFFSET_max_m":max(offsets),
       "vertical_HORIZ_offset_within_direct_observed_horizontal_pair_distance_support":
          min(observed_horizontal)<=max(offsets),
       "cells_with_supported_conditional_interpolation":sum(
           s["horizontal_equivalent_support_gate"]["status"]=="DESCRIPTIVE_WITHIN_OBSERVED_DISTANCE_SUPPORT" for s in strata),
       "forest_campaign_results":strata,
       "not_a_vertical_meters_to_horizontal_meters_conversion":True,
       "unobserved_short_horizontal_distance_not_extrapolated":True,
       "source_2024_already_published_vertical_horiz_beta_result":True,
       "pairs_are_nonindependent_within_2_original_forests":True,
       "no_species_level_richness_claim":True,
       "no_causal_mechanism_or_global_generalization_estimated":True,
       "no_raw_coordinates_eventIDs_taxa_exported":True
    }
    return report


def run(out,request=fetch_json,download=download_small_archive):
    original=request(API+UID)
    if str(original.get("key"))!=UID:raise ValueError("GBIF_source_identity_changed")
    license=str(original.get("license") or "").lower()
    if license not in ("cc_by_4_0","http://creativecommons.org/licenses/by/4.0/legalcode",
                       "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("source_license_unknown_stop")
    data=download(get_archive_endpoint(original))
    if hashlib.sha256(data).hexdigest()!=EXPECTED_SHA:
        raise ValueError("frozen_original_archive_version_mismatch")
    events,occ=original_tables(data)
    result=analyze(events,occ)
    dest=Path(out);dest.mkdir(parents=True,exist_ok=True)
    (dest/"thai_distance_decay_support.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.out)
