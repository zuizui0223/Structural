#!/usr/bin/env python3
"""Response-blind LandFrag geometry census for within-landscape topology H1.

Only the public LandFrag study metadata file is opened. The monolithic abundance
response file is identity-locked by Git blob SHA but is never fetched here.
"""
from __future__ import annotations

from collections import defaultdict, deque
import csv, hashlib, io, json, math
from urllib.parse import quote
from urllib.request import Request, urlopen

import numpy as np

SOURCE_REPO="mauriciovancine/landfrag"
SOURCE_COMMIT="5fd540048a6e60c641c9c1d6e7f26e7b5eece137"
METADATA_PATH="data/00_landfrag_metadata/landfrag_studies_jun2024_final_version.csv"
METADATA_BLOB="3f019e06dd099f89a836afb6996cb3f68f20f9bf"
ABUNDANCE_PATH="data/00_landfrag_metadata/landfrag_abundances_jun2024_final_version.csv"
ABUNDANCE_BLOB="abfdd21712b7f221207e25e62b623e8a8a901a55"

MIN_FOCALS=10
MIN_POSITIVE_GAIN=5
MAX_CONDITION=100.0
GEO_OVERLAP=0.80
ROUND_DECIMALS=5
MODEL_COLUMNS=(
    "intercept","z_log_area","z_log1p_direct_source_isolation",
    "z_topology_gain","direct_x_gain",
)

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def fetch_raw(path:str)->bytes:
    url=f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/"+quote(path,safe="/")
    req=Request(url,headers={"User-Agent":"Structural-LandFrag-metadata-census/0.1"})
    with urlopen(req,timeout=180) as response:
        return response.read()

def number(x):
    if x is None:
        return None
    s=str(x).strip()
    if not s or s.lower() in {"na","nan","continuous"}:
        return None
    try:
        v=float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) else None

def hav_km(a,b):
    r=6371.0088
    p1,p2=math.radians(a["lat"]),math.radians(b["lat"])
    dp=math.radians(b["lat"]-a["lat"])
    dl=math.radians(b["lon"]-a["lon"])
    z=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1.0,math.sqrt(z)))

def zscore(values,label):
    a=np.asarray(values,dtype=float)
    mu=float(a.mean()); sd=float(a.std(ddof=0))
    if sd<=1e-12:
        raise RuntimeError(f"constant predictor: {label}")
    return (a-mu)/sd,{"mean":mu,"sd":sd}

def collapse_fragments(rows):
    by=defaultdict(list)
    for row in rows:
        by[row["fragment_id"]].append(row)
    fragments=[]
    conflicts=[]
    for fragment_id,items in sorted(by.items()):
        vals=[]
        for row in items:
            area=number(row["fragment_area"])
            lon=number(row["longitude"])
            lat=number(row["latitude"])
            if area is None or area<=0 or lon is None or lat is None:
                continue
            vals.append((area,lon,lat))
        if not vals:
            continue
        rounded={(round(a,10),round(lon,10),round(lat,10)) for a,lon,lat in vals}
        if len(rounded)!=1:
            conflicts.append(fragment_id)
            continue
        area,lon,lat=vals[0]
        fragments.append({
            "fragment_id":fragment_id,
            "area_ha":area,
            "lon":lon,
            "lat":lat,
            "metadata_ids":sorted(int(row["id"]) for row in items if str(row["id"]).isdigit()),
            "plot_ids":sorted({row["plot_id"] for row in items}),
        })
    return fragments,conflicts

def minimax_from_source(i,D):
    n=D.shape[0]
    best=np.full(n,np.inf,dtype=float); best[i]=0.0
    used=np.zeros(n,dtype=bool)
    for _ in range(n):
        candidates=np.where(~used)[0]
        u=int(candidates[np.argmin(best[candidates])])
        used[u]=True
        for v in np.where(~used)[0]:
            cand=max(float(best[u]),float(D[u,v]))
            if cand<best[v]:
                best[v]=cand
    return best

def geometry_for_study(fragments):
    n=len(fragments)
    D=np.zeros((n,n),dtype=float)
    for i in range(n):
        for j in range(i+1,n):
            D[i,j]=D[j,i]=hav_km(fragments[i],fragments[j])
    focals=[]
    for i,focal in enumerate(fragments):
        sources=[j for j,s in enumerate(fragments) if s["area_ha"]>focal["area_ha"]]
        if not sources:
            continue
        direct=min(float(D[i,j]) for j in sources)
        best=minimax_from_source(i,D)
        bottleneck=min(float(best[j]) for j in sources)
        gain=max(0.0,math.log1p(direct)-math.log1p(bottleneck))
        focals.append({
            "fragment_id":focal["fragment_id"],
            "area_ha":focal["area_ha"],
            "direct_source_km":direct,
            "minimax_bottleneck_km":bottleneck,
            "topology_gain_log":gain,
        })
    if not focals:
        return None
    try:
        za,s_area=zscore([math.log(x["area_ha"]) for x in focals],"log_area")
        zd,s_direct=zscore([math.log1p(x["direct_source_km"]) for x in focals],"log1p_direct")
        zg,s_gain=zscore([x["topology_gain_log"] for x in focals],"topology_gain")
    except RuntimeError:
        return {
            "n_fragments":n,"n_focals":len(focals),
            "positive_gain":sum(x["topology_gain_log"]>1e-12 for x in focals),
            "design_error":"constant predictor",
            "focals":focals,
        }
    inter=zd*zg
    X=np.column_stack([np.ones(len(focals)),za,zd,zg,inter])
    rank=int(np.linalg.matrix_rank(X,tol=1e-10))
    sv=np.linalg.svd(X,compute_uv=False)
    cond=float(sv[0]/sv[-1]) if sv[-1]>1e-15 else float("inf")
    for i,row in enumerate(focals):
        row["design"]=[float(v) for v in X[i,:]]
    return {
        "n_fragments":n,
        "n_focals":len(focals),
        "positive_gain":sum(x["topology_gain_log"]>1e-12 for x in focals),
        "rank":rank,"n_columns":int(X.shape[1]),"condition_number":cond,
        "full_rank":rank==X.shape[1],
        "scaling":{"log_area":s_area,"log1p_direct":s_direct,"topology_gain":s_gain},
        "focals":focals,
    }

def coord_set(fragments):
    return {
        (round(f["lat"],ROUND_DECIMALS),round(f["lon"],ROUND_DECIMALS))
        for f in fragments
    }

def cluster_geographies(studies):
    ids=sorted(studies)
    sets={sid:coord_set(studies[sid]["fragments"]) for sid in ids}
    adj={sid:set() for sid in ids}; edges=[]
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            inter=len(sets[a]&sets[b])
            denom=min(len(sets[a]),len(sets[b]))
            frac=inter/denom if denom else 0.0
            if frac>=GEO_OVERLAP:
                adj[a].add(b);adj[b].add(a)
                edges.append({"a":a,"b":b,"matched":inter,"fraction_smaller":frac})
    comps=[];seen=set()
    for sid in ids:
        if sid in seen:continue
        q=deque([sid]);seen.add(sid);members=[]
        while q:
            u=q.popleft();members.append(u)
            for v in sorted(adj[u]):
                if v not in seen:
                    seen.add(v);q.append(v)
        comps.append(sorted(members))
    comps.sort(key=lambda x:x[0])
    mapping={}
    for i,members in enumerate(comps,1):
        cid=f"G{i:03d}"
        for sid in members:mapping[sid]=cid
    return comps,mapping,edges

def main():
    raw=fetch_raw(METADATA_PATH)
    if git_blob_sha(raw)!=METADATA_BLOB:
        raise RuntimeError("LandFrag metadata blob drift")
    text=raw.decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(text)))
    if len(rows)!=2916:
        raise RuntimeError(f"metadata row-count drift: {len(rows)}")

    by=defaultdict(list)
    for row in rows:by[row["refshort"]].append(row)

    all_studies={}
    for sid,items in sorted(by.items()):
        fragments,conflicts=collapse_fragments(items)
        geom=geometry_for_study(fragments) if len(fragments)>=2 else None
        all_studies[sid]={
            "fragments":fragments,"conflicts":conflicts,"geometry":geom,
            "taxa":sorted({r["taxa"] for r in items}),
            "country":sorted({r["country"] for r in items}),
            "climate":sorted({r["climate"] for r in items}),
        }

    eligible={}
    exclusions={}
    for sid,s in all_studies.items():
        g=s["geometry"]; reasons=[]
        if s["conflicts"]:reasons.append("fragment_metadata_conflict")
        if g is None:reasons.append("no_geometry")
        else:
            if g["n_focals"]<MIN_FOCALS:reasons.append("fewer_than_10_focals")
            if g["positive_gain"]<MIN_POSITIVE_GAIN:reasons.append("fewer_than_5_positive_gains")
            if not g.get("full_rank",False):reasons.append("design_not_full_rank")
            if g.get("condition_number",float("inf"))>MAX_CONDITION:reasons.append("condition_gt_100")
        if reasons:exclusions[sid]=reasons
        else:eligible[sid]=s

    comps,mapping,edges=cluster_geographies(eligible)
    if len(comps)<30:
        raise RuntimeError(
            f"only {len(comps)} independent geography clusters; v0.2 requires >=30"
        )

    studies_out=[]
    for sid in sorted(eligible):
        s=eligible[sid];g=s["geometry"]
        studies_out.append({
            "refshort":sid,
            "geography_cluster":mapping[sid],
            "taxa":s["taxa"],"country":s["country"],"climate":s["climate"],
            "n_fragments":g["n_fragments"],"n_focals":g["n_focals"],
            "positive_gain":g["positive_gain"],
            "condition_number":g["condition_number"],
            "scaling":g["scaling"],
            "frozen_fragment_ids":sorted(f["fragment_id"] for f in s["fragments"]),
            "focal_rows":g["focals"],
            "focal_design_sha256":sha([(r["fragment_id"],r["design"]) for r in g["focals"]]),
        })

    payload={
        "schema":"structural.landfrag_relative_topology_metadata.v0_2",
        "status":"QUALIFIED_RESPONSE_SEALED_V0_2",
        "source":{
            "repository":SOURCE_REPO,"commit":SOURCE_COMMIT,
            "metadata_path":METADATA_PATH,"metadata_git_blob_sha":METADATA_BLOB,
            "metadata_sha256":hashlib.sha256(raw).hexdigest(),
            "metadata_rows":len(rows),
            "abundance_path":ABUNDANCE_PATH,
            "abundance_git_blob_sha":ABUNDANCE_BLOB,
        },
        "response_values_accessed":False,
        "abundance_file_opened":False,
        "geometry_rules":{
            "source_set":"strictly larger-area numeric forest fragments within refshort study",
            "stepping_nodes":"all numeric-area fragments with complete coordinates within study",
            "direct_source_isolation":"nearest strictly larger-area source great-circle distance",
            "minimax_bottleneck":"minimum possible maximum edge to any strictly larger-area source through complete within-study fragment graph",
            "topology_gain":"log1p(direct_source_km)-log1p(minimax_bottleneck_km), constrained nonnegative",
            "model_columns":list(MODEL_COLUMNS),
            "target":"direct_x_gain = z(log1p direct source isolation) * z(topology gain)",
            "prediction":"positive",
            "minimum_focals":MIN_FOCALS,
            "minimum_positive_gain":MIN_POSITIVE_GAIN,
            "maximum_condition_number":MAX_CONDITION,
        },
        "geography_clustering":{
            "coordinate_rounding_decimals":ROUND_DECIMALS,
            "overlap_threshold_fraction_smaller":GEO_OVERLAP,
            "clusters":[{"cluster_id":f"G{i:03d}","studies":m} for i,m in enumerate(comps,1)],
            "overlap_edges":edges,
        },
        "v0_2_revision":{
            "reason":"v0.1 stopped response-blind at an arbitrary >=50-cluster gate; v0.2 retains every per-study geometry criterion unchanged and requires >=30 independent geography clusters for the cluster-level macro test",
            "v0_1_response_opened":False,
            "per_study_geometry_rules_changed":False,
        },
        "selection":{
            "studies_total":len(all_studies),
            "geometry_qualified_studies":len(eligible),
            "independent_geography_clusters":len(comps),
            "qualified_focals":sum(x["geometry"]["n_focals"] for x in eligible.values()),
            "qualified_fragments":sum(x["geometry"]["n_fragments"] for x in eligible.values()),
            "exclusion_counts":dict(sorted(__import__("collections").Counter(r for rs in exclusions.values() for r in rs).items())),
        },
        "studies":studies_out,
        "response_surface":{
            "path":ABUNDANCE_PATH,
            "git_blob_sha":ABUNDANCE_BLOB,
            "monolithic_all_studies":True,
            "opened":False,
        },
        "response_open_authorized":False,
    }
    payload["census_fingerprint"]=sha(payload)
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
