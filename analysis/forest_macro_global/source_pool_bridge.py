#!/usr/bin/env python3
"""Operator-typed forest/island source-pool features for prospective field tests.

No empirical forest connectivity effect is claimed. The graph must be frozen
from response-free geography/matrix data; occupied donors are TRAINING-only.
Unknown occupancy must not be converted to biological absence. No eBird input.
"""
from __future__ import annotations

from collections import defaultdict
import heapq
import math

ALLOWED={"forest_fragment":"forest_matrix_movement",
         "oceanic_island":"marine_dispersal"}


def great_circle_km(a,b):
    if len(a)!=2 or len(b)!=2:raise ValueError("latitude_longitude_required")
    x1,y1=map(float,a);x2,y2=map(float,b)
    if not all(math.isfinite(x) for x in (x1,y1,x2,y2)):raise ValueError("nonfinite_coordinate")
    if max(abs(x1),abs(x2))>90 or max(abs(y1),abs(y2))>180:raise ValueError("invalid_coordinate")
    u,v=math.radians(x2-x1),math.radians(y2-y1)
    q=math.sin(u/2)**2+math.cos(math.radians(x1))*math.cos(math.radians(x2))*math.sin(v/2)**2
    return 2*6371.0088*math.asin(min(1.0,math.sqrt(max(0.0,q))))


def min_graph_cost(target, occupied, graph_edges, domain):
    adj=defaultdict(list)
    for u,v,cost in graph_edges:
        cost=float(cost)
        if not math.isfinite(cost) or cost<=0:
            raise ValueError("graph_edge_cost_must_be_positive")
        if u not in domain or v not in domain or u==v:
            raise ValueError("invalid_graph_node_or_self_edge")
        adj[u].append((v,cost));adj[v].append((u,cost))
    if not occupied:return None,0
    best={target:0.0}
    todo=[(0.0,target)]
    while todo:
        dist,node=heapq.heappop(todo)
        if dist>best[node]:continue
        if node in occupied:return dist,1
        for nxt,cost in adj[node]:
            new=dist+cost
            if new<best.get(nxt,math.inf):
                best[nxt]=new
                heapq.heappush(todo,(new,nxt))
    return None,0


def source_features(*,target, target_block, training_blocks,
                    all_nodes, donor_occupied, graph_edges,
                    origin, operator, decay_km,
                    target_sample_year=None, donor_sample_years=None):
    """Only training occupied donors. Returns support features, not predictions.

    all_nodes: node->(lat,lon), geometry fixed without outcome data
    donor_occupied: iterable of known observed occupied source nodes (not absences)
    training_blocks: node->block for training candidates ONLY
    target_block: excluded fully from feature creation
    graph_edges: response-free graph of (u,v,positive path cost [km equivalent])
    origin/operator: typed; ocean kernel is not a forest resistance surface
    """
    if origin not in ALLOWED or ALLOWED[origin]!=operator:
        raise ValueError("operator_origin_mismatch")
    if target not in all_nodes:raise ValueError("focal_target_missing_from_geometry")
    decay_km=float(decay_km)
    if not math.isfinite(decay_km) or decay_km<=0:raise ValueError("invalid_decay_scale")
    domain=set(all_nodes)
    # No held-out donor, no focal donor, and no donor with unknown geography.
    occ=set(donor_occupied)
    if occ-domain:raise ValueError("donor_occupancy_has_unknown_geometry")
    donors={x for x in occ if x!=target and x in training_blocks and training_blocks[x]!=target_block}
    if target_sample_year is not None:
        if donor_sample_years is None:raise ValueError("source_dates_required_for_temporal_prediction")
        if any(x not in donor_sample_years for x in donors):
            raise ValueError("dated_donor_missing_year")
        donors={x for x in donors if donor_sample_years[x]<=target_sample_year}
    direct=[great_circle_km(all_nodes[target],all_nodes[d]) for d in donors]
    nearest=min(direct) if direct else None
    pressure=sum(math.exp(-d/decay_km) for d in direct)
    graph_dist,reachable=min_graph_cost(target,donors,graph_edges,domain)
    return {
        "origin":origin,
        "operator":operator,
        "training_occupied_source_count":len(donors),
        "euclidean_nearest_occupied_source_km":nearest,
        "euclidean_diffuse_occupied_source_pressure":pressure,
        "graph_nearest_occupied_source_cost":graph_dist,
        "graph_source_reachable":bool(reachable),
        "species_specific_heldout_target_outcome_accessed":False,
        "unobserved_patches_assumed_absent":False,
        "source_loss_or_demographic_transition_identified":False
    }
