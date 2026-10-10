#!/usr/bin/env python3
"""v1.212 strictly posthoc robustness audit excluding ambiguous treatment row.

Works on immutable 2022 Wolfe author CSV. Does not reassign source metadata.
Only terminal-day exploratory guild outcome is evaluated. Not confirmatory.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path

EXPECTED_BLOB = "e78003d425b646b390ae02e36c007892c1c70926"
EXPECTED_BYTES = 12096
AMBIGUOUS_ROW = "6HoLM1"
CONFIG = {(1,"homogeneous"),(4,"homogeneous"),(4,"heterogeneous"),(6,"homogeneous"),(6,"heterogeneous")}
LEVELS = ("none","low","high")
STRATA = [(n,m,c) for n in (4,6) for m in LEVELS for c in LEVELS]

def load_source(raw):
    if len(raw)!=EXPECTED_BYTES:
        raise ValueError("Source length changed")
    blob = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
    if blob!=EXPECTED_BLOB:
        raise ValueError("Frozen source blob changed")
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required={"", "microcosm","replicate","patch_number","heterogeneity",
        "matrix_dispersal","corridor_dispersal","stentor_coeruleus",
        "didinium_nasutum","dileptus_anser"}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("Missing source columns")
    rows=list(reader)
    if len(rows)!=176:
        raise ValueError("Expected 176 original observations")
    rejected=[r for r in rows if r[""]==AMBIGUOUS_ROW]
    if len(rejected)!=1:
        raise ValueError("Ambiguous unit is missing or duplicated")
    a=rejected[0]
    if (a["microcosm"]!="6HoLM" or a["replicate"]!="1" or
        a["patch_number"]!="6" or a["heterogeneity"]!="homogeneous" or
        a["matrix_dispersal"]!="none" or a["corridor_dispersal"]!="none"):
        raise ValueError("Metadata discrepancy changed")
    seen=set()
    groups=defaultdict(list)
    for r in rows:
        identity=(r["microcosm"],r["replicate"])
        if identity in seen or not all(identity):
            raise ValueError("Invalid microcosm/replicate ID")
        seen.add(identity)
        if r[""]==AMBIGUOUS_ROW:
            continue  # Never decode the excluded unit's predator densities.
        n=int(r["patch_number"])
        het=r["heterogeneity"].strip().lower()
        mat=r["matrix_dispersal"].strip().lower()
        cor=r["corridor_dispersal"].strip().lower()
        if (n,het) not in CONFIG or mat not in LEVELS or cor not in LEVELS:
            raise ValueError("Unknown factorial unit")
        def p(k):
            value=float(r[k])
            if not math.isfinite(value) or value<0:
                raise ValueError("Invalid focal density")
            return int(value>0)
        gen=p("stentor_coeruleus")
        spec=int(bool(p("didinium_nasutum") or p("dileptus_anser")))
        groups[(n,het,mat,cor)].append((gen,spec,gen*spec))
    expected={(n,h,m,c) for n,h in CONFIG for m in LEVELS for c in LEVELS}
    lengths=sorted(map(len,groups.values()))
    if (set(groups)!=expected or sum(map(len,groups.values()))!=175 or
        lengths.count(3)!=5 or lengths.count(4)!=40 or len(lengths)!=45):
        raise ValueError("Unexpected 175-unit retained cell geometry")
    if any(len(groups[(1,"homogeneous",m,c)])!=4 for m in LEVELS for c in LEVELS):
        raise ValueError("Unexpected single-patch missingness")
    return groups

def summary(groups, index):
    contrasts=[]
    for n,m,c in STRATA:
        a=groups[(n,"heterogeneous",m,c)]
        b=groups[(n,"homogeneous",m,c)]
        sa=sum(v[index] for v in a)
        sb=sum(v[index] for v in b)
        contrasts.append({
            "patch_count":n,
            "observed":sa/len(a)-sb/len(b),
            "missing_lower":sa/4-(sb+(4-len(b)))/4,
            "missing_upper":(sa+(4-len(a)))/4-sb/4,
            "missing_count":8-len(a)-len(b)
        })
    def avg(which,rows):
        return sum(row[which] for row in rows)/len(rows)
    out={
        "observed_only":avg("observed",contrasts),
        "lower":avg("missing_lower",contrasts),
        "upper":avg("missing_upper",contrasts),
        "missing_in_4_6":sum(x["missing_count"] for x in contrasts),
    }
    for n in (4,6):
        subset=[x for x in contrasts if x["patch_count"]==n]
        out["patches_"+str(n)]={
            "observed_only":avg("observed",subset),
            "lower":avg("missing_lower",subset),
            "upper":avg("missing_upper",subset),
        }
    return out

def compute(groups):
    joint=summary(groups,2)
    if not (joint["lower"]<=joint["observed_only"]<=joint["upper"]):
        raise ValueError("Bound ordering failed")
    p4,p6=joint["patches_4"],joint["patches_6"]
    return {
        "schema":"structural.wolfe_joint_predator_label_robustness_result.v1_212",
        "status":"POSTHOC_RETROSPECTIVE_AMBIGUOUS_ROW_EXCLUSION_SENSITIVITY",
        "frozen_source_blob":EXPECTED_BLOB,
        "ambiguous_source_row_excluded_unmodified":AMBIGUOUS_ROW,
        "experiment_rows_read_for_outcome":175,
        "five_unknown_outcomes_bounds_not_confidence_intervals":True,
        "joint":joint,
        "difference_patches6_minus_patches4_bounds":[p6["lower"]-p4["upper"],p6["upper"]-p4["lower"]],
        "generalist_secondary":summary(groups,0),
        "specialist_secondary":summary(groups,1),
        "claim_is_confirmatory":False,
        "source_treatment_reassignment_performed":False,
        "ecological_temporal_process_inferred":False,
        "mammal_graph_independent_validation":False,
        "eBird_used":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("source_csv",type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=compute(load_source(args.source_csv.read_bytes()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":
    main()
