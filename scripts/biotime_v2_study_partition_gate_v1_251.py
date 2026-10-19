#!/usr/bin/env python3
"""Strict deterministic BioTIME v2 19/76 disjoint study-level response gate."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def validate(split,frame_csv):
    with frame_csv.open(newline="",encoding="utf-8") as f:
        frame=list(csv.DictReader(f))
    if len(frame)!=226:raise ValueError("Not canonical full physical-frame denominator")
    meta={}
    for r in frame:
        study=str(r["STUDY_ID"]).strip()
        if study in meta:raise ValueError("Duplicate study in original frame")
        meta[study]=r
    seed=split.get("seed")
    if seed!="Structural-BioTIME-v2.0-v1_251-preresponse":raise ValueError("Changed split seed")
    qualifying={}
    for r in frame:
        if int(r["sites_at_least_three_observed_years"])>=5 and int(r["same_month_pairs_each_visit_2plus"])>=10:
            qualifying.setdefault(r["REALM"],set()).add(str(r["STUDY_ID"]).strip())
    if sum(map(len,qualifying.values()))!=95:raise ValueError("95 response-free candidate IDs changed")
    selected=[]
    other=[]
    for realm in ("Freshwater","Marine","Terrestrial"):
        entry=split["realms"][realm]
        ids=qualifying.get(realm,set())
        if entry["total"]!=len(ids):raise ValueError("Incorrect eligible realm count")
        order=sorted(ids,key=lambda sid:hashlib.sha256(f"{seed}|{realm}|{sid}".encode()).hexdigest())
        limit=round(.2*len(ids))
        if order[:limit]!=entry["pilot"] or order[limit:]!=entry["holdout"]:
            raise ValueError("Frozen hashed pilot/holdout cohort mismatch")
        selected.extend(entry["pilot"])
        other.extend(entry["holdout"])
    if len(selected)!=19 or len(other)!=76 or set(selected)&set(other):
        raise ValueError("Failed study-level disjointness")
    return selected,other


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--split",required=True,type=Path)
    p.add_argument("--frame",required=True,type=Path)
    p.add_argument("--out-pilot",required=True,type=Path)
    a=p.parse_args()
    pilot,holdout=validate(json.loads(a.split.read_text()),a.frame)
    a.out_pilot.parent.mkdir(parents=True,exist_ok=True)
    with a.out_pilot.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["STUDY_ID"]);w.writerows([[i] for i in pilot])
    print(json.dumps({"pilot_count":len(pilot),"holdout_studies_never_to_query_for_biology":len(holdout),
                      "status":"PILOT_ONLY_AUTHORIZED_BY_RESPONSE_FREE_HISTORICAL_FRAME"},sort_keys=True))


if __name__=="__main__":main()
