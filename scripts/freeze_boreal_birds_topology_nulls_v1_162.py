#!/usr/bin/env python3
"""Freeze response-independent topology nulls and target sensitivity for boreal birds v1.162."""
from __future__ import annotations

import argparse, csv, hashlib, json, math
from pathlib import Path

from structural.boreal_dual_isolation_operator import (
    adjacency_from_operator,
    freeze_connected_knn_operator,
)
from structural.boreal_spatial_partition import pairwise_distances, type7_quantile

ROOT=Path(__file__).resolve().parents[1]
GEOM=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv"
GEOM_FREEZE=ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"
SPATIAL=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"
OP_FREEZE=ROOT/"development/boreal_19island_source_operator_freeze_v1_01.json"
CONTRACT=ROOT/"development/boreal_birds_topology_sensitivity_contract_v1_162.json"

class Stop(RuntimeError): pass

def loadj(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise Stop(f"{p.name} not object")
    return x

def sha_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def parse_num(x):
    s=str(x).strip()
    v=float.fromhex(s) if s.lower().startswith(("0x","+0x","-0x")) else float(s)
    if not math.isfinite(v): raise Stop("nonfinite coordinate")
    return v

def load_geometry():
    gf=loadj(GEOM_FREEZE)
    if sha_file(GEOM)!=gf["geometry_sha256"]: raise Stop("geometry SHA drift")
    rows=list(csv.DictReader(GEOM.read_text(encoding="utf-8").splitlines()))
    out={r["Island"]:(parse_num(r["Lat"]),parse_num(r["Long"])) for r in rows}
    if sorted(out)!=gf["island_order"]: raise Stop("geometry island drift")
    return out

def canonical_hash(x):
    raw=json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def is_connected(ids, edges):
    adj={x:set() for x in ids}
    for a,b in edges: adj[a].add(b);adj[b].add(a)
    seen={ids[0]}; stack=[ids[0]]
    while stack:
        x=stack.pop()
        for y in sorted(adj[x]):
            if y not in seen: seen.add(y);stack.append(y)
    return len(seen)==len(ids)

def degree(ids,edges):
    out={x:0 for x in ids}
    for a,b in edges: out[a]+=1;out[b]+=1
    return out

def dijkstra(ids, edges, edge_distance, source):
    import heapq
    adj={x:[] for x in ids}
    for a,b in edges:
        w=edge_distance[tuple(sorted((a,b)))]
        adj[a].append((b,w));adj[b].append((a,w))
    dist={x:math.inf for x in ids};dist[source]=0.0;q=[(0.0,source)]
    while q:
        cur,x=heapq.heappop(q)
        if cur>dist[x]+1e-12: continue
        for y,w in adj[x]:
            cand=cur+w
            if cand<dist[y]-1e-12:
                dist[y]=cand;heapq.heappush(q,(cand,y))
    if any(not math.isfinite(v) for v in dist.values()): raise Stop("disconnected graph")
    return dist

def enumerate_swaps(E, ids, edge_bin, null_index, nonce, step, seen_states):
    arr=sorted(E); candidates=[]
    for i,e1 in enumerate(arr):
        for e2 in arr[i+1:]:
            if edge_bin[e1]!=edge_bin[e2]: continue
            a,b=e1;c,d=e2
            if len({a,b,c,d})<4: continue
            for ne1,ne2 in (
                (tuple(sorted((a,c))),tuple(sorted((b,d)))),
                (tuple(sorted((a,d))),tuple(sorted((b,c)))),
            ):
                if ne1==ne2 or ne1 in E or ne2 in E: continue
                if edge_bin.get(ne1)!=edge_bin[e1] or edge_bin.get(ne2)!=edge_bin[e2]: continue
                new=(E-{e1,e2})|{ne1,ne2}; state=tuple(sorted(new))
                if state in seen_states or not is_connected(ids,new): continue
                desc="|".join("-".join(x) for x in (e1,e2,ne1,ne2))
                rank=hashlib.sha256(
                    f"Structural-boreal-birds-v1.162|{null_index}|{nonce}|{step}|{desc}".encode()
                ).hexdigest()
                candidates.append((rank,new))
    return candidates

def build_null(actual, ids, edge_bin, null_index, nonce, swaps):
    E=set(actual);seen={tuple(sorted(E))}
    for step in range(swaps):
        candidates=enumerate_swaps(E,ids,edge_bin,null_index,nonce,step,seen)
        if not candidates: return None
        _,E=min(candidates,key=lambda x:x[0]);seen.add(tuple(sorted(E)))
    return E

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    c=loadj(CONTRACT); spatial=loadj(SPATIAL); freeze=loadj(OP_FREEZE)
    coords=load_geometry();ids=sorted(coords)
    operator=freeze_connected_knn_operator(coords)
    if operator["selected_k"]!=freeze["selected_k"] or len(operator["edges"])!=freeze["edge_count"]:
        raise Stop("actual operator replay drift")
    if canonical_hash(operator)!=freeze["operator_fingerprint"]: raise Stop("operator fingerprint drift")
    pair=pairwise_distances(coords)
    def pd(e): return pair[tuple(sorted(e))]
    actual={tuple(sorted((x["left"],x["right"]))) for x in operator["edges"]}
    lengths=[pd(e) for e in actual]
    cuts=[type7_quantile(lengths,p) for p in (0.2,0.4,0.6,0.8)]
    all_pairs=[tuple(sorted((a,b))) for i,a in enumerate(ids) for b in ids[i+1:]]
    edge_bin={e:sum(pd(e)>cut for cut in cuts) for e in all_pairs}
    actual_bins={str(k):sum(edge_bin[e]==k for e in actual) for k in range(5)}
    if list(actual_bins.values())!=[7,7,7,7,7]: raise Stop("actual quintile counts not 7 each")
    deg=degree(ids,actual)
    nulls=[];seen_final={tuple(sorted(actual))}
    for idx in range(c["topology_null"]["ensemble_size"]):
        nonce=0
        while True:
            E=build_null(actual,ids,edge_bin,idx,nonce,c["topology_null"]["accepted_swaps_per_null"])
            if E is None:
                nonce+=1;continue
            state=tuple(sorted(E))
            if state not in seen_final:
                seen_final.add(state);break
            nonce+=1
        if degree(ids,E)!=deg: raise Stop("degree sequence drift")
        bins={str(k):sum(edge_bin[e]==k for e in E) for k in range(5)}
        if bins!=actual_bins or not is_connected(ids,E): raise Stop("null invariant drift")
        nulls.append({
            "null_index":idx,"nonce":nonce,"edge_count":len(E),
            "edge_bin_counts":bins,
            "edges":[{"left":a,"right":b,"distance_km_hex":float(pd((a,b))).hex(),"bin":edge_bin[(a,b)]}
                     for a,b in sorted(E)],
            "edge_set_sha256":hashlib.sha256(
                "\n".join(f"{a},{b}" for a,b in sorted(E)).encode()
            ).hexdigest(),
        })
    scale=float(operator["kernel_scale_km"])
    pilot=c["fixed_island_split"]["pilot_islands"]
    targets=c["fixed_island_split"]["confirmatory_islands"]
    shortest={x:dijkstra(ids,actual,{e:pd(e) for e in actual},x) for x in ids}
    hrows=[]
    for target in targets:
        weights=[math.exp(-shortest[target][src]/scale) for src in pilot]
        mu=math.fsum(weights)/len(weights)
        var=math.fsum((w-mu)**2 for w in weights)/len(weights)
        H=var/(mu*mu)
        hrows.append({
            "island":target,
            "H_i_hex":float(H).hex(),
            "pilot_weight_mean_hex":float(mu).hex(),
            "pilot_weight_variance_hex":float(var).hex(),
            "pilot_source_weight_hex":{src:float(math.exp(-shortest[target][src]/scale)).hex() for src in pilot}
        })
    result={
      "schema":"structural.boreal_birds_topology_null_freeze.v1_162",
      "status":"RESPONSE_INDEPENDENT_TOPOLOGY_NULLS_AND_H_SURFACE_FROZEN",
      "candidate_id":c["candidate_id"],
      "geometry_sha256":sha_file(GEOM),
      "actual_operator_fingerprint":freeze["operator_fingerprint"],
      "kernel_scale_km_hex":scale.hex(),
      "actual_edge_count":len(actual),
      "actual_degree_sequence":deg,
      "edge_length_quintile_cutpoints_km_hex":[float(x).hex() for x in cuts],
      "actual_edge_bin_counts":actual_bins,
      "null_ensemble":nulls,
      "target_configuration_heterogeneity":hrows,
      "pilot_response_opened":False,
      "confirmatory_response_opened":False,
      "bird_response_values_opened":0,
      "counts_as_empirical_evidence":False,
      "next_action":"commit this exact freeze; only then construct a separately authorized bird burned-pilot router"
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":result["status"],
      "nulls":len(nulls),
      "unique_null_edge_sets":len({x["edge_set_sha256"] for x in nulls}),
      "H_unique":len({x["H_i_hex"] for x in hrows}),
      "bird_response_values_opened":0
    },sort_keys=True))

if __name__=="__main__":
    main()
