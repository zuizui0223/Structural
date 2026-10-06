#!/usr/bin/env python3
"""Aggregate-only t0 diagnostic for Historical_total_log missingness."""
from __future__ import annotations
import argparse,csv,json,math
from collections import Counter,defaultdict
from pathlib import Path

ANCHORS=[
 "Anchusa arvensis","Agrostis stolonifera","Acer platanoides",
 "Allium schoenoprasum","Aster tripolium","Atriplex prostrata",
 "Achillea millefolium"
]

def main():
    p=argparse.ArgumentParser();p.add_argument("safe_csv",type=Path);p.add_argument("--receipt",type=Path,required=True);a=p.parse_args()
    tokens={};counts=Counter();pairs=set();rows=0
    with a.safe_csv.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        assert rd.fieldnames and "outcome" not in rd.fieldnames
        for r in rd:
            rows+=1;sp=r["spp.name"].strip();isl=r["holmkod"].strip();key=(sp,isl)
            if key in pairs:raise SystemExit("duplicate pair")
            pairs.add(key);counts[sp]+=1
            tok=r["Historical_total_log"].strip()
            if sp in tokens and tokens[sp]!=tok:raise SystemExit(f"token drift {sp}")
            tokens[sp]=tok
    numeric={};nonnumeric={}
    raw_hist=Counter()
    for sp,tok in tokens.items():
        try:z=float(tok);ok=math.isfinite(z)
        except ValueError:ok=False
        if ok:numeric[sp]=z
        else:
            nonnumeric[sp]=tok
            raw_hist[tok]+=1
    result={
      "schema":"structural.sw_finland_historical_total_missingness_diagnostic.v1_170_1",
      "status":"T0_AGGREGATE_DIAGNOSTIC_COMPLETE",
      "rows":rows,"species":len(tokens),
      "numeric_species":len(numeric),"nonnumeric_species":len(nonnumeric),
      "nonnumeric_token_histogram":dict(sorted(raw_hist.items())),
      "nonnumeric_with_471_archived_absences":sum(counts[sp]==471 for sp in nonnumeric),
      "nonnumeric_not_471_archived_absences":sum(counts[sp]!=471 for sp in nonnumeric),
      "nonnumeric_absence_count_min":min((counts[sp] for sp in nonnumeric),default=None),
      "nonnumeric_absence_count_max":max((counts[sp] for sp in nonnumeric),default=None),
      "anchors":{
        sp:{
          "Historical_total_log_token":tokens.get(sp),
          "numeric":sp in numeric,
          "archived_absent_count":counts.get(sp)
        } for sp in ANCHORS
      },
      "future_outcome_values_opened":0,
      "protected_outcome_values_decoded":0,
      "counts_as_empirical_evidence":False
    }
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
