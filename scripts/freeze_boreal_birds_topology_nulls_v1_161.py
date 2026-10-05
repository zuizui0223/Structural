#!/usr/bin/env python3
"""Freeze response-independent matched null topologies and S_i(n) for boreal birds."""
from __future__ import annotations

import argparse,csv,hashlib,heapq,json,math
from pathlib import Path
from typing import Mapping

from structural.boreal_dual_isolation_operator import freeze_connected_knn_operator
from structural.boreal_spatial_partition import pairwise_distances,type7_quantile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"development/boreal_birds_topology_null_contract_v1_161.json"
GEOMETRY=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv"
GEOMETRY_FREEZE=ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"
SPATIAL_FREEZE=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"
OPERATOR_FREEZE=ROOT/"development/boreal_19island_source_operator_freeze_v1_01.json"

class Stop(RuntimeError): pass

def sha_file(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def csha(x:Mapping)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def load(p:Path)->dict:
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise Stop(f"{p.name} must be object")
    return x

def num(x)->float:
    s=str(x).strip()
    v=float.fromhex(s) if s.lower().startswith(("0x","+0x","-0x")) else float(s)
    if not math.isfinite(v): raise Stop("nonfinite number")
    return v

def geometry(p:Path)->dict[str,tuple[float,float]]:
    rows=list(csv.DictReader(p.read_text(encoding="utf-8").splitlines()))
    if len(rows)!=19 or tuple(rows[0])!=("Island","Lat","Long"): raise Stop("geometry schema/count drift")
    out={}
    for r in rows:
        i=str(r["Island"]).strip()
        if not i or i in out: raise Stop("blank/duplicate island")
        out[i]=(num(r["Lat"]),num(r["Long"]))
    return out

def ek(a:str,b:str)->tuple[str,str]:
    if a==b: raise Stop("self edge")
    return tuple(sorted((a,b)))

def connected(ids,edges):
    adj={x:set() for x in ids}
    for a,b in edges: adj[a].add(b);adj[b].add(a)
    seen={ids[0]}; stack=[ids[0]]
    while stack:
        u=stack.pop()
        for v in adj[u]:
            if v not in seen: seen.add(v);stack.append(v)
    return len(seen)==len(ids)

def degrees(ids,edges):
    d={x:0 for x in ids}
    for a,b in edges:d[a]+=1;d[b]+=1
    return d

def hidx(text:str,n:int)->int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8],"big")%n

def make_nulls(ids,actual,dist,cuts,cfg):
    def eb(e): return sum(float(dist[e])>c for c in cuts)
    actual_deg=degrees(ids,actual)
    actual_bins={}
    for e in actual: actual_bins[str(eb(e))]=actual_bins.get(str(eb(e)),0)+1
    seen=set(); rows=[]
    for ni in range(int(cfg["count"])):
        variant=0
        while True:
            seed=f'{cfg["salt"]}|null={ni}|variant={variant}'
            edges=set(actual); accepted=0; attempts=0
            while accepted<int(cfg["accepted_swaps_per_null"]) and attempts<int(cfg["maximum_attempts_per_null"]):
                attempts+=1; ordered=sorted(edges)
                i=hidx(f"{seed}|attempt={attempts}|edge1",len(ordered))
                j=hidx(f"{seed}|attempt={attempts}|edge2",len(ordered)-1)
                if j>=i:j+=1
                e1,e2=ordered[i],ordered[j]; a,b=e1;c,d=e2
                if len({a,b,c,d})<4:continue
                if hidx(f"{seed}|attempt={attempts}|pairing",2)==0:
                    new=[ek(a,c),ek(b,d)]
                else:
                    new=[ek(a,d),ek(b,c)]
                if new[0]==new[1] or any(x in edges and x not in {e1,e2} for x in new):continue
                if sorted((eb(e1),eb(e2)))!=sorted((eb(new[0]),eb(new[1]))):continue
                cand=(edges-{e1,e2})|set(new)
                if not connected(ids,cand):continue
                edges=cand;accepted+=1
            if accepted!=int(cfg["accepted_swaps_per_null"]):raise Stop(f"null {ni} swap target not reached")
            key=tuple(sorted(edges)); sym=len(edges^actual)
            if key==tuple(sorted(actual)) or key in seen or sym<int(cfg["minimum_symmetric_edge_difference_count"]):
                variant+=1
                if variant>100:raise Stop("unique null generation exhausted")
                continue
            if degrees(ids,edges)!=actual_deg:raise Stop("degree drift")
            bins={}
            for e in edges:bins[str(eb(e))]=bins.get(str(eb(e)),0)+1
            if bins!=actual_bins:raise Stop("edge-bin drift")
            seen.add(key)
            rows.append({
                "null_id":f"N{ni+1:02d}","seed":seed,"variant":variant,
                "accepted_swaps":accepted,"attempts":attempts,
                "edge_count":len(edges),"shared_edge_count":len(edges&actual),
                "symmetric_edge_difference_count":sym,
                "edges":[{"left":a,"right":b,"distance_km_hex":float(dist[(a,b)]).hex(),"edge_length_bin":eb((a,b))}
                         for a,b in sorted(edges)]
            })
            break
    return rows

def adj(ids,edges,dist):
    a={x:[] for x in ids}
    for x,y in edges:
        w=float(dist[(x,y)]);a[x].append((y,w));a[y].append((x,w))
    return a

def dijkstra(src,a):
    D={x:math.inf for x in a};D[src]=0.;q=[(0.,src)]
    while q:
        cur,u=heapq.heappop(q)
        if cur>D[u]+1e-12:continue
        for v,w in a[u]:
            z=cur+w
            if z<D[v]-1e-12:D[v]=z;heapq.heappush(q,(z,v))
    if any(not math.isfinite(x) for x in D.values()):raise Stop("disconnected graph")
    return D

def sensitivity(ids,actual,dist,cfg,lam):
    A=adj(ids,actual,dist)
    sources=tuple(cfg["possible_sources"]);targets=tuple(cfg["targets"]);M=len(sources)
    shortest={t:dijkstra(t,A) for t in targets};out=[]
    for t in targets:
        w=[math.exp(-shortest[t][s]/lam) for s in sources]
        mu=math.fsum(w)/M;sig=math.fsum((x-mu)**2 for x in w)/M
        for n in cfg["n_values"]:
            n=int(n);S=((M-n)/(n*(M-1)))*(sig/(mu*mu))
            out.append({"target":t,"n":n,"M":M,"mu_hex":mu.hex(),"sigma2_hex":sig.hex(),"S_hex":S.hex()})
    return out

def csv_text(rows):
    cols=["target","n","M","mu_hex","sigma2_hex","S_hex"]
    return ",".join(cols)+"\n"+"\n".join(",".join(str(r[c]) for c in cols) for r in rows)+"\n"

def run(contract_path,geometry_path,geometry_freeze_path,spatial_freeze_path,operator_freeze_path):
    c=load(contract_path);gf=load(geometry_freeze_path);sf=load(spatial_freeze_path);of=load(operator_freeze_path)
    if c.get("schema")!="structural.boreal_birds_topology_null_contract.v1_161":raise Stop("contract schema drift")
    req=c["required_identity"]
    if sha_file(geometry_path)!=req["geometry_sha256"]:raise Stop("geometry SHA drift")
    if sha_file(spatial_freeze_path)!=req["spatial_freeze_sha256"]:raise Stop("spatial SHA drift")
    xy=geometry(geometry_path);ids=tuple(sorted(xy))
    if tuple(gf["island_order"])!=ids:raise Stop("island universe drift")
    if sf["pilot_islands"]!=c["configuration_sensitivity"]["possible_sources"]:raise Stop("pilot source set drift")
    if sf["confirmatory_islands"]!=c["configuration_sensitivity"]["targets"]:raise Stop("confirmatory target set drift")
    op=freeze_connected_knn_operator(xy);fp=csha(op)
    if fp!=req["actual_operator_fingerprint"] or of["operator_fingerprint"]!=fp:raise Stop("operator fingerprint drift")
    if op["selected_k"]!=req["actual_selected_k"] or len(op["edges"])!=req["actual_edge_count"]:raise Stop("operator shape drift")
    if float(op["kernel_scale_km"]).hex()!=req["actual_kernel_scale_km_hex"]:raise Stop("kernel scale drift")
    dist=pairwise_distances(xy); actual={ek(e["left"],e["right"]) for e in op["edges"]}
    lens=sorted(float(e["distance_km"]) for e in op["edges"])
    cuts=tuple(type7_quantile(lens,float(p)) for p in c["null_ensemble"]["edge_length_bin_quantiles"])
    nulls=make_nulls(ids,actual,dist,cuts,c["null_ensemble"])
    actual_rows=[{"left":a,"right":b,"distance_km_hex":float(dist[(a,b)]).hex(),
                  "edge_length_bin":sum(float(dist[(a,b)])>cut for cut in cuts)} for a,b in sorted(actual)]
    ens={
      "schema":"structural.boreal_birds_topology_null_ensemble.v1_161",
      "status":"RESPONSE_INDEPENDENT_NULL_ENSEMBLE_FROZEN",
      "candidate_id":c["candidate_id"],"geometry_sha256":req["geometry_sha256"],
      "actual_operator_fingerprint":fp,"kernel_scale_km_hex":req["actual_kernel_scale_km_hex"],
      "edge_length_bin_cut_hex":[x.hex() for x in cuts],"actual_edges":actual_rows,"nulls":nulls,
      "bird_response_values_opened":0,"counts_as_empirical_evidence":False
    }
    ens["ensemble_fingerprint"]=csha(ens)
    srows=sensitivity(ids,actual,dist,c["configuration_sensitivity"],float(op["kernel_scale_km"]))
    scsv=csv_text(srows)
    etext=json.dumps(ens,indent=2,sort_keys=True)+"\n"
    receipt={
      "schema":"structural.boreal_birds_topology_null_freeze.v1_161",
      "status":"NULL_ENSEMBLE_AND_SENSITIVITY_FROZEN_RESPONSE_INDEPENDENTLY",
      "candidate_id":c["candidate_id"],"ensemble_fingerprint":ens["ensemble_fingerprint"],
      "null_count":len(nulls),"sensitivity_row_count":len(srows),
      "sensitivity_target_count":len(set(r["target"] for r in srows)),
      "sensitivity_n_values":sorted(set(r["n"] for r in srows)),
      "ensemble_json_sha256":hashlib.sha256(etext.encode()).hexdigest(),
      "sensitivity_csv_sha256":hashlib.sha256(scsv.encode()).hexdigest(),
      "bird_file_opened":False,"bird_response_values_opened":0,"beetle_response_used":False,
      "plant_response_used":False,"counts_as_empirical_evidence":False,
      "pilot_response_authorized":False,"confirmatory_response_authorized":False,
      "next_action":c["next_action"]
    }
    return etext,scsv,json.dumps(receipt,indent=2,sort_keys=True)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=CONTRACT);ap.add_argument("--geometry",type=Path,default=GEOMETRY)
    ap.add_argument("--geometry-freeze",type=Path,default=GEOMETRY_FREEZE);ap.add_argument("--spatial-freeze",type=Path,default=SPATIAL_FREEZE)
    ap.add_argument("--operator-freeze",type=Path,default=OPERATOR_FREEZE);ap.add_argument("--ensemble",type=Path,required=True)
    ap.add_argument("--sensitivity",type=Path,required=True);ap.add_argument("--receipt",type=Path,required=True);a=ap.parse_args()
    try:
        et,st,rt=run(a.contract,a.geometry,a.geometry_freeze,a.spatial_freeze,a.operator_freeze)
    except Exception as e:
        rt=json.dumps({"schema":"structural.boreal_birds_topology_null_freeze.v1_161","status":"STOP","reason":str(e),
                       "bird_file_opened":False,"bird_response_values_opened":0,"counts_as_empirical_evidence":False,
                       "pilot_response_authorized":False,"confirmatory_response_authorized":False},indent=2,sort_keys=True)+"\n"
        a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(rt,encoding="utf-8");print(rt,end="");return 2
    for p,t in ((a.ensemble,et),(a.sensitivity,st),(a.receipt,rt)):
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding="utf-8")
    print(rt,end="");return 0
if __name__=="__main__":raise SystemExit(main())
