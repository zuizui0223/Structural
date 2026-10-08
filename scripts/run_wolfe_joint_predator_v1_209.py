#!/usr/bin/env python3
"""Frozen v1.209 retrospective 4-/6-patch guild co-presence contrast."""
import argparse,csv,hashlib,json,math,random
from collections import defaultdict
from pathlib import Path
GIT_BLOB="e78003d425b646b390ae02e36c007892c1c70926"
GIT_SIZE=12096
FACTORS=("patch_number","heterogeneity","matrix_dispersal","corridor_dispersal")
REQUIRED={"microcosm","replicate",*FACTORS,"stentor_coeruleus","didinium_nasutum","dileptus_anser"}
STRATA=[(n,m,c) for n in (4,6) for m in ("none","low","high")
        for c in ("none","low","high")]
def check_git_blob(b):
    h=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\x00"+b).hexdigest()
    if len(b)!=GIT_SIZE or h!=GIT_BLOB:raise ValueError("Frozen Git blob mismatch")
    return h
def positive(s):
    x=float(s)
    if not math.isfinite(x) or x<0:raise ValueError("missing, negative, or nonfinite density")
    return int(x>0)
def read_rows(payload):
    check_git_blob(payload)
    import io
    reader=csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    if not REQUIRED.issubset(reader.fieldnames or []):raise ValueError("Column schema mismatch")
    rows=list(reader)
    if len(rows)!=180:raise ValueError("Expected exactly 180 units")
    groups=defaultdict(list)
    ids=set()
    for row in rows:
        mid=row["microcosm"]
        if not mid or mid in ids:raise ValueError("Duplicate or absent microcosm ID")
        ids.add(mid)
        n=int(row["patch_number"])
        het=row["heterogeneity"].lower().strip()
        mat=row["matrix_dispersal"].lower().strip()
        cor=row["corridor_dispersal"].lower().strip()
        if (n,het) not in {(1,"homogeneous"),(4,"homogeneous"),(4,"heterogeneous"),
                            (6,"homogeneous"),(6,"heterogeneous")}:
            raise ValueError("Unexpected configuration")
        if mat not in ("none","low","high") or cor not in ("none","low","high"):
            raise ValueError("Unexpected movement regime")
        gen=positive(row["stentor_coeruleus"])
        spec=int(positive(row["didinium_nasutum"]) or positive(row["dileptus_anser"]))
        groups[(n,het,mat,cor)].append((gen,spec,gen*spec))
    expected={(n,het,mat,cor) for n,het in ((1,"homogeneous"),(4,"homogeneous"),
       (4,"heterogeneous"),(6,"homogeneous"),(6,"heterogeneous"))
       for mat in ("none","low","high") for cor in ("none","low","high")}
    if set(groups)!=expected or any(len(v)!=4 for v in groups.values()):
        raise ValueError("Incomplete factorial or independent units")
    return groups
def estimate(groups,index):
    effects=[]
    for n,m,c in STRATA:
        hetero=groups[(n,"heterogeneous",m,c)]
        homo=groups[(n,"homogeneous",m,c)]
        effects.append(sum(x[index] for x in hetero)/4-
                       sum(x[index] for x in homo)/4)
    return sum(effects)/len(effects)
def percentile(xs,p):
    ys=sorted(xs);u=p*(len(ys)-1);lo=int(u);hi=min(lo+1,len(ys)-1)
    return ys[lo]*(hi-u)+ys[hi]*(u-lo)
def run(groups,B=10000,seed=20261008):
    rng=random.Random(seed)
    stats={k:estimate(groups,i) for i,k in enumerate(("generalist","specialist","joint"))}
    boots=[]
    for _ in range(B):
        s=0.
        for n,m,c in STRATA:
            ht=groups[(n,"heterogeneous",m,c)]
            hm=groups[(n,"homogeneous",m,c)]
            s+=(sum(ht[rng.randrange(4)][2] for j in range(4))-
                sum(hm[rng.randrange(4)][2] for j in range(4)))/4
        boots.append(s/len(STRATA))
    return {"schema":"structural.wolfe_joint_predator_result.v1_209",
        "classification":"PUBLISHED_OUTCOME_CONTEXT_EXPOSED_RETROSPECTIVE",
        "primary_joint_heterogeneous_minus_homogeneous":stats["joint"],
        "bootstrap_95pct":[percentile(boots,.025),percentile(boots,.975)],
        "secondary_marginal_generalist":stats["generalist"],
        "secondary_marginal_specialist":stats["specialist"],
        "strata":18,"replicates_each_arm_per_stratum":4,
        "microcosm_count":180,"bootstrap_replicates":B,"bootstrap_seed":seed,
        "no_time_ordered_response":True,"independent_mammal_validation":False,
        "rerun_or_threshold_tuning_authorized":False}
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("source_csv",type=Path)
    a.add_argument("--out",type=Path,required=True);args=a.parse_args()
    data=read_rows(args.source_csv.read_bytes())
    r=run(data);args.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print(json.dumps(r,sort_keys=True))
