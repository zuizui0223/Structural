#!/usr/bin/env python3
"""v1.223: retrospective Hopson predator zero-spell/redetection duration audit.

No ecological colonization, extinction or movement inference; no treatment p values.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from hopson_temporal_detection_audit_v1_222 import (
    download_locked, layout_index, rows_locked, OBS_HEADER, optional_count, intish
)

def spells_for_jar(visits):
    """Return runs ending in positive detection, right-censored, or broken by missingness."""
    if not visits:
        raise ValueError("No visits")
    visits=sorted(visits,key=lambda x:x[0])
    if len({x[0] for x in visits})!=len(visits):
        raise ValueError("Duplicate visit day")
    completed=[]
    right_censored=0
    interrupted=0
    zero_start=None
    start_prev_positive=False
    previous_positive_day=None
    for i,(day,positive) in enumerate(visits):
        if positive is None:
            if zero_start is not None:interrupted+=1
            zero_start=None
            previous_positive_day=None
            continue
        if positive == 0:
            if zero_start is None:
                zero_start=i
                start_prev_positive=(previous_positive_day is not None)
            continue
        if positive != 1:
            raise ValueError("must be binary detection or missing")
        if zero_start is not None:
            spell=visits[zero_start:i]
            if not spell or any(x[1]!=0 for x in spell):
                raise ValueError("Malformed zero spell")
            completed.append({
                "zero_count":len(spell),
                "left_censored":not start_prev_positive,
                "days_from_last_zero_to_redetection":day-spell[-1][0],
                "days_from_last_positive_to_redetection":(
                    day-previous_positive_day if start_prev_positive else None
                )
            })
            zero_start=None
        previous_positive_day=day
    if zero_start is not None:right_censored+=1
    return completed,right_censored,interrupted

def parse_by_jar(raw,layout):
    byjar=defaultdict(list)
    for r in rows_locked(raw,OBS_HEADER):
        jar=intish(r["jar.no"],"jar")
        if jar not in layout: raise ValueError("Unexpected jar identifier")
        day=intish(r["day"],"day")
        v=float(r["samp.vol"])
        if not(v>0): positive=None
        else:
            count=optional_count(r["eupl"],"eupl")
            positive=None if count is None else int(count>0)
        byjar[jar].append((day,positive))
    if set(byjar)!=set(layout):raise ValueError("Some jar series absent")
    return byjar

def compute(obs,lay):
    layout=layout_index(lay)
    byjar=parse_by_jar(obs,layout)
    groups=defaultdict(lambda:Counter())
    totals=Counter()
    metapop_counts=defaultdict(Counter)
    duration_counts=Counter()
    for jar,visits in byjar.items():
        meta,patch,trt,block=layout[jar];key=f"block_{block}_{trt}"
        episodes,censored,interrupted=spells_for_jar(visits)
        for episode in episodes:
            length=episode["zero_count"]
            if episode["left_censored"]:
                category="left_censored_start_before_first_recorded_positive"
            elif length==1:
                category="one_zero_between_two_positive_visits"
            elif length==2:
                category="two_zeros_between_positive_visits"
            else:
                category="three_or_more_zeros_between_positive_visits"
            groups[key][category]+=1
            totals[category]+=1
            metapop_counts[str(meta)][category]+=1
            duration_counts[str(episode["days_from_last_zero_to_redetection"])]+=1
        for key_count,value in [
            ("zero_runs_right_censored_at_final_visit",censored),
            ("zero_runs_interrupted_by_missing_measurement",interrupted)
        ]:
            groups[key][key_count]+=value
            totals[key_count]+=value
        groups[key]["jar_series"]+=1
        totals["jar_series"]+=1
    categories=[
        "one_zero_between_two_positive_visits",
        "two_zeros_between_positive_visits",
        "three_or_more_zeros_between_positive_visits",
        "left_censored_start_before_first_recorded_positive"
    ]
    total_redetection=sum(totals[k] for k in categories)
    if total_redetection!=554:
        raise ValueError("Pinned v1.222 554 redetections do not reconcile")
    return {
        "schema":"structural.hopson_zero_spell_descriptive.v1_223",
        "status":"RETROSPECTIVE_EXPOSED_OUTCOMES_ZERO_SPELLS_NOT_COLONIZATION",
        "original_v222_redetections":554,
        "redetections_recomputed":total_redetection,
        "categories":{k:totals[k] for k in categories},
        "zero_runs_right_censored_at_final_visit":totals["zero_runs_right_censored_at_final_visit"],
        "zero_runs_interrupted_by_missing_measurement":totals["zero_runs_interrupted_by_missing_measurement"],
        "per_block_treatment":{key:dict(groups[key]) for key in sorted(groups)},
        "per_independent_metapopulation":{key:dict(metapop_counts[key]) for key in sorted(metapop_counts,key=int)},
        "days_last_zero_to_redetection":dict(sorted(duration_counts.items(),key=lambda x:int(x[0]))),
        "sampling_unit":"210 nested jars × 23 sampling times in 14 independent metapopulations",
        "zero_run_length_is_not_certified_local_extinction_duration":True,
        "one_zero_event_is_not_proven_false_negative":True,
        "long_zero_run_is_not_proven_local_extirpation":True,
        "any_redetection_is_not_proven_recolonization":True,
        "no_movement_operator_or_donor_to_target_trajectory_measured":True,
        "postoutcome_after_v222_response_exposure":True,
        "no_treatment_contrast_test":True,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=compute(download_locked("observations"),download_locked("layout"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
