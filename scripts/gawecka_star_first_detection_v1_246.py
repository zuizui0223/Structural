#!/usr/bin/env python3
"""v1.246 published Gawecka 2025 star-network experiment detection order audit.

Analysis is postpublication and DESCRIPTIVE. It does not replicate the
published recovery-credit ANOVA, infer actual migrant identities, infer
spatial hydra effects, or promote a Structural confirmatory system.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SOURCE_BLOB="18c1aef8ad894e28cd2b6462bd20f471363bf92e"
SOURCE_META="97b77bfad604dcf27a3372e1195c1a78fd6b0bf0"
SOURCE_COMMIT="483ed8ae80790a3ed0fb806e681fcc3162c1ebe7"
SOURCE_LAYOUT={
    "1C":(1,),
    "1P":(2,),
    "4C":(1,2,3,4),
    "4P":(2,3,4,5)
}
COMMUNITIES=("BRBR","BRBR_LIER","BRBR_LIER_DIRA")
GRAPH={1:(2,3,4,5),2:(1,),3:(1,),4:(1,),5:(1,)}

def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

def distance(start,goal):
    if start not in GRAPH or goal not in GRAPH:
        raise ValueError("Not a patch in the published 5-patch star")
    remaining=[(start,0)]
    seen=set()
    while remaining:
        node,steps=remaining.pop(0)
        if node==goal:return steps
        if node in seen:continue
        seen.add(node)
        remaining.extend((j,steps+1) for j in GRAPH[node] if j not in seen)
    raise ValueError("Disconnected graph")

def nonnegative_int_or_missing(raw):
    value=str(raw or "").strip().strip('"')
    if value.casefold() in ("","na","nan","null"):
        return None
    x=float(value)
    if not math.isfinite(x) or x<0 or x!=int(x):
        raise ValueError("Raw aphid count not a finite nonnegative integer")
    return int(x)

def parse_timestamp(date,time):
    s=f"{date.strip()} {time.strip()}"
    try:
        return datetime.strptime(s,"%d/%m/%Y %H:%M:%S")
    except ValueError:
        # Some original recording rows might use hours/minutes only.
        try:return datetime.strptime(s,"%d/%m/%Y %H:%M")
        except ValueError as e:raise ValueError("Unrecognized source observation date/time") from e

def source_rows(raw):
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    required={"date","time","community","landscape","replica"}|{
       f"patch{i}_BRBR" for i in range(1,6)}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("Original author schema has lost one or more required columns")
    for row in reader:
        if None in row:raise ValueError("Malformed extra CSV fields")
        yield row

def first_detected(series,patch):
    """Series is ordered (datetime, patch counts). Valid baseline is zero.

    A first detected positive from two neighboring observation times
    identifies only a detection interval; no proven local colonization time.
    """
    if not series or series[0][1][patch]!=0:
        raise ValueError("Initial empty patch must have zero observed BB")
    t0=series[0][0]
    last_zero=t0
    missing_before=False
    for date,counts in series[1:]:
        val=counts[patch]
        if val is None:
            missing_before=True
            continue
        if val==0:
            last_zero=date
            continue
        return {"first_positive_day":(date-t0).total_seconds()/86400,
                "last_recorded_zero_day":(last_zero-t0).total_seconds()/86400,
                "missing_prior_samples":missing_before,
                "right_censored":False}
    return {"first_positive_day":None,
            "last_recorded_zero_day":(last_zero-t0).total_seconds()/86400,
            "missing_prior_samples":missing_before,
            "right_censored":True}

def center_and_far_category(centre,far):
    """Evaluate first observed positivity ordering, not animal paths."""
    c=centre["first_positive_day"]
    f=[v["first_positive_day"] for v in far
       if v["first_positive_day"] is not None]
    first_far=min(f) if f else None
    if c is None and first_far is None:
        return "neither_centre_nor_far_detected"
    if c is None:
        return "far_detected_centre_never_detected"
    if first_far is None:
        return "centre_detected_far_never_detected"
    if math.isclose(c,first_far,abs_tol=1e-9):
        return "first_centre_and_far_same_visit"
    if first_far<c:
        return "far_detected_BEFORE_centre_first_positive"
    return "centre_detected_BEFORE_far_first_positive"

def analyze(raw):
    experiment=defaultdict(list)
    excluded_control_rows=0
    source_rows_count=0
    for r in source_rows(raw):
        source_rows_count+=1
        community=(r["community"] or "").strip().strip('"')
        layout=(r["landscape"] or "").strip().strip('"')
        replica=nonnegative_int_or_missing(r["replica"])
        if layout=="5":
            excluded_control_rows+=1
            continue
        if community not in COMMUNITIES or layout not in SOURCE_LAYOUT:
            raise ValueError("Unexpected experimental community or spatial treatment")
        if replica is None or not 1<=replica<=5:
            raise ValueError("Unexpected replicate ID")
        ts=parse_timestamp(r["date"],r["time"])
        counts={i:nonnegative_int_or_missing(r[f"patch{i}_BRBR"])
                for i in range(1,6)}
        experiment[(community,layout,replica)].append((ts,counts))
    expected={(community,layout,rep)
              for community in COMMUNITIES for layout in SOURCE_LAYOUT
              for rep in range(1,6)}
    if set(experiment)!=expected:
        raise ValueError(f"Published 3x4x5 landscape design missing or extra groups: {len(experiment)}")
    patch_records=[]
    landscape_records=[]
    main_categories=Counter()
    main_by_community=defaultdict(Counter)
    per_landscape_sampling=[]
    for key in sorted(experiment):
        community,layout,rep=key
        sequence=sorted(experiment[key],key=lambda item:item[0])
        if len(sequence)<3:
            raise ValueError("Too few repeated source-author observation dates")
        if len({date for date,counts in sequence})!=len(sequence):
            raise ValueError("Duplicated observation date within a landscape")
        introduced=set(SOURCE_LAYOUT[layout])
        empty={p for p in range(1,6) if p not in introduced}
        t0=sequence[0][0]
        for patch in range(1,6):
            val=sequence[0][1][patch]
            if val is None:
                raise ValueError("Source initial sample missing")
            if patch in introduced and val<=0:
                raise ValueError("Original introduced patch missing initial BB")
            if patch in empty and val!=0:
                raise ValueError("Source-labelled empty patch not initially empty")
        per_landscape_sampling.append({
            "community":community,"layout":layout,"replica":rep,
            "n_observation_visits":len(sequence),
            "final_observation_day":(sequence[-1][0]-t0).total_seconds()/86400
        })
        detection={}
        for patch in sorted(empty):
            x=first_detected(sequence,patch)
            nearest=min(distance(patch,s) for s in introduced)
            detection[patch]=x
            patch_records.append({"community":community,"layout":layout,
                "replica":rep,"patch":patch,"distance_to_nearest_initial_source":nearest,
                **x})
        if layout=="1P":
            if introduced!={2} or empty!={1,3,4,5}:
                raise AssertionError("Incorrect one-peripheral initial treatment")
            category=center_and_far_category(
                detection[1],[detection[p] for p in (3,4,5)])
            main_categories[category]+=1
            main_by_community[community][category]+=1
            far_times=[detection[p]["first_positive_day"] for p in (3,4,5)
                       if detection[p]["first_positive_day"] is not None]
            center_time=detection[1]["first_positive_day"]
            first_far=min(far_times) if far_times else None
            landscape_records.append({
                "community":community,"replica":rep,"landscape":"1P",
                "centre_patch1_detection":detection[1],
                "three_distance2_patch_detections":{str(p):detection[p] for p in (3,4,5)},
                "classification":category,
                "earliest_distance2_detection_day":first_far,
                "centre_minus_earliest_distance2_detection_days":
                    center_time-first_far if center_time is not None and first_far is not None else None,
                "first_far_positive_without_earlier_centre_sampled_positive":
                    category in ("far_detected_BEFORE_centre_first_positive",
                                 "far_detected_centre_never_detected")
            })
    if len(landscape_records)!=15 or len(patch_records)!=150:
        raise ValueError("Expected 15 1P landscapes and 150 initially empty patches")
    if sum(main_categories.values())!=15:
        raise ValueError("Some predeclared landscape outcomes not classified")
    d1=[r for r in patch_records if r["distance_to_nearest_initial_source"]==1]
    d2=[r for r in patch_records if r["distance_to_nearest_initial_source"]==2]
    if len(d1)!=105 or len(d2)!=45:
        raise ValueError("Original treatment topology does not match expected distances")
    all_community={
        community:{"landscapes":5,"category_counts":dict(main_by_community[community]),
                   "ever_centre_positive":sum(1 for r in landscape_records
                         if r["community"]==community and
                            r["centre_patch1_detection"]["first_positive_day"] is not None),
                   "ever_any_far_positive":sum(1 for r in landscape_records
                         if r["community"]==community and
                            r["earliest_distance2_detection_day"] is not None)}
        for community in COMMUNITIES}
    return {
        "schema":"structural.gawecka_stepstone_first_detection_v1_246",
        "status":"POSTPUBLICATION_OBSERVED_FIRST_POSITIVE_STAR_GEOMETRY_NOT_TRUE_COLONIZATION",
        "author_repo_source_commit":SOURCE_COMMIT,
        "raw_file_git_blob_sha":SOURCE_BLOB,
        "source_rows_all_including_five_source_controls":source_rows_count,
        "excluded_5_source_control_observation_rows":excluded_control_rows,
        "total_independent_spatial_treatment_landscapes":len(experiment),
        "one_peripheral_source_independent_landscapes":len(landscape_records),
        "original_empty_patch_series_total":len(patch_records),
        "distance1_initially_empty_patch_series":len(d1),
        "distance2_initially_empty_patch_series":len(d2),
        "focal_classification_counts":dict(main_categories),
        "focal_three_community_summary":all_community,
        "per_focal_1P_landscape":landscape_records,
        "all_150_empty_patch_first_positivity_and_censoring":patch_records,
        "all_60_landscape_sampling_effort":per_landscape_sampling,
        "first_distance2_positive_does_not_identify_true_migration_path":True,
        "first_sample_count_zero_does_not_exclude_low_abundance_or_undetected_transit":True,
        "patches_are_nested_in_fifteen_focal_independent_landscapes":True,
        "experiment_author_already_published_effects_on_empty_patch_recovery":True,
        "no_synchronous_local_extinction_or_hydra_intervention":True,
        "no_confirmatory_eligible_Structural_system_added":True,
        "GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("author_checkout",type=Path)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    data=args.author_checkout/"Data"
    metadata=(data/"metadata.txt").read_bytes()
    raw=(data/"experiment_data.csv").read_bytes()
    if git_blob(metadata)!=SOURCE_META or git_blob(raw)!=SOURCE_BLOB:
        raise ValueError("Original published author source identity drift")
    result=analyze(raw)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    overview={
        "schema":result["schema"],"status":result["status"],
        "n_focal_1P":result["one_peripheral_source_independent_landscapes"],
        "empty_distance1_series":result["distance1_initially_empty_patch_series"],
        "empty_distance2_series":result["distance2_initially_empty_patch_series"],
        "focal_categories":result["focal_classification_counts"],
        "by_community":result["focal_three_community_summary"],
        "sampling_range":{
            "visits_min":min(x["n_observation_visits"] for x in result["all_60_landscape_sampling_effort"]),
            "visits_max":max(x["n_observation_visits"] for x in result["all_60_landscape_sampling_effort"]),
            "last_day_min":min(x["final_observation_day"] for x in result["all_60_landscape_sampling_effort"]),
            "last_day_max":max(x["final_observation_day"] for x in result["all_60_landscape_sampling_effort"])
        }
    }
    print(json.dumps(overview,sort_keys=True))
if __name__=="__main__":
    main()
