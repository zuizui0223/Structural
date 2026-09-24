#!/usr/bin/env python3
"""Replay a frozen fresh-taxon terminal STOP without reopening response."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

SCHEMA="structural.gift_fresh_taxon_burned_pilot_terminal.v0_1"

def load(path):
    x=json.loads(Path(path).read_text())
    if not isinstance(x,dict): raise RuntimeError(f"{path} must contain object")
    return x

def sha(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--terminal",type=Path,required=True)
    ap.add_argument("--universe",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--lock",type=Path,required=True)
    a=ap.parse_args()

    t=load(a.terminal); u=load(a.universe); p=load(a.protocol); lock=load(a.lock)
    taxon=t.get("taxon_name")
    if t.get("schema")!=SCHEMA: raise RuntimeError("terminal schema drift")
    if t.get("status")!="TERMINAL_STOP_NON_ESTIMABLE": raise RuntimeError("not terminal STOP")
    if t.get("pilot_pass") is not False: raise RuntimeError("terminal unexpectedly passed")
    if t.get("confirmatory_response_authorized") is not False: raise RuntimeError("confirmatory response authorized")
    if t.get("cross_taxon_secondary_authorized") is not False: raise RuntimeError("cross-taxon secondary authorized")
    if taxon not in lock["systems"]: raise RuntimeError("taxon absent from pre-response lock")

    exp=lock["systems"][taxon]
    if t["pre_response_green_commit"]!=lock["pre_response_green_commit"]: raise RuntimeError("pre-response commit drift")
    if t["candidate_selection_fingerprint"]!=lock["candidate_selection_fingerprint"]: raise RuntimeError("selection drift")
    if t["universe_fingerprint"]!=u["universe_fingerprint"] or t["universe_fingerprint"]!=exp["universe_fingerprint"]: raise RuntimeError("universe drift")
    if t["protocol_fingerprint"]!=p["protocol_fingerprint"] or t["protocol_fingerprint"]!=exp["protocol_fingerprint"]: raise RuntimeError("protocol drift")
    if t["pilot_list_set_sha256"]!=p["pilot_selection"]["pilot_list_set_sha256"]: raise RuntimeError("pilot list surface drift")
    if t["confirmatory_list_set_sha256"]!=p["pilot_selection"]["confirmatory_list_set_sha256"]: raise RuntimeError("confirmatory list surface drift")
    if p["pilot_selection"]["list_overlap"]!=0: raise RuntimeError("pilot/confirmatory overlap")

    access=t.get("response_access",{})
    expected={
        "pilot_response_opened":True,
        "confirmatory_response_opened":False,
        "confirmatory_list_query_count":0,
        "model_fits":0,
        "effect_size":None,
        "prediction_score":None,
        "predictive_denominator_contribution":0,
    }
    if access!=expected: raise RuntimeError("response-access ceiling drift")

    audits=t.get("archipelago_audits")
    if not isinstance(audits,list) or len(audits)!=3: raise RuntimeError("expected 3 pilot archipelagos")
    passing=[r for r in audits if r.get("archipelago_pass") is True]
    has_extreme=any(r.get("support_class") in {"extreme_only","paired"} for r in passing)
    has_nonextreme=any(r.get("support_class") in {"nonextreme_only","paired"} for r in passing)
    recomputed_pass=len(passing)>=2 and has_extreme and has_nonextreme
    if recomputed_pass: raise RuntimeError("frozen audit now satisfies pass rule")
    if t.get("species_archipelago_pairs_estimable",0)>t.get("species_archipelago_pairs_checked",0):
        raise RuntimeError("estimable pairs exceed checked pairs")

    supplied=t.get("terminal_receipt_sha256")
    unsigned=dict(t); unsigned.pop("terminal_receipt_sha256",None)
    if sha(unsigned)!=supplied: raise RuntimeError("terminal receipt hash drift")

    out={
        "schema":"structural.gift_fresh_taxon_terminal_validation.v0_1",
        "status":"TERMINAL_STOP_REPLAY_VALID",
        "taxon_name":taxon,
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
