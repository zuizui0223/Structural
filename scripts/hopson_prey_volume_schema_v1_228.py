#!/usr/bin/env python3
"""v1.228: MD5-locked sample/dilution metadata-only audit after v1.227 STOP.

Parses ONLY samp.vol, dil.vol, sub.samp.vol from the already published
observation CSV; does not interpret eupl, tet, outcome, or prediction fields.
Does NOT rerun the failed v1.227 model or amend its contract.
"""
import argparse
import json
import math
from collections import Counter
from pathlib import Path

from hopson_temporal_detection_audit_v1_222 import (
    download_locked, rows_locked, OBS_HEADER,
)

EXPECTED=4830
def classify(sample,dilution,subsample):
    vals=(sample,dilution,subsample)
    if any(not math.isfinite(v) for v in vals):
        return "invalid_nonfinite"
    if sample<=0 or dilution<0 or subsample<0:
        return "invalid_volume"
    if dilution==0 and subsample==0:
        return "both_zero_undiluted"
    if dilution>0 and subsample>0:
        return "both_positive_diluted"
    if dilution>0 and subsample==0:
        return "dilution_positive_subsample_zero"
    if dilution==0 and subsample>0:
        return "dilution_zero_subsample_positive"
    raise AssertionError("Unrecognized nonnegative flags")

def audit(raw):
    counts=Counter()
    combinations=Counter()
    total=0
    for row in rows_locked(raw,OBS_HEADER):
        # Do not decode eupl or tet; these are already exposed, but irrelevant.
        samp=float(row["samp.vol"])
        dil=float(row["dil.vol"])
        sub=float(row["sub.samp.vol"])
        label=classify(samp,dil,sub)
        counts[label]+=1
        combinations[(format(dil,'.12g'),format(sub,'.12g'))]+=1
        total+=1
    if total!=EXPECTED:
        raise ValueError("Published 4,830 row source identity changed")
    contract_allowed=counts["both_zero_undiluted"]+counts["both_positive_diluted"]
    discordant=total-contract_allowed
    return {
      "schema":"structural.hopson_prey_volume_schema_only.v1_228",
      "status":("STOP_V227_ASSAY_DOMAIN_MISMATCH" if discordant
                else "PASS_VOLUME_FLAG_SCHEMA_ONLY_NO_PREDICTION_AUTHORITY"),
      "original_v227_fail_closed":True,
      "n_published_rows":total,
      "assay_flag_category_counts":dict(sorted(counts.items())),
      "distinct_volume_flag_combinations":len(combinations),
      "dilution_subsample_pairs":[
          {"dil_vol_ml":a,"sub_samp_vol_ml":b,"rows":v}
          for (a,b),v in sorted(combinations.items(),
              key=lambda kv:(-kv[1],kv[0]))
      ],
      "rows_matching_v227_frozen_undiluted_or_diluted_rules":contract_allowed,
      "rows_outside_v227_frozen_rules":discordant,
      "author_R_fallback_if_subsample_zero_may_differ_from_v227_domain":True,
      "only_volume_metadata_semantically_read":True,
      "raw_eupl_tet_values_used":False,
      "prey_model_replayed":False,
      "future_response_or_mammal_heldout_reopened":False,
      "new_confirmatory_evidence":False,
      "GEB_scientific_HOLD":True,
      "eBird_used":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    ans=audit(download_locked("observations"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(ans,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(ans,sort_keys=True))
    # Scientific assay mismatch status is a *valid receipt* and not a technical
    # workflow failure. No 227 score is emitted under either status.
if __name__=="__main__":
    main()
