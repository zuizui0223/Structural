#!/usr/bin/env python3
"""Validate the terminal GIFT burned-pilot STOP without reopening any response."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TERMINAL_SCHEMA="structural.gift_global_archipelago_burned_pilot_terminal.v0_1"

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return x

def canonical_sha(value)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--universe",type=Path,required=True)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--geology-crosswalk",type=Path,required=True)
    p.add_argument("--terminal-receipt",type=Path,required=True)
    a=p.parse_args()

    u=load(a.universe)
    protocol=load(a.protocol)
    geology=load(a.geology_crosswalk)
    terminal=load(a.terminal_receipt)

    if terminal.get("schema")!=TERMINAL_SCHEMA:
        raise RuntimeError("unexpected terminal receipt schema")
    if terminal.get("status")!="TERMINAL_STOP_NON_ESTIMABLE":
        raise RuntimeError("GIFT v0.1 is not frozen terminal STOP")
    if terminal.get("pilot_pass") is not False:
        raise RuntimeError("terminal receipt unexpectedly records pilot PASS")
    if terminal.get("confirmatory_response_authorized") is not False:
        raise RuntimeError("terminal receipt authorizes confirmatory response")

    if u.get("universe_fingerprint")!=terminal.get("analysis_universe_fingerprint"):
        raise RuntimeError("analysis universe drift after burned pilot")
    if protocol.get("protocol_fingerprint")!=terminal.get("protocol_fingerprint"):
        raise RuntimeError("study protocol drift after burned pilot")
    if geology.get("crosswalk_fingerprint")!=terminal.get("geology_crosswalk_fingerprint"):
        raise RuntimeError("geology crosswalk drift after burned pilot")

    ep=protocol["evidence_partition"]
    if ep.get("pilot_list_id_set_sha256")!=terminal.get("pilot_list_set_sha256"):
        raise RuntimeError("pilot list surface drift")
    if ep.get("confirmatory_list_id_set_sha256")!=terminal.get("confirmatory_list_set_sha256"):
        raise RuntimeError("confirmatory list surface drift")
    if ep.get("pilot_confirmatory_list_overlap")!=0:
        raise RuntimeError("pilot/confirmatory list surfaces overlap")

    access=terminal.get("response_access",{})
    expected_access={
        "confirmatory_list_query_count":0,
        "confirmatory_response_opened":False,
        "effect_size":None,
        "model_fits":0,
        "pilot_response_opened":True,
        "prediction_score":None,
        "predictive_denominator_contribution":0,
    }
    if access!=expected_access:
        raise RuntimeError("terminal response-access ceiling drift")

    correction=terminal.get("implementation_correction",{})
    if correction.get("new_response_queries_for_correction")!=0:
        raise RuntimeError("implementation correction spent new response queries")
    if correction.get("raw_response_reused_unchanged") is not True:
        raise RuntimeError("implementation correction did not reuse raw response")
    if correction.get("initial_stop_direction_changed") is not False:
        raise RuntimeError("implementation correction changed terminal STOP direction")

    audits=terminal.get("archipelago_audits")
    if not isinstance(audits,list) or len(audits)!=3:
        raise RuntimeError("terminal pilot must contain exactly three archipelago audits")
    by_id={row["archipelago_id"]:row for row in audits}
    expected={
        "Agean and Southern Greece Islands / North-west Agaean Sea Islands":(559,True),
        "Tuvalu":(5,False),
        "West Indies / Lesser Antilles / Leeward Islands":(569,True),
    }
    if set(by_id)!=set(expected):
        raise RuntimeError("terminal pilot archipelago identities drifted")
    for aid,(n,passed) in expected.items():
        row=by_id[aid]
        if row.get("estimable_species")!=n or row.get("archipelago_pass") is not passed:
            raise RuntimeError(f"terminal estimability drift for {aid}")

    all_three=all(row["archipelago_pass"] for row in audits)
    if all_three:
        raise RuntimeError("terminal STOP no longer justified by frozen pass rule")
    if terminal.get("species_archipelago_pairs_checked")!=4827:
        raise RuntimeError("checked species-archipelago count drift")
    if terminal.get("species_archipelago_pairs_estimable")!=1133:
        raise RuntimeError("estimable species-archipelago count drift")

    raw_hash=terminal.get("raw_pilot_response_sha256")
    if raw_hash!="6e63a66daae6a0107c9dca2c2336d2cea6a52cf28c6104689dfadd05195930e3":
        raise RuntimeError("raw burned-pilot response fingerprint drift")

    supplied=terminal.get("terminal_receipt_sha256")
    payload=dict(terminal)
    payload.pop("terminal_receipt_sha256",None)
    observed=canonical_sha(payload)
    if supplied!=observed:
        raise RuntimeError(
            f"terminal receipt SHA mismatch: {supplied} != {observed}"
        )

    out={
        "schema":"structural.gift_terminal_validation.v0_1",
        "status":"TERMINAL_STOP_REPLAY_VALID",
        "analysis_universe_fingerprint":u["universe_fingerprint"],
        "protocol_fingerprint":protocol["protocol_fingerprint"],
        "geology_crosswalk_fingerprint":geology["crosswalk_fingerprint"],
        "terminal_receipt_sha256":supplied,
        "pilot_response_reopened":False,
        "confirmatory_response_opened":False,
        "confirmatory_response_authorized":False,
        "effect_size":None,
        "prediction_score":None,
    }
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
