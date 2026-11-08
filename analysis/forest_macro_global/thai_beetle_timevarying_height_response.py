#!/usr/bin/env python3
"""Time-varying canopy-trap HEIGHT and beetle relative capture in two Thai forests.

Exploratory reanalysis only. Original 18 stations × 2 campaigns; 144 paired
SLAM jars and 1,622 beetles. Station height shifts between campaigns, so use
actual campaign height rather than quietly averaging a constant station height.

Predictor: trap height in m. Outcome: log((canopy + .5)/(understory + .5)).
Four forest×campaign fixed intercepts; height slope per 10 m. Preserve a
TWO-SEASON station height trajectory in 9,999 within-forest permutations and
5,000 within-forest station cluster bootstraps. No independent biome or
temperature-escape inference; no original site ID/coordinates exported.
"""
from __future__ import annotations

import argparse,hashlib,json,math,random,statistics
from collections import defaultdict
from pathlib import Path
from thai_beetle_trap_height_association import (
    UID,API,EXPECTED_SHA,fetch_json,get_archive_endpoint,download_small_archive,
    original_tables,study
)


def valid_design(rows, exact=True):
    groups=defaultdict(set)
    for row in rows:
        if not math.isfinite(row["height_m"]) or not math.isfinite(row["log_canopy_over_understorey"]):
            raise ValueError("nonfinite_original_station_campaign_variable")
        groups[(row["forest"],row["campaign"])].add(row["station"])
    forests={f for f,p in groups}
    if len(forests)!=2 or len(groups)!=4:raise ValueError("need_two_forests_two_campaigns")
    if exact:
        if any(len(s)!=9 for s in groups.values()) or len(rows)!=36:
            raise ValueError("original_18_physical_stations_x_two_campaigns_required")
        for f in forests:
            if groups[f,0]!=groups[f,1]:
                raise ValueError("missing_repeated_physical_station_between_campaigns")
    if len(rows)!=sum(len(v) for v in groups.values()):
        raise ValueError("duplicate_original_station_campaign")
    return groups


def centered_slope(rows, exact=False):
    valid_design(rows,exact=exact)
    strata=defaultdict(list)
    for r in rows:strata[r["forest"],r["campaign"]].append(r)
    numerator=denom=0.
    for rr in strata.values():
        xm=statistics.mean(x["height_m"] for x in rr)
        ym=statistics.mean(x["log_canopy_over_understorey"] for x in rr)
        numerator+=sum((x["height_m"]-xm)*(x["log_canopy_over_understorey"]-ym) for x in rr)
        denom+=sum((x["height_m"]-xm)**2 for x in rr)
    if denom<1e-10:raise ValueError("within_forest_campaign_height_range_nonestimable")
    return 10*numerator/denom


def inference(rows, *, seed=20261108, permutations=9999, bootstraps=5000):
    valid_design(rows,exact=True)
    byf=defaultdict(dict)
    for row in rows:
        key=row["station"]
        byf[row["forest"]].setdefault(key,{})[row["campaign"]]=row
    if any(len(d)!=9 or any(set(r)!={0,1} for r in d.values()) for d in byf.values()):
        raise ValueError("station_height_trajectory_missing_campaign")
    base=centered_slope(rows,exact=True)
    rng=random.Random(seed)
    extrema=0
    for rep in range(permutations):
        permuted=[]
        for f,d in sorted(byf.items()):
            sites=sorted(d)
            donors=sites.copy()
            rng.shuffle(donors)
            for dst,src in zip(sites,donors):
                for phase in (0,1):
                    rec=dict(d[dst][phase])
                    rec["height_m"]=d[src][phase]["height_m"]
                    permuted.append(rec)
        slope=centered_slope(permuted)
        if abs(slope)>=abs(base)-1e-12:extrema+=1
    bootstrap=[]
    for _ in range(bootstraps):
        sampled=[]
        for f,d in sorted(byf.items()):
            keys=sorted(d)
            for i in range(9):
                picked=keys[rng.randrange(9)]
                for phase in (0,1):
                    rec=dict(d[picked][phase])
                    # Resampled station labels are not source IDs.
                    rec["station"]=i
                    sampled.append(rec)
        try:bootstrap.append(centered_slope(sampled))
        except ValueError:continue
    if len(bootstrap)<.95*bootstraps:
        raise ValueError("too_many_singular_station_bootstrap_draws")
    bootstrap.sort()
    lo=bootstrap[int(.025*(len(bootstrap)-1))]
    hi=bootstrap[int(.975*(len(bootstrap)-1))]
    per_stratum=[]
    for f in sorted(byf):
        for phase in (0,1):
            r=[x for x in rows if x["forest"]==f and x["campaign"]==phase]
            xm=statistics.mean(x["height_m"] for x in r)
            ym=statistics.mean(x["log_canopy_over_understorey"] for x in r)
            denom=sum((x["height_m"]-xm)**2 for x in r)
            sl=10*sum((x["height_m"]-xm)*(x["log_canopy_over_understorey"]-ym) for x in r)/denom if denom>1e-10 else None
            per_stratum.append({
                "anonymous_forest":sorted(byf).index(f)+1,
                "campaign":phase+1,
                "physical_station_count":len(r),
                "height_min_m":min(x["height_m"] for x in r),
                "height_max_m":max(x["height_m"] for x in r),
                "within_cell_log_capture_ratio_slope_per10m":sl
            })
    loo=[]
    for f in sorted(byf):
        for k in sorted(byf[f]):
            remaining=[r for r in rows if not (r["forest"]==f and r["station"]==k)]
            try:loo.append(centered_slope(remaining))
            except ValueError:loo.append(None)
    return {
        "forest_campaign_centered_log_capture_ratio_slope_per10m":base,
        "canopy_vs_understorey_capture_ratio_multiplier_per10m_descriptive":math.exp(base),
        "two_sided_site_trajectory_permutation_p_conditional_on_two_forests":(extrema+1)/(permutations+1),
        "within_forest_station_trajectory_bootstrap_95CI_log_ratio_per10m":[lo,hi],
        "LOO_site_exclusions_retaining_same_slope_sign":sum(
            x is not None and x*base>0 for x in loo),
        "LOO_physical_site_exclusions_n":len(loo),
        "forest_campaign_slopes":per_stratum,
        "permutation_replicates":permutations,
        "bootstrap_effective_replicates":len(bootstrap),
        "within_study_site_trajectory_permutations_preserve_both_seasons":True
    }


def analyze(events,occs):
    rows=study(events,occs,return_season_level=True)
    if len(rows)!=36 or sum(r["canopy_individuals"]+r["understorey_individuals"] for r in rows)!=1622:
        raise ValueError("original_complete_slAM_36_pair_record_count_wrong")
    result=inference(rows)
    return {
        "schema":"structural.thai_beetle_actual_timevarying_height_by_campaign.v1",
        "source_original_sha256":EXPECTED_SHA,
        "original_independent_forest_n":2,
        "original_physical_station_n":18,
        "original_station_campaign_pairs":36,
        "original_beetle_individuals":1622,
        "measured_canopy_trap_height_min_m":min(r["height_m"] for r in rows),
        "measured_canopy_trap_height_max_m":max(r["height_m"] for r in rows),
        "forest_and_campaign_fixed_intercepts":True,
        "all_original_stations_included_including_height_movers":True,
        "height_is_actual_trap_location_not_tree_size":True,
        "result":result,
        "posthoc_exploratory_after_station_fixed_height_STOP":True,
        "site_height_trajectory_exchangeability_is_assumption":True,
        "same_stations_in_two_seasons_not_two_independent_samples":True,
        "no_HOBO_temperature_or_light_timeseries_in_the_model":True,
        "not_test_of_thermal_refuge_or_climate_warming":True,
        "not_causal_effect_of_canopy_height":True,
        "not_an_independent_cross_forest_macro_replication":True,
        "raw_coordinates_tree_station_event_ids_not_exported":True
    }


def run(out,request=fetch_json,download=download_small_archive):
    d=request(API+UID)
    if str(d.get("key"))!=UID:raise ValueError("original_dataset_uuid_changed")
    license=str(d.get("license") or "").lower()
    if license not in ("cc_by_4_0","http://creativecommons.org/licenses/by/4.0/legalcode",
                       "https://creativecommons.org/licenses/by/4.0/legalcode"):
        raise ValueError("original_licence_status_changed")
    payload=download(get_archive_endpoint(d))
    if hashlib.sha256(payload).hexdigest()!=EXPECTED_SHA:
        raise ValueError("original_archive_sha256_mismatch")
    events,occ=original_tables(payload)
    report=analyze(events,occ)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"thai_beetle_time_varying_trap_height_association.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    opt=parser.parse_args()
    run(opt.out)
