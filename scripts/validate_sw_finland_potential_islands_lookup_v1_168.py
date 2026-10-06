#!/usr/bin/env python3
"""Validate a t0-only SW Finland Potential_islands lookup.

Input must already be a safe two-column projection. This validator refuses
published future colonization-summary columns by construction.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_potential_islands_lookup_contract_v1_168.json"

class Stop(RuntimeError): pass

def norm_species(x:str)->str:
    return unicodedata.normalize("NFC",str(x)).strip()

def sha256_file(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def validate(path:Path,contract:dict)->tuple[list[dict],dict]:
    if contract.get("schema")!="structural.sw_finland_potential_islands_lookup_contract.v1_168":
        raise Stop("contract schema drift")
    rows=list(csv.DictReader(path.open("r",encoding="utf-8-sig",newline="")))
    if not rows:raise Stop("empty supplementary lookup")
    if tuple(rows[0].keys())!=("species","Potential_islands"):
        raise Stop("safe lookup must contain exactly species,Potential_islands")
    expected=int(contract["validation"]["expected_unique_species"])
    seen={}
    out=[]
    for row in rows:
        sp=norm_species(row["species"])
        if not sp or sp in seen:raise Stop("blank/duplicate species")
        try:p=int(str(row["Potential_islands"]).strip())
        except ValueError as exc:raise Stop(f"invalid Potential_islands for {sp}") from exc
        if not 0<=p<=471:raise Stop(f"Potential_islands outside [0,471] for {sp}")
        seen[sp]=p
        out.append({"species":sp,"Potential_islands":p,"historical_source_count":471-p})
    if len(seen)!=expected:
        raise Stop(f"expected {expected} unique species, found {len(seen)}")
    out.sort(key=lambda r:r["species"])
    receipt={
      "schema":"structural.sw_finland_potential_islands_lookup_result.v1_168",
      "status":"T0_SOURCE_COUNT_LOOKUP_VALIDATED_NO_FUTURE_SUMMARIES_PERSISTED",
      "candidate_id":contract["candidate_id"],
      "source_projection_sha256":sha256_file(path),
      "species_count":len(out),
      "minimum_potential_islands":min(r["Potential_islands"] for r in out),
      "maximum_potential_islands":max(r["Potential_islands"] for r in out),
      "species_with_zero_historical_sources":sum(r["historical_source_count"]==0 for r in out),
      "future_summary_columns_present_in_input":False,
      "future_summary_values_persisted":0,
      "row_level_recent_outcome_opened":False,
      "counts_as_empirical_evidence":False
    }
    return out,receipt

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("lookup_csv",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--canonical-output",type=Path);ap.add_argument("--receipt",type=Path)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text());rows,r=validate(a.lookup_csv,c);code=0
        if a.canonical_output:
            a.canonical_output.parent.mkdir(parents=True,exist_ok=True)
            with a.canonical_output.open("w",encoding="utf-8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["species","Potential_islands","historical_source_count"],lineterminator="\n")
                w.writeheader();w.writerows(rows)
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={"schema":"structural.sw_finland_potential_islands_lookup_result.v1_168",
           "status":"STOP_SUPPLEMENTARY_LOOKUP","reason":str(exc),
           "future_summary_values_persisted":0,"row_level_recent_outcome_opened":False,
           "counts_as_empirical_evidence":False};code=2
    txt=json.dumps(r,indent=2,sort_keys=True)+"\n"
    if a.receipt:
        a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(txt,encoding="utf-8")
    print(txt,end="");return code
if __name__=="__main__":raise SystemExit(main())
