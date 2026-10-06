#!/usr/bin/env python3
"""Audit t0-safe Historical_total_log tokens without reading future outcome."""
from __future__ import annotations
import argparse,csv,json,math,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

class Stop(RuntimeError): pass

def norm(x:str)->str:
    return unicodedata.normalize("NFC",str(x)).strip()

def numeric(token:str):
    try:v=float(token)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None

def audit(path:Path,router:dict,contract:dict)->dict:
    if contract.get("schema")!="structural.sw_finland_historical_total_token_audit_contract.v1_173_1":
        raise Stop("contract schema drift")
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":
        raise Stop("router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:
        raise Stop("future outcome boundary violated")

    rows=0;species_tokens=defaultdict(set);islands=set();invalid=Counter();valid_rows=0
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:raise Stop("unsafe routed schema")
        for key in ("spp.name","holmkod","Historical_total_log"):
            if key not in rd.fieldnames:raise Stop(f"missing {key}")
        for r in rd:
            rows+=1
            sp=norm(r["spp.name"]);isl=norm(r["holmkod"]);tok=str(r["Historical_total_log"]).strip()
            if not sp or not isl:raise Stop("blank species/island routing key")
            islands.add(isl);species_tokens[sp].add(tok)
            if numeric(tok) is None: invalid[tok]+=1
            else: valid_rows+=1

    expected=contract["expected_population"]
    if rows!=int(expected["rows"]):raise Stop(f"row count drift: {rows}")
    if len(species_tokens)!=int(expected["species"]):raise Stop(f"species count drift: {len(species_tokens)}")
    if len(islands)!=int(expected["islands"]):raise Stop(f"island count drift: {len(islands)}")

    inconsistent={sp:sorted(tokens) for sp,tokens in species_tokens.items() if len(tokens)!=1}
    invalid_species={}
    numeric_species=0
    for sp,tokens in sorted(species_tokens.items()):
        if len(tokens)==1:
            tok=next(iter(tokens))
            if numeric(tok) is None:invalid_species[sp]=tok
            else:numeric_species+=1
        else:
            if any(numeric(tok) is None for tok in tokens):
                invalid_species[sp]="|".join(sorted(tokens))

    return {
      "schema":"structural.sw_finland_historical_total_token_audit_result.v1_173_1",
      "status":contract["success_ceiling"]["status"],
      "candidate_id":contract["candidate_id"],
      "data_rows":rows,
      "species_count":len(species_tokens),
      "island_count":len(islands),
      "valid_numeric_rows":valid_rows,
      "nonnumeric_row_count":sum(invalid.values()),
      "nonnumeric_token_counts":dict(sorted(invalid.items())),
      "species_with_numeric_single_token":numeric_species,
      "species_with_nonnumeric_token_count":len(invalid_species),
      "species_with_nonnumeric_token":invalid_species,
      "species_with_multiple_distinct_tokens_count":len(inconsistent),
      "species_with_multiple_distinct_tokens":inconsistent,
      "future_outcome_values_opened":0,
      "protected_outcome_values_decoded":0,
      "counts_as_empirical_evidence":False
    }

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        r=audit(a.safe_csv,json.loads(a.router_receipt.read_text()),json.loads(a.contract.read_text()));code=0
    except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_historical_total_token_audit_result.v1_173_1",
          "status":"STOP_T0_HISTORICAL_TOTAL_TOKEN_AUDIT",
          "reason":str(exc),
          "future_outcome_values_opened":0,
          "protected_outcome_values_decoded":0,
          "counts_as_empirical_evidence":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
