#!/usr/bin/env python3
"""Diagnose Historical_total_log tokens from t0-safe SW Finland projection only."""
from __future__ import annotations
import argparse,csv,json,math,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

def norm(x:str)->str:
    return unicodedata.normalize("NFC",str(x)).strip()

def diagnose(path:Path,anchors:set[str])->dict:
    token_counts=Counter();numeric_by_species=defaultdict(set);missing_by_species=Counter()
    rows_by_species=Counter();rows=0
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:
            raise RuntimeError("unsafe t0 projection")
        for key in ("spp.name","Historical_total_log"):
            if key not in rd.fieldnames:raise RuntimeError(f"missing {key}")
        for row in rd:
            rows+=1;sp=norm(row["spp.name"]);tok=str(row["Historical_total_log"]).strip()
            rows_by_species[sp]+=1;token_counts[tok]+=1
            try:v=float(tok)
            except ValueError:
                missing_by_species[sp]+=1;continue
            if not math.isfinite(v):
                missing_by_species[sp]+=1;continue
            numeric_by_species[sp].add(v)
    species=set(rows_by_species)
    multiple={sp:sorted(vals) for sp,vals in numeric_by_species.items() if len(vals)>1}
    no_numeric=sorted(sp for sp in species if not numeric_by_species.get(sp))
    one_numeric=sorted(sp for sp in species if len(numeric_by_species.get(sp,set()))==1)
    anchor={}
    for sp in sorted(anchors):
        vals=sorted(numeric_by_species.get(sp,set()))
        anchor[sp]={
          "row_count":rows_by_species.get(sp,0),
          "missing_or_nonfinite_rows":missing_by_species.get(sp,0),
          "numeric_unique_count":len(vals),
          "numeric_values_hex":[float(v).hex() for v in vals],
        }
    return {
      "schema":"structural.sw_finland_historical_total_diagnostic.v1_170_2",
      "status":"T0_HISTORICAL_TOTAL_TOKEN_DIAGNOSTIC",
      "rows":rows,
      "species":len(species),
      "numeric_token_rows":sum(len_vals for tok,len_vals in token_counts.items() if _finite(tok)),
      "nonnumeric_token_rows":sum(len_vals for tok,len_vals in token_counts.items() if not _finite(tok)),
      "nonnumeric_token_histogram":{tok:n for tok,n in token_counts.items() if not _finite(tok)},
      "species_with_exactly_one_numeric_value":len(one_numeric),
      "species_with_no_numeric_value":len(no_numeric),
      "species_with_multiple_numeric_values":len(multiple),
      "species_no_numeric":no_numeric,
      "species_multiple_numeric_hex":{sp:[float(v).hex() for v in vals] for sp,vals in multiple.items()},
      "anchors":anchor,
      "future_outcome_values_opened":0,
      "protected_outcome_values_decoded":0,
      "counts_as_empirical_evidence":False
    }

def _finite(tok:str)->bool:
    try:v=float(tok)
    except ValueError:return False
    return math.isfinite(v)

def main():
    p=argparse.ArgumentParser();p.add_argument("safe_csv",type=Path);p.add_argument("--anchor-contract",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    c=json.loads(a.anchor_contract.read_text())
    anchors=set(c["anchor_checks"])
    r=diagnose(a.safe_csv,anchors)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
