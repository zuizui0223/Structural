#!/usr/bin/env python3
"""Validate committed aggregate-only BioTIME pilot counts without biological response access."""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

COUNTS=("n00","n01","n10","n11","n01_2plus","n10_2plus")
TIERS=("1","2","3-4",">=5")

def audit(group_csv: Path, freeze_json: Path, split_json:Path):
    freeze=json.loads(freeze_json.read_text(encoding="utf-8"))
    split=json.loads(split_json.read_text(encoding="utf-8"))
    with group_csv.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    if freeze.get("schema")!="structural.biotime_v2_burned_pilot_aggregate_freeze.v1_252" or len(rows)!=54:
        raise ValueError("Original 54-row v1.252 aggregate proof surface changed")
    allowed=set(freeze["strict_method_quality"]["nonzero_eligible_study_ids"])
    pilot=set()
    by_study_realm={}
    for realm,item in split["realms"].items():
        for id in item["pilot"]:
            pilot.add(id);by_study_realm[id]=realm
    if len(pilot)!=19 or not allowed<=pilot:
        raise ValueError("Pilot split or response-qualified study membership changed")
    seen=set();study=defaultdict(lambda:defaultdict(dict));group=defaultdict(lambda:{x:0 for x in COUNTS})
    total={x:0 for x in COUNTS};realm_sum=defaultdict(lambda:{x:0 for x in COUNTS})
    for r in rows:
        sid=r["study"]; tier=r["source_group"]; key=(sid,tier)
        if sid not in allowed or tier not in TIERS or key in seen:
            raise ValueError("Invalid/duplicate study×source-count cell")
        seen.add(key)
        vals={k:int(r[k]) for k in COUNTS}
        if any(v<0 for v in vals.values()) or vals["n01_2plus"]>vals["n01"] or vals["n10_2plus"]>vals["n10"]:
            raise ValueError("Negative count or impossible replicated detection subset")
        study[sid][tier]=vals
        for k,v in vals.items():
            group[tier][k]+=v;total[k]+=v;realm_sum[by_study_realm[sid]][k]+=v
    if set(study)!=allowed:
        raise ValueError("Nonzero study identity mismatch")
    for k in COUNTS:
        if total[k]!=freeze["overall"][k]:
            raise ValueError("Frozen overall transition totals mismatch")
    for expected in freeze["source_count_groups"]:
        # The original per-tier freeze only reported n01_2plus, not n10_2plus.
        # Do not invent missing per-tier historical reference values; the overall
        # n10_2plus still has an authoritative frozen total.
        for k in ("n00","n01","n10","n11","n01_2plus"):
            if group[expected["sources"]][k]!=expected[k]:
                raise ValueError("Original source-tier total changed: "+expected["sources"]+" "+k)
    for expected in freeze["by_realm"]:
        for k in ("n00","n01","n10","n11"):
            if realm_sum[expected["realm"]][k]!=expected[k]:
                raise ValueError("Original realm total changed: "+expected["realm"]+" "+k)
    if sum(total[k] for k in ("n00","n01","n10","n11"))!=freeze["overall"]["eligible_species_pair_cells"]:
        raise ValueError("Grand denominator no longer reconciles")
    direction=[]
    for sid,v in study.items():
        if not all(t in v for t in ("1",">=5")):
            raise ValueError("Study missing a 1 or 5+ source tier: "+sid)
        a=v["1"]; b=v[">=5"]; n1=a["n00"]+a["n01"];n5=b["n00"]+b["n01"]
        if not n1 or not n5: raise ValueError("Cannot compare zero-denominator source bins")
        d=b["n01"]/n5-a["n01"]/n1
        d_rep=b["n01_2plus"]/n5-a["n01_2plus"]/n1
        direction.append({"study":sid,"difference":d,"difference_repeated":d_rep})
    signs=[sum(1 for q in direction if q[key]>0) for key in ("difference","difference_repeated")]
    ties=[sum(1 for q in direction if q[key]==0) for key in ("difference","difference_repeated")]
    negatives=[sum(1 for q in direction if q[key]<0) for key in ("difference","difference_repeated")]
    if signs!=[13,13] or ties!=[1,1] or negatives!=[0,0]:
        raise ValueError("Frozen within-study directional summary changed")
    by_study_01=sorted(((sid,sum(row["n01"] for row in records.values())) for sid,records in study.items()), key=lambda p:-p[1])
    if by_study_01[:3]!=[("110",2979),("693",1086),("377",605)]:
        raise ValueError("Study contribution concentration changed")
    return {
        "schema":"structural.biotime_pilot_response_free_aggregate_replay.v1_252",
        "aggregate_comparisons":sum(total[k] for k in ("n00","n01","n10","n11")),
        "net_pilot_studies":len(study),
        "heldout_taxon_queries":0,
        "zero_to_one_detected":total["n01"],
        "zero_to_one_2plus":total["n01_2plus"],
        "source_5plus_higher_rate_studies":signs[0],
        "source_5plus_equal_rate_studies":ties[0],
        "source_5plus_lower_rate_studies":negatives[0],
        "source_5plus_repeated_higher_studies":signs[1],
        "largest_studies_01":by_study_01[:3],
        "C_minus_CAL_not_scored":True,
        "causal_colonization_not_established":True
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--groups",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--split",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(audit(args.groups,args.freeze,args.split),indent=2,sort_keys=True))
if __name__=="__main__":main()
