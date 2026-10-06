#!/usr/bin/env python3
"""Freeze SW Finland t0 spatial blocks, source graph, nulls and sensitivity."""
from __future__ import annotations

import argparse,csv,hashlib,heapq,json,math
from collections import Counter,defaultdict
from pathlib import Path
from typing import Mapping,Sequence

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_topology_freeze_contract_v1_172.json"
DEFAULT_RECON=ROOT/"development/sw_finland_exact_source_reconstruction_v1_171.json"
DEFAULT_SPECIES=ROOT/"development/sw_finland_exact_source_species_v1_171.csv"
DEFAULT_MEMBERS=ROOT/"development/sw_finland_exact_source_membership_v1_171.csv"
DEFAULT_GEOMETRY=ROOT/"development/sw_finland_t0_island_geometry_v1_171.csv"

class Stop(RuntimeError):pass

def load_json(p:Path)->dict:
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise Stop(f"{p.name} must contain object")
    return x

def type7(values:Sequence[float],p:float)->float:
    xs=sorted(float(x) for x in values)
    if not xs:raise Stop("empty quantile")
    if len(xs)==1:return xs[0]
    h=(len(xs)-1)*p;lo=int(math.floor(h));hi=int(math.ceil(h))
    if lo==hi:return xs[lo]
    f=h-lo;return xs[lo]*(1-f)+xs[hi]*f

def canonical_sha(x)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def hash_mod(seed:int,attempt:int,label:str,n:int)->int:
    if n<=0:raise Stop("invalid modulus")
    h=hashlib.sha256(f"{seed}|{attempt}|{label}".encode()).digest()
    return int.from_bytes(h[:8],"big")%n

def parse_float(x,label):
    try:v=float(str(x).strip())
    except ValueError as exc:raise Stop(f"invalid {label}") from exc
    if not math.isfinite(v):raise Stop(f"nonfinite {label}")
    return v

def load_geometry(path:Path)->dict[str,tuple[float,float]]:
    rows=list(csv.DictReader(path.open("r",encoding="utf-8-sig",newline="")))
    if not rows or tuple(rows[0].keys())!=("holmkod","Euref_X_original","Euref_Y_original"):
        raise Stop("geometry schema drift")
    out={}
    for r in rows:
        i=str(r["holmkod"]).strip()
        if not i or i in out:raise Stop("blank/duplicate geometry island")
        out[i]=(parse_float(r["Euref_X_original"],"x"),parse_float(r["Euref_Y_original"],"y"))
    return out

def load_species(path:Path)->dict[str,int]:
    rows=list(csv.DictReader(path.open("r",encoding="utf-8-sig",newline="")))
    expected=("species","status","archived_absent_count","Potential_islands","historical_source_count")
    if not rows or tuple(rows[0].keys())!=expected:raise Stop("species-status schema drift")
    out={}
    for r in rows:
        if r["status"]!="exact_source_identity":continue
        sp=str(r["species"]).strip()
        if not sp or sp in out:raise Stop("blank/duplicate exact species")
        n=int(r["historical_source_count"])
        if not 1<=n<=470:raise Stop(f"invalid exact source count for {sp}")
        out[sp]=n
    return out

def verify_membership(path:Path,species:Mapping[str,int],universe:set[str])->None:
    rows=list(csv.DictReader(path.open("r",encoding="utf-8-sig",newline="")))
    if not rows or tuple(rows[0].keys())!=("species","source_holmkod"):
        raise Stop("source-membership schema drift")
    seen=set();counts=Counter()
    for r in rows:
        sp=str(r["species"]).strip();isl=str(r["source_holmkod"]).strip()
        if sp not in species:raise Stop("membership contains non-exact species")
        if isl not in universe:raise Stop("membership source outside island universe")
        key=(sp,isl)
        if key in seen:raise Stop("duplicate source membership")
        seen.add(key);counts[sp]+=1
    if set(counts)!=set(species):raise Stop("exact species missing membership")
    for sp,n in species.items():
        if counts[sp]!=n:raise Stop(f"membership count drift for {sp}")

def pairwise(coords:Mapping[str,tuple[float,float]])->dict[tuple[str,str],float]:
    ids=sorted(coords);out={}
    for a_i,a in enumerate(ids):
        ax,ay=coords[a]
        for b in ids[a_i+1:]:
            bx,by=coords[b]
            d=math.hypot(ax-bx,ay-by)/1000.0
            if not math.isfinite(d) or d<=0:raise Stop("invalid pairwise distance")
            out[(a,b)]=d
    return out

def edge_key(a,b):return (a,b) if a<b else (b,a)

def dist(D,a,b):
    if a==b:return 0.0
    return D[edge_key(a,b)]

def adjacency(ids,edges,D):
    out={i:[] for i in ids}
    for a,b in edges:
        w=dist(D,a,b);out[a].append((b,w));out[b].append((a,w))
    return out

def connected(ids,edges,D)->bool:
    A=adjacency(ids,edges,D);seen={ids[0]};stack=[ids[0]]
    while stack:
        u=stack.pop()
        for v,_ in A[u]:
            if v not in seen:seen.add(v);stack.append(v)
    return len(seen)==len(ids)

def degree_map(ids,edges):
    c=Counter()
    for a,b in edges:c[a]+=1;c[b]+=1
    return {i:c[i] for i in ids}

def minimal_connected_knn(coords,D):
    ids=sorted(coords)
    ranking={}
    for a in ids:
        ranking[a]=sorted((dist(D,a,b),b) for b in ids if b!=a)
    audit=[]
    for k in range(1,len(ids)):
        E=set()
        for a in ids:
            for _,b in ranking[a][:k]:E.add(edge_key(a,b))
        ok=connected(ids,E,D);audit.append({"k":k,"edge_count":len(E),"connected":ok})
        if ok:return k,E,audit
    raise Stop("no connected kNN graph")

def dijkstra(source,A):
    d={i:math.inf for i in A};d[source]=0.0;q=[(0.0,source)]
    while q:
        cur,u=heapq.heappop(q)
        if cur>d[u]+1e-12:continue
        for v,w in A[u]:
            z=cur+w
            if z<d[v]-1e-12:d[v]=z;heapq.heappush(q,(z,v))
    if any(not math.isfinite(x) for x in d.values()):raise Stop("disconnected shortest paths")
    return d

def edge_fp(edges,D):
    return canonical_sha([{"left":a,"right":b,"distance_hex":float(dist(D,a,b)).hex()} for a,b in sorted(edges)])

def make_length_bin(edges,D):
    vals=sorted(dist(D,*e) for e in edges)
    bounds=[type7(vals,p) for p in (0.2,0.4,0.6,0.8)]
    def b(v):
        for i,x in enumerate(bounds):
            if v<=x+1e-12:return i
        return 4
    return bounds,b

def generate_null(actual,ids,D,binfn,seed,target,max_attempts):
    E=set(actual);accepted=0;attempt=0
    while attempt<max_attempts and accepted<target:
        attempt+=1
        by={i:[] for i in range(5)}
        for e in sorted(E):by[binfn(dist(D,*e))].append(e)
        bi=hash_mod(seed,attempt,"bin",5);cand=by[bi]
        if len(cand)<2:continue
        i1=hash_mod(seed,attempt,"i1",len(cand))
        z=hash_mod(seed,attempt,"i2",len(cand)-1);i2=z if z<i1 else z+1
        (a,b),(c,d)=cand[i1],cand[i2]
        if len({a,b,c,d})<4:continue
        opts=[(edge_key(a,c),edge_key(b,d)),(edge_key(a,d),edge_key(b,c))]
        if hash_mod(seed,attempt,"orient",2):opts.reverse()
        for n1,n2 in opts:
            if n1==n2 or n1 in E or n2 in E:continue
            if binfn(dist(D,*n1))!=bi or binfn(dist(D,*n2))!=bi:continue
            P=(E-{(a,b),(c,d)})|{n1,n2}
            if connected(ids,P,D):E=P;accepted+=1;break
    if accepted!=target:raise Stop(f"null seed {seed}: only {accepted}/{target} accepted swaps")
    return E,accepted,attempt

def partition(coords,contract):
    rule=contract["spatial_validation"];blocks=defaultdict(list)
    for isl,(x,y) in coords.items():
        gx=math.floor(x/rule["grid_size_m"]);gy=math.floor(y/rule["grid_size_m"])
        bid="SWF_"+hashlib.sha256(f"{gx},{gy}".encode()).hexdigest()[:12]
        blocks[(gx,gy,bid)].append(isl)
    bitems=[]
    for (gx,gy,bid),islands in blocks.items():
        rank=hashlib.sha256(f"sw-finland-v1.165-pilot|{bid}".encode()).hexdigest()
        bitems.append((rank,bid,gx,gy,tuple(sorted(islands))))
    bitems.sort()
    n=len(bitems)
    if n<int(rule["minimum_total_blocks"]):raise Stop("too few spatial blocks")
    npilot=math.ceil(float(rule["pilot_fraction"])*n)
    if npilot<int(rule["minimum_pilot_blocks"]) or n-npilot<int(rule["minimum_confirmatory_blocks"]):
        raise Stop("pilot/confirmatory block support insufficient")
    pilot={x[1] for x in bitems[:npilot]}
    rows=[]
    for _,bid,gx,gy,islands in sorted(bitems,key=lambda z:z[1]):
        part="pilot" if bid in pilot else "confirmatory"
        for isl in islands:rows.append((isl,gx,gy,bid,part))
    rows.sort()
    return rows,n,npilot,n-npilot

def freeze(geometry_path,species_path,membership_path,recon,contract):
    if contract.get("schema")!="structural.sw_finland_topology_freeze_contract.v1_172":raise Stop("contract schema drift")
    req=contract["required_inputs"]
    if recon.get("status")!=req["source_reconstruction_status"]:raise Stop("source reconstruction not qualified")
    if recon.get("future_outcome_values_opened")!=0:raise Stop("future outcome boundary violated")
    coords=load_geometry(geometry_path)
    if len(coords)!=int(req["geometry_rows"]):raise Stop("geometry row count drift")
    species=load_species(species_path)
    if len(species)<int(req["minimum_exact_source_species"]):raise Stop("too few exact source species")
    verify_membership(membership_path,species,set(coords))

    part_rows,nblocks,npilot,nconfirm=partition(coords,contract)
    D=pairwise(coords);ids=sorted(coords)
    k,actual,audit=minimal_connected_knn(coords,D)
    edge_lengths=[dist(D,*e) for e in actual]
    scale=type7(edge_lengths,0.5)
    if scale<=0:raise Stop("invalid kernel scale")
    bounds,binfn=make_length_bin(actual,D)
    deg=degree_map(ids,actual);actual_counts=Counter(binfn(dist(D,*e)) for e in actual)
    actual_fp=edge_fp(actual,D)

    nrule=contract["matched_nulls"];target=2*len(actual);max_attempts=400*len(actual)
    topologies=[("actual",actual)]
    null_meta=[];fps=set()
    for j in range(1,int(nrule["count"])+1):
        seed=int(nrule["base_seed"])+j
        E,accepted,attempts=generate_null(actual,ids,D,binfn,seed,target,max_attempts)
        if degree_map(ids,E)!=deg:raise Stop("null degree drift")
        if Counter(binfn(dist(D,*e)) for e in E)!=actual_counts:raise Stop("null length-bin drift")
        fp=edge_fp(E,D)
        if fp==actual_fp or fp in fps:raise Stop("duplicate/actual null fingerprint")
        fps.add(fp);null_meta.append({"null_index":j,"seed":seed,"fingerprint":fp,"accepted_swaps":accepted,"attempts":attempts})
        topologies.append((f"null_{j:02d}",E))

    A=adjacency(ids,actual,D)
    context=[];hrows=[]
    for isl in ids:
        paths=dijkstra(isl,A)
        vals=[paths[x] for x in ids if x!=isl]
        total=math.fsum(vals)
        context.append((isl,len(A[isl])/(len(ids)-1), (total/(len(ids)-1)).hex(), ((len(ids)-1)/total).hex()))
        weights=[math.exp(-paths[x]/scale) for x in ids if x!=isl]
        mu=math.fsum(weights)/len(weights)
        var=math.fsum((w-mu)**2 for w in weights)/len(weights)
        H=var/(mu*mu)
        hrows.append((isl,mu.hex(),var.hex(),H.hex()))

    M=int(contract["configuration_sensitivity"]["possible_source_count_M"])
    if M!=len(ids)-1:raise Stop("M does not equal island count minus target")
    factors=[]
    for sp,n in sorted(species.items()):
        f=(M-n)/(n*(M-1))
        factors.append((sp,n,float(f).hex()))

    edge_rows=[]
    for name,E in topologies:
        for a,b in sorted(E):
            edge_rows.append((name,a,b,float(dist(D,a,b)).hex(),binfn(dist(D,a,b))))

    receipt={
      "schema":"structural.sw_finland_topology_freeze_result.v1_172",
      "status":contract["success_ceiling"]["status"],
      "candidate_id":contract["candidate_id"],
      "islands":len(ids),
      "exact_source_species":len(species),
      "spatial_blocks":nblocks,
      "pilot_blocks":npilot,
      "confirmatory_blocks":nconfirm,
      "actual_selected_k":k,
      "actual_edge_count":len(actual),
      "actual_graph_fingerprint":actual_fp,
      "kernel_scale_km_hex":float(scale).hex(),
      "edge_length_quintile_bounds_km_hex":[float(x).hex() for x in bounds],
      "actual_edge_length_bin_counts":[actual_counts[i] for i in range(5)],
      "target_swaps_per_null":target,
      "max_attempts_per_null":max_attempts,
      "null_count":len(null_meta),
      "nulls":null_meta,
      "all_nulls_unique":len(fps)==int(nrule["count"]),
      "future_outcome_values_opened":0,
      "pilot_future_outcome_authorized":False,
      "confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    return part_rows,edge_rows,context,hrows,factors,receipt

def write(path,header,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(header);w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--geometry",type=Path,default=DEFAULT_GEOMETRY)
    p.add_argument("--species",type=Path,default=DEFAULT_SPECIES)
    p.add_argument("--membership",type=Path,default=DEFAULT_MEMBERS)
    p.add_argument("--reconstruction",type=Path,default=DEFAULT_RECON)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--partition-output",type=Path,required=True)
    p.add_argument("--edges-output",type=Path,required=True)
    p.add_argument("--context-output",type=Path,required=True)
    p.add_argument("--H-output",type=Path,required=True)
    p.add_argument("--factor-output",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        outs=freeze(a.geometry,a.species,a.membership,load_json(a.reconstruction),load_json(a.contract));code=0
        part,edges,context,hrows,factors,r=outs
        write(a.partition_output,["holmkod","grid_x","grid_y","block_id","partition"],part)
        write(a.edges_output,["topology","left","right","distance_km_hex","length_bin"],edges)
        write(a.context_output,["holmkod","degree_fraction","mean_shortest_path_km_hex","closeness_per_km_hex"],context)
        write(a.H_output,["holmkod","mu_hex","sigma2_hex","H_hex"],hrows)
        write(a.factor_output,["species","historical_source_count","configuration_factor_hex"],factors)
        for key,path in {
          "partition_sha256":a.partition_output,"topology_edges_sha256":a.edges_output,
          "generic_context_sha256":a.context_output,"target_H_sha256":a.H_output,
          "species_factor_sha256":a.factor_output}.items():
            h=hashlib.sha256(path.read_bytes()).hexdigest();r[key]=h
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={"schema":"structural.sw_finland_topology_freeze_result.v1_172","status":"STOP_T0_TOPOLOGY_FREEZE","reason":str(exc),
           "future_outcome_values_opened":0,"pilot_future_outcome_authorized":False,
           "confirmatory_future_outcome_authorized":False,"counts_as_empirical_evidence":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
