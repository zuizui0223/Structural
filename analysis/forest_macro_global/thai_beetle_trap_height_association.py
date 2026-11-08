#!/usr/bin/env python3
"""Exploratory, within-forest trap HEIGHT vs vertical beetle capture asymmetry.

Primary (one post-result question): across 18 station-paired traps in two Thai
forests, does canopy-trap height relate to the season-averaged log
((canopy_count+0.5)/(understorey_count+0.5))? The data are original 2019–2020
SLAM beetles and actual measured Event trap heights, not thermal logger data.

Forest-mean-centered slope per 10m, 9999 within-forest station-height
permutations, and within-forest station bootstrap; preserve two seasonal
replicates as one station outcome. This is *not* a forest-level replicated,
climate-escape, causal canopy-height, or previously unseen confirmation.
"""
from __future__ import annotations

import argparse,datetime,hashlib,json,math,random,statistics
from collections import Counter,defaultdict
from pathlib import Path

from thai_beetle_vertical_horizontal_beta import (
    UID,API,EXPECTED_SHA,fetch_json,get_archive_endpoint,download_small_archive,
    original_tables,compare,protocol_category,campaigns
)
from thai_beetle_thermal_height_gate import (
    extract_named_numeric,CANOPY_HEIGHT_NAMES
)


def numeric_trap_height(e):
    val=[]
    for field in ("dynamicProperties","eventRemarks","locationRemarks"):
        for k,v in extract_named_numeric(e.get(field)):
            if k in CANOPY_HEIGHT_NAMES:
                val.append(float(v))
    distinct={round(v,3) for v in val}
    if len(distinct)!=1:
        raise ValueError("original_trap_height_missing_or_conflicting")
    h=next(iter(distinct))
    if not 1<=h<=60:
        raise ValueError("original_trap_height_outside_physical_range")
    return h


def forest_centered_slope_10m(stations):
    """One station = season mean; study forest fixed effects removed exactly."""
    byf=defaultdict(list)
    for row in stations:
        byf[row["forest"]].append(row)
    if len(byf)!=2 or sorted(len(v) for v in byf.values())!=[9,9]:
        raise ValueError("two_forests_of_nine_physical_stations_required")
    covariance=0.
    denom=0.
    for rr in byf.values():
        xbar=statistics.mean(t["height_m"] for t in rr)
        ybar=statistics.mean(t["log_canopy_over_lower"] for t in rr)
        covariance+=sum((t["height_m"]-xbar)*(t["log_canopy_over_lower"]-ybar) for t in rr)
        denom+=sum((t["height_m"]-xbar)**2 for t in rr)
    if denom<1e-10:raise ValueError("insufficient_within_forest_trap_height_variation")
    return 10*covariance/denom


def inference(stations, seed=20261108, permutations=9999, bootstraps=5000):
    slope=forest_centered_slope_10m(stations)
    byf={f:[dict(v) for v in stations if v["forest"]==f]
         for f in sorted({v["forest"] for v in stations})}
    r=random.Random(seed)
    count=0
    for rep in range(permutations):
        sampled=[]
        for forest,rr in byf.items():
            heights=[v["height_m"] for v in rr]
            r.shuffle(heights)
            sampled.extend(dict(v,height_m=h) for v,h in zip(rr,heights))
        permuted=forest_centered_slope_10m(sampled)
        if abs(permuted)>=abs(slope)-1e-12:count+=1
    boots=[]
    for _ in range(bootstraps):
        sampled=[]
        for rr in byf.values():
            sampled.extend(dict(rr[r.randrange(9)]) for i in range(9))
        try:boots.append(forest_centered_slope_10m(sampled))
        except ValueError:continue
    if len(boots)<0.95*bootstraps:
        raise ValueError("too_many_bootstrap_singular_height_samples")
    boots.sort()
    lo=boots[int(.025*(len(boots)-1))]
    hi=boots[int(.975*(len(boots)-1))]
    loo=[]
    for i in range(len(stations)):
        remaining=[q for k,q in enumerate(stations) if k!=i]
        # Forest-size gate is for original prebootstrap cohort only.
        mf=defaultdict(list)
        for t in remaining:mf[t["forest"]].append(t)
        num=denom=0.
        for group in mf.values():
            xm=statistics.mean(t["height_m"] for t in group)
            ym=statistics.mean(t["log_canopy_over_lower"] for t in group)
            num+=sum((t["height_m"]-xm)*(t["log_canopy_over_lower"]-ym) for t in group)
            denom+=sum((t["height_m"]-xm)**2 for t in group)
        loo.append(10*num/denom if denom>1e-10 else None)
    return {
        "within_forest_centered_log_ratio_slope_per_10m":slope,
        "canopy_capture_ratio_multiplier_per_10m_descriptive":math.exp(slope),
        "two_sided_station_height_permutation_p_within_2_forests":(count+1)/(permutations+1),
        "within_forest_station_bootstrap_95CI_log_ratio_slope_per_10m":[lo,hi],
        "leave_one_station_out_same_sign_count":sum(
            v is not None and (v==0 and slope==0 or v*slope>0) for v in loo),
        "leave_one_station_out_n":len(loo),
        "permutation_reps":permutations,
        "bootstrap_reps":len(boots)
    }


def study(events,occ, *, return_season_level=False):
    _,intern=compare(events,occ,return_internal=True)
    forests=intern["forest_names"]
    coords=intern["horizontal_coords"]
    index={ (f,layer,coord):i for (f,layer,i),coord in coords.items() }
    sampling=[e for e in events if protocol_category(e["samplingProtocol"])[0]=="SLAM"]
    if len(sampling)!=144:raise ValueError("original_SLAM_number_mismatch")
    dates={}
    for f in forests:
        c,grp=campaigns([e["eventDate"] for e in sampling if e["locationID"]==f])
        if len(grp)!=2:raise ValueError("original_campaign_mismatch")
        for phase,mapping in enumerate(c):
            for d in mapping:dates[f,d]=phase
    core={}
    heights=defaultdict(list)
    effort=defaultdict(Counter)
    methods=Counter()
    for e in sampling:
        f=e["locationID"]
        _,layer=protocol_category(e["samplingProtocol"])
        lat=round(float(e["decimalLatitude"]),6)
        lon=round(float(e["decimalLongitude"]),6)
        ksite=index.get((f,layer,(lat,lon)))
        day=datetime.date.fromisoformat(e["eventDate"][:10])
        ph=dates.get((f,day))
        if ksite is None or ph is None:
            raise ValueError("height_or_occurrence_not_joined_to_station_campaign")
        key=(f,ksite,ph,layer)
        cid=e["_core_id"]
        if cid in core:raise ValueError("original_duplicate_core_Event")
        core[cid]=key
        methods[key]+=1
        heights[key].append(numeric_trap_height(e))
        effort[layer][(e["sampleSizeUnit"],e["sampleSizeValue"],e["samplingEffort"])]+=1
    if effort["canopy"]!=effort["understorey"]:
        raise ValueError("effort_unequal_across_canopy_understory")
    if len(methods)!=72 or any(n!=2 for n in methods.values()):
        raise ValueError("expected_2_jars_in_all_72_station_campaign_layer_deployments")
    per_layer_height={}
    for key,val in heights.items():
        if len(val)!=2:raise ValueError("height_missing_on_jar_pair")
        if max(val)-min(val)>2.0:
            raise ValueError("height_disagreement_between_top_bottom_jars")
        per_layer_height[key]=statistics.mean(val)
        if key[3]=="understorey" and abs(per_layer_height[key]-2)>0.2:
            raise ValueError("understory_expected_2m_source_protocol")
    counts=Counter()
    for row in occ:
        k=core.get(row["_core_id"])
        if k is None:raise ValueError("unexpected_non_SLAM_beetle_observation")
        n=float(row["individualCount"])
        if not math.isfinite(n) or n<1 or not n.is_integer():
            raise ValueError("invalid_source_beetle_count")
        counts[k]+=int(n)
    out=[]
    season_rows=[]
    for f in forests:
        for site in range(9):
            cs=[];us=[];hs=[]
            for phase in range(2):
                ck=(f,site,phase,"canopy");uk=(f,site,phase,"understorey")
                if ck not in per_layer_height or uk not in per_layer_height:
                    raise ValueError("site_does_not_have_both_strata_and_seasons")
                c,u=counts[ck],counts[uk]
                cs.append(c);us.append(u)
                hs.append(per_layer_height[ck])
                season_rows.append({
                    "forest":f,"station":site,"campaign":phase,
                    "height_m":per_layer_height[ck],
                    "log_canopy_over_understorey":math.log((c+.5)/(u+.5)),
                    "canopy_individuals":c,"understorey_individuals":u
                })
            h=statistics.mean(hs)
            if max(hs)-min(hs)>4 and not return_season_level:
                raise ValueError("same_station_canopy_trap_height_changed_gt4m_across_seasons")
            out.append({
                "forest":f,
                "height_m":h,
                "season_averaged_height_m":h,
                "log_canopy_over_lower":statistics.mean(
                    math.log((c+.5)/(u+.5)) for c,u in zip(cs,us)),
                "canopy_total_two_seasons":sum(cs),
                "lower_total_two_seasons":sum(us)
            })
    if sum(r["canopy_total_two_seasons"]+r["lower_total_two_seasons"] for r in out)!=1622:
        raise ValueError("exact_original_beetle_count_not_reproduced")
    if return_season_level:
        return season_rows  # In-memory original station IDs only; never exported directly.
    calculated=inference(out)
    byf=defaultdict(list)
    for q in out:byf[q["forest"]].append(q)
    forest_summary=[]
    for f in forests:
        rr=byf[f]
        h=[x["height_m"] for x in rr]
        forest_summary.append({
            "anonymous_forest":forests.index(f)+1,
            "physical_station_count":len(rr),
            "canopy_trap_height_min_m":min(h),
            "canopy_trap_height_median_m":statistics.median(h),
            "canopy_trap_height_max_m":max(h),
            "canopy_beetles":sum(q["canopy_total_two_seasons"] for q in rr),
            "understorey_beetles":sum(q["lower_total_two_seasons"] for q in rr),
            "mean_paired_season_log_ratio":statistics.mean(q["log_canopy_over_lower"] for q in rr)
        })
    return {
        "schema":"structural.thai_beetle_trap_height_vs_capture_vertical_asymmetry.v1",
        "source_archive_sha256":EXPECTED_SHA,
        "original_forest_n":2,
        "physical_stations_n":len(out),
        "campaigns_per_station":2,
        "source_original_SLAM_jar_events":len(sampling),
        "source_original_beetle_individuals":1622,
        "source_canopy_trap_height_m_min":min(q["height_m"] for q in out),
        "source_canopy_trap_height_m_max":max(q["height_m"] for q in out),
        "source_canopy_trap_height_m_median":statistics.median(q["height_m"] for q in out),
        "understory_trap_height_m":2.0,
        "per_forest_descriptive":forest_summary,
        "association_estimate":calculated,
        "based_on_post_result_exploratory_question":True,
        "trapping_height_not_equivalent_to_tree_height_or_canopy_coverage":True,
        "temperature_and_light_logger_time_series_not_used":True,
        "not_evidence_of_thermal_escape_behavior_or_warming_response":True,
        "no_global_replicate_or_causal_claim":True,
        "raw_station_forest_identifiers_and_coordinates_not_exported":True
    }


def run(out,request=fetch_json,download=download_small_archive):
    original=request(API+UID)
    if str(original.get("key"))!=UID:raise ValueError("original_source_UUID_changed")
    license=str(original.get("license") or "").lower()
    if license not in ("cc_by_4_0","http://creativecommons.org/licenses/by/4.0/legalcode",
                       "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("original_source_license_changed")
    data=download(get_archive_endpoint(original))
    if hashlib.sha256(data).hexdigest()!=EXPECTED_SHA:
        raise ValueError("original_Thai_archive_hash_changed")
    event,occ=original_tables(data)
    result=study(event,occ)
    dst=Path(out);dst.mkdir(parents=True,exist_ok=True)
    (dst/"thai_beetle_height_vs_vertical_capture_ratio.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    opts=parser.parse_args()
    run(opts.out)
