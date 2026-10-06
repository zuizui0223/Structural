#!/usr/bin/env python3
"""Consume the one-shot boreal bird pilot authorization and freeze its snapshot."""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from typing import Mapping

from structural.boreal_19island_bird_pilot_router import (
    Boreal19BirdPilotRouterError,
    build_boreal_19island_bird_pilot_surface,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_AUTH=ROOT/"development/boreal_19island_bird_pilot_authorization_v1_163.json"
DEFAULT_TOPOLOGY=ROOT/"development/boreal_19island_topology_sensitivity_freeze_v1_162.json"

class Stop(RuntimeError): pass

def load(path):
    x=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise Stop(f"{Path(path).name} must contain object")
    return x

def canonical_sha256(x:Mapping)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def sha256_bytes(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def validate_authorization(auth,topology,response_bytes):
    if auth.get("schema")!="structural.boreal_19island_bird_pilot_authorization.v1_163": raise Stop("authorization schema drift")
    if auth.get("status")!="AUTHORIZED_ONE_SHOT_BIRD_PILOT_ONLY": raise Stop("authorization status drift")
    core=dict(auth);fp=core.pop("authorization_fingerprint",None)
    if fp!=canonical_sha256(core): raise Stop("authorization fingerprint mismatch")
    if auth.get("authorization_consumed") is not False: raise Stop("authorization already consumed")
    if auth.get("pilot_response_authorized") is not True: raise Stop("pilot not authorized")
    if auth.get("confirmatory_response_authorized") is not False: raise Stop("confirmatory ceiling violated")
    target=auth["response_file"]
    if len(response_bytes)!=target["size_bytes"] or sha256_bytes(response_bytes)!=target["sha256"]: raise Stop("bird response exact-byte identity mismatch")
    if topology.get("status")!="RESPONSE_FREE_TOPOLOGY_NULL_AND_SENSITIVITY_SURFACE_FROZEN": raise Stop("topology parent not frozen")
    if topology["actual_graph"]["edge_fingerprint"]!=auth["topology_parent"]["actual_edge_fingerprint"]: raise Stop("actual topology drift")
    fps=[x["edge_fingerprint"] for x in topology["null_ensemble"]["nulls"]]
    if fps!=auth["topology_parent"]["null_edge_fingerprints"]: raise Stop("null topology drift")


def build_snapshot(auth,topology,routed,qualified):
    base=routed.base
    n_by_species=[{"species":s,"n":n} for s,n in routed.pilot_occupancy_count_by_species]
    snapshot={
      "schema":"structural.boreal_19island_bird_pilot_snapshot.v1_164",
      "status":"BIRD_PILOT_SNAPSHOT_FROZEN_FROM_SINGLE_SEMANTIC_OPEN",
      "candidate_id":auth["candidate_id"],
      "response_file_sha256":auth["response_file"]["sha256"],
      "authorization_fingerprint":auth["authorization_fingerprint"],
      "topology_actual_edge_fingerprint":topology["actual_graph"]["edge_fingerprint"],
      "topology_null_edge_fingerprints":auth["topology_parent"]["null_edge_fingerprints"],
      "raw_pilot_surface_sha256":base.raw_surface_sha256,
      "fixed_species_order":list(base.pilot_species_universe),
      "fixed_species_count":base.pilot_species_universe_count,
      "fixed_species_sha256":base.pilot_species_universe_sha256,
      "pilot_occupancy_count_by_species":n_by_species,
      "distinct_pilot_occupancy_counts":list(routed.distinct_pilot_occupancy_counts),
      "pilot_island_order":list(base.pilot_island_order),
      "pilot_island_to_block":dict(base.pilot_island_to_block),
      "targets_hex_by_island":dict(base.pilot_targets_hex_by_island),
      "pilot_target_values_parsed":base.pilot_target_values_parsed,
      "confirmatory_target_values_parsed":0,
      "excluded_target_values_parsed":0,
      "confirmatory_occurrence_values_stored":False,
      "excluded_occurrence_values_stored":False,
      "qualified_for_prediction_freeze":bool(qualified),
    }
    snapshot["snapshot_fingerprint"]=canonical_sha256(snapshot)
    return snapshot


def execute(auth,topology,response_bytes):
    validate_authorization(auth,topology,response_bytes)
    semantic_started=False
    try:
        semantic_started=True
        routed=build_boreal_19island_bird_pilot_surface(
          response_csv_bytes=response_bytes,
          full_expected_islands=auth["full_source_island_order"],
          analysis_expected_islands=auth["analysis_island_order"],
          analysis_island_to_block=auth["island_to_block"],
          pilot_partition=auth["pilot_block_ids"],
          confirmatory_partition=auth["confirmatory_block_ids"],
          expected_species_count=auth["response_file"]["expected_species_columns"],
        )
    except Boreal19BirdPilotRouterError as exc:
        raise Stop(str(exc)) from exc

    fixed=routed.base.pilot_species_universe_count
    distinct=tuple(routed.distinct_pilot_occupancy_counts)
    gate=auth["pilot_gate"]
    allowed=set(gate["allowed_n"])
    if any(n not in allowed for n in distinct): raise Stop("pilot n outside frozen domain")
    qualified=(fixed>=gate["minimum_fixed_species"] and len(distinct)>=gate["minimum_distinct_n"])
    snapshot=build_snapshot(auth,topology,routed,qualified)
    histogram=Counter(n for _,n in routed.pilot_occupancy_count_by_species)
    result={
      "schema":"structural.boreal_19island_bird_pilot_execution.v1_164",
      "status":("BIRD_PILOT_QUALIFIED_TO_FREEZE_PREDICTIONS" if qualified else "BIRD_PILOT_TERMINAL_ESTIMABILITY_STOP"),
      "candidate_id":auth["candidate_id"],
      "authorization_fingerprint":auth["authorization_fingerprint"],
      "authorization_consumed":True,
      "bird_pilot_opened":True,
      "fixed_species_count":fixed,
      "fixed_species_sha256":routed.base.pilot_species_universe_sha256,
      "distinct_pilot_occupancy_counts":list(distinct),
      "pilot_occupancy_histogram":{str(k):histogram[k] for k in sorted(histogram)},
      "pilot_target_values_parsed":routed.base.pilot_target_values_parsed,
      "confirmatory_target_values_parsed":0,
      "excluded_target_values_parsed":0,
      "model_snapshot_frozen":True,
      "model_snapshot_fingerprint":snapshot["snapshot_fingerprint"],
      "qualified_for_prediction_freeze":bool(qualified),
      "effect_size":None,
      "prediction_score":None,
      "predictive_denominator_contribution":0,
      "counts_as_empirical_evidence":False,
      "confirmatory_response_authorized":False,
      "eligible_action":("freeze_bird_actual_and_20_null_prediction_surfaces" if qualified else None),
    }
    return result,snapshot


def main():
    p=argparse.ArgumentParser();p.add_argument("response_csv",type=Path);p.add_argument("--authorization",type=Path,default=DEFAULT_AUTH);p.add_argument("--topology",type=Path,default=DEFAULT_TOPOLOGY);p.add_argument("--execution-receipt",type=Path);p.add_argument("--snapshot",type=Path)
    a=p.parse_args();semantic_started=False
    try:
        auth=load(a.authorization);topology=load(a.topology);raw=a.response_csv.read_bytes()
        validate_authorization(auth,topology,raw)
        semantic_started=True
        result,snapshot=execute(auth,topology,raw)
        code=0 if result["qualified_for_prediction_freeze"] else 2
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,Stop,Boreal19BirdPilotRouterError) as e:
        result={
          "schema":"structural.boreal_19island_bird_pilot_execution.v1_164",
          "status":("BIRD_PILOT_TERMINAL_AFTER_SEMANTIC_OPEN" if semantic_started else "STOP_PRE_ACCESS"),
          "reason":str(e),
          "authorization_consumed":bool(semantic_started),
          "bird_pilot_opened":bool(semantic_started),
          "confirmatory_target_values_parsed":0,
          "excluded_target_values_parsed":0,
          "model_snapshot_frozen":False,
          "effect_size":None,"prediction_score":None,"predictive_denominator_contribution":0,
          "counts_as_empirical_evidence":False,"confirmatory_response_authorized":False,
          "eligible_action":None,
        };snapshot=None;code=2
    if snapshot is not None and a.snapshot:
        a.snapshot.parent.mkdir(parents=True,exist_ok=True);a.snapshot.write_text(json.dumps(snapshot,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.execution_receipt:a.execution_receipt.parent.mkdir(parents=True,exist_ok=True);a.execution_receipt.write_text(text,encoding="utf-8")
    print(text,end="");return code
if __name__=="__main__": raise SystemExit(main())
