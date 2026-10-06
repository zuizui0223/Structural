#!/usr/bin/env python3
"""Audit SW Finland t0 source-count support from safe projection only.

This diagnostic reads no future outcome. It counts archived historical-absence
rows per species and tests the prospectively documented inversion of
Historical_total_log. It emits aggregate support only and does not construct
historical occupied source identities.
"""
from __future__ import annotations
import argparse,csv,json,math
from collections import Counter
from pathlib import Path

class Stop(RuntimeError): pass

def inv(x,tol=1e-6):
    try:z=float(str(x).strip())
    except ValueError:return None
    if not math.isfinite(z):return None
    raw=10.0**z-1.0;n=int(round(raw))
    if 0<=n<=471 and abs(raw-n)<=tol*max(1.0,abs(raw)): return n
    return None

def audit(path:Path,router:dict):
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE": raise Stop("router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0: raise Stop("future endpoint boundary violated")
    counts=Counter();hist={}
    islands=set();rows=0
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None:raise Stop("safe projection missing header")
        if "outcome" in rd.fieldnames:raise Stop("outcome leaked")
        for key in ("spp.name","holmkod","Historical_total_log"):
            if key not in rd.fieldnames:raise Stop(f"missing {key}")
        for row in rd:
            rows+=1;sp=str(row["spp.name"]).strip();isl=str(row["holmkod"]).strip()
            if not sp or not isl:raise Stop("blank routing key")
            counts[sp]+=1;islands.add(isl)
            v=str(row["Historical_total_log"]).strip()
            if sp in hist and hist[sp]!=v:raise Stop(f"Historical_total_log drift within {sp}")
            hist[sp]=v
    exact=0;incomplete=0;impossible=0;zero=0;unresolved=0
    n_hist=Counter()
    for sp,n_abs in counts.items():
        n=inv(hist[sp])
        if n is None:unresolved+=1;continue
        n_hist[n]+=1
        if n==0:zero+=1
        total=n_abs+n
        if total==471 and n>=1:exact+=1
        elif total<471:incomplete+=1
        else:impossible+=1
    return {
      "schema":"structural.sw_finland_t0_source_count_support_audit.v1_169",
      "status":("DIRECT_LOG_INVERSION_SUPPORTS_EXACT_SOURCE_GATE" if exact>=30 and impossible==0 else "DIRECT_LOG_INVERSION_INSUFFICIENT_USE_FROZEN_SUPPLEMENT_LOOKUP"),
      "archived_event_rows":rows,
      "archive_species_count":len(counts),
      "unique_island_count":len(islands),
      "direct_inversion_exact_source_species":exact,
      "direct_inversion_incomplete_species":incomplete,
      "direct_inversion_impossible_species":impossible,
      "direct_inversion_zero_source_species":zero,
      "direct_inversion_unresolved_species":unresolved,
      "direct_inversion_source_count_histogram":{str(k):n_hist[k] for k in sorted(n_hist)},
      "minimum_exact_species_required":30,
      "supplement_lookup_required":not(exact>=30 and impossible==0),
      "protected_field_values_decoded":0,
      "outcome_values_read":0,
      "future_outcome_opened":False,
      "counts_as_empirical_evidence":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("safe_csv",type=Path);p.add_argument("--router-receipt",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True);a=p.parse_args()
    router=json.loads(a.router_receipt.read_text());r=audit(a.safe_csv,router)
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
