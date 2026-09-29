from __future__ import annotations
import heapq, math
from dataclasses import dataclass
from typing import Mapping, Sequence

EARTH_RADIUS_KM=6371.0088

class MacroSourceFeatureError(RuntimeError):
    pass

@dataclass(frozen=True)
class MacroSourceFeatures:
    nearest_euclidean_km: float
    euclidean_pressure: float
    nearest_graph_km: float
    graph_pressure: float

def haversine_km(a: tuple[float,float], b: tuple[float,float]) -> float:
    lat1,lon1=a; lat2,lon2=b
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*EARTH_RADIUS_KM*math.asin(min(1.0,math.sqrt(x)))

def adjacency_from_edges(ids: Sequence[str], edges: Sequence[tuple[str,str,float]]) -> dict[str,list[tuple[str,float]]]:
    out={str(i):[] for i in ids}
    for a,b,d in edges:
        a=str(a);b=str(b);d=float(d)
        if a not in out or b not in out or a==b or not math.isfinite(d) or d<=0:
            raise MacroSourceFeatureError("invalid frozen graph edge")
        out[a].append((b,d));out[b].append((a,d))
    return out

def dijkstra(target: str, adjacency: Mapping[str,Sequence[tuple[str,float]]]) -> dict[str,float]:
    if target not in adjacency: raise MacroSourceFeatureError("target outside graph")
    dist={target:0.0}; q=[(0.0,target)]
    while q:
        d,u=heapq.heappop(q)
        if d!=dist[u]: continue
        for v,w in adjacency[u]:
            nd=d+w
            if nd < dist.get(v,math.inf):
                dist[v]=nd;heapq.heappush(q,(nd,v))
    return dist

def source_features(
    *,
    target: str,
    occupied_sources: Sequence[str],
    coordinates: Mapping[str,tuple[float,float]],
    pool_by_id: Mapping[str,str],
    adjacency_by_pool: Mapping[str,Mapping[str,Sequence[tuple[str,float]]]],
    scale_by_pool: Mapping[str,float],
    max_edge_by_pool: Mapping[str,float],
    node_count_by_pool: Mapping[str,int],
) -> MacroSourceFeatures:
    target=str(target)
    if target not in coordinates or target not in pool_by_id:
        raise MacroSourceFeatureError("target missing response-independent context")
    pool=pool_by_id[target]
    scale=float(scale_by_pool[pool])
    if not math.isfinite(scale) or scale<=0: raise MacroSourceFeatureError("invalid pool scale")
    sources=sorted({str(s) for s in occupied_sources if str(s)!=target})
    if any(s not in coordinates for s in sources):
        raise MacroSourceFeatureError("source outside coordinate universe")

    if sources:
        ed=[haversine_km(coordinates[target],coordinates[s]) for s in sources]
        nearest_e=min(ed)
        pressure_e=math.fsum(math.exp(-d/scale) for d in ed)
    else:
        nearest_e=math.pi*EARTH_RADIUS_KM+scale
        pressure_e=0.0

    adj=adjacency_by_pool[pool]
    paths=dijkstra(target,adj)
    reachable=[s for s in sources if s in paths]
    if reachable:
        gd=[paths[s] for s in reachable]
        nearest_g=min(gd)
        pressure_g=math.fsum(math.exp(-d/scale) for d in gd)
    else:
        n=int(node_count_by_pool[pool]); mx=float(max_edge_by_pool[pool])
        if n<2 or not math.isfinite(mx) or mx<=0:
            raise MacroSourceFeatureError("invalid graph sentinel context")
        nearest_g=(n-1)*mx+scale
        pressure_g=0.0
    return MacroSourceFeatures(float(nearest_e),float(pressure_e),float(nearest_g),float(pressure_g))

def jeffreys_logit(successes: int, trials: int) -> float:
    if isinstance(successes,bool) or isinstance(trials,bool):
        raise MacroSourceFeatureError("invalid binomial counts")
    successes=int(successes);trials=int(trials)
    if trials<0 or successes<0 or successes>trials:
        raise MacroSourceFeatureError("invalid binomial counts")
    p=(successes+0.5)/(trials+1.0)
    return math.log(p/(1.0-p))
