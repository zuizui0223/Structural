#!/usr/bin/env python3
"""Freeze topology-residual sparse-source sensitivity for boreal birds, response-free."""
from __future__ import annotations

import argparse,csv,hashlib,heapq,json,math
from pathlib import Path

from structural.boreal_dual_isolation_operator import freeze_connected_knn_operator
from structural.boreal_spatial_partition import pairwise_distances

ROOT=Path(__file__).resolve().parents[1]
DESIGN=ROOT/"development/boreal_birds_topology_residual_preintake_v1_162.json"
GEOMETRY=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv"

class Stop(RuntimeError): pass

def load(p):
    x=json.loads(Path(p).read_text())
    if not isinstance(x,dict):raise Stop("JSON object required")
    return x

def num(x):
    s=str(x).strip()
    v=float.fromhex(s) if s.lower().startswith(("0x","+0x","-0x")) else float(s)
    if not math.isfinite(v):raise Stop("nonfinite")
    return v

def load_geometry(p):
    rows=list(csv.DictReader(Path(p).read_text().splitlines()))
    if len(rows)!=19 or tuple(rows[0])!=("Island","Lat","Long"):raise Stop("geometry drift")
    return {r["Island"]:(num(r["Lat"]),num(r["Long"])) for r in rows}

def ek(a,b):return tuple(sorted((a,b)))

def adjacency(ids,edges,dist):
    out={x:[] for x in ids}
    for a,b in edges:
        d=float(dist[ek(a,b)]);out[a].append((b,d));out[b].append((a,d))
    return out

def dijkstra(src,adj):
    D={x:math.inf for x in adj};D[src]=0.;q=[(0.,src)]
    while q:
        cur,u=heapq.heappop(q)
        if cur>D[u]+1e-12:continue
        for v,w in adj[u]:
            z=cur+w
            if z<D[v]-1e-12:D[v]=z;heapq.heappush(q,(z,v))
    if any(not math.isfinite(v) for v in D.values()):raise Stop("disconnected")
    return D

def render(rows):
    cols=["target","n","M","mu_q_hex","sigma2_q_hex","H_topo_hex","S_topo_hex"]
    return ",".join(cols)+"\n"+"\n".join(",".join(str(r[c]) for c in cols) for r in rows)+"\n"

def freeze(design_path=DESIGN,geometry_path=GEOMETRY):
    d=load(design_path)
    if d.get("schema")!="structural.boreal_birds_topology_residual_preintake.v1_162":raise Stop("design schema drift")
    if d["evidence_boundary"]["bird_response_values_opened"]!=0:raise Stop("bird boundary drift")
    xy=load_geometry(geometry_path)
    op=freeze_connected_knn_operator(xy)
    expected=d["frozen_geometry_and_operator"]
    if op["selected_k"]!=3:raise Stop("operator k drift")
    if float(op["kernel_scale_km"]).hex()!=expected["kernel_scale_km_hex"]:raise Stop("lambda drift")
    ids=tuple(op["island_order"]);dist=pairwise_distances(xy)
    edges={ek(e["left"],e["right"]) for e in op["edges"]}
    adj=adjacency(ids,edges,dist)
    sources=tuple(expected["possible_sources"]);targets=tuple(expected["targets"]);M=len(sources);lam=float(op["kernel_scale_km"])
    shortest={t:dijkstra(t,adj) for t in targets}
    rows=[];audit=[]
    for t in targets:
        q=[]
        for s in sources:
            dg=shortest[t][s];de=float(dist[ek(t,s)])
            if dg+1e-10<de:raise Stop("graph path shorter than Euclidean")
            q.append(math.exp(-(dg-de)/lam))
        mu=math.fsum(q)/M;sig=math.fsum((x-mu)**2 for x in q)/M;H=sig/(mu*mu)
        audit.append({"target":t,"H_topo_hex":H.hex(),"q_min_hex":min(q).hex(),"q_max_hex":max(q).hex()})
        for n in (1,2,3,4,5,6):
            S=((M-n)/(n*(M-1)))*H
            rows.append({"target":t,"n":n,"M":M,"mu_q_hex":mu.hex(),"sigma2_q_hex":sig.hex(),"H_topo_hex":H.hex(),"S_topo_hex":S.hex()})
    hs=[float.fromhex(x["H_topo_hex"]) for x in audit]
    if max(hs)-min(hs)<=1e-12:raise Stop("topology residual heterogeneity is constant")
    text=render(rows)
    receipt={
      "schema":"structural.boreal_birds_topology_residual_sensitivity_freeze.v1_162",
      "status":"TOPOLOGY_RESIDUAL_SENSITIVITY_FROZEN_RESPONSE_INDEPENDENTLY",
      "candidate_id":d["candidate_id"],"target_count":len(targets),"row_count":len(rows),"M":M,
      "H_topo_min_hex":min(hs).hex(),"H_topo_max_hex":max(hs).hex(),"H_topo_unique_count":len(set(h.hex() for h in hs)),
      "target_audit":audit,"surface_sha256":hashlib.sha256(text.encode()).hexdigest(),
      "bird_file_opened":False,"bird_response_values_opened":0,"counts_as_empirical_evidence":False,
      "pilot_response_authorized":False,"confirmatory_response_authorized":False,
      "next_action":"commit this surface; after the matched-null freeze is also committed, build a one-shot bird pilot router"
    }
    return text,json.dumps(receipt,indent=2,sort_keys=True)+"\n"

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--design",type=Path,default=DESIGN);ap.add_argument("--geometry",type=Path,default=GEOMETRY)
    ap.add_argument("--surface",type=Path,required=True);ap.add_argument("--receipt",type=Path,required=True);a=ap.parse_args()
    try:surface,receipt=freeze(a.design,a.geometry)
    except Exception as e:
        receipt=json.dumps({"schema":"structural.boreal_birds_topology_residual_sensitivity_freeze.v1_162","status":"STOP","reason":str(e),
                            "bird_file_opened":False,"bird_response_values_opened":0,"counts_as_empirical_evidence":False,
                            "pilot_response_authorized":False,"confirmatory_response_authorized":False},indent=2,sort_keys=True)+"\n"
        a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(receipt);print(receipt,end="");return 2
    for p,t in ((a.surface,surface),(a.receipt,receipt)):
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
    print(receipt,end="");return 0
if __name__=="__main__":raise SystemExit(main())
