#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"development/source_loss_leverage_intake_contract_v1_126.json"

class Stop(RuntimeError):
    pass

def adjudicate(candidate:dict, contract:dict)->dict:
    required=contract["required_metadata_fields"]
    missing=[k for k in required if k not in candidate or candidate[k] in (None,"",[])]
    if missing:
        return {"status":"HOLD_METADATA_INCOMPLETE","missing_fields":missing,"response_access_authorized":False}

    if int(candidate["ordered_wave_count"]) < int(contract["hard_gates"]["ordered_wave_count_min"]):
        return {"status":"STOP_TWO_WAVE","reason":"fewer than three ordered waves","response_access_authorized":False}

    if candidate.get("response_values_currently_unopened") is not True:
        return {"status":"STOP_RESPONSE_EXPOSED","reason":"future occupancy response is already exposed for proposed hypothesis","response_access_authorized":False}

    if candidate.get("stable_unit_ids") is not True or candidate.get("stable_species_ids") is not True:
        return {"status":"HOLD_METADATA_INCOMPLETE","reason":"stable unit/species IDs unresolved","response_access_authorized":False}

    if candidate.get("response_is_occupancy_or_presence_absence") is not True:
        return {"status":"HOLD_METADATA_INCOMPLETE","reason":"endpoint semantics are not occupancy/presence-absence","response_access_authorized":False}

    if candidate.get("geometry_available_response_independently") is not True:
        return {"status":"STOP_NO_GEOMETRY","reason":"source leverage cannot be frozen response-independently","response_access_authorized":False}

    overlap=str(candidate.get("known_overlap_with_existing_structural_systems","")).strip().lower()
    if overlap in {"same response","same_response","reused response","reused_response"}:
        return {"status":"STOP_NONINDEPENDENT_RESPONSE","reason":"candidate reuses an existing Structural biological response","response_access_authorized":False}

    waves=candidate["wave_labels"]
    if not isinstance(waves,list) or len(waves)<3 or len(set(map(str,waves)))<3:
        return {"status":"HOLD_METADATA_INCOMPLETE","reason":"three distinct ordered wave labels are not resolved","response_access_authorized":False}

    return {
      "status":"QUALIFIED_METADATA_ONLY",
      "candidate_id":candidate["candidate_id"],
      "next_action":"freeze exact source identity, response domain, t0/t1/t2 semantics, response-independent geometry and disjoint burned-pilot/confirmatory partitions",
      "response_access_authorized":False,
      "counts_as_empirical_evidence":False
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("candidate_json",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    contract=json.loads(a.contract.read_text())
    candidate=json.loads(a.candidate_json.read_text())
    if contract.get("schema")!="structural.source_loss_leverage_intake_contract.v1_126":
        raise Stop("contract schema drift")
    out=adjudicate(candidate,contract)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out["status"] in {"QUALIFIED_METADATA_ONLY","HOLD_METADATA_INCOMPLETE"} else 2

if __name__=="__main__":
    raise SystemExit(main())
