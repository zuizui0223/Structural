#!/usr/bin/env python3
"""Build the response-free one-shot authorization for the boreal bird pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/boreal_19island_bird_pilot_authorization_contract_v1_163.json"
DEFAULT_PROTOCOL=ROOT/"development/boreal_bird_topology_sensitivity_contract_v1_162.json"
DEFAULT_TOPOLOGY=ROOT/"development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
DEFAULT_FULL=ROOT/"development/boreal_lake_islands_thesis_safe_table_v0_69.json"
DEFAULT_METADATA=ROOT/"development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
DEFAULT_SPATIAL=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"
DEFAULT_GEOMETRY=ROOT/"development/boreal_19island_safe_geometry_freeze_v0_97.json"


class BirdPilotAuthorizationError(RuntimeError):
    pass


def load(path:Path)->dict:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise BirdPilotAuthorizationError(f"{path.name} must contain an object")
    return value


def canonical_sha256(value:Mapping)->str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build(*,contract:Mapping,protocol:Mapping,topology:Mapping,full:Mapping,metadata:Mapping,spatial:Mapping,geometry:Mapping)->dict:
    if contract.get("schema")!="structural.boreal_19island_bird_pilot_authorization_contract.v1_163":
        raise BirdPilotAuthorizationError("unexpected authorization contract schema")
    if protocol.get("status")!=contract["required_parent_state"]["protocol_status"]:
        raise BirdPilotAuthorizationError("protocol status drift")
    if topology.get("status")!=contract["required_parent_state"]["topology_status"]:
        raise BirdPilotAuthorizationError("topology status drift")
    if topology["null_ensemble"]["count"]!=20 or topology["null_ensemble"]["unique_topologies"]!=20:
        raise BirdPilotAuthorizationError("topology null ensemble drift")
    if protocol["response_boundary"]["bird_pilot_opened"] is not False:
        raise BirdPilotAuthorizationError("bird pilot already opened")
    if protocol["response_boundary"]["bird_confirmatory_opened"] is not False:
        raise BirdPilotAuthorizationError("bird confirmatory already opened")
    if protocol["response_boundary"]["eBird_enabled"] is not False:
        raise BirdPilotAuthorizationError("eBird policy drift")

    response=protocol["response_file"]
    focal=metadata["focal_files"][response["name"]]
    if focal["sha256"]!=response["expected_sha256"] or focal["file_id"]!=response["dryad_file_id"]:
        raise BirdPilotAuthorizationError("bird response identity drift")
    if focal["size"]!=response["expected_size_bytes"]:
        raise BirdPilotAuthorizationError("bird response size drift")

    full_order=list(full["current_study_island_universe"]["codes"])
    analysis_order=list(geometry["island_order"])
    pilot=list(spatial["pilot_islands"])
    confirmatory=list(spatial["confirmatory_islands"])
    if len(full_order)!=42 or len(set(full_order))!=42:
        raise BirdPilotAuthorizationError("full island universe drift")
    if len(analysis_order)!=19 or set(pilot)|set(confirmatory)!=set(analysis_order):
        raise BirdPilotAuthorizationError("analysis island universe drift")
    excluded=sorted(set(full_order)-set(analysis_order))
    if len(pilot)!=6 or len(confirmatory)!=13 or len(excluded)!=23:
        raise BirdPilotAuthorizationError("pilot/confirmatory/excluded count drift")

    core={
      "schema":"structural.boreal_19island_bird_pilot_authorization.v1_163",
      "status":"AUTHORIZED_ONE_SHOT_BIRD_PILOT_ONLY",
      "candidate_id":contract["candidate_id"],
      "response_file":{
        "name":response["name"],
        "dryad_file_id":response["dryad_file_id"],
        "download_url":f"https://datadryad.org/api/v2/files/{response['dryad_file_id']}/download",
        "size_bytes":response["expected_size_bytes"],
        "sha256":response["expected_sha256"],
        "expected_species_columns":response["reported_species_count"],
        "expected_full_source_island_rows":response["reported_island_count"],
      },
      "full_source_island_order":full_order,
      "analysis_island_order":analysis_order,
      "pilot_islands":pilot,
      "confirmatory_islands":confirmatory,
      "excluded_islands":excluded,
      "pilot_block_ids":list(spatial["pilot_block_ids"]),
      "confirmatory_block_ids":list(spatial["confirmatory_block_ids"]),
      "island_to_block":dict(spatial["island_to_block"]),
      "topology_parent":{
        "actual_edge_fingerprint":topology["actual_graph"]["edge_fingerprint"],
        "null_edge_fingerprints":[x["edge_fingerprint"] for x in topology["null_ensemble"]["nulls"]],
        "bird_response_sha256":topology["parents"]["bird_response_sha256"],
      },
      "allowed_semantic_access":dict(contract["semantic_access"]),
      "pilot_gate":dict(contract["pilot_gate"]),
      "one_shot":dict(contract["one_shot"]),
      "authorization_consumed":False,
      "response_values_opened_by_authorization":False,
      "pilot_response_authorized":True,
      "confirmatory_response_authorized":False,
      "effect_size":None,
      "prediction_score":None,
      "counts_as_empirical_evidence":False,
    }
    core["authorization_fingerprint"]=canonical_sha256(core)
    return core


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--protocol",type=Path,default=DEFAULT_PROTOCOL)
    p.add_argument("--topology",type=Path,default=DEFAULT_TOPOLOGY)
    p.add_argument("--full",type=Path,default=DEFAULT_FULL)
    p.add_argument("--metadata",type=Path,default=DEFAULT_METADATA)
    p.add_argument("--spatial",type=Path,default=DEFAULT_SPATIAL)
    p.add_argument("--geometry",type=Path,default=DEFAULT_GEOMETRY)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    result=build(
      contract=load(a.contract),protocol=load(a.protocol),topology=load(a.topology),
      full=load(a.full),metadata=load(a.metadata),spatial=load(a.spatial),geometry=load(a.geometry)
    )
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(text,encoding="utf-8")
    print(text,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
