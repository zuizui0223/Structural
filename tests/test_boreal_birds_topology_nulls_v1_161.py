from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_boreal_birds_topology_nulls_v1_161.py"
CONTRACT=ROOT/"development/boreal_birds_topology_null_contract_v1_161.json"
GEOMETRY=ROOT/"development/boreal_19island_safe_geometry_v0_97.csv"
GF=ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"
SF=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"
OF=ROOT/"development/boreal_19island_source_operator_freeze_v1_01.json"

def load_module():
    spec=importlib.util.spec_from_file_location("birdnull161",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_contract_keeps_bird_response_sealed():
    x=json.loads(CONTRACT.read_text())
    assert x["response_boundary"]["bird_file_opened"] is False
    assert x["response_boundary"]["bird_response_values_opened"]==0
    assert x["response_boundary"]["pilot_response_authorized"] is False
    assert x["response_boundary"]["confirmatory_response_authorized"] is False
    assert x["null_ensemble"]["count"]==20
    assert x["configuration_sensitivity"]["M"]==6

def test_actual_geometry_freezes_twenty_matched_nulls_and_s_surface():
    m=load_module()
    ensemble,surface,receipt=m.run(CONTRACT,GEOMETRY,GF,SF,OF)
    e=json.loads(ensemble)
    assert e["status"]=="RESPONSE_INDEPENDENT_NULL_ENSEMBLE_FROZEN"
    assert len(e["actual_edges"])==35
    assert len(e["nulls"])==20
    assert len({n["seed"] for n in e["nulls"]})==20
    actual_degree={}
    for edge in e["actual_edges"]:
        for node in (edge["left"],edge["right"]):
            actual_degree[node]=actual_degree.get(node,0)+1
    actual_bins={}
    for edge in e["actual_edges"]:
        b=str(edge["edge_length_bin"]);actual_bins[b]=actual_bins.get(b,0)+1
    seen=set()
    actual_pairs=frozenset((x["left"],x["right"]) for x in e["actual_edges"])
    for null in e["nulls"]:
        pairs=frozenset((x["left"],x["right"]) for x in null["edges"])
        assert pairs not in seen;seen.add(pairs)
        assert len(pairs)==35
        assert len(pairs^actual_pairs)>=4
        degree={}
        bins={}
        for edge in null["edges"]:
            for node in (edge["left"],edge["right"]):
                degree[node]=degree.get(node,0)+1
            b=str(edge["edge_length_bin"]);bins[b]=bins.get(b,0)+1
        assert degree==actual_degree
        assert bins==actual_bins
    rows=list(csv.DictReader(surface.splitlines()))
    assert len(rows)==78
    assert {r["target"] for r in rows}==set(json.loads(CONTRACT.read_text())["configuration_sensitivity"]["targets"])
    assert {int(r["n"]) for r in rows}=={1,2,3,4,5,6}
    rr=json.loads(receipt)
    assert rr["null_count"]==20
    assert rr["sensitivity_row_count"]==78
    assert rr["bird_file_opened"] is False
    assert rr["bird_response_values_opened"]==0
