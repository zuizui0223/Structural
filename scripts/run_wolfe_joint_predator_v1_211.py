#!/usr/bin/env python3
"""v1.211 exploratory Wolfe treatment contrast with 4 missing-outcome bounds."""
import argparse,csv,hashlib,io,json,math,random
from collections import defaultdict
from pathlib import Path
BLOB="e78003d425b646b390ae02e36c007892c1c70926"
STRATA=[(n,m,c) for n in (4,6) for m in ("none","low","high") for c in ("none","low","high")]
CONFIG={(1,"homogeneous"),(4,"homogeneous"),(4,"heterogeneous"),(6,"homogeneous"),(6,"heterogeneous")}
def read_experiment(content):
    h=hashlib.sha1(b"blob "+str(len(content)).encode()+b"\0"+content).hexdigest()
    if len(content)!=12096 or h!=BLOB:raise ValueError("Author source byte identity mismatch")
    reader=csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    keys={"microcosm","replicate","patch_number","heterogeneity","matrix_dispersal",
          "corridor_dispersal","stentor_coeruleus","didinium_nasutum","dileptus_anser"}
    if not keys.issubset(reader.fieldnames or []):raise ValueError("Unexpected data columns")
    rows=list(reader)
    if len(rows)!=176:raise ValueError("176 source rows required")
    groups=defaultdict(list);ids=set()
    for r in rows:
        id=(r["microcosm"],r["replicate"])
        if not all(id) or id in ids:raise ValueError("Invalid independent microcosm")
        ids.add(id)
        n=int(r["patch_number"]);het=r["heterogeneity"].strip().lower()
        m=r["matrix_dispersal"].strip().lower();c=r["corridor_dispersal"].strip().lower()
        if r.get("")=="6HoLM1":
            if (r["microcosm"]!="6HoLM" or r["replicate"]!="1"
                    or n!=6 or het!="homogeneous" or m!="none" or c!="none"):
                raise ValueError("Frozen single-source coding discrepancy changed")
            m="low"  # response-blind provisional correction from matching code 6HoLM2..4
        if (n,het) not in CONFIG or m not in ("none","low","high") or c not in ("none","low","high"):
            raise ValueError("Factorial identity mismatch")
        def positive(col):
            q=float(r[col])
            if q<0 or not math.isfinite(q):raise ValueError("Invalid density")
            return int(q>0)
        g=positive("stentor_coeruleus")
        s=int(bool(positive("didinium_nasutum") or positive("dileptus_anser")))
        groups[(n,het,m,c)].append((g,s,g*s))
    expected={(n,het,m,c) for n,het in CONFIG for m in ("none","low","high")
              for c in ("none","low","high")}
    if set(groups)!=expected or sorted(map(len,groups.values())).count(3)!=4:
        raise ValueError("Missing factorial cells or wrong attrition")
    if any(len(v) not in (3,4) for v in groups.values()) or sum(map(len,groups.values()))!=176:
        raise ValueError("Observed experiment units not as frozen")
    if any(len(groups[(1,"homogeneous",m,c)])!=4
           for m in ("none","low","high") for c in ("none","low","high")):
        raise ValueError("Single patch leakage unexpected")
    return groups
def measures(groups,idx):
    strata=[]
    for n,m,c in STRATA:
        a=groups[(n,"heterogeneous",m,c)];b=groups[(n,"homogeneous",m,c)]
        sa=sum(v[idx] for v in a);sb=sum(v[idx] for v in b)
        strata.append({"patches":n,"matrix":m,"corridor":c,
           "heterogeneous_n":len(a),"homogeneous_n":len(b),
           "heterogeneous_successes":sa,"homogeneous_successes":sb,
           "observed_contrast":sa/len(a)-sb/len(b),
           "missing_lower":sa/4-(sb+4-len(b))/4,
           "missing_upper":(sa+4-len(a))/4-sb/4})
    def mean(key,arr):return sum(z[key] for z in arr)/len(arr)
    return {"observed":mean("observed_contrast",strata),
     "full_assignment_missing_lower":mean("missing_lower",strata),
     "full_assignment_missing_upper":mean("missing_upper",strata),
     "by_n":{str(n):mean("observed_contrast",[v for v in strata if v["patches"]==n]) for n in (4,6)}}
def bootstrap(groups,B=10000,seed=20261008):
    rng=random.Random(seed);out=[]
    for _ in range(B):
        s=0.0
        for n,m,c in STRATA:
            a=groups[(n,"heterogeneous",m,c)];b=groups[(n,"homogeneous",m,c)]
            s+=sum(a[rng.randrange(len(a))][2] for j in range(len(a)))/len(a)
            s-=sum(b[rng.randrange(len(b))][2] for j in range(len(b)))/len(b)
        out.append(s/18)
    out.sort()
    def q(p):
        x=p*(B-1);i=int(x);j=min(i+1,B-1);return out[i]*(j-x)+out[j]*(x-i)
    return [q(.025),q(.975)]
def run(groups):
    return {
      "schema":"structural.wolfe_joint_predator_exploratory_result.v1_210",
      "status":"RETROSPECTIVE_NONCONFIRMATORY_INFERENTIAL_CEILING",
      "source_blob_git_sha1":BLOB,
      "original_v209_status":"TERMINAL_FAILED_N180_GATE",
      "observed_rows":sum(len(v) for v in groups.values()),
      "primary_joint":measures(groups,2),
      "primary_observed_only_bootstrap95":bootstrap(groups),
      "secondary_generalist":measures(groups,0),
      "secondary_specialist":measures(groups,1),
      "biological_interpretation_ceiling":"joint end-of-experiment guild presence only, not time-ordered rescue or island dispersal",
      "mammal_graph_independent_replication":False,
      "original_BALA_or_ALA_reopened":False,
      "eBird_used":False
    }
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("source",type=Path);a.add_argument("--out",type=Path,required=True)
    opt=a.parse_args()
    x=run(read_experiment(opt.source.read_bytes()))
    opt.out.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
    print(json.dumps(x,sort_keys=True))
